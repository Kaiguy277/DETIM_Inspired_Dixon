"""
Comprehensive calibration of Dixon Glacier DETIM — v4.

Major changes:
  - Statistical temperature transfer from Nuka SNOTEL to on-glacier (D-007)
  - Input is raw Nuka temperature (1230m), not pre-adjusted
  - Elevation-dependent melt factor (Phase 3)
  - internal_lapse replaces lapse_rate (on-glacier vertical gradient)
  - 8 calibrated parameters

See research_log/decisions.md and project_plan.md for full rationale.

Calibration targets:
  1. Stake mass balance at 3 elevations, 2023-2025
  2. Geodetic mass balance (Hugonnet et al. 2021), 2000-2020
  3. Physical constraint: r_ice > r_snow
"""
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.optimize import differential_evolution
import json
import time

# ── Paths ───────────────────────────────────────────────────────────
PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
DEM_PATH = PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif'
GLACIER_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
NUKA_PATH = PROJECT / 'data' / 'climate' / 'nuka_snotel_full.csv'
STAKE_PATH = PROJECT / 'stake_observations_dixon.csv'
GEODETIC_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_hugonnet.csv'
OUTPUT_DIR = PROJECT / 'calibration_output'
OUTPUT_DIR.mkdir(exist_ok=True)

# ── DE Configuration ────────────────────────────────────────────────
GRID_RES = 100.0
DE_MAXITER = 150
DE_POPSIZE = 15
DE_SEED = 42
DE_TOL = 1e-4
DE_MUTATION = (0.5, 1.0)
DE_RECOMBINATION = 0.7

# Objective weights
W_STAKE_ANNUAL = 1.0
W_STAKE_SUMMER = 0.6
W_GEODETIC = 0.4
W_PHYSICS = 0.3

# Parameters and bounds (8 params)
PARAM_NAMES = ['MF', 'MF_grad', 'r_snow', 'r_ice', 'internal_lapse',
               'precip_grad', 'precip_corr', 'T0']
PARAM_BOUNDS = [
    (1.0, 12.0),            # MF (mm d-1 K-1)
    (-0.01, 0.0),           # MF_grad (mm d-1 K-1 per m; negative = less melt higher)
    (0.02e-3, 1.5e-3),      # r_snow
    (0.05e-3, 3.0e-3),      # r_ice
    (-8.0e-3, -3.0e-3),     # internal_lapse (C/m, on-glacier)
    (0.0002, 0.006),        # precip_grad (fraction/m)
    (0.5, 5.0),             # precip_corr
    (0.5, 3.0),             # T0 (C)
]


def load_nuka_raw():
    """Load raw Nuka SNOTEL data — temperature at 1230m, precipitation."""
    df = pd.read_csv(NUKA_PATH, parse_dates=['Date'])
    df = df.rename(columns={
        'Date': 'date',
        'Air Temperature Average (degF)': 'tavg_f',
        'Precipitation Accumulation (in) Start of Day Values': 'precip_accum_in',
    })

    # Temperature: F -> C
    df['temperature'] = (df['tavg_f'] - 32) * 5 / 9
    bad = (df['temperature'] < -50) | (df['temperature'] > 40)
    df.loc[bad, 'temperature'] = np.nan

    # Precipitation: cumulative inches -> daily mm
    if 'precip_accum_in' in df.columns:
        accum = df['precip_accum_in'].copy()
        diff = accum.diff()
        resets = diff < -1.0
        daily_in = diff.clip(lower=0)
        daily_in.iloc[0] = 0
        daily_in[resets] = 0
        df['precipitation'] = daily_in * 25.4
    else:
        df['precipitation'] = 0.0

    df = df.set_index('date').sort_index()
    df['temperature'] = df['temperature'].interpolate(method='linear', limit=3)
    return df[['temperature', 'precipitation']]


def prepare_water_year_arrays(climate, wy_year):
    """Extract numpy arrays for a water year from raw Nuka data."""
    start = f'{wy_year - 1}-10-01'
    end = f'{wy_year}-09-30'
    wy = climate.loc[start:end]
    if len(wy) < 300:
        return None
    T = wy['temperature'].ffill().fillna(0).values.astype(np.float64)
    P = wy['precipitation'].fillna(0).values.astype(np.float64)
    doy = np.array([d.timetuple().tm_yday for d in wy.index], dtype=np.int64)
    return T, P, doy


