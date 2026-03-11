"""
Animate Dixon Glacier retreat under SSP2-4.5 and SSP5-8.5.

Runs the best (MAP) parameter set with the ensemble-median GCM for each
scenario, saving yearly spatial snapshots. Then renders a side-by-side
animation showing ice thickness on a hillshaded DEM with live stats.

Output: projection_output/<run_dir>/glacier_retreat.mp4

Usage:
    python animate_glacier_retreat.py [output_dir]
"""
import numpy as np
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


def run_snapshot_projection(scenario, gcm_name=None):
    """Run a single projection saving yearly spatial snapshots."""
    from run_projection import (
        load_top_param_sets, run_single_gcm,
        DEM_PATH, GLACIER_PATH, NUKA_PATH, CMIP6_DIR, FARINOTTI_PATH,
    )
    from dixon_melt.terrain import prepare_grid
    from dixon_melt.model import precompute_ipot
    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config
    from dixon_melt.glacier_dynamics import initialize_ice_thickness, compute_bedrock
    from dixon_melt.climate_projections import prepare_gcm_ensemble

    # Use the single best parameter set (MAP)
    param_sets = load_top_param_sets(n_top=1)
    params = param_sets[0]

    # Grid
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
    ice_thickness, _ = initialize_ice_thickness(grid, farinotti_path=farinotti)
    bedrock = compute_bedrock(grid['elevation'], ice_thickness)

    # Climate
    ensemble = prepare_gcm_ensemble(
        str(CMIP6_DIR), str(NUKA_PATH), scenario)

    if gcm_name is None:
        # Pick the "middle" GCM by end-of-century area from PROJ-002
        gcm_name = 'EC-Earth3'
    if gcm_name not in ensemble:
        gcm_name = list(ensemble.keys())[0]

    gcm_climate = ensemble[gcm_name]
    routing_params = config.DEFAULT_ROUTING

    print(f"  Running {scenario} / {gcm_name} with snapshots...")
    t0 = time.time()
    results = run_single_gcm(
        fmodel, gcm_climate, ice_thickness, bedrock, grid,
        params, routing_params, 2026, 2100, gcm_name,
        save_snapshots=True,
    )
    print(f"  Done in {time.time() - t0:.0f}s, {len(results['snapshots'])} snapshots")

    return results, grid, ice_thickness


def _build_figure(hs_crop, elev_crop, ice_cmap, ice_norm, init_area,
                  figsize=(16, 11), font_scale=1.0):
    """Build the animation figure with all static elements.

    Returns (fig, im_layers, stat_texts, area_bars, year_text) — the
    mutable artists that get updated each frame.
    """
    s = font_scale
    bg = '#1a1a2e'
    ssp_labels = ['SSP2-4.5 (moderate)', 'SSP5-8.5 (high emissions)']
    ssp_colors = ['#1b9e77', '#d95f02']

    fig, axes = plt.subplots(1, 2, figsize=figsize, facecolor=bg)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.84, bottom=0.16,
                        wspace=0.04)

    im_layers = []
    stat_texts = []
    area_bars = []

    for i, ax in enumerate(axes):
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

        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(ssp_labels[i], color=ssp_colors[i],
                     fontsize=int(16 * s), fontweight='bold', pad=8)

        st = ax.text(0.03, 0.97, '', transform=ax.transAxes,
                     fontsize=int(11 * s), color='white', va='top',
                     fontfamily='monospace',
                     bbox=dict(boxstyle='round,pad=0.4',
                               facecolor=bg, alpha=0.85,
                               edgecolor='#555555'))
        stat_texts.append(st)

        # Area bar
        bar_ax = fig.add_axes([0.05 + i * 0.5, 0.10, 0.40, 0.02])
        bar_ax.set_xlim(0, init_area)
        bar_ax.set_facecolor('#2d2d44')
        bar_ax.tick_params(colors='white', labelsize=int(8 * s))
        bar_ax.set_xlabel('Area (km²)', color='white',
                          fontsize=int(9 * s))
        bar_ax.spines['bottom'].set_color('#555555')
        bar_ax.spines['top'].set_visible(False)
        bar_ax.spines['right'].set_visible(False)
        bar_ax.spines['left'].set_visible(False)
        bar = bar_ax.barh(0, init_area, height=0.6, color=ssp_colors[i],
                          alpha=0.8)
        area_bars.append((bar_ax, bar))

    # Colorbar with explicit label
    cbar_ax = fig.add_axes([0.25, 0.04, 0.50, 0.018])
    cb = fig.colorbar(im_layers[0], cax=cbar_ax, orientation='horizontal')
    cbar_ax.set_xlabel('Ice Thickness (m)', color='white',
                       fontsize=int(12 * s), labelpad=6)
    cb.ax.tick_params(colors='white', labelsize=int(9 * s))
    cbar_ax.spines['top'].set_color('#555555')
    cbar_ax.spines['bottom'].set_color('#555555')

    # Year title
    year_text = fig.text(0.5, 0.91, '', ha='center', va='bottom',
                         fontsize=int(28 * s), fontweight='bold',
                         color='white', fontfamily='monospace')

    return fig, im_layers, stat_texts, area_bars, year_text


