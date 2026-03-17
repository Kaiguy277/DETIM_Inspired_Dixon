"""
Side-by-side comparison of modeled snowline with k_wind=0 vs k_wind=0.5 vs k_wind=1.0
for selected well-constrained years.

Shows whether wind redistribution shifts the modeled B=0 contour to match
the observed west-side dip in the snowline.

Output:
    calibration_output/kwind_spatial_comparison.png
"""
import numpy as np
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

# Years with good data and clear spatial snowline structure
EXAMPLE_YEARS = [2006, 2010, 2015, 2017]
K_WIND_VALUES = [0.0, 0.5, 1.0]


def make_hillshade(elev, azimuth=315, altitude=45):
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
        load_all_snowlines, validate_snowline_year,
    )

    print("Preparing model...")
    params_base = load_top_param_sets(n_top=1)[0]
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
    obs_by_year = {o['year']: o for o in obs_list}

    # Crop bounds
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
    norm = TwoSlopeNorm(vmin=-6, vcenter=0, vmax=6)

    n_years = len(EXAMPLE_YEARS)
    n_kw = len(K_WIND_VALUES)

    fig, axes = plt.subplots(n_years, n_kw,
                              figsize=(n_kw * 4.0, n_years * 5.0))

    for yi, yr in enumerate(EXAMPLE_YEARS):
        obs = obs_by_year.get(yr)
        if obs is None:
            print(f"  {yr}: no snowline data, skipping")
            continue

        for ki, kw in enumerate(K_WIND_VALUES):
            ax = axes[yi, ki]
            params = dict(params_base)
            params['k_wind'] = kw

            r = validate_snowline_year(fmodel, climate, grid, params, obs)
            if r is None or r == 'bad_climate':
                ax.set_visible(False)
                continue

            net = (r['cum_accum'] - r['cum_melt']) / 1000.0
            net_crop = np.where(mask_crop, net[r0:r1, c0:c1], np.nan)

            # Hillshade background
            ax.imshow(hs_crop, cmap='gray', vmin=0, vmax=1,
                      interpolation='nearest')

            # Net balance
            im = ax.imshow(net_crop, cmap='RdBu', norm=norm,
                           interpolation='nearest')

            # Observed snowline (yellow)
            obs_mask_crop = obs['snowline_mask'][r0:r1, c0:c1]
            if obs_mask_crop.any():
                ax.contour(obs_mask_crop.astype(float), levels=[0.5],
                           colors='gold', linewidths=2.5)

            # Modeled B=0 contour (black dashed)
            net_glacier = np.where(mask_crop, net_crop, np.nan)
            try:
                ax.contour(net_glacier, levels=[0], colors='black',
                           linewidths=2.0, linestyles='--')
            except ValueError:
                pass

            obs_e = r['obs_snowline_elev']
            mod_e = r['modeled_snowline_elev']
            bias = r['elev_bias']

            if yi == 0:
                ax.set_title(f'k_wind = {kw:.1f}\n\n'
                             f'{yr} ({r["obs_date"][5:]})\n'
                             f'obs:{obs_e:.0f}  mod:{mod_e:.0f}  '
                             f'\u0394:{bias:+.0f}m',
                             fontsize=9, fontweight='bold')
            else:
                ax.set_title(f'{yr} ({r["obs_date"][5:]})\n'
                             f'obs:{obs_e:.0f}  mod:{mod_e:.0f}  '
                             f'\u0394:{bias:+.0f}m',
                             fontsize=9, fontweight='bold')

            ax.set_xticks([])
            ax.set_yticks([])

            print(f"  {yr} k_wind={kw:.1f}: "
                  f"obs={obs_e:.0f}m, mod={mod_e:.0f}m, bias={bias:+.0f}m")

    # Colorbar
    cbar_ax = fig.add_axes([0.93, 0.15, 0.015, 0.70])
    cb = fig.colorbar(
        plt.cm.ScalarMappable(norm=norm, cmap='RdBu'), cax=cbar_ax)
    cb.set_label('Net Balance (m w.e.)', fontsize=11)

    # Legend
    legend_elements = [
        Line2D([0], [0], color='gold', lw=2.5, label='Observed snowline'),
        Line2D([0], [0], color='black', lw=2, ls='--',
               label='Modeled snowline (B = 0)'),
    ]
    fig.legend(handles=legend_elements, loc='lower center',
               ncol=2, fontsize=11, bbox_to_anchor=(0.45, 0.01))

    fig.suptitle('Dixon Glacier \u2014 Effect of Wind Redistribution (k_wind) '
                 'on Modeled Snowline\n'
                 'Blue = accumulation    Red = ablation',
                 fontsize=13, fontweight='bold', y=0.99)

    plt.tight_layout(rect=[0, 0.04, 0.92, 0.96])
    out_path = OUTPUT_DIR / 'kwind_spatial_comparison.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"\nSaved: {out_path}")


if __name__ == '__main__':
    main()