def prepare_period_arrays(climate, start_date, end_date):
    """Extract arrays for an arbitrary period."""
    wy = climate.loc[start_date:end_date]
    if len(wy) < 30:
        return None
    T = wy['temperature'].ffill().fillna(0).values.astype(np.float64)
    P = wy['precipitation'].fillna(0).values.astype(np.float64)
    doy = np.array([d.timetuple().tm_yday for d in wy.index], dtype=np.int64)
    return T, P, doy


def build_calibration_targets(stakes, geodetic, climate):
    """Build calibration targets with precomputed arrays."""
    targets = {
        'stake_annual': [],
        'stake_summer': [],
        'geodetic': [],
        'winter_swe_obs': {},
    }

    for _, row in stakes[stakes['period_type'] == 'winter'].iterrows():
        yr = row['year']
        if yr not in targets['winter_swe_obs']:
            targets['winter_swe_obs'][yr] = {}
        targets['winter_swe_obs'][yr][row['site_id']] = row['mb_obs_mwe'] * 1000

    for _, row in stakes[stakes['period_type'] == 'annual'].iterrows():
        yr = row['year']
        is_estimated = 'estimated' in str(row.get('notes', '')).lower()
        unc = row['mb_obs_uncertainty_mwe']
        if is_estimated:
            unc = max(unc, 0.3)
        wy_arrays = prepare_water_year_arrays(climate, yr)
        if wy_arrays is None:
            continue
        targets['stake_annual'].append({
            'site': row['site_id'], 'year': yr, 'obs': row['mb_obs_mwe'],
            'unc': unc, 'arrays': wy_arrays, 'estimated': is_estimated,
        })

    for _, row in stakes[stakes['period_type'] == 'summer'].iterrows():
        yr = row['year']
        is_estimated = 'estimated' in str(row.get('notes', '')).lower()
        unc = row['mb_obs_uncertainty_mwe']
        if is_estimated:
            unc = max(unc, 0.3)
        start_str = row['date_start'].strftime('%Y-%m-%d')
        end_str = row['date_end'].strftime('%Y-%m-%d')
        period_arrays = prepare_period_arrays(climate, start_str, end_str)
        if period_arrays is None:
            continue
        obs_swe = targets['winter_swe_obs'].get(yr, {}).get('ELA', None)
        targets['stake_summer'].append({
            'site': row['site_id'], 'year': yr, 'obs': row['mb_obs_mwe'],
            'unc': unc, 'arrays': period_arrays, 'estimated': is_estimated,
            'obs_winter_swe_mm': obs_swe,
        })

    good_years = {}
    for wy_year in range(2001, 2021):
        wy_data = climate.loc[f'{wy_year-1}-10-01':f'{wy_year}-09-30']
        if len(wy_data) < 300:
            continue
        t_cov = wy_data['temperature'].notna().mean()
        if t_cov < 0.85:
            continue
        arrays = prepare_water_year_arrays(climate, wy_year)
        if arrays is not None:
            good_years[wy_year] = arrays

    for _, row in geodetic.iterrows():
        period = row['period']
        start_str, end_str = period.split('_')
        start_year = pd.Timestamp(start_str).year
        end_year = pd.Timestamp(end_str).year
        year_data = {y: v for y, v in good_years.items() if start_year < y <= end_year}
        targets['geodetic'].append({
            'period': period, 'obs': row['dmdtda'], 'unc': row['err_dmdtda'],
            'year_data': year_data,
        })

    print(f"\nCalibration targets:")
    print(f"  Stake annual: {len(targets['stake_annual'])} ({len([t for t in targets['stake_annual'] if not t['estimated']])} measured)")
    print(f"  Stake summer: {len(targets['stake_summer'])} ({len([t for t in targets['stake_summer'] if not t['estimated']])} measured)")
    print(f"  Geodetic periods: {len(targets['geodetic'])}")
    for g in targets['geodetic']:
        print(f"    {g['period']}: {len(g['year_data'])} usable years")
    return targets


