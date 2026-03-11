"""
Run snowline validation for Dixon Glacier DETIM.

Compares modeled snowline positions against 22 years of digitized
snowline observations (1999-2024). Uses the MAP (best) parameter set
from CAL-010.

Output:
    calibration_output/snowline_validation.csv
    calibration_output/snowline_validation_summary.json
    calibration_output/snowline_scatter.png
    calibration_output/snowline_timeseries.png
    calibration_output/snowline_spatial_examples.png

Usage:
    python run_snowline_validation.py
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import json

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
DEM_PATH = PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif'
GLACIER_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
NUKA_PATH = PROJECT / 'data' / 'climate' / 'nuka_snotel_full.csv'
SNOWLINE_DIR = PROJECT / 'snowlines_all'
OUTPUT_DIR = PROJECT / 'calibration_output'


def main():
    from run_projection import load_top_param_sets
    from dixon_melt.terrain import prepare_grid
    from dixon_melt.model import precompute_ipot
    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config
    from dixon_melt.climate import load_nuka_snotel
    from dixon_melt.snowline_validation import run_all_validation

    print("=" * 60)
    print("SNOWLINE VALIDATION — Dixon Glacier DETIM")
    print("=" * 60)

    # Load MAP parameters (best single set)
    params = load_top_param_sets(n_top=1)[0]
    print(f"\n  Parameters: MAP from MCMC")
    print(f"    MF={params['MF']:.3f}, r_snow={params['r_snow']:.6f}, "
          f"T0={params['T0']:.3f}")

    # Grid
    print("\n  Preparing grid...")
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

    # Climate
    print("  Loading Nuka SNOTEL...")
    climate_raw = load_nuka_snotel(str(NUKA_PATH))
    # Prepare: need temperature and precipitation columns with DatetimeIndex
    climate = climate_raw[['tavg_c', 'precip_mm']].rename(
        columns={'tavg_c': 'temperature', 'precip_mm': 'precipitation'})
    climate['temperature'] = climate['temperature'].interpolate(
        method='linear', limit=3)

    # Run validation
    print(f"\n  Running snowline validation against {SNOWLINE_DIR.name}/...")
    df, summary, full_results = run_all_validation(
        fmodel, climate, grid, params, str(SNOWLINE_DIR))

    if len(df) == 0:
        print("  No valid comparisons!")
        return

    # Save results
    OUTPUT_DIR.mkdir(exist_ok=True)
    csv_path = OUTPUT_DIR / 'snowline_validation.csv'
    df.to_csv(csv_path, index=False)
    print(f"\n  Saved: {csv_path.name}")

    summary_path = OUTPUT_DIR / 'snowline_validation_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"  Saved: {summary_path.name}")

    # ── Plot 1: Scatter (observed vs modeled snowline elevation) ──────
    fig, ax = plt.subplots(figsize=(7, 7))
    valid = df.dropna(subset=['obs_snowline_elev', 'modeled_snowline_elev'])
    obs = valid['obs_snowline_elev']
    mod = valid['modeled_snowline_elev']

    ax.scatter(obs, mod, s=60, c='#2166ac', edgecolors='white',
               linewidths=0.5, zorder=3)

    # Label years
    for _, row in valid.iterrows():
        ax.annotate(str(int(row['year'])), (row['obs_snowline_elev'],
                    row['modeled_snowline_elev']),
                    fontsize=7, ha='left', va='bottom',
                    xytext=(3, 3), textcoords='offset points')

    # 1:1 line
    lo = min(obs.min(), mod.min()) - 30
    hi = max(obs.max(), mod.max()) + 30
    ax.plot([lo, hi], [lo, hi], 'k--', lw=1, alpha=0.5, label='1:1')
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect('equal')
    ax.set_xlabel('Observed Snowline Elevation (m)', fontsize=12)
    ax.set_ylabel('Modeled Snowline Elevation (m)', fontsize=12)
    ax.set_title(f'Dixon Glacier — Snowline Validation\n'
                 f'RMSE={summary["rmse_m"]:.0f}m, '
                 f'bias={summary["mean_bias_m"]:+.0f}m, '
                 f'r={summary["correlation"]:.2f}, '
                 f'n={summary["n_years"]}', fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    scatter_path = OUTPUT_DIR / 'snowline_scatter.png'
    fig.savefig(scatter_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {scatter_path.name}")

    # ── Plot 2: Time series ───────────────────────────────────────────
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True,
                                    gridspec_kw={'height_ratios': [3, 1]})

    years = valid['year']
    ax1.plot(years, obs, 'o-', color='#2166ac', lw=1.5, ms=6,
             label='Observed', zorder=3)
    ax1.plot(years, mod, 's-', color='#b2182b', lw=1.5, ms=6,
             label='Modeled', zorder=3)
    ax1.fill_between(years, obs, mod, alpha=0.15, color='gray')
    ax1.set_ylabel('Snowline Elevation (m)', fontsize=12)
    ax1.set_title('Dixon Glacier — Snowline Elevation Time Series')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    # Bias panel
    bias = valid['elev_bias']
    colors = ['#b2182b' if b > 0 else '#2166ac' for b in bias]
    ax2.bar(years, bias, color=colors, alpha=0.7, width=0.8)
    ax2.axhline(0, color='k', lw=0.5)
    ax2.set_ylabel('Bias (m)', fontsize=11)
    ax2.set_xlabel('Year', fontsize=12)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    ts_path = OUTPUT_DIR / 'snowline_timeseries.png'
    fig.savefig(ts_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {ts_path.name}")

    # ── Plot 3: Spatial examples (3 representative years) ─────────────
    # Pick early, middle, late years with data
    example_years = []
    sorted_results = sorted(full_results, key=lambda r: r['year'])
    if len(sorted_results) >= 3:
        n = len(sorted_results)
        example_years = [sorted_results[0], sorted_results[n // 2],
                         sorted_results[-1]]
    else:
        example_years = sorted_results

    if example_years:
        from dixon_melt.snowline_validation import load_snowline

        fig, axes = plt.subplots(1, len(example_years),
                                  figsize=(6 * len(example_years), 8))
        if len(example_years) == 1:
            axes = [axes]

        elev = grid['elevation']
        mask = grid['glacier_mask']

        # Crop to glacier
        rows = np.where(mask.any(axis=1))[0]
        cols = np.where(mask.any(axis=0))[0]
        pad = 5
        r0 = max(0, rows[0] - pad)
        r1 = min(elev.shape[0], rows[-1] + pad + 1)
        c0 = max(0, cols[0] - pad)
        c1 = min(elev.shape[1], cols[-1] + pad + 1)

        for i, r in enumerate(example_years):
            ax = axes[i]
            yr = r['year']

            # Background: net balance
            net = (r['cum_accum'] - r['cum_melt']) / 1000.0  # m w.e.
            net_display = np.where(mask, net, np.nan)
            crop = net_display[r0:r1, c0:c1]

            im = ax.imshow(crop, cmap='RdBu', vmin=-5, vmax=5,
                           interpolation='nearest')

            # Observed snowline overlay
            obs_mask = r.get('obs_mask', None)
            # Re-load from the file list
            dem_info = {
                'elevation': grid['elevation'],
                'glacier_mask': grid['glacier_mask'],
                'transform': grid['transform'],
                'cell_size': grid['cell_size'],
                'nrows': grid['elevation'].shape[0],
                'ncols': grid['elevation'].shape[1],
            }
            # Find the matching shapefile
            shp_files = sorted(SNOWLINE_DIR.glob(f'{yr}*_snowline*.shp'))
            if shp_files:
                sl = load_snowline(str(shp_files[0]), dem_info)
                obs_crop = sl['snowline_mask'][r0:r1, c0:c1]
                # Draw observed snowline as contour
                ax.contour(obs_crop.astype(float), levels=[0.5],
                           colors='yellow', linewidths=2.5)

            # Modeled snowline (net balance = 0 contour)
            net_glacier = np.where(mask[r0:r1, c0:c1], crop, np.nan)
            try:
                ax.contour(net_glacier, levels=[0], colors='black',
                           linewidths=2, linestyles='--')
            except ValueError:
                pass

            ax.set_xticks([])
            ax.set_yticks([])
            bias_val = r['elev_bias']
            ax.set_title(f"WY {yr}\n"
                         f"obs={r['obs_snowline_elev']:.0f}m, "
                         f"mod={r['modeled_snowline_elev']:.0f}m\n"
                         f"bias={bias_val:+.0f}m",
                         fontsize=11)

        # Legend
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color='yellow', lw=2.5, label='Observed snowline'),
            Line2D([0], [0], color='black', lw=2, ls='--',
                   label='Modeled snowline (B=0)'),
        ]
        fig.legend(handles=legend_elements, loc='lower center',
                   ncol=2, fontsize=11, bbox_to_anchor=(0.5, 0.01))

        fig.suptitle('Dixon Glacier — Spatial Snowline Comparison\n'
                     '(blue = accumulation, red = ablation)',
                     fontsize=13, y=0.98)

        # Colorbar
        cbar_ax = fig.add_axes([0.92, 0.15, 0.015, 0.65])
        cb = fig.colorbar(im, cax=cbar_ax)
        cb.set_label('Net Balance (m w.e.)', fontsize=10)

        plt.tight_layout(rect=[0, 0.05, 0.90, 0.93])
        spatial_path = OUTPUT_DIR / 'snowline_spatial_examples.png'
        fig.savefig(spatial_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  Saved: {spatial_path.name}")

    print(f"\nAll outputs saved to {OUTPUT_DIR}/")


if __name__ == '__main__':
    main()
