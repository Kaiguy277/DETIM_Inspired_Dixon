"""
Comprehensive multi-decade calibration of Dixon Glacier DETIM.

Uses Numba JIT-compiled model core (FastDETIM) for speed.

Calibration strategy
--------------------
Training data:
  1. Point mass balance at 3 stakes (ABL 804m, ELA 1078m, ACC 1293m)
     - Annual and summer balances, 2023-2024 (measured)
     - 2025 available estimates used with higher uncertainty
  2. Geodetic mass balance (Hugonnet et al. 2021)
     - 2000-2010: -1.072 ± 0.225 m w.e./yr
     - 2010-2020: -0.806 ± 0.202 m w.e./yr
  3. Physical constraint: r_ice > r_snow

Objective function:
  J = w_stake * RMSE_stake + w_geodetic * RMSE_geodetic + w_phys * penalty
  All errors normalized by observational uncertainty.

Parameters calibrated (8):
  MF, r_snow, r_ice, lapse_rate, precip_grad, precip_corr, T0, snow_redist

Method: scipy.optimize.differential_evolution, Latin hypercube init
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
CLIMATE_PATH = PROJECT / 'data' / 'climate' / 'dixon_model_climate.csv'
STAKE_PATH = PROJECT / 'stake_observations_dixon.csv'
GEODETIC_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_hugonnet.csv'
OUTPUT_DIR = PROJECT / 'calibration_output'
OUTPUT_DIR.mkdir(exist_ok=True)

# ── DE Configuration ────────────────────────────────────────────────
GRID_RES = 100.0
DE_MAXITER = 80
DE_POPSIZE = 15         # per parameter → total pop = 15 * 8 = 120
DE_SEED = 42
DE_TOL = 1e-4
DE_MUTATION = (0.5, 1.0)
DE_RECOMBINATION = 0.7

# Objective weights
W_STAKE_ANNUAL = 1.0
W_STAKE_SUMMER = 0.6
W_GEODETIC = 0.4
W_PHYSICS = 0.3

# Parameters and bounds
PARAM_NAMES = ['MF', 'r_snow', 'r_ice', 'lapse_rate', 'precip_grad', 'precip_corr', 'T0', 'snow_redist']
PARAM_BOUNDS = [
    (1.0, 12.0),          # MF (mm d⁻¹ K⁻¹)
    (0.02e-3, 1.5e-3),    # r_snow (mm m² W⁻¹ d⁻¹ K⁻¹)
    (0.05e-3, 3.0e-3),    # r_ice
    (-8.5e-3, -3.5e-3),   # lapse_rate (°C/m)
    (0.0002, 0.006),      # precip_grad (fraction/m)
    (1.0, 4.0),           # precip_corr
    (0.5, 3.0),           # T0 (°C)
    (0.5, 2.5),           # snow_redist
]


def load_all_data():
    """Load and prepare all calibration datasets."""
    print("Loading datasets...")

    climate = pd.read_csv(CLIMATE_PATH, index_col='date', parse_dates=True)
    climate['temperature'] = climate['temperature'].ffill().fillna(0)
    climate['precipitation'] = climate['precipitation'].fillna(0)
    print(f"  Climate: {len(climate)} days ({climate.index.min().date()} to {climate.index.max().date()})")

    stakes = pd.read_csv(STAKE_PATH, parse_dates=['date_start', 'date_end'])
    print(f"  Stakes: {len(stakes)} observations")

    geodetic = pd.read_csv(GEODETIC_PATH)
    print(f"  Geodetic: {len(geodetic)} periods")
    for _, row in geodetic.iterrows():
        print(f"    {row['period']}: {row['dmdtda']:.3f} ± {row['err_dmdtda']:.3f} m w.e./yr")

    return climate, stakes, geodetic


def prepare_water_year_arrays(climate, wy_year):
    """Extract numpy arrays for a water year. Returns T, P, doy or None."""
    start = f'{wy_year - 1}-10-01'
    end = f'{wy_year}-09-30'
    wy = climate.loc[start:end]
    if len(wy) < 300:
        return None
    T = wy['temperature'].values.astype(np.float64)
    P = wy['precipitation'].values.astype(np.float64)
    doy = np.array([d.timetuple().tm_yday for d in wy.index], dtype=np.int64)
    return T, P, doy


def prepare_period_arrays(climate, start_date, end_date):
    """Extract arrays for an arbitrary period."""
    wy = climate.loc[start_date:end_date]
    if len(wy) < 30:
        return None
    T = wy['temperature'].values.astype(np.float64)
    P = wy['precipitation'].values.astype(np.float64)
    doy = np.array([d.timetuple().tm_yday for d in wy.index], dtype=np.int64)
    return T, P, doy


def estimate_winter_swe(climate, wy_year, T0=1.5):
    """Estimate winter SWE from fall-spring cold precipitation."""
    fall_spring = climate.loc[f'{wy_year-1}-10-01':f'{wy_year}-04-30']
    if len(fall_spring) == 0:
        return 1500.0
    cold = fall_spring[fall_spring['temperature'] < T0]
    return max(cold['precipitation'].sum(), 500.0)


def build_calibration_targets(stakes, geodetic, climate):
    """Build all calibration targets with precomputed arrays.

    Returns structured dict of targets.
    """
    targets = {
        'stake_annual': [],
        'stake_summer': [],
        'geodetic': [],
        'winter_swe': {},
    }

    # Stake annual (2023, 2024 measured; 2025 estimated with higher uncertainty)
    for _, row in stakes[stakes['period_type'] == 'annual'].iterrows():
        yr = row['year']
        is_estimated = 'estimated' in str(row.get('notes', '')).lower()
        unc = row['mb_obs_uncertainty_mwe']
        if is_estimated:
            unc = max(unc, 0.3)  # inflate uncertainty for estimated values

        wy_arrays = prepare_water_year_arrays(climate, yr)
        if wy_arrays is None:
            continue

        targets['stake_annual'].append({
            'site': row['site_id'],
            'year': yr,
            'obs': row['mb_obs_mwe'],
            'unc': unc,
            'arrays': wy_arrays,
            'estimated': is_estimated,
        })

    # Stake summer
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

        targets['stake_summer'].append({
            'site': row['site_id'],
            'year': yr,
            'obs': row['mb_obs_mwe'],
            'unc': unc,
            'arrays': period_arrays,
            'estimated': is_estimated,
        })

    # Winter SWE from observations
    for _, row in stakes[stakes['period_type'] == 'winter'].iterrows():
        yr = row['year']
        if yr not in targets['winter_swe']:
            targets['winter_swe'][yr] = {}
        targets['winter_swe'][yr][row['site_id']] = row['mb_obs_mwe'] * 1000

    # Geodetic: precompute arrays for each year in the 2000-2020 period
    good_years_arrays = {}
    for wy_year in range(2001, 2021):
        # Check coverage
        wy_data = climate.loc[f'{wy_year-1}-10-01':f'{wy_year}-09-30']
        if len(wy_data) < 300:
            continue
        t_cov = wy_data['temperature'].notna().mean()
        if t_cov < 0.85:
            continue
        arrays = prepare_water_year_arrays(climate, wy_year)
        if arrays is not None:
            winter_swe = estimate_winter_swe(climate, wy_year)
            good_years_arrays[wy_year] = (arrays, winter_swe)

    for _, row in geodetic.iterrows():
        period = row['period']
        start_str, end_str = period.split('_')
        start_year = pd.Timestamp(start_str).year
        end_year = pd.Timestamp(end_str).year

        year_data = {y: v for y, v in good_years_arrays.items() if start_year < y <= end_year}

        targets['geodetic'].append({
            'period': period,
            'obs': row['dmdtda'],
            'unc': row['err_dmdtda'],
            'year_data': year_data,
        })

    # Summary
    print(f"\nCalibration targets:")
    print(f"  Stake annual: {len(targets['stake_annual'])} ({len([t for t in targets['stake_annual'] if not t['estimated']])} measured)")
    print(f"  Stake summer: {len(targets['stake_summer'])} ({len([t for t in targets['stake_summer'] if not t['estimated']])} measured)")
    print(f"  Geodetic periods: {len(targets['geodetic'])}")
    for g in targets['geodetic']:
        print(f"    {g['period']}: {len(g['year_data'])} usable years")

    return targets


def compute_objective(x, fmodel, targets):
    """Compute multi-objective cost function.

    All run_simulation calls use precomputed numpy arrays — no pandas overhead.
    """
    params = {name: val for name, val in zip(PARAM_NAMES, x)}

    # ── Physical constraints ────────────────────────────────────────
    penalty = 0.0
    if params['r_ice'] < params['r_snow']:
        penalty += 5.0 * (params['r_snow'] - params['r_ice']) / params['r_snow']

    # ── Stake annual balances ───────────────────────────────────────
    # Group by year to avoid redundant runs
    annual_by_year = {}
    for tgt in targets['stake_annual']:
        yr = tgt['year']
        if yr not in annual_by_year:
            annual_by_year[yr] = []
        annual_by_year[yr].append(tgt)

    annual_errors = []
    for yr, tgts in annual_by_year.items():
        T, P, doy = tgts[0]['arrays']
        winter_swe = targets['winter_swe'].get(yr, {}).get('ELA', 2500.0)
        result = fmodel.run(T, P, doy, params, winter_swe)

        for tgt in tgts:
            mod = result['stake_balances'].get(tgt['site'], np.nan)
            if not np.isnan(mod):
                err = (mod - tgt['obs']) / tgt['unc']
                annual_errors.append(err ** 2)

    # ── Stake summer balances ───────────────────────────────────────
    summer_errors = []
    for tgt in targets['stake_summer']:
        T, P, doy = tgt['arrays']
        winter_swe = targets['winter_swe'].get(tgt['year'], {}).get('ELA', 2500.0)
        result = fmodel.run(T, P, doy, params, winter_swe)

        mod = result['stake_balances'].get(tgt['site'], np.nan)
        if not np.isnan(mod):
            err = (mod - tgt['obs']) / tgt['unc']
            summer_errors.append(err ** 2)

    # ── Geodetic MB ─────────────────────────────────────────────────
    geodetic_errors = []
    for gtgt in targets['geodetic']:
        if not gtgt['year_data']:
            continue
        annual_bals = []
        for wy_year, (arrays, base_swe) in gtgt['year_data'].items():
            T, P, doy = arrays
            winter_swe = base_swe * params['precip_corr'] * params.get('snow_redist', 1.0)
            winter_swe = max(winter_swe, 500.0)
            result = fmodel.run(T, P, doy, params, winter_swe)
            annual_bals.append(result['glacier_wide_balance'])

        if annual_bals:
            mean_bal = np.mean(annual_bals)
            err = (mean_bal - gtgt['obs']) / gtgt['unc']
            geodetic_errors.append(err ** 2)

    # ── Combine ─────────────────────────────────────────────────────
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
    print("DIXON GLACIER DETIM — COMPREHENSIVE CALIBRATION")
    print("Numba JIT-compiled core for fast evaluation")
    print("=" * 70)

    # ── Load data ───────────────────────────────────────────────────
    climate, stakes, geodetic = load_all_data()

    # ── Prepare grid and precompute solar ───────────────────────────
    print(f"\nPreparing grid ({GRID_RES}m)...")
    from dixon_melt.terrain import prepare_grid
    grid = prepare_grid(str(DEM_PATH), str(GLACIER_PATH), target_res=GRID_RES)
    n_glacier = grid['glacier_mask'].sum()
    area_km2 = n_glacier * grid['cell_size']**2 / 1e6
    print(f"  Shape: {grid['elevation'].shape}, Glacier cells: {n_glacier}, Area: {area_km2:.1f} km²")

    print("\nPrecomputing potential direct radiation (365 DOYs)...")
    from dixon_melt.model import precompute_ipot
    t0 = time.time()
    ipot_table = precompute_ipot(grid, doy_range=range(1, 366), dt_hours=3.0)
    print(f"  Done in {time.time()-t0:.1f}s")

    # ── Initialize FastDETIM ────────────────────────────────────────
    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config
    fmodel = FastDETIM(grid, ipot_table, config.SNOTEL_ELEV)

    # ── Build targets (precomputes all numpy arrays) ────────────────
    targets = build_calibration_targets(stakes, geodetic, climate)

    # ── JIT warm-up ─────────────────────────────────────────────────
    print("\nJIT compilation warm-up...")
    t0 = time.time()
    test_x = np.array([5.0, 0.3e-3, 0.6e-3, -6.5e-3, 0.001, 2.0, 1.5, 1.0])
    _ = compute_objective(test_x, fmodel, targets)
    print(f"  Done in {time.time()-t0:.1f}s")

    # Benchmark
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
    print(f"  Population: {DE_POPSIZE} × {len(PARAM_NAMES)} = {DE_POPSIZE * len(PARAM_NAMES)}")
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
                  f"MF={params['MF']:.2f} lr={params['lapse_rate']*1e3:.1f} "
                  f"pc={params['precip_corr']:.2f} sr={params['snow_redist']:.2f} | "
                  f"{elapsed:.0f}s")

        return cost

    result = differential_evolution(
        wrapper,
        bounds=PARAM_BOUNDS,
        maxiter=DE_MAXITER,
        popsize=DE_POPSIZE,
        seed=DE_SEED,
        tol=DE_TOL,
        mutation=DE_MUTATION,
        recombination=DE_RECOMBINATION,
        init='latinhypercube',
        disp=True,
        workers=1,
    )

    elapsed = time.time() - t_start
    best_params = {name: val for name, val in zip(PARAM_NAMES, result.x)}

    # ── Print results ───────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print(f"CALIBRATION COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Success: {result.success}")
    print(f"  Message: {result.message}")
    print(f"  Final cost: {result.fun:.4f}")
    print(f"  Evaluations: {eval_count[0]}")
    print(f"  Wall time: {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"\n  Optimized parameters:")
    for k, v in best_params.items():
        if 'r_' in k:
            print(f"    {k:15s}: {v:.6f} ({v*1000:.3f} × 10⁻³)")
        elif 'lapse' in k:
            print(f"    {k:15s}: {v:.5f} (= {v*1000:.2f} °C/km)")
        else:
            print(f"    {k:15s}: {v:.4f}")

    # ── Validation: run each year with best params ──────────────────
    print(f"\n{'=' * 70}")
    print("VALIDATION")
    print(f"{'=' * 70}")

    for yr in [2023, 2024, 2025]:
        arrays = prepare_water_year_arrays(climate, yr)
        if arrays is None:
            print(f"\n  WY{yr}: insufficient climate data, skipping")
            continue

        T, P, doy = arrays
        winter_swe = targets['winter_swe'].get(yr, {}).get('ELA', 2500.0)
        result_run = fmodel.run(T, P, doy, best_params, winter_swe)

        print(f"\n  WY{yr}:")
        print(f"    Glacier-wide balance: {result_run['glacier_wide_balance']:+.3f} m w.e.")
        obs_annual = stakes[(stakes['period_type'] == 'annual') & (stakes['year'] == yr)]
        for site in ['ABL', 'ELA', 'ACC']:
            mod = result_run['stake_balances'].get(site, np.nan)
            obs_row = obs_annual[obs_annual['site_id'] == site]
            obs = obs_row['mb_obs_mwe'].values[0] if len(obs_row) > 0 else np.nan
            diff = mod - obs if not (np.isnan(mod) or np.isnan(obs)) else np.nan
            obs_str = f"{obs:+.2f}" if not np.isnan(obs) else "  n/a"
            diff_str = f"{diff:+.2f}" if not np.isnan(diff) else "  n/a"
            print(f"      {site}: modeled={mod:+.2f}, observed={obs_str}, residual={diff_str}")

    # Geodetic validation
    print(f"\n  Geodetic MB:")
    for gtgt in targets['geodetic']:
        if not gtgt['year_data']:
            continue
        annual_bals = []
        for wy_year, (arrays, base_swe) in gtgt['year_data'].items():
            T, P, doy = arrays
            wswe = base_swe * best_params['precip_corr'] * best_params.get('snow_redist', 1.0)
            wswe = max(wswe, 500.0)
            r = fmodel.run(T, P, doy, best_params, wswe)
            annual_bals.append(r['glacier_wide_balance'])
        mean_bal = np.mean(annual_bals) if annual_bals else np.nan
        print(f"    {gtgt['period']}: modeled={mean_bal:+.3f}, observed={gtgt['obs']:+.3f} "
              f"± {gtgt['unc']:.3f} ({len(annual_bals)} years)")

    # ── Save outputs ────────────────────────────────────────────────
    with open(OUTPUT_DIR / 'best_params.json', 'w') as f:
        json.dump(best_params, f, indent=2)

    log_df = pd.DataFrame(log)
    log_df.to_csv(OUTPUT_DIR / 'calibration_log.csv', index=False)

    summary = {
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
    with open(OUTPUT_DIR / 'calibration_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n  Outputs saved to {OUTPUT_DIR}/")
    print("Done!")


if __name__ == '__main__':
    main()