def compute_objective(x, fmodel, targets):
    """Multi-objective cost function with statistical temperature transfer."""
    params = {name: val for name, val in zip(PARAM_NAMES, x)}

    penalty = 0.0
    if params['r_ice'] < params['r_snow']:
        penalty += 5.0 * (params['r_snow'] - params['r_ice']) / params['r_snow']

    # ── Stake annual (Oct 1, SWE=0) ────────────────────────────────
    annual_by_year = {}
    for tgt in targets['stake_annual']:
        yr = tgt['year']
        if yr not in annual_by_year:
            annual_by_year[yr] = []
        annual_by_year[yr].append(tgt)

    annual_errors = []
    for yr, tgts in annual_by_year.items():
        T, P, doy = tgts[0]['arrays']
        result = fmodel.run(T, P, doy, params, 0.0)
        for tgt in tgts:
            mod = result['stake_balances'].get(tgt['site'], np.nan)
            if not np.isnan(mod):
                err = (mod - tgt['obs']) / tgt['unc']
                annual_errors.append(err ** 2)

    # ── Stake summer (observed winter SWE) ─────────────────────────
    summer_errors = []
    for tgt in targets['stake_summer']:
        T, P, doy = tgt['arrays']
        obs_swe = tgt.get('obs_winter_swe_mm')
        winter_swe = obs_swe if obs_swe is not None else 2500.0
        result = fmodel.run(T, P, doy, params, winter_swe)
        mod = result['stake_balances'].get(tgt['site'], np.nan)
        if not np.isnan(mod):
            err = (mod - tgt['obs']) / tgt['unc']
            summer_errors.append(err ** 2)

    # ── Geodetic MB (Oct 1, SWE=0) ─────────────────────────────────
    geodetic_errors = []
    for gtgt in targets['geodetic']:
        if not gtgt['year_data']:
            continue
        annual_bals = []
        for wy_year, arrays in gtgt['year_data'].items():
            T, P, doy = arrays
            result = fmodel.run(T, P, doy, params, 0.0)
            annual_bals.append(result['glacier_wide_balance'])
        if annual_bals:
            mean_bal = np.mean(annual_bals)
            err = (mean_bal - gtgt['obs']) / gtgt['unc']
            geodetic_errors.append(err ** 2)

    J_annual = np.sqrt(np.mean(annual_errors)) if annual_errors else 10.0
    J_summer = np.sqrt(np.mean(summer_errors)) if summer_errors else 10.0
    J_geodetic = np.sqrt(np.mean(geodetic_errors)) if geodetic_errors else 10.0

    total = (W_STAKE_ANNUAL * J_annual
             + W_STAKE_SUMMER * J_summer
             + W_GEODETIC * J_geodetic
             + W_PHYSICS * penalty)
    return total