def create_animation(snapshots_245, snapshots_585, grid, ice_thickness_init,
                     results_245, results_585, output_path, fps=4):
    """Create side-by-side retreat animation (MP4 + GIF)."""

    elev = grid['elevation']
    nodata_mask = elev < 1
    hs = hillshade(np.where(nodata_mask, np.nan, elev))

    # Initial state
    init_mask = grid['glacier_mask']
    init_area = float(init_mask.sum()) * grid['cell_size']**2 / 1e6
    init_vol = float(ice_thickness_init[init_mask].sum()) * grid['cell_size']**2 / 1e9
    max_thick = float(ice_thickness_init.max())

    # Crop to glacier region with padding
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

    def make_update(im_layers, stat_texts, area_bars, year_text, full_stats):
        """Return an update function for FuncAnimation."""
        def update(frame):
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

            year_text.set_text(f"WY {all_snapshots[0][frame]['year']}")
            return im_layers + stat_texts + [year_text]
        return update

    # ── MP4 (high res) ────────────────────────────────────────────────
    fig, im_layers, stat_texts, area_bars, year_text = _build_figure(
        hs_crop, elev_crop, ice_cmap, ice_norm, init_area,
        figsize=(16, 11), font_scale=1.0)

    update_fn = make_update(im_layers, stat_texts, area_bars, year_text,
                            full_stats=True)

    print(f"\n  Rendering MP4 ({n_snap} frames)...")
    anim = FuncAnimation(fig, update_fn, frames=n_snap,
                         interval=1000 // fps, blit=False)
    writer = FFMpegWriter(fps=fps, bitrate=3000,
                          metadata={'title': 'Dixon Glacier Retreat'})
    anim.save(str(output_path), writer=writer, dpi=120)
    plt.close(fig)
    print(f"  Saved: {output_path}")

    # ── GIF (lower res, same layout) ──────────────────────────────────
    gif_path = output_path.with_suffix('.gif')
    fig2, im2, st2, ab2, yt2 = _build_figure(
        hs_crop, elev_crop, ice_cmap, ice_norm, init_area,
        figsize=(14, 9.5), font_scale=0.9)

    update_gif = make_update(im2, st2, ab2, yt2, full_stats=False)

    print(f"  Rendering GIF...")
    anim_gif = FuncAnimation(fig2, update_gif, frames=n_snap,
                             interval=1000 // fps, blit=False)
    anim_gif.save(str(gif_path), writer='pillow', fps=fps, dpi=90)
    plt.close(fig2)
    print(f"  Saved: {gif_path}")


def main():
    from run_projection import OUTPUT_BASE, create_run_dir

    if len(sys.argv) > 1:
        output_dir = Path(sys.argv[1])
    else:
        # Find most recent PROJ folder or create new one
        dirs = sorted([d for d in OUTPUT_BASE.iterdir()
                       if d.is_dir() and d.name.startswith('PROJ-')])
        output_dir = dirs[-1] if dirs else create_run_dir(1, ['ssp245', 'ssp585'],
                                                          label='animation')

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output: {output_dir.name}/")

    print("\n--- SSP2-4.5 ---")
    r245, grid, ice_init = run_snapshot_projection('ssp245')

    print("\n--- SSP5-8.5 ---")
    r585, _, _ = run_snapshot_projection('ssp585')

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
