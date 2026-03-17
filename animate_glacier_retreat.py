"""
Animate Dixon Glacier retreat from WY2000 through WY2100.

Runs the MAP parameter set through two phases:
  1. Historical (WY2000–2025): observed gap-filled climate, shared by both panels
  2. Projected (WY2026–2100): CMIP6 forcing, SSP2-4.5 vs SSP5-8.5 side-by-side

Geometry evolves continuously via delta-h (Huss et al. 2010) from the 2010
DEM/outline, giving 100 years of glacier evolution in one animation.

Output: projection_output/<run_dir>/glacier_retreat.mp4 + .gif

Usage:
    python animate_glacier_retreat.py [output_dir]
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.animation import FuncAnimation, FFMpegWriter
from pathlib import Path
import json
import time
import sys

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')


def hillshade(elevation, azimuth=315, altitude=35):
    """Compute hillshade from elevation grid."""
    az_rad = np.radians(azimuth)
    alt_rad = np.radians(altitude)
    dy, dx = np.gradient(elevation)
    slope = np.arctan(np.sqrt(dx**2 + dy**2))
    aspect = np.arctan2(-dx, dy)
    hs = (np.sin(alt_rad) * np.cos(slope) +
          np.cos(alt_rad) * np.sin(slope) * np.cos(az_rad - aspect))
    return np.clip(hs, 0, 1)


def _run_single_trajectory(fmodel, obs_df, gcm_climate, ice_thickness_init,
                           bedrock, grid, params, routing_params,
                           wy_start=2000, wy_end=2100, wy_split=2025):
    """Run one parameter set from wy_start to wy_end with continuous geometry.

    Returns dict with per-year scalars and per-year spatial arrays.
    """
    from dixon_melt.glacier_dynamics import apply_deltah
    from dixon_melt.routing import route_linear_reservoirs
    from dixon_melt.climate_projections import extract_water_year

    cell_size = grid['cell_size']
    current_elev = grid['elevation'].copy()
    current_mask = grid['glacier_mask'].copy()
    ice_thickness = ice_thickness_init.copy()

    years = []
    thickness_snaps = []
    mask_snaps = []
    area_list = []
    vol_list = []
    mb_list = []
    mean_thick_list = []
    peak_q_list = []
    mean_q_list = []
    cum_balance = 0.0

    for wy_year in range(wy_start, wy_end + 1):
        n_glacier = int(current_mask.sum())
        if n_glacier == 0:
            # Glacier gone — fill remaining years with zeros
            for fill_yr in range(wy_year, wy_end + 1):
                years.append(fill_yr)
                thickness_snaps.append(np.zeros_like(ice_thickness))
                mask_snaps.append(np.zeros_like(current_mask))
                area_list.append(0.0)
                vol_list.append(0.0)
                mb_list.append(0.0)
                mean_thick_list.append(0.0)
                peak_q_list.append(0.0)
                mean_q_list.append(0.0)
            break

        glacier_thick = ice_thickness[current_mask]
        area_km2 = n_glacier * cell_size**2 / 1e6
        area_m2 = n_glacier * cell_size**2
        vol_km3 = glacier_thick.sum() * cell_size**2 / 1e9

        years.append(wy_year)
        thickness_snaps.append(ice_thickness.copy())
        mask_snaps.append(current_mask.copy())
        area_list.append(area_km2)
        vol_list.append(vol_km3)
        mean_thick_list.append(float(glacier_thick.mean()))

        # Select climate source
        if wy_year <= wy_split:
            wy_climate = extract_water_year(obs_df, wy_year)
        else:
            wy_climate = extract_water_year(gcm_climate, wy_year)

        if wy_climate is None:
            mb_list.append(0.0)
            peak_q_list.append(0.0)
            mean_q_list.append(0.0)
            continue

        T = wy_climate['temperature'].values.astype(np.float64)
        P = wy_climate['precipitation'].values.astype(np.float64)
        doy = np.array(wy_climate.index.dayofyear, dtype=np.int64)

        fmodel.update_geometry(current_elev, current_mask)
        r = fmodel.run(T, P, doy, params, 0.0)
        mb = r['glacier_wide_balance']
        cum_balance += mb
        mb_list.append(mb)

        # Route discharge
        Q_total, _, _, _ = route_linear_reservoirs(
            r['daily_runoff'], area_m2,
            routing_params['k_fast'], routing_params['k_slow'],
            routing_params['k_gw'], routing_params['f_fast'],
            routing_params['f_slow'],
        )
        peak_q_list.append(float(Q_total.max()))
        mean_q_list.append(float(Q_total.mean()))

        current_elev, current_mask, _ = apply_deltah(
            current_elev, current_mask, ice_thickness, bedrock,
            mb, cell_size,
        )

    return {
        'years': years,
        'thickness': thickness_snaps,
        'mask': mask_snaps,
        'area_km2': area_list,
        'volume_km3': vol_list,
        'glacier_wide_balance': mb_list,
        'mean_thickness_m': mean_thick_list,
        'peak_discharge_m3s': peak_q_list,
        'mean_discharge_m3s': mean_q_list,
    }


def run_continuous_projection(scenario, gcm_name=None, n_top=250):
    """Run WY2000–2100 ensemble: historical observed, then CMIP6 projected.

    Runs all n_top parameter sets independently (each with its own geometry
    evolution), then averages snapshots (thickness, mask fraction, stats)
    across the ensemble.

    Returns (results_dict, grid, ice_thickness_init).
    """
    from run_projection import (
        load_top_param_sets, DEM_PATH, GLACIER_PATH, CLIMATE_PATH,
        CMIP6_DIR, FARINOTTI_PATH,
    )
    from dixon_melt.terrain import prepare_grid
    from dixon_melt.model import precompute_ipot
    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config
    from dixon_melt.glacier_dynamics import (
        initialize_ice_thickness, compute_bedrock,
    )
    from dixon_melt.climate_projections import prepare_gcm_ensemble

    # Load all parameter sets
    param_sets = load_top_param_sets(n_top=n_top)
    n_params = len(param_sets)

    # Grid & model setup
    grid = prepare_grid(str(DEM_PATH), str(GLACIER_PATH), target_res=100.0)
    print("  Precomputing I_pot...")
    ipot_table = precompute_ipot(grid, doy_range=range(1, 366), dt_hours=3.0)

    fmodel = FastDETIM(
        grid, ipot_table,
        transfer_alpha=config.TRANSFER_ALPHA,
        transfer_beta=config.TRANSFER_BETA,
        ref_elev=config.SNOTEL_ELEV,
        stake_names=config.STAKE_NAMES,
        stake_elevs=config.STAKE_ELEVS,
    )

    farinotti = str(FARINOTTI_PATH) if FARINOTTI_PATH.exists() else None
    ice_thickness_init, _ = initialize_ice_thickness(grid, farinotti_path=farinotti)
    bedrock = compute_bedrock(grid['elevation'], ice_thickness_init)
    routing_params = config.DEFAULT_ROUTING

    # Load observed climate (WY2000–2025)
    obs_df = pd.read_csv(CLIMATE_PATH, parse_dates=['date'], index_col='date')
    obs_df = obs_df[['temperature', 'precipitation']].copy()

    # Load GCM climate (WY2026–2100)
    print(f"  Loading CMIP6 ensemble for {scenario}...")
    ensemble = prepare_gcm_ensemble(
        str(CMIP6_DIR), str(CLIMATE_PATH), scenario)

    if gcm_name is None:
        gcm_name = 'EC-Earth3'
    if gcm_name not in ensemble:
        gcm_name = list(ensemble.keys())[0]
    gcm_climate = ensemble[gcm_name]

    print(f"  Running WY2000–2100 / {scenario} / {gcm_name}")
    print(f"  Ensemble: {n_params} parameter sets")
    t0 = time.time()

    # Run all parameter sets
    all_traj = []
    for pi, params in enumerate(param_sets):
        traj = _run_single_trajectory(
            fmodel, obs_df, gcm_climate, ice_thickness_init, bedrock,
            grid, params, routing_params,
        )
        all_traj.append(traj)

        if (pi + 1) % max(1, n_params // 5) == 0 or pi == 0:
            a = traj['area_km2'][-1]
            print(f"    [{pi+1}/{n_params}]  final area={a:.1f} km²")

    dt_runs = time.time() - t0
    print(f"  All {n_params} runs done in {dt_runs:.0f}s "
          f"({dt_runs / n_params:.1f}s/run)")

    # Average snapshots across ensemble
    n_years = len(all_traj[0]['years'])
    grid_shape = grid['elevation'].shape

    results = {
        'year': all_traj[0]['years'],
        'glacier_wide_balance': [],
        'area_km2': [],
        'volume_km3': [],
        'mean_thickness_m': [],
        'cum_balance': [],
        'peak_discharge_m3s': [],
        'mean_discharge_m3s': [],
        'snapshots': [],
        'phase': [],
    }

    cum_balance = 0.0
    for yi in range(n_years):
        wy = all_traj[0]['years'][yi]

        # Collect spatial arrays from all ensemble members
        thick_stack = np.array([t['thickness'][yi] for t in all_traj])
        mask_stack = np.array([t['mask'][yi] for t in all_traj])

        # Mean thickness and ice fraction across ensemble
        mean_thickness = thick_stack.mean(axis=0)
        ice_fraction = mask_stack.astype(np.float64).mean(axis=0)

        # Ensemble mask: cell is glacierized if >50% of runs have ice
        ens_mask = ice_fraction > 0.5

        # Mean scalar stats
        mean_area = float(np.mean([t['area_km2'][yi] for t in all_traj]))
        mean_vol = float(np.mean([t['volume_km3'][yi] for t in all_traj]))
        mean_mb = float(np.mean([t['glacier_wide_balance'][yi]
                                 for t in all_traj]))
        mean_ht = float(np.mean([t['mean_thickness_m'][yi]
                                 for t in all_traj]))
        cum_balance += mean_mb

        mean_peak_q = float(np.mean([t['peak_discharge_m3s'][yi]
                                      for t in all_traj]))
        mean_mean_q = float(np.mean([t['mean_discharge_m3s'][yi]
                                     for t in all_traj]))

        results['glacier_wide_balance'].append(mean_mb)
        results['area_km2'].append(mean_area)
        results['volume_km3'].append(mean_vol)
        results['mean_thickness_m'].append(mean_ht)
        results['cum_balance'].append(cum_balance)
        results['peak_discharge_m3s'].append(mean_peak_q)
        results['mean_discharge_m3s'].append(mean_mean_q)
        results['phase'].append('observed' if wy <= 2025 else 'projected')

        results['snapshots'].append({
            'year': wy,
            'mask': ens_mask,
            'thickness': mean_thickness,
            'ice_fraction': ice_fraction,
        })

        if wy % 10 == 0 or wy == 2025:
            phase = 'observed' if wy <= 2025 else 'projected'
            print(f"    WY{wy} [{phase:9s}]  "
                  f"area={mean_area:.1f} km²  vol={mean_vol:.3f} km³  "
                  f"MB={mean_mb:+.2f}")

    dt = time.time() - t0
    print(f"  Done in {dt:.0f}s, {len(results['snapshots'])} snapshots")

    return results, grid, ice_thickness_init


def create_animation(snapshots_245, snapshots_585, grid, ice_thickness_init,
                     results_245, results_585, output_path, fps=4):
    """Create retreat animation: maps, area bars, discharge plots, colorbar.

    Layout (top to bottom):
      - Year title + phase label
      - SSP2-4.5 map  |  SSP5-8.5 map  (with stats overlay)
      - Area bar left  |  Area bar right
      - Discharge plot left  |  Discharge plot right
      - Ice thickness colorbar

    During WY2000–2025, both panels are identical. After WY2025 they diverge.
    """
    elev = grid['elevation']
    nodata_mask = elev < 1
    hs = hillshade(np.where(nodata_mask, np.nan, elev))

    init_mask = grid['glacier_mask']
    init_area = float(init_mask.sum()) * grid['cell_size']**2 / 1e6
    init_vol = float(ice_thickness_init[init_mask].sum()) * grid['cell_size']**2 / 1e9
    max_thick = float(ice_thickness_init.max())

    rows = np.where(init_mask.any(axis=1))[0]
    cols = np.where(init_mask.any(axis=0))[0]
    pad = 8
    r0 = max(0, rows[0] - pad)
    r1 = min(elev.shape[0], rows[-1] + pad + 1)
    c0 = max(0, cols[0] - pad)
    c1 = min(elev.shape[1], cols[-1] + pad + 1)

    ice_cmap = plt.colormaps['YlGnBu']
    ice_norm = mcolors.Normalize(vmin=0, vmax=max_thick * 0.85)
    n_snap = min(len(snapshots_245), len(snapshots_585))

    hs_crop = hs[r0:r1, c0:c1]
    elev_crop = elev[r0:r1, c0:c1]

    all_snapshots = [snapshots_245, snapshots_585]
    all_results = [results_245, results_585]

    ssp_colors = ['#1b9e77', '#d95f02']
    ssp_labels = ['SSP2-4.5 (moderate)', 'SSP5-8.5 (high emissions)']
    bg = '#1a1a2e'

    # Precompute smoothed discharge
    years_arr = np.array(results_245['year'])
    q_raw = [np.array(results_245['mean_discharge_m3s']),
             np.array(results_585['mean_discharge_m3s'])]

    window = 11
    kernel = np.ones(window) / window
    q_smooth = []
    for q in q_raw:
        if len(q) >= window:
            qs = np.convolve(q, kernel, mode='same')
            for k in range(window // 2):
                qs[k] = q[:2*k+1].mean()
                qs[-(k+1)] = q[-(2*k+1):].mean()
        else:
            qs = q.copy()
        q_smooth.append(qs)

    q_max = max(q_smooth[0].max(), q_smooth[1].max()) * 1.15

    def _build_and_animate(figsize, font_scale, full_stats, render_func):
        s = font_scale

        fig = plt.figure(figsize=figsize, facecolor=bg)

        # Use gridspec: maps (row 0), discharge (row 1)
        gs = fig.add_gridspec(2, 2, height_ratios=[2.2, 1],
                              left=0.05, right=0.95, top=0.84, bottom=0.10,
                              wspace=0.06, hspace=0.28)

        map_axes = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])]
        q_axes = [fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])]

        im_layers = []
        stat_texts = []
        area_bars = []
        q_lines = []
        q_dots = []

        for i, ax in enumerate(map_axes):
            ax.set_facecolor('#2d2d44')
            ax.imshow(hs_crop, cmap='gray', vmin=0.2, vmax=1.0,
                      alpha=0.6, interpolation='bilinear')
            valid = np.where(elev_crop < 1, np.nan, elev_crop)
            ax.contour(valid, levels=np.arange(200, 1800, 100),
                       colors='#555555', linewidths=0.3, alpha=0.4)

            blank = np.full_like(hs_crop, np.nan)
            im = ax.imshow(blank, cmap=ice_cmap, norm=ice_norm,
                           interpolation='nearest', alpha=0.9)
            im_layers.append(im)
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_title(ssp_labels[i], color=ssp_colors[i],
                         fontsize=int(16 * s), fontweight='bold', pad=8)

            st = ax.text(0.03, 0.97, '', transform=ax.transAxes,
                         fontsize=int(11 * s), color='white', va='top',
                         fontfamily='monospace',
                         bbox=dict(boxstyle='round,pad=0.4',
                                   facecolor=bg, alpha=0.85,
                                   edgecolor='#555555'))
            stat_texts.append(st)

            # Area bar (below each map)
            bar_pos = ax.get_position()
            bar_ax = fig.add_axes([bar_pos.x0, bar_pos.y0 - 0.025,
                                   bar_pos.width, 0.015])
            bar_ax.set_xlim(0, init_area)
            bar_ax.set_facecolor('#2d2d44')
            bar_ax.tick_params(colors='white', labelsize=int(8 * s))
            bar_ax.set_xlabel('Area (km²)', color='white',
                              fontsize=int(9 * s))
            bar_ax.spines['bottom'].set_color('#555555')
            bar_ax.spines['top'].set_visible(False)
            bar_ax.spines['right'].set_visible(False)
            bar_ax.spines['left'].set_visible(False)
            bar = bar_ax.barh(0, init_area, height=0.6,
                              color=ssp_colors[i], alpha=0.8)
            area_bars.append((bar_ax, bar))

        # Discharge time series (one per SSP, below each map)
        for i, qax in enumerate(q_axes):
            qax.set_facecolor('#2d2d44')
            # Faded full curve as background
            qax.plot(years_arr, q_smooth[i], color=ssp_colors[i],
                     alpha=0.2, linewidth=1.5)
            # Observed/projected boundary
            qax.axvline(2025.5, color='#555555', linestyle='--',
                        linewidth=0.7, alpha=0.5)
            # Animated line
            line, = qax.plot([], [], color=ssp_colors[i], linewidth=2.5)
            q_lines.append(line)
            # Current year dot
            dot, = qax.plot([], [], 'o', color=ssp_colors[i], markersize=7,
                            markeredgecolor='white', markeredgewidth=1.5,
                            zorder=5)
            q_dots.append(dot)

            qax.set_xlim(years_arr[0] - 1, years_arr[-1] + 1)
            qax.set_ylim(0, q_max)
            if i == 0:
                qax.set_ylabel('Discharge (m³/s)', color='white',
                               fontsize=int(10 * s))
            qax.set_xlabel('Water Year', color='white',
                           fontsize=int(9 * s))
            qax.tick_params(colors='white', labelsize=int(8 * s))
            qax.spines['bottom'].set_color('#555555')
            qax.spines['left'].set_color('#555555')
            qax.spines['top'].set_visible(False)
            qax.spines['right'].set_visible(False)

        # Ice thickness colorbar at the very bottom
        cbar_ax = fig.add_axes([0.25, 0.03, 0.50, 0.015])
        cb = fig.colorbar(im_layers[0], cax=cbar_ax,
                          orientation='horizontal')
        cbar_ax.set_xlabel('Ice Thickness (m)', color='white',
                           fontsize=int(11 * s), labelpad=5)
        cb.ax.tick_params(colors='white', labelsize=int(9 * s))
        cbar_ax.spines['top'].set_color('#555555')
        cbar_ax.spines['bottom'].set_color('#555555')

        # Year + phase text
        year_text = fig.text(0.5, 0.91, '', ha='center', va='bottom',
                             fontsize=int(28 * s), fontweight='bold',
                             color='white', fontfamily='monospace')
        phase_text = fig.text(0.5, 0.875, '', ha='center', va='bottom',
                              fontsize=int(14 * s), color='#aaaaaa',
                              fontfamily='monospace', style='italic')

        def update(frame):
            wy = all_snapshots[0][frame]['year']
            is_hist = wy <= 2025

            for i in range(2):
                snap = all_snapshots[i][frame]
                mask_crop = snap['mask'][r0:r1, c0:c1]
                thick_crop = snap['thickness'][r0:r1, c0:c1].copy()
                thick_display = np.where(mask_crop, thick_crop, np.nan)
                im_layers[i].set_data(thick_display)

                res = all_results[i]
                idx = min(frame, len(res['year']) - 1)
                area = res['area_km2'][idx]
                vol = res['volume_km3'][idx]
                pct_area = 100 * area / init_area
                pct_vol = 100 * vol / init_vol

                if full_stats:
                    mb = res['glacier_wide_balance'][idx]
                    thick_mean = res['mean_thickness_m'][idx]
                    stat_texts[i].set_text(
                        f"Area:  {area:6.1f} km²  ({pct_area:.0f}%)\n"
                        f"Vol:   {vol:6.3f} km³  ({pct_vol:.0f}%)\n"
                        f"H̄:     {thick_mean:6.0f} m\n"
                        f"Bal:   {mb:+6.2f} m w.e."
                    )
                else:
                    stat_texts[i].set_text(
                        f"Area: {area:.1f} km² ({pct_area:.0f}%)\n"
                        f"Vol:  {vol:.3f} km³ ({pct_vol:.0f}%)"
                    )

                bar_ax, bar = area_bars[i]
                bar[0].set_width(area)

                # Update discharge line
                x_data = years_arr[:idx+1]
                q_lines[i].set_data(x_data, q_smooth[i][:idx+1])
                q_dots[i].set_data([years_arr[idx]],
                                   [q_smooth[i][idx]])

            year_text.set_text(f"WY {wy}")
            if is_hist:
                phase_text.set_text('Observed Climate')
                phase_text.set_color('#88ccff')
            else:
                phase_text.set_text('CMIP6 Projected')
                phase_text.set_color('#ffcc88')

            return (im_layers + stat_texts + q_lines + q_dots +
                    [year_text, phase_text])

        anim = FuncAnimation(fig, update, frames=n_snap,
                             interval=1000 // fps, blit=False)
        render_func(fig, anim)
        plt.close(fig)

    # ── MP4 ──────────────────────────────────────────────────────────
    print(f"\n  Rendering MP4 ({n_snap} frames)...")

    def render_mp4(fig, anim):
        writer = FFMpegWriter(fps=fps, bitrate=4000,
                              metadata={'title': 'Dixon Glacier Retreat WY2000-2100'})
        anim.save(str(output_path), writer=writer, dpi=120)
        print(f"  Saved: {output_path}")

    _build_and_animate((16, 16), 1.0, True, render_mp4)

    # ── GIF ──────────────────────────────────────────────────────────
    gif_path = output_path.with_suffix('.gif')
    print(f"  Rendering GIF...")

    def render_gif(fig, anim):
        anim.save(str(gif_path), writer='pillow', fps=fps, dpi=80)
        print(f"  Saved: {gif_path}")

    _build_and_animate((14, 14), 0.85, False, render_gif)

    # ── Key frame PNGs ───────────────────────────────────────────────
    key_years = [2000, 2010, 2025, 2050, 2075, 2100]
    snap_years = [s['year'] for s in snapshots_245]

    for ky in key_years:
        if ky in snap_years:
            fidx = snap_years.index(ky)

            def render_png(fig, anim, _ky=ky, _fidx=fidx):
                anim._func(_fidx)
                frame_path = output_path.parent / f'frame_{_ky}.png'
                fig.savefig(str(frame_path), dpi=150,
                            facecolor=fig.get_facecolor())
                print(f"  Saved: {frame_path.name}")

            _build_and_animate((16, 16), 1.0, True, render_png)


def main():
    from run_projection import OUTPUT_BASE, create_run_dir

    if len(sys.argv) > 1:
        output_dir = Path(sys.argv[1])
    else:
        output_dir = create_run_dir(1, ['ssp245', 'ssp585'],
                                    label='animation-2000-2100')

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output: {output_dir.name}/")

    # Run both scenarios with continuous history + projection
    print("\n--- SSP2-4.5 (WY2000–2100) ---")
    r245, grid, ice_init = run_continuous_projection('ssp245')

    print("\n--- SSP5-8.5 (WY2000–2100) ---")
    r585, _, _ = run_continuous_projection('ssp585')

    output_path = output_dir / 'glacier_retreat.mp4'
    create_animation(
        r245['snapshots'], r585['snapshots'],
        grid, ice_init,
        r245, r585,
        output_path, fps=4,
    )

    print(f"\nAll outputs in {output_dir}/")


if __name__ == '__main__':
    main()
