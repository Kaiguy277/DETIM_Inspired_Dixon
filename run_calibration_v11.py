"""
Bayesian ensemble calibration of Dixon Glacier DETIM — v11 (D-026).

Recalibration with multi-station gap-filled climate data (D-025).

Same framework as CAL-010 (D-017):
  Phase 1: Differential evolution -> MAP estimate
  Phase 2: emcee MCMC -> posterior ensemble for projections

Changes from CAL-010:
  - Climate input: gap-filled via 5-station cascade (D-025), zero NaN
  - Coverage filter removed: all 20 geodetic years (WY2001-2020) now usable
  - Previously poisoned years (WY2000, WY2001, WY2005, WY2020) now contribute
    real information instead of noise
  - Same 6 free parameters, bounds, priors, and fixed parameters

See research_log/decisions.md D-026 for rationale.
"""
import sys
import os
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True)

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.optimize import differential_evolution
from scipy.stats import truncnorm
import json
import time
import emcee

# -- Paths ---------------------------------------------------------------
PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
DEM_PATH = PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif'
GLACIER_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
CLIMATE_PATH = PROJECT / 'data' / 'climate' / 'dixon_gap_filled_climate.csv'
STAKE_PATH = PROJECT / 'stake_observations_dixon.csv'
GEODETIC_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_hugonnet.csv'
OUTPUT_DIR = PROJECT / 'calibration_output'
OUTPUT_DIR.mkdir(exist_ok=True)

# -- DE Configuration ----------------------------------------------------
GRID_RES = 100.0
DE_MAXITER = 200
DE_POPSIZE = 15
DE_SEED = 42
DE_TOL = 1e-4
DE_MUTATION = (0.5, 1.0)
DE_RECOMBINATION = 0.7

# -- MCMC Configuration --------------------------------------------------
MCMC_NWALKERS = 24       # 4x ndim (Foreman-Mackey et al. 2013 recommendation)
MCMC_NSTEPS = 10000      # per walker (Rounce et al. 2020 precedent)
MCMC_BURNIN = 2000       # minimum; will use max(2000, 2x autocorr_time)
MCMC_INIT_SPREAD = 1e-3  # relative spread for walker initialization

# -- Fixed parameters (D-017) -------------------------------------------
FIXED_LAPSE_RATE = -5.0e-3  # C/m (Gardner & Sharp 2009: -4.9, Roth 2023: -5.0)
FIXED_RICE_RATIO = 2.0      # r_ice/r_snow (Hock 1999 Table 4 mid-range)
FIXED_K_WIND = 0.0          # CAL-007 converged to ~0

# Geodetic hard constraint penalty (D-014)
GEODETIC_LAMBDA = 50.0

# -- Parameters and bounds (6 free) -------------------------------------
PARAM_NAMES = ['MF', 'MF_grad', 'r_snow', 'precip_grad', 'precip_corr', 'T0']
PARAM_BOUNDS = [
    (1.0, 12.0),            # MF (mm d-1 K-1)
    (-0.01, 0.0),           # MF_grad (mm d-1 K-1 per m)
    (0.02e-3, 2.0e-3),      # r_snow (widened: CAL-010a hit 1.5e-3 upper bound)
    (0.0002, 0.006),        # precip_grad (fraction/m)
    (1.2, 4.0),             # precip_corr
    (0.0, 3.0),             # T0 (C) (lowered: CAL-010a hit 0.5 lower bound)
]

# -- Prior distributions (D-017) ----------------------------------------
# MF: Truncated Normal(5.0, 3.0) on [1, 12] -- Braithwaite (2008)
# T0: Truncated Normal(1.5, 0.5) on [0.0, 3.0] -- standard range
# All others: Uniform within bounds

def _truncnorm_logpdf(x, mu, sigma, lo, hi):
    """Log-PDF of truncated normal distribution."""
    a = (lo - mu) / sigma
    b = (hi - mu) / sigma
    return truncnorm.logpdf(x, a, b, loc=mu, scale=sigma)


