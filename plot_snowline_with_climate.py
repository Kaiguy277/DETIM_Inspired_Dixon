"""
Plot observed vs modeled snowline spatial maps with climate input graphs.

Each year gets two vertically stacked panels:
  Top: Spatial map (net balance, observed/modeled snowline)
  Bottom: Daily temperature and precipitation time series for that water year

Uses CAL-012 (v12) MAP parameters.

Output:
    calibration_output/snowline_with_climate.png

Usage:
    python plot_snowline_with_climate.py
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.colors import TwoSlopeNorm
from matplotlib.dates import MonthLocator, DateFormatter
from pathlib import Path

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
DEM_PATH = PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif'
GLACIER_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
CLIMATE_PATH = PROJECT / 'data' / 'climate' / 'dixon_gap_filled_climate.csv'
SNOWLINE_DIR = PROJECT / 'snowlines_all'
PARAMS_PATH = PROJECT / 'calibration_output' / 'best_params_v12.json'
OUTPUT_DIR = PROJECT / 'calibration_output'

NCOLS = 5  # panels per row (fewer than 6 to fit climate graphs)


def make_hillshade(elev, azimuth=315, altitude=45):
    """Simple hillshade from elevation grid."""
    dx = np.gradient(elev, axis=1)
    dy = np.gradient(elev, axis=0)
    az_rad = np.radians(azimuth)
    alt_rad = np.radians(altitude)
    slope = np.arctan(np.sqrt(dx**2 + dy**2))
    aspect = np.arctan2(-dy, dx)
    hs = np.sin(alt_rad) * np.cos(slope) + \
         np.cos(alt_rad) * np.sin(slope) * np.cos(az_rad - aspect)
    return np.clip(hs, 0, 1)


def main():
    import json
    from dixon_melt.terrain import prepare_grid
    from dixon_melt.model import precompute_ipot
    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config
    from dixon_melt.snowline_validation import (
        load_all_snowlines, validate_snowline_year,
    )

    print("Loading CAL-012 params...")
    with open(PARAMS_PATH) as f:
        params = json.load(f)
    # Ensure all needed keys
    params.setdefault('internal_lapse', params.get('lapse_rate', -5.0e-3))
    params.setdefault('k_wind', 0.0)
    print(f"  MF={params['MF']:.3f}, pc={params['precip_corr']:.3f}, "
          f"T0={params['T0']:.3f}, r_snow={params['r_snow']*1e3:.3f}e-3")

    print("Preparing model...")
    grid = prepare_grid(str(DEM_PATH), str(GLACIER_PATH), target_res=100.0)
    ipot_table = precompute_ipot(grid, doy_range=range(1, 366), dt_hours=3.0)

    fmodel = FastDETIM(
        grid, ipot_table,
        transfer_alpha=config.TRANSFER_ALPHA,
        transfer_beta=config.TRANSFER_BETA,
        ref_elev=config.SNOTEL_ELEV,
        stake_names=config.STAKE_NAMES,
        stake_elevs=config.STAKE_ELEVS,
    )

    print("Loading climate...")
    climate = pd.read_csv(CLIMATE_PATH, parse_dates=['date'], index_col='date')
    climate = climate[['temperature', 'precipitation']]

    dem_info = {
        'elevation': grid['elevation'],
        'glacier_mask': grid['glacier_mask'],
        'transform': grid['transform'],
        'cell_size': grid['cell_size'],
        'nrows': grid['elevation'].shape[0],
        'ncols': grid['elevation'].shape[1],
    }
    obs_list = load_all_snowlines(str(SNOWLINE_DIR), dem_info)

    # Run validation for each year
    print("Running model for all snowline years...")
    all_results = []
    for obs in obs_list:
        yr = obs['year']
        r = validate_snowline_year(fmodel, climate, grid, params, obs)
        if r is None:
            print(f"  {yr}: skipped (insufficient data)")
            continue
        if r == 'bad_climate':
            print(f"  {yr}: skipped (>30% melt-season T missing)")
            continue
        r['obs_snowline'] = obs
        all_results.append(r)
        bias = r['elev_bias']
        print(f"  {yr}: obs={r['obs_snowline_elev']:.0f}m, "
              f"mod={r['modeled_snowline_elev']:.0f}m, bias={bias:+.0f}m")

    n = len(all_results)
    nrows_grid = int(np.ceil(n / NCOLS))
    print(f"\nPlotting {n} years in {nrows_grid} x {NCOLS} grid...")

    # Compute crop bounds (shared across all panels)
    elev = grid['elevation']
    mask = grid['glacier_mask']
    rows_idx = np.where(mask.any(axis=1))[0]
    cols_idx = np.where(mask.any(axis=0))[0]
    pad = 5
    r0 = max(0, rows_idx[0] - pad)
    r1 = min(elev.shape[0], rows_idx[-1] + pad + 1)
    c0 = max(0, cols_idx[0] - pad)
    c1 = min(elev.shape[1], cols_idx[-1] + pad + 1)

    hs = make_hillshade(elev)
    hs_crop = hs[r0:r1, c0:c1]
    mask_crop = mask[r0:r1, c0:c1]

    # Figure: each column holds one year; each year gets 2 rows (map + climate)
    # So total grid rows = nrows_grid * 2
    map_height = 3.5
    clim_height = 1.8
    col_width = 3.5
    fig_w = NCOLS * col_width + 1.5  # extra for colorbar
    fig_h = nrows_grid * (map_height + clim_height) + 1.5  # extra for title/legend

    fig = plt.figure(figsize=(fig_w, fig_h))

    # Use GridSpec: for each logical row, 2 physical rows (map=3, climate=2 height ratio)
    from matplotlib.gridspec import GridSpec
    gs = GridSpec(nrows_grid * 2, NCOLS,
                  height_ratios=[map_height, clim_height] * nrows_grid,
                  hspace=0.45, wspace=0.30,
                  left=0.04, right=0.90, top=0.94, bottom=0.04)

    norm = TwoSlopeNorm(vmin=-6, vcenter=0, vmax=6)
    im_ref = None  # for colorbar

    for idx in range(nrows_grid * NCOLS):
        row_i = idx // NCOLS
        col_i = idx % NCOLS

        # Map axis
        ax_map = fig.add_subplot(gs[row_i * 2, col_i])
        # Climate axis
        ax_clim = fig.add_subplot(gs[row_i * 2 + 1, col_i])

        if idx >= n:
            ax_map.set_visible(False)
            ax_clim.set_visible(False)
            continue

        r = all_results[idx]
        yr = r['year']
        obs_date = r['obs_date']
        month_day = obs_date[5:]

        # --- Map panel ---
        net = (r['cum_accum'] - r['cum_melt']) / 1000.0
        net_crop = np.where(mask_crop, net[r0:r1, c0:c1], np.nan)

        ax_map.imshow(hs_crop, cmap='gray', vmin=0, vmax=1,
                      interpolation='nearest', alpha=1.0)
        im = ax_map.imshow(net_crop, cmap='RdBu', norm=norm,
                           interpolation='nearest')
        if im_ref is None:
            im_ref = im

        # Observed snowline (yellow)
        obs_sl = r['obs_snowline']
        obs_mask_crop = obs_sl['snowline_mask'][r0:r1, c0:c1]
        if obs_mask_crop.any():
            ax_map.contour(obs_mask_crop.astype(float), levels=[0.5],
                           colors='gold', linewidths=1.5)

        # Modeled snowline (B=0 dashed black)
        net_glacier = np.where(mask_crop, net_crop, np.nan)
        try:
            ax_map.contour(net_glacier, levels=[0], colors='black',
                           linewidths=1.2, linestyles='--')
        except ValueError:
            pass

        obs_e = r['obs_snowline_elev']
        mod_e = r['modeled_snowline_elev']
        bias = r['elev_bias']
        if np.isnan(mod_e):
            title = (f"{yr} ({month_day})\n"
                     f"obs:{obs_e:.0f}  mod:nan  \u0394:N/A")
        else:
            title = (f"{yr} ({month_day})\n"
                     f"obs:{obs_e:.0f}  mod:{mod_e:.0f}  "
                     f"\u0394:{bias:+.0f}m")
        ax_map.set_title(title, fontsize=7, fontweight='bold', pad=2)
        ax_map.set_xticks([])
        ax_map.set_yticks([])

        # --- Climate panel ---
        # Get water year data (Oct 1 to obs date)
        start = f'{yr - 1}-10-01'
        end = f'{yr}-{obs_sl["month"]:02d}-{obs_sl["day"]:02d}'
        wy_clim = climate.loc[start:end]

        if len(wy_clim) > 0:
            dates = wy_clim.index
            temps = wy_clim['temperature'].values
            precip = wy_clim['precipitation'].values

            # Temperature on left y-axis
            color_t = '#d62728'
            ax_clim.plot(dates, temps, color=color_t, linewidth=0.4, alpha=0.5)
            # 7-day rolling mean for readability
            if len(temps) > 7:
                t_smooth = pd.Series(temps, index=dates).rolling(7, center=True).mean()
                ax_clim.plot(dates, t_smooth, color=color_t, linewidth=1.0)
            ax_clim.axhline(0, color='gray', linewidth=0.5, linestyle='-', alpha=0.5)
            ax_clim.set_ylabel('T', fontsize=6, color=color_t)
            ax_clim.tick_params(axis='y', labelsize=5, colors=color_t, labelcolor=color_t)
            ax_clim.set_ylim(-25, 25)

            # Precipitation on right y-axis
            ax_p = ax_clim.twinx()
            color_p = '#1f77b4'
            ax_p.bar(dates, precip, width=1.0, color=color_p, alpha=0.35, linewidth=0)
            ax_p.set_ylabel('P', fontsize=6, color=color_p)
            ax_p.tick_params(axis='y', labelsize=5, colors=color_p, labelcolor=color_p)
            ax_p.set_ylim(0, 80)

            # X-axis formatting
            ax_clim.xaxis.set_major_locator(MonthLocator(bymonth=[1, 4, 7, 10]))
            ax_clim.xaxis.set_major_formatter(DateFormatter('%b'))
            ax_clim.tick_params(axis='x', labelsize=5, rotation=0)
            ax_clim.set_xlim(dates[0], dates[-1])
        else:
            ax_clim.text(0.5, 0.5, 'No data', transform=ax_clim.transAxes,
                         ha='center', va='center', fontsize=7)
            ax_clim.set_xticks([])
            ax_clim.set_yticks([])

    # Colorbar
    cbar_ax = fig.add_axes([0.92, 0.25, 0.015, 0.50])
    cb = fig.colorbar(
        plt.cm.ScalarMappable(norm=norm, cmap='RdBu'),
        cax=cbar_ax)
    cb.set_label('Net Balance (m w.e.)', fontsize=9)
    cb.ax.tick_params(labelsize=7)

    # Legend at bottom
    legend_elements = [
        Line2D([0], [0], color='gold', lw=2.5, label='Observed snowline'),
        Line2D([0], [0], color='black', lw=2, ls='--',
               label='Modeled snowline (B = 0)'),
        Line2D([0], [0], color='#d62728', lw=1.5, label='Temperature (7d mean)'),
        Line2D([], [], color='#1f77b4', lw=6, alpha=0.35, label='Precipitation'),
    ]
    fig.legend(handles=legend_elements, loc='lower center',
               ncol=4, fontsize=8, bbox_to_anchor=(0.47, 0.005))

    fig.suptitle('Dixon Glacier \u2014 Observed vs Modeled Snowline + Climate Inputs (CAL-012)\n'
                 'Blue = snow-covered (accumulation)    Red = bare ice (ablation)',
                 fontsize=12, fontweight='bold')

    out_path = OUTPUT_DIR / 'snowline_with_climate.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"\nSaved: {out_path}")


if __name__ == '__main__':
    main()