def main():
    t_start = time.time()
    print("=" * 70)
    print("DIXON GLACIER DETIM — CALIBRATION v4")
    print("Statistical temp transfer + elevation-dependent MF")
    print("=" * 70)

    # ── Load data ───────────────────────────────────────────────────
    print("Loading raw Nuka SNOTEL data...")
    climate = load_nuka_raw()
    climate['temperature'] = climate['temperature'].ffill().fillna(0)
    climate['precipitation'] = climate['precipitation'].fillna(0)
    print(f"  {len(climate)} days ({climate.index.min().date()} to {climate.index.max().date()})")

    stakes = pd.read_csv(STAKE_PATH, parse_dates=['date_start', 'date_end'])
    print(f"  Stakes: {len(stakes)} observations")

    geodetic = pd.read_csv(GEODETIC_PATH)
    print(f"  Geodetic: {len(geodetic)} periods")

    # ── Prepare grid ────────────────────────────────────────────────
    print(f"\nPreparing grid ({GRID_RES}m)...")
    from dixon_melt.terrain import prepare_grid
    grid = prepare_grid(str(DEM_PATH), str(GLACIER_PATH), target_res=GRID_RES)
    n_glacier = grid['glacier_mask'].sum()
    area_km2 = n_glacier * grid['cell_size']**2 / 1e6
    print(f"  Shape: {grid['elevation'].shape}, Glacier cells: {n_glacier}, Area: {area_km2:.1f} km2")

    print("\nPrecomputing potential direct radiation (365 DOYs)...")
    from dixon_melt.model import precompute_ipot
    t0 = time.time()
    ipot_table = precompute_ipot(grid, doy_range=range(1, 366), dt_hours=3.0)
    print(f"  Done in {time.time()-t0:.1f}s")

    # ── Initialize FastDETIM v2 ─────────────────────────────────────
    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config

    fmodel = FastDETIM(
        grid, ipot_table,
        transfer_alpha=config.TRANSFER_ALPHA,
        transfer_beta=config.TRANSFER_BETA,
        ref_elev=config.DIXON_AWS_ELEV,
        stake_names=config.STAKE_NAMES,
        stake_elevs=config.STAKE_ELEVS,
        stake_tol=config.STAKE_TOL,
    )

    # ── Build targets ───────────────────────────────────────────────
    targets = build_calibration_targets(stakes, geodetic, climate)

    # ── JIT warm-up ─────────────────────────────────────────────────
    print("\nJIT compilation warm-up...")
    t0 = time.time()
    test_x = np.array([5.0, -0.003, 0.3e-3, 0.6e-3, -5.5e-3, 0.001, 2.0, 1.5])
    _ = compute_objective(test_x, fmodel, targets)
    print(f"  Done in {time.time()-t0:.1f}s")

    t0 = time.time()
    for _ in range(5):
        compute_objective(test_x, fmodel, targets)
    t_per_eval = (time.time() - t0) / 5
    print(f"  {t_per_eval*1000:.0f} ms per objective evaluation")

    n_total_evals = DE_POPSIZE * len(PARAM_NAMES) * (DE_MAXITER + 1)
    est_minutes = n_total_evals * t_per_eval / 60
    print(f"  Estimated calibration time: {est_minutes:.0f} min for {n_total_evals} evaluations")

    # ── Run calibration ─────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print(f"DIFFERENTIAL EVOLUTION")
    print(f"  Parameters: {len(PARAM_NAMES)}")
    print(f"  Population: {DE_POPSIZE} x {len(PARAM_NAMES)} = {DE_POPSIZE * len(PARAM_NAMES)}")
    print(f"  Max iterations: {DE_MAXITER}")
    print(f"  Bounds:")
    for name, (lo, hi) in zip(PARAM_NAMES, PARAM_BOUNDS):
        print(f"    {name:15s}: [{lo:.6f}, {hi:.6f}]")
    print(f"{'=' * 70}\n")

    eval_count = [0]
    best_cost = [np.inf]
    log = []

    def wrapper(x):
        eval_count[0] += 1
        cost = compute_objective(x, fmodel, targets)
        if cost < best_cost[0]:
            best_cost[0] = cost
        params = {n: v for n, v in zip(PARAM_NAMES, x)}
        log.append({**params, 'cost': cost, 'eval': eval_count[0]})
        if eval_count[0] % 50 == 0:
            elapsed = time.time() - t_start
            print(f"  eval {eval_count[0]:5d} | cost={cost:.3f} | best={best_cost[0]:.3f} | "
                  f"MF={params['MF']:.2f} MFg={params['MF_grad']*1e3:.2f} "
                  f"il={params['internal_lapse']*1e3:.1f} "
                  f"pc={params['precip_corr']:.2f} | {elapsed:.0f}s")
        return cost

    result = differential_evolution(
        wrapper, bounds=PARAM_BOUNDS,
        maxiter=DE_MAXITER, popsize=DE_POPSIZE, seed=DE_SEED,
        tol=DE_TOL, mutation=DE_MUTATION, recombination=DE_RECOMBINATION,
        init='latinhypercube', disp=True, workers=1,
    )

    elapsed = time.time() - t_start
    best_params = {name: val for name, val in zip(PARAM_NAMES, result.x)}

    print(f"\n{'=' * 70}")
    print(f"CALIBRATION v4 COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Success: {result.success}")
    print(f"  Message: {result.message}")
    print(f"  Final cost: {result.fun:.4f}")
    print(f"  Evaluations: {eval_count[0]}")
    print(f"  Wall time: {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"\n  Optimized parameters:")
    for k, v in best_params.items():
        if 'r_' in k:
            print(f"    {k:15s}: {v:.6f} ({v*1000:.3f} x 10^-3)")
        elif 'lapse' in k:
            print(f"    {k:15s}: {v:.5f} (= {v*1000:.2f} C/km)")
        elif 'MF_grad' in k:
            print(f"    {k:15s}: {v:.6f} (= {v*1000:.3f} per km)")
        else:
            print(f"    {k:15s}: {v:.4f}")

    # ── Validation ──────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("VALIDATION")
    print(f"{'=' * 70}")

    for yr in [2023, 2024, 2025]:
        arrays = prepare_water_year_arrays(climate, yr)
        if arrays is None:
            print(f"\n  WY{yr}: insufficient data, skipping")
            continue
        T, P, doy = arrays
        r = fmodel.run(T, P, doy, best_params, 0.0)
        print(f"\n  WY{yr}:")
        print(f"    Glacier-wide balance: {r['glacier_wide_balance']:+.3f} m w.e.")
        obs_annual = stakes[(stakes['period_type'] == 'annual') & (stakes['year'] == yr)]
        for site in ['ABL', 'ELA', 'ACC']:
            mod = r['stake_balances'].get(site, np.nan)
            obs_row = obs_annual[obs_annual['site_id'] == site]
            obs = obs_row['mb_obs_mwe'].values[0] if len(obs_row) > 0 else np.nan
            diff = mod - obs if not (np.isnan(mod) or np.isnan(obs)) else np.nan
            obs_str = f"{obs:+.2f}" if not np.isnan(obs) else "  n/a"
            diff_str = f"{diff:+.2f}" if not np.isnan(diff) else "  n/a"
            print(f"      {site}: modeled={mod:+.2f}, observed={obs_str}, residual={diff_str}")

    print(f"\n  Geodetic MB:")
    for gtgt in targets['geodetic']:
        if not gtgt['year_data']:
            continue
        annual_bals = []
        for wy_year, arrays in gtgt['year_data'].items():
            T, P, doy = arrays
            r = fmodel.run(T, P, doy, best_params, 0.0)
            annual_bals.append(r['glacier_wide_balance'])
        mean_bal = np.mean(annual_bals) if annual_bals else np.nan
        print(f"    {gtgt['period']}: modeled={mean_bal:+.3f}, observed={gtgt['obs']:+.3f} "
              f"+/- {gtgt['unc']:.3f} ({len(annual_bals)} years)")

    # ── Save outputs ────────────────────────────────────────────────
    with open(OUTPUT_DIR / 'best_params_v4.json', 'w') as f:
        json.dump(best_params, f, indent=2)

    log_df = pd.DataFrame(log)
    log_df.to_csv(OUTPUT_DIR / 'calibration_log_v4.csv', index=False)

    summary = {
        'version': 4,
        'fixes': [
            'Statistical temp transfer: Nuka -> on-glacier (D-007)',
            'Elevation-dependent melt factor (MF_grad)',
            'Raw Nuka input (not pre-adjusted)',
            'internal_lapse replaces lapse_rate',
        ],
        'success': bool(result.success),
        'message': result.message,
        'cost': float(result.fun),
        'n_evaluations': eval_count[0],
        'wall_time_s': elapsed,
        'params': best_params,
        'config': {
            'grid_res': GRID_RES,
            'de_maxiter': DE_MAXITER,
            'de_popsize': DE_POPSIZE,
            'w_stake_annual': W_STAKE_ANNUAL,
            'w_stake_summer': W_STAKE_SUMMER,
            'w_geodetic': W_GEODETIC,
            'w_physics': W_PHYSICS,
        },
    }
    with open(OUTPUT_DIR / 'calibration_summary_v4.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n  Outputs saved to {OUTPUT_DIR}/ (v4)")
    print("Done!")


if __name__ == '__main__':
    main()