def log_prior(x):
    """Compute log-prior for parameter vector x."""
    params = {n: v for n, v in zip(PARAM_NAMES, x)}

    # Check bounds (hard walls)
    for name, val in params.items():
        lo, hi = dict(zip(PARAM_NAMES, PARAM_BOUNDS))[name]
        if val < lo or val > hi:
            return -np.inf

    lp = 0.0

    # MF: Truncated Normal(5.0, 3.0) on [1, 12]
    lp += _truncnorm_logpdf(params['MF'], 5.0, 3.0, 1.0, 12.0)

    # T0: Truncated Normal(1.5, 0.5) on [0.0, 3.0]
    lp += _truncnorm_logpdf(params['T0'], 1.5, 0.5, 0.0, 3.0)

    # Others: Uniform (log-prior = -log(hi - lo), constant, can omit)
    return lp


# -- Data loading --------------------------------------------------------
def load_gap_filled_climate():
    """Load gap-filled climate CSV (D-025)."""
    df = pd.read_csv(CLIMATE_PATH, parse_dates=['date'], index_col='date')
    return df[['temperature', 'precipitation']]


def prepare_water_year_arrays(climate, wy_year):
    """Extract numpy arrays for a water year from gap-filled climate."""
    start = f'{wy_year - 1}-10-01'
    end = f'{wy_year}-09-30'
    wy = climate.loc[start:end]
    if len(wy) < 300:
        return None
    T = wy['temperature'].values.astype(np.float64)
    P = wy['precipitation'].values.astype(np.float64)
    assert not np.any(np.isnan(T)), f"WY{wy_year} has NaN temperature -- check gap-filled CSV"
    assert not np.any(np.isnan(P)), f"WY{wy_year} has NaN precipitation -- check gap-filled CSV"
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


