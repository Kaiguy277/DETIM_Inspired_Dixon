"""
Comprehensive calibration of Dixon Glacier DETIM — v8.

Changes (D-013, D-014, D-015):
  - SNOTEL elevation corrected: 1230 ft = 375 m (was 1230 m)
  - Lapse rate fixed at -5.0 C/km (removed from calibration)
  - k_wind removed (converged to ~0 in v7)
  - precip_corr bounds tightened to [1.2, 3.0]
  - r_ice upper bound widened to 5.0e-3
  - Geodetic 2000-2020 dropped (not independent of sub-periods)
  - Cost function: inverse-variance weighting with geodetic hard penalty
  - 7 calibrated parameters

See research_log/decisions.md D-013 through D-015 for full rationale.
"""
import sys
import os
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True)

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
DE_MAXITER = 200
DE_POPSIZE = 15
DE_SEED = 42
DE_TOL = 1e-4
DE_MUTATION = (0.5, 1.0)
DE_RECOMBINATION = 0.7

# Fixed parameters (D-015)
FIXED_K_WIND = 0.0          # Off; converged to ~0 in CAL-007

# Geodetic hard constraint penalty (D-014)
GEODETIC_LAMBDA = 50.0  # penalty multiplier when geodetic exceeds uncertainty

# Parameters and bounds (8 params — k_wind fixed, lapse_rate bounded)
PARAM_NAMES = ['MF', 'MF_grad', 'r_snow', 'r_ice', 'lapse_rate',
               'precip_grad', 'precip_corr', 'T0']
