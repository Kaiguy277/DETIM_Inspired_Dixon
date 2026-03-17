"""
Plot observed vs modeled snowline spatial maps for all valid years.

Produces a grid of panels (one per year), each showing:
  - Net balance (blue = accumulation, red = ablation) on glacier
  - Hillshade background off-glacier
  - Observed snowline (yellow contour)
  - Modeled snowline / B=0 contour (black dashed)
  - Title with obs/mod elevations and bias

Excludes years with >30% melt-season NaN (D-022: WY2000, WY2005).

Output:
    calibration_output/snowline_all_years.png

Usage:
    python plot_snowline_all_years.py
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.colors import TwoSlopeNorm
from pathlib import Path

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
DEM_PATH = PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif'
GLACIER_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
CLIMATE_PATH = PROJECT / 'data' / 'climate' / 'dixon_gap_filled_climate.csv'
SNOWLINE_DIR = PROJECT / 'snowlines_all'
OUTPUT_DIR = PROJECT / 'calibration_output'

NCOLS = 6  # panels per row


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
    from run_projection import load_top_param_sets
    from dixon_melt.terrain import prepare_grid
    from dixon_melt.model import precompute_ipot
    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config
    from dixon_melt.climate import load_gap_filled_climate
    from dixon_melt.snowline_validation import (
        load_all_snowlines, validate_snowline_year, load_snowline,
    )

    print("Preparing model...")
    params = load_top_param_sets(n_top=1)[0]
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

    climate = load_gap_filled_climate(str(CLIMATE_PATH))
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

    # Run validation for each year, collect results
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
        # Attach obs info for plotting
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

    # Hillshade for background
    hs = make_hillshade(elev)
    hs_crop = hs[r0:r1, c0:c1]
    mask_crop = mask[r0:r1, c0:c1]

    # Create figure
    fig, axes = plt.subplots(nrows_grid, NCOLS,
                              figsize=(NCOLS * 3.2, nrows_grid * 4.0))
    if nrows_grid == 1:
        axes = axes[np.newaxis, :]

    norm = TwoSlopeNorm(vmin=-6, vcenter=0, vmax=6)

    for idx in range(nrows_grid * NCOLS):
        row_i = idx // NCOLS
        col_i = idx % NCOLS
        ax = axes[row_i, col_i]

        if idx >= n:
            ax.set_visible(False)
            continue

        r = all_results[idx]
        yr = r['year']
        obs_date = r['obs_date']
        month_day = obs_date[5:]  # MM-DD

        # Net balance
        net = (r['cum_accum'] - r['cum_melt']) / 1000.0  # m w.e.
        net_crop = np.where(mask_crop, net[r0:r1, c0:c1], np.nan)

        # Hillshade background (gray off-glacier)
        ax.imshow(hs_crop, cmap='gray', vmin=0, vmax=1,
                  interpolation='nearest', alpha=1.0)

        # Net balance on glacier
        im = ax.imshow(net_crop, cmap='RdBu', norm=norm,
                       interpolation='nearest')

        # Observed snowline (yellow contour)
        obs_sl = r['obs_snowline']
        obs_mask_crop = obs_sl['snowline_mask'][r0:r1, c0:c1]
        if obs_mask_crop.any():
            ax.contour(obs_mask_crop.astype(float), levels=[0.5],
                       colors='gold', linewidths=2.0)

        # Modeled snowline (B=0 dashed black contour)
        net_glacier = np.where(mask_crop, net_crop, np.nan)
        try:
            ax.contour(net_glacier, levels=[0], colors='black',
                       linewidths=1.5, linestyles='--')
        except ValueError:
            pass

        # Title
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
        ax.set_title(title, fontsize=8, fontweight='bold', pad=3)
        ax.set_xticks([])
        ax.set_yticks([])

    # Colorbar on the right side
    cbar_ax = fig.add_axes([0.93, 0.15, 0.015, 0.70])
    cb = fig.colorbar(
        plt.cm.ScalarMappable(norm=norm, cmap='RdBu'),
        cax=cbar_ax)
    cb.set_label('Net Balance (m w.e.)', fontsize=10)

    # Legend at bottom
    legend_elements = [
        Line2D([0], [0], color='gold', lw=2.5, label='Observed snowline'),
        Line2D([0], [0], color='black', lw=2, ls='--',
               label='Modeled snowline (B = 0)'),
    ]
    fig.legend(handles=legend_elements, loc='lower center',
               ncol=2, fontsize=10, bbox_to_anchor=(0.45, 0.01))

    fig.suptitle('Dixon Glacier \u2014 Observed vs Modeled Snowline, '
                 f'{n} Valid Years\n'
                 'Blue = snow-covered (accumulation)    '
                 'Red = bare ice (ablation)',
                 fontsize=13, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0, 0.04, 0.92, 0.94])
    out_path = OUTPUT_DIR / 'snowline_all_years.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"\nSaved: {out_path}")


if __name__ == '__main__':
    main()