def build_calibration_targets(stakes, geodetic, climate):
    """Build calibration targets.

    Key change from v10: no coverage filter on geodetic years.
    Gap-filled climate (D-025) guarantees zero NaN, so all 20 water years
    (WY2001-2020) contribute to the geodetic constraint.
    """
    targets = {
        'stake_annual': [],
        'stake_summer': [],
        'stake_winter': [],
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

    # Geodetic years: all WY2001-2020 usable with gap-filled climate (D-025)
    # No coverage filter needed -- gap-filled CSV guarantees zero NaN
    good_years = {}
    for wy_year in range(2001, 2021):
        arrays = prepare_water_year_arrays(climate, wy_year)
        if arrays is not None:
            good_years[wy_year] = arrays

    for _, row in geodetic.iterrows():
        period = row['period']
        if period != '2000-01-01_2020-01-01':
            print(f"    {period}: SKIPPED (validation only, D-016)")
            continue
        start_str, end_str = period.split('_')
        start_year = pd.Timestamp(start_str).year
        end_year = pd.Timestamp(end_str).year
        year_data = {y: v for y, v in good_years.items() if start_year < y <= end_year}
        targets['geodetic'].append({
            'period': period, 'obs': row['dmdtda'], 'unc': row['err_dmdtda'],
            'year_data': year_data,
        })

    n_meas = lambda lst: len([t for t in lst if not t['estimated']])
    print(f"\nCalibration targets:")
    print(f"  Stake annual: {len(targets['stake_annual'])} ({n_meas(targets['stake_annual'])} measured)")
    print(f"  Stake summer: {len(targets['stake_summer'])} ({n_meas(targets['stake_summer'])} measured)")
    print(f"  Stake winter: {len(targets['stake_winter'])} ({n_meas(targets['stake_winter'])} measured)")
    print(f"  Geodetic periods: {len(targets['geodetic'])}")
    for g in targets['geodetic']:
        print(f"    {g['period']}: {len(g['year_data'])} usable years")
    return targets


def _x_to_full_params(x):
    """Convert 6-element vector to full parameter dict for the model."""
    params = {n: v for n, v in zip(PARAM_NAMES, x)}
    # Derived parameters
    params['r_ice'] = FIXED_RICE_RATIO * params['r_snow']
    params['internal_lapse'] = FIXED_LAPSE_RATE
    params['k_wind'] = FIXED_K_WIND
    return params


def compute_chi2_terms(x, fmodel, targets):
    """Compute individual chi-squared terms for the parameter vector.

    Returns list of (residual/sigma)^2 values and the geodetic penalty.
    Used by both the DE cost function and the MCMC log-likelihood.
    """
    params = _x_to_full_params(x)

    all_chi2 = []

    # -- Stake annual (Oct 1, SWE=0) ------------------------------------
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

    # -- Stake summer (observed winter SWE) ------------------------------
    for tgt in targets['stake_summer']:
        T, P, doy = tgt['arrays']
        obs_swe = tgt.get('obs_winter_swe_mm')
        winter_swe = obs_swe if obs_swe is not None else 2500.0
        result = fmodel.run(T, P, doy, params, winter_swe)
        mod = result['stake_balances'].get(tgt['site'], np.nan)
        if not np.isnan(mod):
            all_chi2.append(((mod - tgt['obs']) / tgt['unc']) ** 2)

    # -- Stake winter (Oct 1, SWE=0) ------------------------------------
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

    # -- Geodetic MB (Oct 1, SWE=0) -------------------------------------
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
            all_chi2.append((residual / gtgt['unc']) ** 2)
            excess = max(0.0, abs(residual) - gtgt['unc'])
            geodetic_penalty += GEODETIC_LAMBDA * (excess / gtgt['unc']) ** 2

    return all_chi2, geodetic_penalty


def compute_objective(x, fmodel, targets):
    """Cost function for DE."""
    all_chi2, geodetic_penalty = compute_chi2_terms(x, fmodel, targets)

    if not all_chi2:
        return 100.0

    total = np.sqrt(np.mean(all_chi2)) + geodetic_penalty
    return total


def log_likelihood(x, fmodel, targets):
    """Log-likelihood for MCMC: -0.5 * sum(chi2) + geodetic penalty."""
    # Check bounds first
    for val, (lo, hi) in zip(x, PARAM_BOUNDS):
        if val < lo or val > hi:
            return -np.inf

    try:
        all_chi2, geodetic_penalty = compute_chi2_terms(x, fmodel, targets)
    except Exception:
        return -np.inf

    if not all_chi2:
        return -np.inf

    # Standard Gaussian log-likelihood
    ll = -0.5 * np.sum(all_chi2)

    # Geodetic hard penalty (converts to log-space)
    if geodetic_penalty > 0:
        ll -= geodetic_penalty

    return ll


def log_probability(x, fmodel, targets):
    """Log-posterior = log-prior + log-likelihood."""
    lp = log_prior(x)
    if not np.isfinite(lp):
        return -np.inf
    ll = log_likelihood(x, fmodel, targets)
    if not np.isfinite(ll):
        return -np.inf
    return lp + ll


# -- Main ----------------------------------------------------------------
def main():
    t_start = time.time()
    print("=" * 70)
    print("DIXON GLACIER DETIM -- CALIBRATION v11 (CAL-011)")
    print("Bayesian Ensemble: DE (MAP) + MCMC (posterior)")
    print("D-026: Recalibration with gap-filled climate (D-025)")
    print("=" * 70)

    # -- Load data -------------------------------------------------------
    print("\nLoading gap-filled climate data (D-025)...")
    climate = load_gap_filled_climate()
    print(f"  {len(climate)} days ({climate.index.min().date()} to {climate.index.max().date()})")
    assert climate['temperature'].isna().sum() == 0, "Gap-filled climate has T NaN!"
    assert climate['precipitation'].isna().sum() == 0, "Gap-filled climate has P NaN!"

    stakes = pd.read_csv(STAKE_PATH, parse_dates=['date_start', 'date_end'])
    print(f"  Stakes: {len(stakes)} observations")

    geodetic = pd.read_csv(GEODETIC_PATH)
    print(f"  Geodetic: {len(geodetic)} periods")

    # -- Prepare grid ----------------------------------------------------
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

    # -- Initialize FastDETIM --------------------------------------------
    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config

    fmodel = FastDETIM(
        grid, ipot_table,
        transfer_alpha=config.TRANSFER_ALPHA,
        transfer_beta=config.TRANSFER_BETA,
        ref_elev=config.SNOTEL_ELEV,  # 375m (D-013)
        stake_names=config.STAKE_NAMES,
        stake_elevs=config.STAKE_ELEVS,
        stake_tol=config.STAKE_TOL,
    )

    # -- Build targets ---------------------------------------------------
    targets = build_calibration_targets(stakes, geodetic, climate)

    # -- JIT warm-up -----------------------------------------------------
    print("\nJIT compilation warm-up...")
    t0 = time.time()
    test_x = np.array([5.0, -0.003, 0.3e-3, 0.001, 2.0, 1.5])
    _ = compute_objective(test_x, fmodel, targets)
    print(f"  Done in {time.time()-t0:.1f}s")

    t0 = time.time()
    for _ in range(5):
        compute_objective(test_x, fmodel, targets)
    t_per_eval = (time.time() - t0) / 5
    print(f"  {t_per_eval*1000:.0f} ms per objective evaluation")

    # ====================================================================
    # PHASE 1: DIFFERENTIAL EVOLUTION (MAP ESTIMATE)
    # ====================================================================
    n_de_evals = DE_POPSIZE * len(PARAM_NAMES) * (DE_MAXITER + 1)
    est_de_min = n_de_evals * t_per_eval / 60

    print(f"\n{'=' * 70}")
    print(f"PHASE 1: DIFFERENTIAL EVOLUTION (MAP estimate)")
    print(f"{'=' * 70}")
    print(f"  Parameters: {len(PARAM_NAMES)}")
    print(f"  Population: {DE_POPSIZE} x {len(PARAM_NAMES)} = {DE_POPSIZE * len(PARAM_NAMES)}")
    print(f"  Max iterations: {DE_MAXITER}")
    print(f"  Estimated time: {est_de_min:.0f} min for {n_de_evals} evaluations")
    print(f"  Fixed: lapse_rate={FIXED_LAPSE_RATE*1000:.1f} C/km, "
          f"r_ice/r_snow={FIXED_RICE_RATIO:.1f}, k_wind={FIXED_K_WIND}")
    print(f"  Bounds:")
    for name, (lo, hi) in zip(PARAM_NAMES, PARAM_BOUNDS):
        print(f"    {name:15s}: [{lo:.6f}, {hi:.6f}]")
    print(f"  Priors: MF~TN(5,3), T0~TN(1.5,0.5), others uniform")
    print(f"  Cost: inverse-variance + geodetic hard penalty (lambda={GEODETIC_LAMBDA})")
    print()

    eval_count = [0]
    best_cost = [np.inf]
    de_log = []

    def de_wrapper(x):
        eval_count[0] += 1
        cost = compute_objective(x, fmodel, targets)
        if cost < best_cost[0]:
            best_cost[0] = cost
        params = {n: v for n, v in zip(PARAM_NAMES, x)}
        de_log.append({**params, 'cost': cost, 'eval': eval_count[0]})
        if eval_count[0] % 50 == 0:
            elapsed = time.time() - t_start
            print(f"  eval {eval_count[0]:5d} | cost={cost:.3f} | best={best_cost[0]:.3f} | "
                  f"MF={params['MF']:.2f} pc={params['precip_corr']:.2f} "
                  f"T0={params['T0']:.1f} r_s={params['r_snow']*1e3:.3f} | {elapsed:.0f}s")
        return cost

    de_result = differential_evolution(
        de_wrapper, bounds=PARAM_BOUNDS,
        maxiter=DE_MAXITER, popsize=DE_POPSIZE, seed=DE_SEED,
        tol=DE_TOL, mutation=DE_MUTATION, recombination=DE_RECOMBINATION,
        init='latinhypercube', disp=True, workers=1,
    )

    map_params = {name: val for name, val in zip(PARAM_NAMES, de_result.x)}
    de_elapsed = time.time() - t_start

    print(f"\n{'=' * 70}")
    print(f"PHASE 1 COMPLETE -- MAP estimate")
    print(f"{'=' * 70}")
    print(f"  Success: {de_result.success}")
    print(f"  Message: {de_result.message}")
    print(f"  Final cost: {de_result.fun:.4f}")
    print(f"  Evaluations: {eval_count[0]}")
    print(f"  Wall time: {de_elapsed:.0f}s ({de_elapsed/60:.1f} min)")
    print(f"\n  MAP parameters:")
    for k, v in map_params.items():
        if 'r_' in k:
            print(f"    {k:15s}: {v:.6f} ({v*1000:.3f} x 10^-3)")
        else:
            print(f"    {k:15s}: {v:.4f}")
    print(f"  Derived: r_ice = {FIXED_RICE_RATIO * map_params['r_snow']*1000:.3f} x 10^-3")
    print(f"  Fixed: lapse_rate = {FIXED_LAPSE_RATE*1000:.1f} C/km")

    # Save DE outputs
    with open(OUTPUT_DIR / 'best_params_v11.json', 'w') as f:
        save_params = dict(map_params)
        save_params['r_ice'] = FIXED_RICE_RATIO * map_params['r_snow']
        save_params['lapse_rate'] = FIXED_LAPSE_RATE
        save_params['k_wind'] = FIXED_K_WIND
        json.dump(save_params, f, indent=2)

    pd.DataFrame(de_log).to_csv(OUTPUT_DIR / 'calibration_log_v11_de.csv', index=False)

    # -- Validation at MAP -----------------------------------------------
    run_params = _x_to_full_params(de_result.x)

    print(f"\n{'=' * 70}")
    print("MAP VALIDATION")
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
                    obs_row_s = obs_rows[obs_rows['site_id'] == site]
                    obs = obs_row_s['mb_obs_mwe'].values[0] if len(obs_row_s) > 0 else np.nan
                    diff = mod - obs if not (np.isnan(mod) or np.isnan(obs)) else np.nan
                    obs_str = f"{obs:+.2f}" if not np.isnan(obs) else "  n/a"
                    diff_str = f"{diff:+.2f}" if not np.isnan(diff) else "  n/a"
                    print(f"      {site} annual: mod={mod:+.2f}, obs={obs_str}, res={diff_str}")

    # Geodetic validation
    print(f"\n  Geodetic MB (calibration target):")
    good_years = {}
    for wy_year in range(2001, 2021):
        arrays = prepare_water_year_arrays(climate, wy_year)
        if arrays is not None:
            good_years[wy_year] = arrays

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

    print(f"\n  Geodetic sub-periods (validation only):")
    geodetic_all = pd.read_csv(GEODETIC_PATH)
    for _, row in geodetic_all.iterrows():
        period = row['period']
        if period == '2000-01-01_2020-01-01':
            continue
        start_str, end_str = period.split('_')
        start_year = pd.Timestamp(start_str).year
        end_year = pd.Timestamp(end_str).year
        year_data = {y: v for y, v in good_years.items() if start_year < y <= end_year}
        if not year_data:
            continue
        bals = []
        for wy_year, arrays in year_data.items():
            T, P, doy = arrays
            r = fmodel.run(T, P, doy, run_params, 0.0)
            bals.append(r['glacier_wide_balance'])
        mean_bal = np.mean(bals)
        print(f"    {period}: modeled={mean_bal:+.3f}, observed={row['dmdtda']:+.3f} "
              f"+/- {row['err_dmdtda']:.3f} ({len(bals)} years)")

    # ====================================================================
    # PHASE 2: MCMC SAMPLING (POSTERIOR ENSEMBLE)
    # ====================================================================
    mcmc_start = time.time()
    ndim = len(PARAM_NAMES)
    est_mcmc_evals = MCMC_NWALKERS * MCMC_NSTEPS
    est_mcmc_hrs = est_mcmc_evals * t_per_eval / 3600

    print(f"\n{'=' * 70}")
    print(f"PHASE 2: MCMC SAMPLING (emcee)")
    print(f"{'=' * 70}")
    print(f"  Walkers: {MCMC_NWALKERS}")
    print(f"  Steps: {MCMC_NSTEPS}")
    print(f"  Total evaluations: {est_mcmc_evals}")
    print(f"  Estimated time: {est_mcmc_hrs:.1f} hours (single core)")
    print(f"  Burn-in: {MCMC_BURNIN} steps minimum")
    print()

    # Initialize walkers around MAP estimate
    map_x = de_result.x.copy()
    pos = np.empty((MCMC_NWALKERS, ndim))
    for i in range(MCMC_NWALKERS):
        while True:
            # Small random perturbation around MAP
            proposal = map_x * (1.0 + MCMC_INIT_SPREAD * np.random.randn(ndim))
            # Ensure within bounds
            in_bounds = True
            for j, (lo, hi) in enumerate(PARAM_BOUNDS):
                if proposal[j] < lo or proposal[j] > hi:
                    in_bounds = False
                    break
            if in_bounds:
                pos[i] = proposal
                break

    # Set up sampler (single-core -- numba handles inner parallelism)
    sampler = emcee.EnsembleSampler(
        MCMC_NWALKERS, ndim, log_probability,
        args=(fmodel, targets),
    )

    # Run MCMC with progress reporting
    print("  Running MCMC chain...")
    step_count = 0
    for sample in sampler.sample(pos, iterations=MCMC_NSTEPS, progress=False):
        step_count += 1
        if step_count % 500 == 0:
            elapsed = time.time() - mcmc_start
            accept_frac = np.mean(sampler.acceptance_fraction)
            rate = step_count / elapsed if elapsed > 0 else 0
            eta = (MCMC_NSTEPS - step_count) / rate / 3600 if rate > 0 else 0
            print(f"    step {step_count:5d}/{MCMC_NSTEPS} | "
                  f"accept={accept_frac:.3f} | "
                  f"elapsed={elapsed/60:.1f}min | "
                  f"ETA={eta:.1f}hrs")

    mcmc_elapsed = time.time() - mcmc_start

    print(f"\n  MCMC complete in {mcmc_elapsed:.0f}s ({mcmc_elapsed/3600:.1f} hours)")
    print(f"  Mean acceptance fraction: {np.mean(sampler.acceptance_fraction):.3f}")

    # -- Convergence diagnostics -----------------------------------------
    print(f"\n  Convergence diagnostics:")
    try:
        tau = sampler.get_autocorr_time(quiet=True)
        print(f"    Autocorrelation times: {', '.join(f'{t:.0f}' for t in tau)}")
        print(f"    Max tau: {np.max(tau):.0f}")
        print(f"    Chain length / max(tau): {MCMC_NSTEPS / np.max(tau):.0f}x "
              f"(want >50x)")
        burnin = int(2 * np.max(tau))
        thin = int(0.5 * np.min(tau))
        thin = max(thin, 1)
    except emcee.autocorr.AutocorrError:
        print("    WARNING: Autocorrelation time estimate unreliable")
        print("    Using default burn-in and thinning")
        burnin = MCMC_BURNIN
        thin = 10
        tau = None

    burnin = max(burnin, MCMC_BURNIN)
    print(f"    Burn-in: {burnin} steps")
    print(f"    Thinning: every {thin} steps")

    # -- Extract posterior samples ----------------------------------------
    flat_samples = sampler.get_chain(discard=burnin, thin=thin, flat=True)
    n_samples = len(flat_samples)
    print(f"    Independent posterior samples: {n_samples}")

    # Save full chain
    chain = sampler.get_chain()  # shape: (nsteps, nwalkers, ndim)
    np.save(OUTPUT_DIR / 'mcmc_chain_v11.npy', chain)

    # Save log-probability chain
    log_prob = sampler.get_log_prob()
    np.save(OUTPUT_DIR / 'mcmc_logprob_v11.npy', log_prob)

    # Save posterior samples as CSV
    posterior_df = pd.DataFrame(flat_samples, columns=PARAM_NAMES)
    # Add derived parameters
    posterior_df['r_ice'] = FIXED_RICE_RATIO * posterior_df['r_snow']
    posterior_df['lapse_rate'] = FIXED_LAPSE_RATE
    posterior_df.to_csv(OUTPUT_DIR / 'posterior_samples_v11.csv', index=False)

    # -- Posterior summary ------------------------------------------------
    print(f"\n{'=' * 70}")
    print("POSTERIOR SUMMARY")
    print(f"{'=' * 70}")
    print(f"  {'Parameter':15s} {'Median':>10s} {'16th':>10s} {'84th':>10s} {'MAP':>10s}")
    print(f"  {'-'*55}")
    for i, name in enumerate(PARAM_NAMES):
        q16, q50, q84 = np.percentile(flat_samples[:, i], [16, 50, 84])
        map_val = map_params[name]
        if 'r_' in name:
            print(f"  {name:15s} {q50*1e3:10.3f} {q16*1e3:10.3f} {q84*1e3:10.3f} {map_val*1e3:10.3f}  (x10^-3)")
        else:
            print(f"  {name:15s} {q50:10.4f} {q16:10.4f} {q84:10.4f} {map_val:10.4f}")

    # -- Corner plot -----------------------------------------------------
    try:
        import corner
        labels = [
            r'MF (mm d$^{-1}$ K$^{-1}$)',
            r'MF$_{\rm grad}$ (mm d$^{-1}$ K$^{-1}$ m$^{-1}$)',
            r'$r_{\rm snow}$ (mm m$^2$ W$^{-1}$ d$^{-1}$ K$^{-1}$)',
            r'$\gamma_p$ (m$^{-1}$)',
            r'$C_p$',
            r'$T_0$ ($^\circ$C)',
        ]
        fig = corner.corner(
            flat_samples, labels=labels,
            quantiles=[0.16, 0.5, 0.84],
            show_titles=True, title_kwargs={"fontsize": 10},
            truths=de_result.x,
        )
        fig.savefig(OUTPUT_DIR / 'corner_plot_v11.png', dpi=150, bbox_inches='tight')
        print(f"\n  Corner plot saved to {OUTPUT_DIR / 'corner_plot_v11.png'}")
    except Exception as e:
        print(f"\n  Corner plot failed: {e}")

    # -- Save summary ----------------------------------------------------
    total_elapsed = time.time() - t_start
    summary = {
        'version': 11,
        'calibration_id': 'CAL-011',
        'method': 'DE (MAP) + emcee MCMC (posterior ensemble)',
        'decision': 'D-026',
        'changes_from_v10': [
            'Gap-filled climate input (D-025): 5-station cascade, zero NaN',
            'Coverage filter removed: all 20 geodetic years now contribute',
            'Previously poisoned years (WY2000, WY2001, WY2005, WY2020) fixed',
            'Same 6 free params, bounds, priors, and fixed params as CAL-010',
        ],
        'de': {
            'success': bool(de_result.success),
            'message': de_result.message,
            'cost': float(de_result.fun),
            'n_evaluations': eval_count[0],
            'wall_time_s': de_elapsed,
            'map_params': map_params,
        },
        'mcmc': {
            'n_walkers': MCMC_NWALKERS,
            'n_steps': MCMC_NSTEPS,
            'burn_in': burnin,
            'thin': thin,
            'n_posterior_samples': n_samples,
            'mean_acceptance_fraction': float(np.mean(sampler.acceptance_fraction)),
            'autocorr_times': tau.tolist() if tau is not None else None,
            'wall_time_s': mcmc_elapsed,
        },
        'fixed_params': {
            'lapse_rate': FIXED_LAPSE_RATE,
            'r_ice_ratio': FIXED_RICE_RATIO,
            'k_wind': FIXED_K_WIND,
            'ref_elev': float(config.SNOTEL_ELEV),
        },
        'total_wall_time_s': total_elapsed,
    }
    with open(OUTPUT_DIR / 'calibration_summary_v11.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n{'=' * 70}")
    print(f"CALIBRATION v11 (CAL-011) COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Total wall time: {total_elapsed:.0f}s ({total_elapsed/3600:.1f} hours)")
    print(f"  DE evaluations: {eval_count[0]}")
    print(f"  MCMC evaluations: {MCMC_NWALKERS * MCMC_NSTEPS}")
    print(f"  Posterior samples: {n_samples}")
    print(f"\n  Outputs saved to {OUTPUT_DIR}/ (v11)")
    print("Done!")


if __name__ == '__main__':
    main()