PARAM_BOUNDS = [
    (1.0, 12.0),            # MF (mm d-1 K-1)
    (-0.01, 0.0),           # MF_grad (mm d-1 K-1 per m; negative = less melt higher)
    (0.02e-3, 1.5e-3),      # r_snow
    (0.05e-3, 5.0e-3),      # r_ice (widened upper bound)
    (-7.0e-3, -4.0e-3),     # lapse_rate (C/m; literature: -4 to -7 C/km)
    (0.0002, 0.006),        # precip_grad (fraction/m)
    (1.2, 3.0),             # precip_corr (D-013: bounded by literature)
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
    """Build calibration targets including winter balance."""
    targets = {
        'stake_annual': [],
        'stake_summer': [],
        'stake_winter': [],
        'geodetic': [],
        'winter_swe_obs': {},
    }

    # Collect winter SWE observations
    for _, row in stakes[stakes['period_type'] == 'winter'].iterrows():
        yr = row['year']
        if yr not in targets['winter_swe_obs']:
            targets['winter_swe_obs'][yr] = {}
        targets['winter_swe_obs'][yr][row['site_id']] = row['mb_obs_mwe'] * 1000

    # Annual targets
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

    # Summer targets
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

    # Winter targets (NEW in v7)
    for _, row in stakes[stakes['period_type'] == 'winter'].iterrows():
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
        targets['stake_winter'].append({
            'site': row['site_id'], 'year': yr, 'obs': row['mb_obs_mwe'],
            'unc': unc, 'arrays': period_arrays, 'estimated': is_estimated,
        })

    # Geodetic targets
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
        # D-014: Skip 2000-2020 (not independent of sub-periods)
        if period == '2000-01-01_2020-01-01':
            print(f"    {period}: SKIPPED (not independent of sub-periods, D-014)")
            continue
        start_str, end_str = period.split('_')
        start_year = pd.Timestamp(start_str).year
        end_year = pd.Timestamp(end_str).year
        year_data = {y: v for y, v in good_years.items() if start_year < y <= end_year}
        targets['geodetic'].append({
            'period': period, 'obs': row['dmdtda'], 'unc': row['err_dmdtda'],
            'year_data': year_data,
        })

    print(f"\nCalibration targets:")
    n_meas = lambda lst: len([t for t in lst if not t['estimated']])
    print(f"  Stake annual: {len(targets['stake_annual'])} ({n_meas(targets['stake_annual'])} measured)")
    print(f"  Stake summer: {len(targets['stake_summer'])} ({n_meas(targets['stake_summer'])} measured)")
    print(f"  Stake winter: {len(targets['stake_winter'])} ({n_meas(targets['stake_winter'])} measured)")
    print(f"  Geodetic periods: {len(targets['geodetic'])}")
    for g in targets['geodetic']:
        print(f"    {g['period']}: {len(g['year_data'])} usable years")
    return targets


def compute_objective(x, fmodel, targets):
    """Inverse-variance cost function with geodetic hard constraint (D-014).

    Each observation is weighted by 1/sigma^2 (its reported uncertainty).
    Geodetic observations that exceed their uncertainty bounds incur an
    additional hard penalty (lambda * excess^2).
    """
    params = {name: val for name, val in zip(PARAM_NAMES, x)}
    # Map lapse_rate -> internal_lapse for the model
    params['internal_lapse'] = params.pop('lapse_rate')
    params['k_wind'] = FIXED_K_WIND

    # Physics penalty: r_ice should be >= r_snow
    penalty = 0.0
    if params['r_ice'] < params['r_snow']:
        penalty += 5.0 * (params['r_snow'] - params['r_ice']) / params['r_snow']

    all_chi2 = []  # all (residual/sigma)^2 terms

    # ── Stake annual (Oct 1, SWE=0) ────────────────────────────────
    annual_by_year = {}
    for tgt in targets['stake_annual']:
        yr = tgt['year']
        if yr not in annual_by_year:
            annual_by_year[yr] = []
        annual_by_year[yr].append(tgt)

    for yr, tgts in annual_by_year.items():
        T, P, doy = tgts[0]['arrays']
        result = fmodel.run(T, P, doy, params, 0.0)
        for tgt in tgts:
            mod = result['stake_balances'].get(tgt['site'], np.nan)
            if not np.isnan(mod):
                all_chi2.append(((mod - tgt['obs']) / tgt['unc']) ** 2)

    # ── Stake summer (observed winter SWE) ─────────────────────────
    for tgt in targets['stake_summer']:
        T, P, doy = tgt['arrays']
        obs_swe = tgt.get('obs_winter_swe_mm')
        winter_swe = obs_swe if obs_swe is not None else 2500.0
        result = fmodel.run(T, P, doy, params, winter_swe)
        mod = result['stake_balances'].get(tgt['site'], np.nan)
        if not np.isnan(mod):
            all_chi2.append(((mod - tgt['obs']) / tgt['unc']) ** 2)

    # ── Stake winter (Oct 1, SWE=0) ───────────────────────────────
    winter_by_year = {}
    for tgt in targets['stake_winter']:
        yr = tgt['year']
        if yr not in winter_by_year:
            winter_by_year[yr] = []
        winter_by_year[yr].append(tgt)

    for yr, tgts in winter_by_year.items():
        T, P, doy = tgts[0]['arrays']
        result = fmodel.run(T, P, doy, params, 0.0)
        for tgt in tgts:
            mod = result['stake_balances'].get(tgt['site'], np.nan)
            if not np.isnan(mod):
                all_chi2.append(((mod - tgt['obs']) / tgt['unc']) ** 2)

    # ── Geodetic MB (Oct 1, SWE=0) — with hard penalty ─────────────
    geodetic_penalty = 0.0
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
            residual = mean_bal - gtgt['obs']
            # Inverse-variance term (same as stakes)
            all_chi2.append((residual / gtgt['unc']) ** 2)
            # Hard penalty for exceeding uncertainty bounds
            excess = max(0.0, abs(residual) - gtgt['unc'])
            geodetic_penalty += GEODETIC_LAMBDA * (excess / gtgt['unc']) ** 2

    if not all_chi2:
        return 100.0

    # Total: sqrt of mean chi-squared + geodetic hard penalty + physics penalty
    total = np.sqrt(np.mean(all_chi2)) + geodetic_penalty + penalty
    return total


def main():
    t_start = time.time()
    print("=" * 70)
    print("DIXON GLACIER DETIM — CALIBRATION v8")
    print("Elevation fix + inv-variance cost + fixed lapse (D-013/014/015)")
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

    # Wind exposure stats
    sx = grid['sx_norm'][grid['glacier_mask']]
    print(f"  Sx_norm on glacier: min={sx.min():.3f}, max={sx.max():.3f}, std={sx.std():.3f}")

    print("\nPrecomputing potential direct radiation (365 DOYs)...")
    from dixon_melt.model import precompute_ipot
    t0 = time.time()
    ipot_table = precompute_ipot(grid, doy_range=range(1, 366), dt_hours=3.0)
    print(f"  Done in {time.time()-t0:.1f}s")

    # ── Initialize FastDETIM ─────────────────────────────────────
    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config

    fmodel = FastDETIM(
        grid, ipot_table,
        transfer_alpha=config.TRANSFER_ALPHA,
        transfer_beta=config.TRANSFER_BETA,
        ref_elev=config.SNOTEL_ELEV,  # 375m (D-013: corrected from 1230m)
        stake_names=config.STAKE_NAMES,
        stake_elevs=config.STAKE_ELEVS,
        stake_tol=config.STAKE_TOL,
    )

    # ── Build targets ───────────────────────────────────────────────
    targets = build_calibration_targets(stakes, geodetic, climate)

    # ── JIT warm-up ─────────────────────────────────────────────────
    print("\nJIT compilation warm-up...")
    t0 = time.time()
    test_x = np.array([5.0, -0.003, 0.3e-3, 0.6e-3, -5.0e-3, 0.001, 2.0, 1.5])
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
    print(f"  Fixed: k_wind={FIXED_K_WIND}")
    print(f"  ref_elev: {config.SNOTEL_ELEV} m (D-013: 1230 ft corrected)")
    print(f"  Geodetic penalty lambda: {GEODETIC_LAMBDA}")
    print(f"  Bounds:")
    for name, (lo, hi) in zip(PARAM_NAMES, PARAM_BOUNDS):
        print(f"    {name:15s}: [{lo:.6f}, {hi:.6f}]")
    print(f"  Cost function: inverse-variance (1/sigma^2) + geodetic hard penalty")
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
                  f"pc={params['precip_corr']:.2f} T0={params['T0']:.1f} | {elapsed:.0f}s")
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
    print(f"CALIBRATION v8 COMPLETE")
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
    print(f"\n  Fixed parameters:")
    print(f"    k_wind         : {FIXED_K_WIND:.4f}")
    print(f"    ref_elev       : {config.SNOTEL_ELEV:.1f} m (1230 ft)")

    # ── Validation ──────────────────────────────────────────────────
    # Map lapse_rate -> internal_lapse for model runs
    run_params = dict(best_params)
    run_params['internal_lapse'] = run_params.pop('lapse_rate')
    run_params['k_wind'] = FIXED_K_WIND

    print(f"\n{'=' * 70}")
    print("VALIDATION")
    print(f"{'=' * 70}")

    for yr in [2023, 2024, 2025]:
        arrays = prepare_water_year_arrays(climate, yr)
        if arrays is None:
            print(f"\n  WY{yr}: insufficient data, skipping")
            continue
        T, P, doy = arrays
        r = fmodel.run(T, P, doy, run_params, 0.0)
        print(f"\n  WY{yr}:")
        print(f"    Glacier-wide balance: {r['glacier_wide_balance']:+.3f} m w.e.")
        for ptype in ['annual', 'winter', 'summer']:
            obs_rows = stakes[(stakes['period_type'] == ptype) & (stakes['year'] == yr)]
            if len(obs_rows) == 0:
                continue
            # For winter/summer, run the specific period
            if ptype != 'annual':
                for _, obs_row in obs_rows.iterrows():
                    site = obs_row['site_id']
                    start_str = obs_row['date_start'].strftime('%Y-%m-%d')
                    end_str = obs_row['date_end'].strftime('%Y-%m-%d')
                    parr = prepare_period_arrays(climate, start_str, end_str)
                    if parr is None:
                        continue
                    Tp, Pp, doyp = parr
                    if ptype == 'summer':
                        w_ela = stakes[(stakes['year']==yr) & (stakes['site_id']=='ELA')
                                       & (stakes['period_type']=='winter')]
                        wswe = w_ela['mb_obs_mwe'].values[0] * 1000 if len(w_ela) else 2500.0
                    else:
                        wswe = 0.0
                    rp = fmodel.run(Tp, Pp, doyp, run_params, wswe)
                    mod = rp['stake_balances'].get(site, np.nan)
                    obs = obs_row['mb_obs_mwe']
                    res = mod - obs if not np.isnan(mod) else np.nan
                    print(f"      {site} {ptype}: mod={mod:+.2f}, obs={obs:+.2f}, res={res:+.2f}")
            else:
                for site in ['ABL', 'ELA', 'ACC']:
                    mod = r['stake_balances'].get(site, np.nan)
                    obs_row = obs_rows[obs_rows['site_id'] == site]
                    obs = obs_row['mb_obs_mwe'].values[0] if len(obs_row) > 0 else np.nan
                    diff = mod - obs if not (np.isnan(mod) or np.isnan(obs)) else np.nan
                    obs_str = f"{obs:+.2f}" if not np.isnan(obs) else "  n/a"
                    diff_str = f"{diff:+.2f}" if not np.isnan(diff) else "  n/a"
                    print(f"      {site} annual: mod={mod:+.2f}, obs={obs_str}, res={diff_str}")

    print(f"\n  Geodetic MB:")
    for gtgt in targets['geodetic']:
        if not gtgt['year_data']:
            continue
        annual_bals = []
        for wy_year, arrays in gtgt['year_data'].items():
            T, P, doy = arrays
            r = fmodel.run(T, P, doy, run_params, 0.0)
            annual_bals.append(r['glacier_wide_balance'])
        mean_bal = np.mean(annual_bals) if annual_bals else np.nan
        print(f"    {gtgt['period']}: modeled={mean_bal:+.3f}, observed={gtgt['obs']:+.3f} "
              f"+/- {gtgt['unc']:.3f} ({len(annual_bals)} years)")

    # ── Save outputs ────────────────────────────────────────────────
    with open(OUTPUT_DIR / 'best_params_v8.json', 'w') as f:
        json.dump(best_params, f, indent=2)

    log_df = pd.DataFrame(log)
    log_df.to_csv(OUTPUT_DIR / 'calibration_log_v8.csv', index=False)

    summary = {
        'version': 8,
        'fixes': [
            'SNOTEL elevation corrected: 1230 ft = 375 m (D-013)',
            'Lapse rate fixed at -5.0 C/km (D-015)',
            'k_wind removed from calibration (D-015)',
            'precip_corr bounded [1.2, 3.0] (D-013)',
            'r_ice upper bound widened to 5.0e-3',
            'Geodetic 2000-2020 dropped (D-014)',
            'Inverse-variance cost function + geodetic hard penalty (D-014)',
        ],
        'success': bool(result.success),
        'message': result.message,
        'cost': float(result.fun),
        'n_evaluations': eval_count[0],
        'wall_time_s': elapsed,
        'params': best_params,
        'fixed_params': {
            'k_wind': FIXED_K_WIND,
            'ref_elev': config.SNOTEL_ELEV,
        },
        'config': {
            'grid_res': GRID_RES,
            'de_maxiter': DE_MAXITER,
            'de_popsize': DE_POPSIZE,
            'geodetic_lambda': GEODETIC_LAMBDA,
            'cost_function': 'inverse-variance (1/sigma^2) + geodetic hard penalty',
        },
    }
    with open(OUTPUT_DIR / 'calibration_summary_v8.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n  Outputs saved to {OUTPUT_DIR}/ (v8)")
    print("Done!")


if __name__ == '__main__':
    main()
