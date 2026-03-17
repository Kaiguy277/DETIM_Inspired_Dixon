"""
Grid search for k_wind against snowline validation data.

Keeps the 6 MCMC parameters fixed at MAP values and sweeps k_wind
from 0.0 to 1.0. For each value, runs all valid snowline years and
computes spatial metrics that stakes/geodetic cannot constrain.

Key metric: mean absolute net balance along the observed snowline
contour (ideal = 0 m w.e. everywhere along the line).

Output:
    calibration_output/kwind_gridsearch.csv
    calibration_output/kwind_gridsearch.png

Usage:
    python run_kwind_gridsearch.py
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
DEM_PATH = PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif'
GLACIER_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
CLIMATE_PATH = PROJECT / 'data' / 'climate' / 'dixon_gap_filled_climate.csv'
SNOWLINE_DIR = PROJECT / 'snowlines_all'
OUTPUT_DIR = PROJECT / 'calibration_output'

# k_wind values to test
K_WIND_VALUES = np.arange(0.0, 1.05, 0.05)


def main():
    from run_projection import load_top_param_sets
    from dixon_melt.terrain import prepare_grid
    from dixon_melt.model import precompute_ipot
    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config
    from dixon_melt.climate import load_gap_filled_climate
    from dixon_melt.snowline_validation import (
        load_all_snowlines, validate_snowline_year,
        modeled_snowline_elevation,
    )

    print("=" * 60)
    print("k_wind GRID SEARCH — Dixon Glacier Snowline Validation")
    print("=" * 60)

    # Load MAP parameters
    params_base = load_top_param_sets(n_top=1)[0]
    print(f"\n  Base parameters (MAP from MCMC):")
    print(f"    MF={params_base['MF']:.3f}, r_snow={params_base['r_snow']:.6f}, "
          f"T0={params_base['T0']:.3f}")

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
    print("  Loading gap-filled climate (D-025)...")
    climate = load_gap_filled_climate(str(CLIMATE_PATH))
    climate = climate[['temperature', 'precipitation']]

    # Load all observed snowlines
    dem_info = {
        'elevation': grid['elevation'],
        'glacier_mask': grid['glacier_mask'],
        'transform': grid['transform'],
        'cell_size': grid['cell_size'],
        'nrows': grid['elevation'].shape[0],
        'ncols': grid['elevation'].shape[1],
    }
    obs_list = load_all_snowlines(str(SNOWLINE_DIR), dem_info)
    print(f"  Loaded {len(obs_list)} observed snowlines\n")

    # Grid search
    results = []
    for k_wind in K_WIND_VALUES:
        params = dict(params_base)
        params['k_wind'] = k_wind

        year_biases = []
        year_abs_bal = []     # |balance| along observed snowline
        year_bal_std = []     # std of balance along observed snowline
        year_rmse = []
        valid_years = []

        for obs in obs_list:
            yr = obs['year']
            r = validate_snowline_year(fmodel, climate, grid, params, obs)
            if r is None or r == 'bad_climate':
                continue

            if not np.isnan(r['elev_bias']):
                year_biases.append(r['elev_bias'])
                valid_years.append(yr)

            if not np.isnan(r['balance_at_obs_mean']):
                year_abs_bal.append(abs(r['balance_at_obs_mean']))
                year_bal_std.append(r['balance_at_obs_std'])

        biases = np.array(year_biases)
        mean_bias = np.mean(biases)
        rmse = np.sqrt(np.mean(biases**2))
        mae = np.mean(np.abs(biases))
        mean_abs_bal = np.mean(year_abs_bal)
        mean_bal_std = np.mean(year_bal_std)

        # Correlation
        obs_elevs = []
        mod_elevs = []
        for obs in obs_list:
            yr = obs['year']
            r = validate_snowline_year(fmodel, climate, grid, params, obs)
            if r is None or r == 'bad_climate':
                continue
            if not np.isnan(r['obs_snowline_elev']) and not np.isnan(r['modeled_snowline_elev']):
                obs_elevs.append(r['obs_snowline_elev'])
                mod_elevs.append(r['modeled_snowline_elev'])

        corr = np.corrcoef(obs_elevs, mod_elevs)[0, 1] if len(obs_elevs) > 2 else np.nan

        row = {
            'k_wind': k_wind,
            'mean_bias_m': mean_bias,
            'rmse_m': rmse,
            'mae_m': mae,
            'correlation': corr,
            'mean_abs_balance_at_obs': mean_abs_bal,
            'mean_balance_std_at_obs': mean_bal_std,
            'n_years': len(year_biases),
        }
        results.append(row)
        print(f"  k_wind={k_wind:.2f}: bias={mean_bias:+.0f}m, "
              f"RMSE={rmse:.0f}m, MAE={mae:.0f}m, r={corr:.2f}, "
              f"|bal@obs|={mean_abs_bal:.2f} m w.e.")

    df = pd.DataFrame(results)

    # Save CSV
    OUTPUT_DIR.mkdir(exist_ok=True)
    csv_path = OUTPUT_DIR / 'kwind_gridsearch.csv'
    df.to_csv(csv_path, index=False)
    print(f"\n  Saved: {csv_path}")

    # Find optima
    best_rmse_idx = df['rmse_m'].idxmin()
    best_bal_idx = df['mean_abs_balance_at_obs'].idxmin()
    best_mae_idx = df['mae_m'].idxmin()

    print(f"\n  OPTIMAL k_wind VALUES:")
    print(f"    Min RMSE ({df.loc[best_rmse_idx, 'rmse_m']:.0f}m): "
          f"k_wind = {df.loc[best_rmse_idx, 'k_wind']:.2f}")
    print(f"    Min MAE ({df.loc[best_mae_idx, 'mae_m']:.0f}m): "
          f"k_wind = {df.loc[best_mae_idx, 'k_wind']:.2f}")
    print(f"    Min |bal@obs| ({df.loc[best_bal_idx, 'mean_abs_balance_at_obs']:.2f}): "
          f"k_wind = {df.loc[best_bal_idx, 'k_wind']:.2f}")

    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))

    ax = axes[0, 0]
    ax.plot(df['k_wind'], df['rmse_m'], 'o-', color='#b2182b', lw=2, ms=5)
    ax.axvline(df.loc[best_rmse_idx, 'k_wind'], ls='--', color='gray', alpha=0.5)
    ax.set_ylabel('RMSE (m)')
    ax.set_title('Snowline Elevation RMSE')
    ax.grid(True, alpha=0.3)

    ax = axes[0, 1]
    ax.plot(df['k_wind'], df['mae_m'], 'o-', color='#2166ac', lw=2, ms=5)
    ax.axvline(df.loc[best_mae_idx, 'k_wind'], ls='--', color='gray', alpha=0.5)
    ax.set_ylabel('MAE (m)')
    ax.set_title('Snowline Elevation MAE')
    ax.grid(True, alpha=0.3)

    ax = axes[1, 0]
    ax.plot(df['k_wind'], df['mean_bias_m'], 'o-', color='#1b7837', lw=2, ms=5)
    ax.axhline(0, color='k', lw=0.5)
    ax.set_ylabel('Mean Bias (m)')
    ax.set_xlabel('k_wind')
    ax.set_title('Snowline Elevation Bias')
    ax.grid(True, alpha=0.3)

    ax = axes[1, 1]
    ax.plot(df['k_wind'], df['mean_abs_balance_at_obs'], 'o-',
            color='#762a83', lw=2, ms=5)
    ax.axvline(df.loc[best_bal_idx, 'k_wind'], ls='--', color='gray', alpha=0.5)
    ax.set_ylabel('Mean |Balance| at Obs Snowline (m w.e.)')
    ax.set_xlabel('k_wind')
    ax.set_title('Balance Error Along Observed Snowline')
    ax.grid(True, alpha=0.3)

    fig.suptitle('k_wind Grid Search — Dixon Glacier Snowline Validation\n'
                 f'(MAP parameters, {df.iloc[0]["n_years"]:.0f} years)',
                 fontsize=13)
    plt.tight_layout()
    plot_path = OUTPUT_DIR / 'kwind_gridsearch.png'
    fig.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {plot_path}")


if __name__ == '__main__':
    main()
