"""
Run the historical ensemble (WY1999-2025) with top-250 posterior params.

Produces annual glacier-wide balance for each (param, water_year) pair,
then derives winter/summer/annual balance time series for thesis figures
(Geck et al. 2021 Fig 8/9 analogs).

Winter balance: Oct 1 to May 12 (DOY 132, approximate spring probe date)
Summer balance: May 12 to Sep 30
Annual balance: Oct 1 to Sep 30

Output: validation_output/historical_ensemble.csv
"""
import sys, os
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True)

import numpy as np
import pandas as pd
from pathlib import Path
import json
import time

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
DEM_PATH = PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif'
GLACIER_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
CLIMATE_PATH = PROJECT / 'data' / 'climate' / 'dixon_gap_filled_climate.csv'
RANKED_PATH = PROJECT / 'calibration_output' / 'ranking_v13_full.csv'
OUTPUT_DIR = PROJECT / 'validation_output'
OUTPUT_DIR.mkdir(exist_ok=True)

GRID_RES = 100.0
N_TOP = 250
WY_START = 1999
WY_END = 2025

# Approximate spring probe date (consistent with stake data)
WINTER_END_DOY = 132  # ~May 12


def load_top_params(n=N_TOP):
    """Load top-N parameter sets from ranked CSV."""
    df = pd.read_csv(RANKED_PATH)
    df = df[df['selected'] == True].head(n)
    param_cols = ['MF', 'MF_grad', 'r_snow', 'precip_grad', 'precip_corr', 'T0']
    params_list = []
    for _, row in df.iterrows():
        p = {c: row[c] for c in param_cols}
        p['r_ice'] = 2.0 * p['r_snow']
        p['internal_lapse'] = -5.0e-3
        p['k_wind'] = 0.0
        params_list.append(p)
    return params_list


def main():
    t_start = time.time()
    print("=" * 70)
    print(f"HISTORICAL ENSEMBLE — WY{WY_START} to WY{WY_END}, top {N_TOP} params")
    print("=" * 70)

    # Load climate
    climate = pd.read_csv(CLIMATE_PATH, parse_dates=['date'], index_col='date')
    climate = climate[['temperature', 'precipitation']]
    print(f"Climate: {len(climate)} days")

    # Load params
    params_list = load_top_params(N_TOP)
    print(f"Params: {len(params_list)} sets")

    # Setup model
    print("Preparing grid and model...")
    from dixon_melt.terrain import prepare_grid
    from dixon_melt.model import precompute_ipot
    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config

    grid = prepare_grid(str(DEM_PATH), str(GLACIER_PATH), target_res=GRID_RES)
    ipot_table = precompute_ipot(grid, doy_range=range(1, 366), dt_hours=3.0)
    fmodel = FastDETIM(
        grid, ipot_table,
        transfer_alpha=config.TRANSFER_ALPHA,
        transfer_beta=config.TRANSFER_BETA,
        ref_elev=config.SNOTEL_ELEV,
        stake_names=config.STAKE_NAMES,
        stake_elevs=config.STAKE_ELEVS,
        stake_tol=config.STAKE_TOL,
    )

    # Pre-extract water year arrays
    wy_arrays = {}
    for wy in range(WY_START, WY_END + 1):
        start = f'{wy - 1}-10-01'
        end = f'{wy}-09-30'
        wy_df = climate.loc[start:end]
        if len(wy_df) < 300:
            print(f"  WY{wy}: skipped ({len(wy_df)} days)")
            continue
        T = wy_df['temperature'].values.astype(np.float64)
        P = wy_df['precipitation'].values.astype(np.float64)
        doy = np.array([d.timetuple().tm_yday for d in wy_df.index], dtype=np.int64)
        wy_arrays[wy] = (T, P, doy)
    print(f"  {len(wy_arrays)} usable water years")

    # Also extract winter-only periods (Oct 1 to ~May 12)
    winter_arrays = {}
    for wy in wy_arrays:
        start = f'{wy - 1}-10-01'
        end = f'{wy}-05-12'
        w_df = climate.loc[start:end]
        if len(w_df) < 100:
            continue
        T = w_df['temperature'].values.astype(np.float64)
        P = w_df['precipitation'].values.astype(np.float64)
        doy = np.array([d.timetuple().tm_yday for d in w_df.index], dtype=np.int64)
        winter_arrays[wy] = (T, P, doy)

    # Warm up numba
    print("Warming up JIT...")
    wy0 = list(wy_arrays.keys())[0]
    T, P, doy = wy_arrays[wy0]
    _ = fmodel.run(T, P, doy, params_list[0], 0.0)

    # Run ensemble
    print(f"\nRunning {len(params_list)} × {len(wy_arrays)} = "
          f"{len(params_list) * len(wy_arrays)} simulations...")

    results = []
    n_total = len(params_list) * len(wy_arrays)
    count = 0

    for pi, params in enumerate(params_list):
        for wy in sorted(wy_arrays.keys()):
            # Annual balance (full WY)
            T, P, doy = wy_arrays[wy]
            r_annual = fmodel.run(T, P, doy, params, 0.0)
            annual_bal = r_annual['glacier_wide_balance']

            # Winter balance (Oct 1 to May 12)
            winter_bal = np.nan
            if wy in winter_arrays:
                T_w, P_w, doy_w = winter_arrays[wy]
                r_winter = fmodel.run(T_w, P_w, doy_w, params, 0.0)
                winter_bal = r_winter['glacier_wide_balance']

            # Summer = annual - winter
            summer_bal = annual_bal - winter_bal if not np.isnan(winter_bal) else np.nan

            results.append({
                'param_idx': pi,
                'water_year': wy,
                'annual_balance': annual_bal,
                'winter_balance': winter_bal,
                'summer_balance': summer_bal,
                'stake_ABL': r_annual['stake_balances'].get('ABL', np.nan),
                'stake_ELA': r_annual['stake_balances'].get('ELA', np.nan),
                'stake_ACC': r_annual['stake_balances'].get('ACC', np.nan),
            })

            count += 1
            if count % 500 == 0:
                print(f"  {count}/{n_total} ({100*count/n_total:.0f}%)")

    df = pd.DataFrame(results)
    out_path = OUTPUT_DIR / 'historical_ensemble.csv'
    df.to_csv(out_path, index=False, float_format='%.6f')

    # Print summary
    summary = df.groupby('water_year').agg(
        annual_mean=('annual_balance', 'mean'),
        annual_std=('annual_balance', 'std'),
        winter_mean=('winter_balance', 'mean'),
        summer_mean=('summer_balance', 'mean'),
    )
    print(f"\nHistorical mass balance summary (ensemble mean):")
    print(f"  Period mean annual: {summary['annual_mean'].mean():.3f} m w.e./yr")
    print(f"  Most negative year: WY{summary['annual_mean'].idxmin()} "
          f"({summary['annual_mean'].min():.3f})")
    print(f"  Most positive year: WY{summary['annual_mean'].idxmax()} "
          f"({summary['annual_mean'].max():.3f})")

    elapsed = time.time() - t_start
    print(f"\nDone in {elapsed:.0f}s. Saved: {out_path}")


if __name__ == '__main__':
    main()
