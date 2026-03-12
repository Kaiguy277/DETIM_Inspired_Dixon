"""
Bayesian ensemble calibration of Dixon Glacier DETIM — v12 (D-027).

Multi-seed DE + multi-chain MCMC to address potential multimodality.

Approach (Option A from Rounce et al. 2020, adapted):
  Phase 1: Run DE with N_SEEDS different random seeds to find distinct optima
  Phase 2: Cluster DE optima — if multiple distinct modes exist, run separate
           MCMC chains from each; if all converge to one region, run single MCMC
  Phase 3: Combine posterior samples from all chains

Same model configuration as CAL-011 (D-026):
  - Gap-filled climate (D-025), zero NaN, all 20 geodetic years
  - 6 free parameters, same bounds and priors
  - Fixed lapse=-5.0 C/km, r_ice=2×r_snow, k_wind=0

See research_log/decisions.md D-027 for rationale.
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
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import fcluster, linkage
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
DE_TOL = 1e-4
DE_MUTATION = (0.5, 1.0)
DE_RECOMBINATION = 0.7

# Multiple seeds to probe for multimodality
DE_SEEDS = [42, 123, 456, 789, 2024]
N_SEEDS = len(DE_SEEDS)

# Clustering: if two DE optima are within this fraction of parameter range,
# they are considered the same mode
CLUSTER_THRESHOLD = 0.10  # 10% of parameter range

# -- MCMC Configuration --------------------------------------------------
MCMC_NWALKERS = 24       # 4x ndim
MCMC_NSTEPS = 10000      # per walker per chain
MCMC_BURNIN = 2000       # minimum burn-in
MCMC_INIT_SPREAD = 1e-3  # relative spread for walker initialization

# -- Fixed parameters (D-017) -------------------------------------------
FIXED_LAPSE_RATE = -5.0e-3  # C/m
FIXED_RICE_RATIO = 2.0      # r_ice/r_snow
FIXED_K_WIND = 0.0

# Geodetic hard constraint penalty (D-014)
GEODETIC_LAMBDA = 50.0

# -- Parameters and bounds (6 free) -------------------------------------
PARAM_NAMES = ['MF', 'MF_grad', 'r_snow', 'precip_grad', 'precip_corr', 'T0']
PARAM_BOUNDS = [
    (1.0, 12.0),            # MF (mm d-1 K-1)
    (-0.01, 0.0),           # MF_grad (mm d-1 K-1 per m)
    (0.02e-3, 2.0e-3),      # r_snow
    (0.0002, 0.006),        # precip_grad (fraction/m)
    (1.2, 4.0),             # precip_corr
    (0.0, 3.0),             # T0 (C)
]
PARAM_RANGES = np.array([hi - lo for lo, hi in PARAM_BOUNDS])


# -- Prior distributions (D-017) ----------------------------------------
def _truncnorm_logpdf(x, mu, sigma, lo, hi):
    """Log-PDF of truncated normal distribution."""
    a = (lo - mu) / sigma
    b = (hi - mu) / sigma
    return truncnorm.logpdf(x, a, b, loc=mu, scale=sigma)


def log_prior(x):
    """Compute log-prior for parameter vector x."""
    params = {n: v for n, v in zip(PARAM_NAMES, x)}
    for name, val in params.items():
        lo, hi = dict(zip(PARAM_NAMES, PARAM_BOUNDS))[name]
        if val < lo or val > hi:
            return -np.inf
    lp = 0.0
    lp += _truncnorm_logpdf(params['MF'], 5.0, 3.0, 1.0, 12.0)
    lp += _truncnorm_logpdf(params['T0'], 1.5, 0.5, 0.0, 3.0)
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
    assert not np.any(np.isnan(T)), f"WY{wy_year} has NaN temperature"
    assert not np.any(np.isnan(P)), f"WY{wy_year} has NaN precipitation"
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
    """Build calibration targets (same as v11 -- no coverage filter)."""
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

    # All WY2001-2020 usable with gap-filled climate (D-025)
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
    params['r_ice'] = FIXED_RICE_RATIO * params['r_snow']
    params['internal_lapse'] = FIXED_LAPSE_RATE
    params['k_wind'] = FIXED_K_WIND
    return params


def compute_chi2_terms(x, fmodel, targets):
    """Compute individual chi-squared terms for the parameter vector."""
    params = _x_to_full_params(x)
    all_chi2 = []

    # Stake annual (Oct 1, SWE=0)
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

    # Stake summer (observed winter SWE)
    for tgt in targets['stake_summer']:
        T, P, doy = tgt['arrays']
        obs_swe = tgt.get('obs_winter_swe_mm')
        winter_swe = obs_swe if obs_swe is not None else 2500.0
        result = fmodel.run(T, P, doy, params, winter_swe)
        mod = result['stake_balances'].get(tgt['site'], np.nan)
        if not np.isnan(mod):
            all_chi2.append(((mod - tgt['obs']) / tgt['unc']) ** 2)

    # Stake winter (Oct 1, SWE=0)
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

    # Geodetic MB (Oct 1, SWE=0)
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
    return np.sqrt(np.mean(all_chi2)) + geodetic_penalty


def log_likelihood(x, fmodel, targets):
    """Log-likelihood for MCMC."""
    for val, (lo, hi) in zip(x, PARAM_BOUNDS):
        if val < lo or val > hi:
            return -np.inf
    try:
        all_chi2, geodetic_penalty = compute_chi2_terms(x, fmodel, targets)
    except Exception:
        return -np.inf
    if not all_chi2:
        return -np.inf
    ll = -0.5 * np.sum(all_chi2)
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


# -- Clustering ----------------------------------------------------------
def cluster_optima(optima_x, optima_cost):
    """Cluster DE optima into distinct modes.

    Uses normalized parameter distance. Two optima within CLUSTER_THRESHOLD
    of each other (fraction of parameter range) are the same mode.

    Returns list of mode dicts: {x, cost, seed_indices}
    """
    n = len(optima_x)
    if n == 1:
        return [{'x': optima_x[0], 'cost': optima_cost[0], 'seed_indices': [0]}]

    # Normalize parameters to [0, 1] by their ranges
    X_norm = np.array([(x - np.array([lo for lo, hi in PARAM_BOUNDS])) / PARAM_RANGES
                       for x in optima_x])

    # Hierarchical clustering with complete linkage
    dists = pdist(X_norm, metric='chebyshev')  # max per-dimension distance
    Z = linkage(dists, method='complete')
    labels = fcluster(Z, t=CLUSTER_THRESHOLD, criterion='distance')

    modes = []
    for label in np.unique(labels):
        mask = labels == label
        indices = np.where(mask)[0].tolist()
        # Pick the best (lowest cost) within the cluster
        best_idx = indices[np.argmin([optima_cost[i] for i in indices])]
        modes.append({
            'x': optima_x[best_idx],
            'cost': optima_cost[best_idx],
            'seed_indices': indices,
        })

    # Sort by cost
    modes.sort(key=lambda m: m['cost'])
    return modes


# -- Main ----------------------------------------------------------------
def main():
    t_start = time.time()
    print("=" * 70)
    print("DIXON GLACIER DETIM -- CALIBRATION v12 (CAL-012)")
    print("Multi-seed DE + Multi-chain MCMC")
    print("D-027: Address potential posterior multimodality")
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
        ref_elev=config.SNOTEL_ELEV,
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
    # PHASE 1: MULTI-SEED DIFFERENTIAL EVOLUTION
    # ====================================================================
    n_de_evals_per = DE_POPSIZE * len(PARAM_NAMES) * (DE_MAXITER + 1)
    est_de_min_per = n_de_evals_per * t_per_eval / 60
    est_de_total = est_de_min_per * N_SEEDS

    print(f"\n{'=' * 70}")
    print(f"PHASE 1: MULTI-SEED DIFFERENTIAL EVOLUTION ({N_SEEDS} seeds)")
    print(f"{'=' * 70}")
    print(f"  Seeds: {DE_SEEDS}")
    print(f"  Per seed: ~{est_de_min_per:.0f} min ({n_de_evals_per} evals)")
    print(f"  Total estimated: ~{est_de_total:.0f} min ({est_de_total/60:.1f} hrs)")
    print(f"  Parameters: {len(PARAM_NAMES)}")
    print(f"  Cluster threshold: {CLUSTER_THRESHOLD*100:.0f}% of parameter range")
    print(f"  Bounds:")
    for name, (lo, hi) in zip(PARAM_NAMES, PARAM_BOUNDS):
        print(f"    {name:15s}: [{lo:.6f}, {hi:.6f}]")
    print()

    all_optima_x = []
    all_optima_cost = []
    all_de_logs = []

    for seed_idx, seed in enumerate(DE_SEEDS):
        print(f"\n{'─' * 50}")
        print(f"  DE seed {seed_idx+1}/{N_SEEDS} (seed={seed})")
        print(f"{'─' * 50}")

        seed_start = time.time()
        eval_count = [0]
        best_cost = [np.inf]
        de_log = []

        def de_wrapper(x, _seed=seed, _eval=eval_count, _best=best_cost, _log=de_log):
            _eval[0] += 1
            cost = compute_objective(x, fmodel, targets)
            if cost < _best[0]:
                _best[0] = cost
            params = {n: v for n, v in zip(PARAM_NAMES, x)}
            _log.append({**params, 'cost': cost, 'eval': _eval[0], 'seed': _seed})
            if _eval[0] % 200 == 0:
                elapsed = time.time() - seed_start
                print(f"    eval {_eval[0]:5d} | cost={cost:.3f} | best={_best[0]:.3f} | "
                      f"MF={params['MF']:.2f} pc={params['precip_corr']:.2f} "
                      f"T0={params['T0']:.1f} r_s={params['r_snow']*1e3:.3f} | {elapsed:.0f}s")
            return cost

        result = differential_evolution(
            de_wrapper, bounds=PARAM_BOUNDS,
            maxiter=DE_MAXITER, popsize=DE_POPSIZE, seed=seed,
            tol=DE_TOL, mutation=DE_MUTATION, recombination=DE_RECOMBINATION,
            init='latinhypercube', disp=False, workers=1,
        )

        seed_elapsed = time.time() - seed_start
        params = {n: v for n, v in zip(PARAM_NAMES, result.x)}

        print(f"\n    Seed {seed}: cost={result.fun:.4f}, converged={result.success}, "
              f"evals={eval_count[0]}, time={seed_elapsed:.0f}s")
        print(f"    Params: MF={params['MF']:.3f}, MF_grad={params['MF_grad']:.5f}, "
              f"r_snow={params['r_snow']*1e3:.3f}e-3, "
              f"pg={params['precip_grad']:.5f}, pc={params['precip_corr']:.3f}, "
              f"T0={params['T0']:.3f}")

        all_optima_x.append(result.x.copy())
        all_optima_cost.append(result.fun)
        all_de_logs.extend(de_log)

    # Save all DE logs
    pd.DataFrame(all_de_logs).to_csv(OUTPUT_DIR / 'calibration_log_v12_de.csv', index=False)

    # ====================================================================
    # PHASE 1.5: CLUSTER OPTIMA
    # ====================================================================
    de_elapsed = time.time() - t_start

    print(f"\n{'=' * 70}")
    print(f"PHASE 1.5: CLUSTERING DE OPTIMA")
    print(f"{'=' * 70}")
    print(f"  DE total time: {de_elapsed:.0f}s ({de_elapsed/60:.1f} min)")
    print(f"\n  All optima:")
    for i, (x, cost) in enumerate(zip(all_optima_x, all_optima_cost)):
        p = {n: v for n, v in zip(PARAM_NAMES, x)}
        print(f"    Seed {DE_SEEDS[i]:4d}: cost={cost:.4f} | "
              f"MF={p['MF']:.3f} pc={p['precip_corr']:.3f} T0={p['T0']:.3f} "
              f"r_s={p['r_snow']*1e3:.3f}")

    modes = cluster_optima(all_optima_x, all_optima_cost)

    print(f"\n  Distinct modes found: {len(modes)}")
    for i, mode in enumerate(modes):
        p = {n: v for n, v in zip(PARAM_NAMES, mode['x'])}
        seed_list = [DE_SEEDS[j] for j in mode['seed_indices']]
        print(f"\n    Mode {i+1} (seeds: {seed_list}, cost={mode['cost']:.4f}):")
        for name in PARAM_NAMES:
            val = p[name]
            lo, hi = dict(zip(PARAM_NAMES, PARAM_BOUNDS))[name]
            at_lo = val <= lo + 0.01 * (hi - lo)
            at_hi = val >= hi - 0.01 * (hi - lo)
            flag = " <-- AT LOWER BOUND" if at_lo else (" <-- AT UPPER BOUND" if at_hi else "")
            if 'r_' in name:
                print(f"      {name:15s}: {val:.6f} ({val*1e3:.3f}e-3){flag}")
            else:
                print(f"      {name:15s}: {val:.6f}{flag}")

    # Save DE summary
    de_summary = {
        'n_seeds': N_SEEDS,
        'seeds': DE_SEEDS,
        'optima': [
            {
                'seed': DE_SEEDS[i],
                'cost': float(all_optima_cost[i]),
                'params': {n: float(v) for n, v in zip(PARAM_NAMES, all_optima_x[i])},
            }
            for i in range(N_SEEDS)
        ],
        'n_modes': len(modes),
        'modes': [
            {
                'mode_id': i + 1,
                'cost': float(mode['cost']),
                'seeds': [DE_SEEDS[j] for j in mode['seed_indices']],
                'params': {n: float(v) for n, v in zip(PARAM_NAMES, mode['x'])},
            }
            for i, mode in enumerate(modes)
        ],
        'cluster_threshold': CLUSTER_THRESHOLD,
        'de_wall_time_s': de_elapsed,
    }
    with open(OUTPUT_DIR / 'de_multistart_v12.json', 'w') as f:
        json.dump(de_summary, f, indent=2)

    # Save best overall params
    best_mode = modes[0]
    with open(OUTPUT_DIR / 'best_params_v12.json', 'w') as f:
        save_params = {n: float(v) for n, v in zip(PARAM_NAMES, best_mode['x'])}
        save_params['r_ice'] = FIXED_RICE_RATIO * save_params['r_snow']
        save_params['lapse_rate'] = FIXED_LAPSE_RATE
        save_params['k_wind'] = FIXED_K_WIND
        json.dump(save_params, f, indent=2)

    # ====================================================================
    # PHASE 2: MCMC FROM EACH MODE
    # ====================================================================
    ndim = len(PARAM_NAMES)
    est_mcmc_evals = MCMC_NWALKERS * MCMC_NSTEPS
    est_mcmc_hrs_per = est_mcmc_evals * t_per_eval / 3600

    print(f"\n{'=' * 70}")
    print(f"PHASE 2: MCMC SAMPLING ({len(modes)} chain(s))")
    print(f"{'=' * 70}")
    print(f"  Chains to run: {len(modes)}")
    print(f"  Per chain: {MCMC_NWALKERS} walkers x {MCMC_NSTEPS} steps = {est_mcmc_evals} evals")
    print(f"  Per chain estimated: {est_mcmc_hrs_per:.1f} hours")
    print(f"  Total estimated: {est_mcmc_hrs_per * len(modes):.1f} hours")
    print()

    all_flat_samples = []
    chain_summaries = []

    for mode_idx, mode in enumerate(modes):
        mcmc_start = time.time()
        mode_id = mode_idx + 1

        print(f"\n{'─' * 50}")
        print(f"  MCMC chain {mode_id}/{len(modes)} (mode cost={mode['cost']:.4f})")
        print(f"{'─' * 50}")

        # Initialize walkers around this mode's optimum
        map_x = mode['x'].copy()
        pos = np.empty((MCMC_NWALKERS, ndim))
        for i in range(MCMC_NWALKERS):
            while True:
                proposal = map_x * (1.0 + MCMC_INIT_SPREAD * np.random.randn(ndim))
                in_bounds = True
                for j, (lo, hi) in enumerate(PARAM_BOUNDS):
                    if proposal[j] < lo or proposal[j] > hi:
                        in_bounds = False
                        break
                if in_bounds:
                    pos[i] = proposal
                    break

        sampler = emcee.EnsembleSampler(
            MCMC_NWALKERS, ndim, log_probability,
            args=(fmodel, targets),
        )

        print(f"    Running MCMC chain {mode_id}...")
        step_count = 0
        for sample in sampler.sample(pos, iterations=MCMC_NSTEPS, progress=False):
            step_count += 1
            if step_count % 500 == 0:
                elapsed = time.time() - mcmc_start
                accept_frac = np.mean(sampler.acceptance_fraction)
                rate = step_count / elapsed if elapsed > 0 else 0
                eta = (MCMC_NSTEPS - step_count) / rate / 3600 if rate > 0 else 0
                print(f"      step {step_count:5d}/{MCMC_NSTEPS} | "
                      f"accept={accept_frac:.3f} | "
                      f"elapsed={elapsed/60:.1f}min | "
                      f"ETA={eta:.1f}hrs")

        mcmc_elapsed = time.time() - mcmc_start
        accept_frac = float(np.mean(sampler.acceptance_fraction))

        print(f"\n    Chain {mode_id} complete in {mcmc_elapsed:.0f}s ({mcmc_elapsed/3600:.1f} hrs)")
        print(f"    Acceptance fraction: {accept_frac:.3f}")

        # Convergence diagnostics
        try:
            tau = sampler.get_autocorr_time(quiet=True)
            print(f"    Autocorr times: {', '.join(f'{t:.0f}' for t in tau)}")
            print(f"    Max tau: {np.max(tau):.0f}, chain/tau: {MCMC_NSTEPS/np.max(tau):.0f}x")
            burnin = int(2 * np.max(tau))
            thin = max(int(0.5 * np.min(tau)), 1)
            tau_list = tau.tolist()
        except emcee.autocorr.AutocorrError:
            print("    WARNING: Autocorrelation time unreliable, using defaults")
            burnin = MCMC_BURNIN
            thin = 10
            tau_list = None

        burnin = max(burnin, MCMC_BURNIN)
        flat_samples = sampler.get_chain(discard=burnin, thin=thin, flat=True)
        n_samples = len(flat_samples)
        print(f"    Burn-in: {burnin}, thin: {thin}, posterior samples: {n_samples}")

        # Save per-chain outputs
        chain = sampler.get_chain()
        np.save(OUTPUT_DIR / f'mcmc_chain_v12_mode{mode_id}.npy', chain)
        np.save(OUTPUT_DIR / f'mcmc_logprob_v12_mode{mode_id}.npy', sampler.get_log_prob())

        all_flat_samples.append(flat_samples)
        chain_summaries.append({
            'mode_id': mode_id,
            'mode_cost': float(mode['cost']),
            'mode_seeds': [DE_SEEDS[j] for j in mode['seed_indices']],
            'mode_params': {n: float(v) for n, v in zip(PARAM_NAMES, mode['x'])},
            'n_walkers': MCMC_NWALKERS,
            'n_steps': MCMC_NSTEPS,
            'burn_in': burnin,
            'thin': thin,
            'n_samples': n_samples,
            'acceptance_fraction': accept_frac,
            'autocorr_times': tau_list,
            'wall_time_s': mcmc_elapsed,
        })

    # ====================================================================
    # PHASE 3: COMBINE POSTERIORS
    # ====================================================================
    print(f"\n{'=' * 70}")
    print(f"PHASE 3: COMBINING POSTERIORS")
    print(f"{'=' * 70}")

    # Equal weighting across modes (conservative; could use BIC/evidence)
    combined_samples = np.vstack(all_flat_samples)
    n_total = len(combined_samples)

    print(f"  Chains: {len(modes)}")
    for i, fs in enumerate(all_flat_samples):
        print(f"    Mode {i+1}: {len(fs)} samples")
    print(f"  Combined: {n_total} samples")

    # Save combined posterior
    posterior_df = pd.DataFrame(combined_samples, columns=PARAM_NAMES)
    posterior_df['r_ice'] = FIXED_RICE_RATIO * posterior_df['r_snow']
    posterior_df['lapse_rate'] = FIXED_LAPSE_RATE
    posterior_df.to_csv(OUTPUT_DIR / 'posterior_samples_v12.csv', index=False)

    # -- Posterior summary ------------------------------------------------
    print(f"\n{'=' * 70}")
    print("POSTERIOR SUMMARY (combined)")
    print(f"{'=' * 70}")
    print(f"  {'Parameter':15s} {'Median':>10s} {'16th':>10s} {'84th':>10s} {'Best MAP':>10s}")
    print(f"  {'-'*55}")
    best_x = modes[0]['x']
    for i, name in enumerate(PARAM_NAMES):
        q16, q50, q84 = np.percentile(combined_samples[:, i], [16, 50, 84])
        map_val = best_x[i]
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
            combined_samples, labels=labels,
            quantiles=[0.16, 0.5, 0.84],
            show_titles=True, title_kwargs={"fontsize": 10},
            truths=best_x,
        )
        fig.savefig(OUTPUT_DIR / 'corner_plot_v12.png', dpi=150, bbox_inches='tight')
        print(f"\n  Corner plot saved to {OUTPUT_DIR / 'corner_plot_v12.png'}")
    except Exception as e:
        print(f"\n  Corner plot failed: {e}")

    # -- MAP Validation --------------------------------------------------
    run_params = _x_to_full_params(best_x)

    print(f"\n{'=' * 70}")
    print("MAP VALIDATION (best mode)")
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

    # -- Save final summary ----------------------------------------------
    total_elapsed = time.time() - t_start
    summary = {
        'version': 12,
        'calibration_id': 'CAL-012',
        'method': 'Multi-seed DE + Multi-chain MCMC (Option A)',
        'decision': 'D-027',
        'changes_from_v11': [
            'Multi-seed DE (5 seeds) to detect multimodality',
            'Hierarchical clustering of DE optima',
            'Separate MCMC chain from each distinct mode',
            'Combined posterior from all chains (equal weighting)',
        ],
        'de': de_summary,
        'mcmc_chains': chain_summaries,
        'combined_posterior': {
            'n_total_samples': n_total,
            'n_modes': len(modes),
        },
        'fixed_params': {
            'lapse_rate': FIXED_LAPSE_RATE,
            'r_ice_ratio': FIXED_RICE_RATIO,
            'k_wind': FIXED_K_WIND,
            'ref_elev': float(config.SNOTEL_ELEV),
        },
        'total_wall_time_s': total_elapsed,
    }
    with open(OUTPUT_DIR / 'calibration_summary_v12.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n{'=' * 70}")
    print(f"CALIBRATION v12 (CAL-012) COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Total wall time: {total_elapsed:.0f}s ({total_elapsed/3600:.1f} hours)")
    print(f"  DE seeds: {N_SEEDS}, modes found: {len(modes)}")
    print(f"  MCMC chains: {len(modes)}, combined samples: {n_total}")
    print(f"\n  Outputs saved to {OUTPUT_DIR}/ (v12)")
    print("Done!")


if __name__ == '__main__':
    main()
