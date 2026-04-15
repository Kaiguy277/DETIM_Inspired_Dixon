"""
Bayesian ensemble calibration of Dixon Glacier DETIM — v14 (CAL-014, D-034+D-035).

Multi-objective calibration with snowline elevation in the MCMC likelihood
(inherited from CAL-013), PLUS two new parameters freed based on
literature review (2026-04-14):
  - lapse_rate: was fixed at -5.0 °C km⁻¹, now calibrated (D-034)
  - r_ice: was derived as 2×r_snow, now independent (D-035)

Changes from CAL-013 (v13):
  + 2 new free parameters → 8 total (was 6)
  + Updated priors for lapse_rate and r_ice (see log_prior docstring)
  + Increased MCMC walkers 24→32 (4×ndim rule)
  + Multi-seed DE retains 5 seeds for mode detection

Motivation (see research_log/decisions.md):
  D-034: Geck 2021 calibrated lapse at -2 to -6 °C/km (mean -3); our
         fixed -5.0 was at the steep end, likely causing MF compensation
         (our CAL-013 MF=7.30 is high relative to Geck mode 5.75-6.00)
  D-035: Geck calibrated r_ice/r_snow = 4.22 independently; fixing at 2.0
         was inconsistent with the closest analog study. Independent
         calibration preserves the albedo feedback for projections.

Approach (unchanged from CAL-013):
  Phase 1: Multi-seed DE (with snowline in objective)
  Phase 1.5: Cluster DE optima
  Phase 2: MCMC from each mode (with snowline in likelihood)
  Phase 3: Combine posteriors + snowline validation summary
  Phase 4: Post-hoc area evolution behavioral filter on top N posterior samples

Literature References (all verified in papers_verified/):
    Geck et al. (2021) J. Glaciol. — Eklutna precedent
    Schuster et al. (2023) Ann. Glaciol. — TI equifinality
    Petersen et al. (2013) Ann. Glaciol. — constant lapse suitability
    Gardner & Sharp (2009) Ann. Glaciol. — MF/lapse compensation
    Trüssel et al. (2015) J. Glaciol. — Yakutat DETIM
    Sjursen et al. (2023) J. Glaciol. — Bayesian ensemble
    Gabbi et al. (2012) HESS — multi-criteria behavioral filtering
    Rabatel et al. (2005) J. Glaciol. — snowline altitude uncertainties
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
SNOWLINE_DIR = PROJECT / 'snowlines_all'
OUTLINE_JSON = PROJECT / 'data' / 'glacier_outlines' / 'digitized' / 'outline_areas.json'
FARINOTTI_PATH = PROJECT / 'data' / 'ice_thickness' / 'RGI60-01.18059_thickness.tif'
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
MCMC_NWALKERS = 32       # 4x ndim (8 params in CAL-014)
MCMC_NSTEPS = 10000      # per walker per chain
MCMC_BURNIN = 2000       # minimum burn-in
MCMC_INIT_SPREAD = 1e-3  # relative spread for walker initialization

# -- Fixed parameters (CAL-014 — only k_wind remains fixed) ---------------
# D-034 (2026-04-14): Lapse rate freed based on lit review
# D-035 (2026-04-14): r_ice freed based on lit review
FIXED_K_WIND = 0.0

# Geodetic hard constraint penalty (D-014)
GEODETIC_LAMBDA = 50.0

# -- Snowline uncertainty (D-028) ----------------------------------------
# Combined uncertainty from: observed spatial spread (~50-80m),
# model grid resolution (100m), temporal mismatch.
# Consistent with Rabatel et al. (2005): 50-100m for satellite snowlines.
SIGMA_SNOWLINE = 75.0  # m

# -- Post-MCMC area filter (D-028) --------------------------------------
AREA_FILTER_N_TOP = 1000    # draw top N from posterior for area screening
AREA_RMSE_MAX = 1.0         # km²

# -- Parameters and bounds (8 free — CAL-014) ----------------------------
# Added parameters vs CAL-013:
#  - lapse_rate (D-034): truncated-normal prior N(-4.5e-3, 1.0e-3)
#  - r_ice (D-035): truncated-normal prior N(4.0e-3, 2.0e-3), decoupled from r_snow
PARAM_NAMES = ['MF', 'MF_grad', 'r_snow', 'r_ice', 'precip_grad', 'precip_corr', 'T0', 'lapse_rate']
PARAM_BOUNDS = [
    (1.0, 12.0),            # MF (mm d-1 K-1)
    (-0.01, 0.0),           # MF_grad (mm d-1 K-1 per m)
    (0.02e-3, 2.0e-3),      # r_snow
    (0.02e-3, 10.0e-3),     # r_ice (D-035, decoupled)
    (0.0002, 0.006),        # precip_grad (fraction/m)
    (1.2, 4.0),             # precip_corr
    (0.0, 3.0),             # T0 (C)
    (-6.5e-3, -2.0e-3),     # lapse_rate (D-034, °C/m)
]
PARAM_RANGES = np.array([hi - lo for lo, hi in PARAM_BOUNDS])


# -- Prior distributions (D-017) ----------------------------------------
def _truncnorm_logpdf(x, mu, sigma, lo, hi):
    """Log-PDF of truncated normal distribution."""
    a = (lo - mu) / sigma
    b = (hi - mu) / sigma
    return truncnorm.logpdf(x, a, b, loc=mu, scale=sigma)


def log_prior(x):
    """Compute log-prior for parameter vector x.

    Priors (CAL-014):
      MF:         TN(5.0, 3.0) on [1, 12] — Braithwaite 2008 range
      T0:         TN(1.5, 0.5) on [0, 3]  — standard rain/snow threshold
      lapse_rate: TN(-4.5e-3, 1.0e-3) on [-6.5e-3, -2.0e-3]
                  D-034: covers Geck 2021 (-2 to -6), Schuster 2023 (-6.5),
                  Petersen 2013 (-3.2)
      r_ice:      TN(4.0e-3, 2.0e-3) on [0.02e-3, 10e-3]
                  D-035: allows wide range; informative but not dogmatic
      Others (MF_grad, r_snow, precip_grad, precip_corr): uniform in bounds
    """
    params = {n: v for n, v in zip(PARAM_NAMES, x)}
    for name, val in params.items():
        lo, hi = dict(zip(PARAM_NAMES, PARAM_BOUNDS))[name]
        if val < lo or val > hi:
            return -np.inf
    lp = 0.0
    lp += _truncnorm_logpdf(params['MF'], 5.0, 3.0, 1.0, 12.0)
    lp += _truncnorm_logpdf(params['T0'], 1.5, 0.5, 0.0, 3.0)
    # D-034: informative prior for lapse rate centered between Geck and OGGM
    lp += _truncnorm_logpdf(params['lapse_rate'], -4.5e-3, 1.0e-3,
                            -6.5e-3, -2.0e-3)
    # D-035: informative prior for r_ice centered ~2x typical r_snow
    lp += _truncnorm_logpdf(params['r_ice'], 4.0e-3, 2.0e-3,
                            0.02e-3, 10.0e-3)
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


def build_snowline_targets(climate, grid, snowline_dir):
    """Pre-load observed snowlines and prepare climate arrays for each.

    Returns list of dicts, each with:
        year, month, day : observation date
        obs_mean_elev : observed mean snowline elevation (m)
        obs_std_elev : spatial std of observed snowline elevation (m)
        arrays : (T, P, doy) from Oct 1 to observation date
    """
    from dixon_melt.snowline_validation import load_all_snowlines

    dem_info = {
        'elevation': grid['elevation'],
        'glacier_mask': grid['glacier_mask'],
        'transform': grid['transform'],
        'cell_size': grid['cell_size'],
        'nrows': grid['elevation'].shape[0],
        'ncols': grid['elevation'].shape[1],
    }

    obs_list = load_all_snowlines(str(snowline_dir), dem_info)
    targets = []

    for obs in obs_list:
        year = obs['year']
        month = obs['month']
        day = obs['day']

        # Run period: Oct 1 of previous year to observation date
        start = f'{year - 1}-10-01'
        end = f'{year}-{month:02d}-{day:02d}'

        wy = climate.loc[start:end]
        if len(wy) < 200:
            print(f"    Snowline {year}: skipped (insufficient climate data)")
            continue

        # Check melt-season data quality (D-022)
        melt_season = wy.loc[f'{year}-05-01':f'{year}-09-30']
        if len(melt_season) > 0:
            nan_frac = melt_season['temperature'].isna().mean()
            if nan_frac > 0.30:
                print(f"    Snowline {year}: skipped (>{nan_frac*100:.0f}% melt-season T NaN)")
                continue

        T = wy['temperature'].values.astype(np.float64)
        P = wy['precipitation'].values.astype(np.float64)
        T = np.where(np.isnan(T), 0.0, T)
        P = np.where(np.isnan(P), 0.0, P)
        doy = np.array(wy.index.dayofyear, dtype=np.int64)

        targets.append({
            'year': year,
            'month': month,
            'day': day,
            'obs_mean_elev': obs['mean_elevation'],
            'obs_std_elev': obs.get('std_elevation', np.nan),
            'arrays': (T, P, doy),
        })

    return targets


def build_calibration_targets(stakes, geodetic, climate, grid, snowline_dir):
    """Build all calibration targets: stakes + geodetic + snowlines."""
    targets = {
        'stake_annual': [],
        'stake_summer': [],
        'stake_winter': [],
        'geodetic': [],
        'snowline': [],
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

    # Snowline targets (D-028)
    print("\n  Building snowline targets...")
    targets['snowline'] = build_snowline_targets(climate, grid, str(snowline_dir))

    n_meas = lambda lst: len([t for t in lst if not t['estimated']])
    print(f"\nCalibration targets:")
    print(f"  Stake annual: {len(targets['stake_annual'])} ({n_meas(targets['stake_annual'])} measured)")
    print(f"  Stake summer: {len(targets['stake_summer'])} ({n_meas(targets['stake_summer'])} measured)")
    print(f"  Stake winter: {len(targets['stake_winter'])} ({n_meas(targets['stake_winter'])} measured)")
    print(f"  Geodetic periods: {len(targets['geodetic'])}")
    for g in targets['geodetic']:
        print(f"    {g['period']}: {len(g['year_data'])} usable years")
    print(f"  Snowline years: {len(targets['snowline'])}")
    for s in targets['snowline']:
        print(f"    {s['year']} ({s['year']}-{s['month']:02d}-{s['day']:02d}): "
              f"obs={s['obs_mean_elev']:.0f}m +/- {s['obs_std_elev']:.0f}m")
    return targets


def _x_to_full_params(x):
    """Convert 8-element vector to full parameter dict for the model (CAL-014).

    Changes from v13:
      - `r_ice` is now a free parameter (was `FIXED_RICE_RATIO * r_snow`)
      - `internal_lapse` ← `lapse_rate` (free parameter; was fixed -5e-3)
    Only `k_wind` remains fixed at 0.
    """
    params = {n: v for n, v in zip(PARAM_NAMES, x)}
    # r_ice and lapse_rate are now in params directly (from x)
    # Map lapse_rate -> internal_lapse for the model kernel
    params['internal_lapse'] = params['lapse_rate']
    params['k_wind'] = FIXED_K_WIND
    return params


def compute_chi2_terms(x, fmodel, targets):
    """Compute individual chi-squared terms for the parameter vector.

    Includes: stakes (annual, summer, winter), geodetic, and snowline elevation.
    """
    from dixon_melt.snowline_validation import modeled_snowline_elevation

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

    # Snowline elevation (D-028)
    n_snowline_nan = 0
    for stgt in targets['snowline']:
        T, P, doy = stgt['arrays']
        result = fmodel.run(T, P, doy, params, 0.0)
        modeled = modeled_snowline_elevation(
            result['cum_accum'], result['cum_melt'],
            fmodel.elevation, fmodel.glacier_mask)
        mod_elev = modeled['mean_elevation']
        if np.isnan(mod_elev):
            n_snowline_nan += 1
            continue
        obs_elev = stgt['obs_mean_elev']
        all_chi2.append(((mod_elev - obs_elev) / SIGMA_SNOWLINE) ** 2)

    # Penalty: if too many snowline years produce NaN (all snow or all ice),
    # the parameter set is suspect
    if n_snowline_nan > 5:
        geodetic_penalty += 10.0 * n_snowline_nan

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
    """Cluster DE optima into distinct modes."""
    n = len(optima_x)
    if n == 1:
        return [{'x': optima_x[0], 'cost': optima_cost[0], 'seed_indices': [0]}]

    X_norm = np.array([(x - np.array([lo for lo, hi in PARAM_BOUNDS])) / PARAM_RANGES
                       for x in optima_x])

    dists = pdist(X_norm, metric='chebyshev')
    Z = linkage(dists, method='complete')
    labels = fcluster(Z, t=CLUSTER_THRESHOLD, criterion='distance')

    modes = []
    for label in np.unique(labels):
        mask = labels == label
        indices = np.where(mask)[0].tolist()
        best_idx = indices[np.argmin([optima_cost[i] for i in indices])]
        modes.append({
            'x': optima_x[best_idx],
            'cost': optima_cost[best_idx],
            'seed_indices': indices,
        })

    modes.sort(key=lambda m: m['cost'])
    return modes


# -- Main ----------------------------------------------------------------
def main(resume=False):
    t_start = time.time()
    print("=" * 70)
    print("DIXON GLACIER DETIM -- CALIBRATION v13 (CAL-013)")
    print("Multi-objective: stakes + geodetic + snowline elevation")
    print("D-028: Snowline in likelihood, area as post-hoc filter")
    if resume:
        print("*** RESUME MODE: skipping DE, loading saved optima ***")
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

    # -- Build targets (now includes snowlines) --------------------------
    targets = build_calibration_targets(stakes, geodetic, climate, grid, SNOWLINE_DIR)

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
    print(f"  {t_per_eval*1000:.0f} ms per objective evaluation "
          f"(includes {len(targets['snowline'])} snowline years)")

    # ====================================================================
    # PHASE 1: MULTI-SEED DIFFERENTIAL EVOLUTION (skip if --resume)
    # ====================================================================
    de_summary = None

    if resume and (OUTPUT_DIR / 'de_multistart_v14.json').exists():
        print(f"\n{'=' * 70}")
        print(f"PHASE 1: SKIPPED (loading saved DE results)")
        print(f"{'=' * 70}")
        with open(OUTPUT_DIR / 'de_multistart_v14.json') as f:
            de_summary = json.load(f)
        modes = []
        for m in de_summary['modes']:
            modes.append({
                'x': np.array([m['params'][n] for n in PARAM_NAMES]),
                'cost': m['cost'],
                'seed_indices': list(range(N_SEEDS)),  # all seeds
            })
        print(f"  Loaded {len(modes)} mode(s), best cost={modes[0]['cost']:.4f}")
        for name in PARAM_NAMES:
            print(f"    {name:15s}: {de_summary['modes'][0]['params'][name]:.6f}")

    else:
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
        print(f"  Snowline sigma: {SIGMA_SNOWLINE:.0f} m")
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
        pd.DataFrame(all_de_logs).to_csv(OUTPUT_DIR / 'calibration_log_v14_de.csv', index=False)

        # ================================================================
        # PHASE 1.5: CLUSTER OPTIMA
        # ================================================================
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
        with open(OUTPUT_DIR / 'de_multistart_v14.json', 'w') as f:
            json.dump(de_summary, f, indent=2)

        # Save best overall params
        best_mode = modes[0]
        with open(OUTPUT_DIR / 'best_params_v14.json', 'w') as f:
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

        # Check for existing checkpoint to resume from
        chain_file = OUTPUT_DIR / f'mcmc_chain_v14_mode{mode_id}.npy'
        lp_file = OUTPUT_DIR / f'mcmc_logprob_v14_mode{mode_id}.npy'
        prev_chain = None
        prev_lp = None
        steps_done = 0

        if resume and chain_file.exists() and lp_file.exists():
            prev_chain = np.load(chain_file)
            prev_lp = np.load(lp_file)
            steps_done = prev_chain.shape[0]
            if steps_done >= MCMC_NSTEPS:
                print(f"    Chain already complete ({steps_done} steps). Skipping.")
                # Use saved chain for downstream
                burnin_use = max(MCMC_BURNIN, steps_done // 2)
                try:
                    tau = emcee.autocorr.integrated_time(
                        prev_chain[burnin_use:], quiet=True)
                    thin = max(int(0.5 * np.min(tau)), 1)
                    tau_list = tau.tolist()
                except Exception:
                    thin = 10
                    tau_list = None
                flat_samples = prev_chain[burnin_use::thin].reshape(
                    -1, prev_chain.shape[2])
                all_flat_samples.append(flat_samples)
                chain_summaries.append({
                    'mode_id': mode_id, 'n_steps': steps_done,
                    'n_samples': len(flat_samples), 'resumed': True,
                })
                continue
            # Resume: use last walker positions as starting point
            pos = prev_chain[-1]  # shape (n_walkers, n_params)
            steps_remaining = MCMC_NSTEPS - steps_done
            print(f"    Resuming from checkpoint: {steps_done} steps done, "
                  f"{steps_remaining} remaining")
        else:
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
            steps_remaining = MCMC_NSTEPS

        sampler = emcee.EnsembleSampler(
            MCMC_NWALKERS, ndim, log_probability,
            args=(fmodel, targets),
        )

        print(f"    Running MCMC chain {mode_id} ({steps_remaining} steps)...")
        new_chains = []
        new_lps = []
        step_count = 0
        for sample in sampler.sample(pos, iterations=steps_remaining, progress=False):
            step_count += 1
            total_steps = steps_done + step_count
            if step_count % 500 == 0:
                elapsed = time.time() - mcmc_start
                accept_frac = np.mean(sampler.acceptance_fraction)
                rate = step_count / elapsed if elapsed > 0 else 0
                eta = (steps_remaining - step_count) / rate / 3600 if rate > 0 else 0
                print(f"      step {total_steps:5d}/{MCMC_NSTEPS} | "
                      f"accept={accept_frac:.3f} | "
                      f"elapsed={elapsed/60:.1f}min | "
                      f"ETA={eta:.1f}hrs")
            # Checkpoint every 1000 steps — merge with previous chain
            if step_count % 1000 == 0:
                new_chain_so_far = sampler.get_chain()
                new_lp_so_far = sampler.get_log_prob()
                if prev_chain is not None:
                    merged_chain = np.concatenate([prev_chain, new_chain_so_far], axis=0)
                    merged_lp = np.concatenate([prev_lp, new_lp_so_far], axis=0)
                else:
                    merged_chain = new_chain_so_far
                    merged_lp = new_lp_so_far
                np.save(chain_file, merged_chain)
                np.save(lp_file, merged_lp)
                print(f"      [checkpoint saved: {total_steps} steps total]")

        mcmc_elapsed = time.time() - mcmc_start
        accept_frac = float(np.mean(sampler.acceptance_fraction))

        # Final save: merge new chain with previous
        new_chain = sampler.get_chain()
        new_lp = sampler.get_log_prob()
        if prev_chain is not None:
            full_chain = np.concatenate([prev_chain, new_chain], axis=0)
            full_lp_arr = np.concatenate([prev_lp, new_lp], axis=0)
        else:
            full_chain = new_chain
            full_lp_arr = new_lp
        np.save(chain_file, full_chain)
        np.save(lp_file, full_lp_arr)

        total_steps_final = full_chain.shape[0]
        print(f"\n    Chain {mode_id} complete: {total_steps_final} total steps "
              f"in {mcmc_elapsed:.0f}s ({mcmc_elapsed/3600:.1f} hrs this run)")
        print(f"    Acceptance fraction: {accept_frac:.3f}")

        # Convergence diagnostics (use full merged chain)
        try:
            # Compute autocorrelation on the full chain
            tau = emcee.autocorr.integrated_time(
                full_chain.transpose(1, 0, 2).reshape(MCMC_NWALKERS, -1, ndim)
                .mean(axis=0), quiet=True)
            print(f"    Autocorr times: {', '.join(f'{t:.0f}' for t in tau)}")
            print(f"    Max tau: {np.max(tau):.0f}, chain/tau: "
                  f"{total_steps_final/np.max(tau):.0f}x")
            burnin = int(2 * np.max(tau))
            thin = max(int(0.5 * np.min(tau)), 1)
            tau_list = tau.tolist()
        except Exception:
            print("    WARNING: Autocorrelation time unreliable, using defaults")
            burnin = MCMC_BURNIN
            thin = 10
            tau_list = None

        burnin = max(burnin, MCMC_BURNIN)
        flat_samples = full_chain[burnin::thin].reshape(-1, ndim)
        n_samples = len(flat_samples)
        print(f"    Burn-in: {burnin}, thin: {thin}, posterior samples: {n_samples}")

        all_flat_samples.append(flat_samples)
        chain_summaries.append({
            'mode_id': mode_id,
            'mode_cost': float(mode['cost']),
            'mode_seeds': [DE_SEEDS[j] for j in mode['seed_indices']],
            'mode_params': {n: float(v) for n, v in zip(PARAM_NAMES, mode['x'])},
            'n_walkers': MCMC_NWALKERS,
            'n_steps': total_steps_final,
            'burn_in': burnin,
            'thin': thin,
            'n_samples': n_samples,
            'acceptance_fraction': accept_frac,
            'autocorr_times': tau_list,
            'wall_time_s': mcmc_elapsed,
        })

    # Save param names for downstream scripts
    with open(OUTPUT_DIR / 'posterior_param_names_v14.json', 'w') as f:
        json.dump(PARAM_NAMES, f)

    # ====================================================================
    # PHASE 3: COMBINE POSTERIORS + SNOWLINE VALIDATION
    # ====================================================================
    print(f"\n{'=' * 70}")
    print(f"PHASE 3: COMBINING POSTERIORS")
    print(f"{'=' * 70}")

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
    posterior_df.to_csv(OUTPUT_DIR / 'posterior_samples_v14.csv', index=False)

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
        fig.savefig(OUTPUT_DIR / 'corner_plot_v14.png', dpi=150, bbox_inches='tight')
        print(f"\n  Corner plot saved to {OUTPUT_DIR / 'corner_plot_v14.png'}")
    except Exception as e:
        print(f"\n  Corner plot failed: {e}")

    # -- MAP Snowline Validation -----------------------------------------
    from dixon_melt.snowline_validation import modeled_snowline_elevation

    run_params = _x_to_full_params(best_x)

    print(f"\n{'=' * 70}")
    print("MAP SNOWLINE VALIDATION")
    print(f"{'=' * 70}")
    sl_biases = []
    for stgt in targets['snowline']:
        T, P, doy = stgt['arrays']
        result = fmodel.run(T, P, doy, run_params, 0.0)
        modeled = modeled_snowline_elevation(
            result['cum_accum'], result['cum_melt'],
            fmodel.elevation, fmodel.glacier_mask)
        mod_elev = modeled['mean_elevation']
        obs_elev = stgt['obs_mean_elev']
        bias = mod_elev - obs_elev if not np.isnan(mod_elev) else np.nan
        if not np.isnan(bias):
            sl_biases.append(bias)
        status = f"bias={bias:+.0f}m" if not np.isnan(bias) else "NaN (all snow/ice)"
        print(f"  {stgt['year']}: obs={obs_elev:.0f}m, mod={mod_elev:.0f}m, {status}")

    sl_biases = np.array(sl_biases)
    print(f"\n  Snowline summary ({len(sl_biases)} years):")
    print(f"    Mean bias: {sl_biases.mean():+.0f} m")
    print(f"    RMSE:      {np.sqrt((sl_biases**2).mean()):.0f} m")
    print(f"    MAE:       {np.abs(sl_biases).mean():.0f} m")

    # -- MAP Stake Validation --------------------------------------------
    print(f"\n{'=' * 70}")
    print("MAP STAKE VALIDATION (best mode)")
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
    # PHASE 4: POST-HOC AREA BEHAVIORAL FILTER
    # ====================================================================
    print(f"\n{'=' * 70}")
    print(f"PHASE 4: AREA EVOLUTION BEHAVIORAL FILTER")
    print(f"{'=' * 70}")

    from dixon_melt.glacier_dynamics import initialize_ice_thickness, compute_bedrock
    from dixon_melt.behavioral_filter import score_area_evolution, load_observed_areas

    # Load observed areas
    observed_areas = load_observed_areas(str(OUTLINE_JSON))
    print(f"  Area checkpoints: {sorted(observed_areas.keys())}")
    for yr, area in sorted(observed_areas.items()):
        print(f"    {yr}: {area:.2f} km²")

    # Initialize ice thickness
    farinotti = str(FARINOTTI_PATH) if FARINOTTI_PATH.exists() else None
    ice_thickness, thickness_source = initialize_ice_thickness(
        grid, farinotti_path=farinotti)
    bedrock = compute_bedrock(grid['elevation'], ice_thickness)
    print(f"  Ice thickness: {thickness_source}")

    # Select top N from posterior (ranked by log-prob from the chain)
    # Load chain and logprob to rank
    chain_files = sorted(OUTPUT_DIR.glob('mcmc_chain_v14_mode*.npy'))
    lp_files = sorted(OUTPUT_DIR.glob('mcmc_logprob_v14_mode*.npy'))

    all_flat_chain = []
    all_flat_lp = []
    for cf, lf in zip(chain_files, lp_files):
        c = np.load(cf)
        lp = np.load(lf)
        burnin_idx = max(MCMC_BURNIN, c.shape[0] // 2)
        flat_c = c[burnin_idx:].reshape(-1, c.shape[2])
        flat_lp = lp[burnin_idx:].flatten()
        all_flat_chain.append(flat_c)
        all_flat_lp.append(flat_lp)

    full_chain = np.vstack(all_flat_chain)
    full_lp = np.concatenate(all_flat_lp)

    # Rank and deduplicate
    ranked = np.argsort(full_lp)[::-1]
    seen = set()
    top_indices = []
    for idx in ranked:
        key = tuple(full_chain[idx])
        if key not in seen:
            seen.add(key)
            top_indices.append(idx)
        if len(top_indices) >= AREA_FILTER_N_TOP:
            break

    n_area_candidates = len(top_indices)
    print(f"\n  Selected top {n_area_candidates} param sets for area screening")
    print(f"  Area RMSE threshold: {AREA_RMSE_MAX:.1f} km²")

    wy_start = min(observed_areas.keys())
    area_survivors = []
    area_survivor_indices = []
    area_scores = []
    t_area = time.time()

    for count, idx in enumerate(top_indices):
        x = full_chain[idx]
        params = _x_to_full_params(x)

        fmodel.update_geometry(grid['elevation'], grid['glacier_mask'])
        area_score = score_area_evolution(
            fmodel, climate, grid, params, observed_areas,
            ice_thickness, bedrock, wy_start=wy_start,
        )

        area_pass = (not np.isnan(area_score['rmse_km2'])
                     and area_score['rmse_km2'] <= AREA_RMSE_MAX)

        area_scores.append({
            'rank': count,
            'log_prob': float(full_lp[idx]),
            'area_rmse_km2': area_score['rmse_km2'],
            'area_bias_km2': area_score['mean_bias_km2'],
            'passed': area_pass,
            **{n: float(v) for n, v in zip(PARAM_NAMES, x)},
        })

        if area_pass:
            area_survivors.append(params)
            area_survivor_indices.append(count)

        if (count + 1) % max(1, n_area_candidates // 10) == 0 or count == 0:
            status = "PASS" if area_pass else "FAIL"
            elapsed = time.time() - t_area
            rate = (count + 1) / elapsed if elapsed > 0 else 0
            eta = (n_area_candidates - count - 1) / rate if rate > 0 else 0
            print(f"    [{count+1:4d}/{n_area_candidates}] "
                  f"area RMSE={area_score['rmse_km2']:5.2f} km² → {status}  "
                  f"({rate:.1f}/s, ETA {eta/60:.0f}min)")

    t_area_done = time.time() - t_area
    n_survived = len(area_survivors)
    print(f"\n  Area filter: {n_survived}/{n_area_candidates} passed "
          f"({100 * n_survived / max(n_area_candidates, 1):.1f}%) "
          f"in {t_area_done/60:.1f} min")

    # Save area filter results
    pd.DataFrame(area_scores).to_csv(
        OUTPUT_DIR / 'area_filter_v14_scores.csv', index=False)

    # Save filtered params (compatible with run_projection.py --filtered-params)
    filtered_data = {
        'n_survivors': n_survived,
        'filter_config': {
            'source': 'CAL-013 (v13 multi-objective MCMC)',
            'n_area_candidates': n_area_candidates,
            'area_rmse_threshold_km2': AREA_RMSE_MAX,
            'area_checkpoints': {str(k): v for k, v in observed_areas.items()},
            'sigma_snowline_m': SIGMA_SNOWLINE,
        },
        'param_sets': area_survivors,
    }
    with open(OUTPUT_DIR / 'filtered_params_v14.json', 'w') as f:
        json.dump(filtered_data, f, indent=2)
    print(f"  Filtered params saved: filtered_params_v14.json ({n_survived} sets)")

    if n_survived > 0:
        print(f"\n  Survivor parameter summary:")
        for key in PARAM_NAMES:
            vals = [s[key] for s in area_survivors]
            print(f"    {key:12s}: median={np.median(vals):.4f}  "
                  f"[{np.percentile(vals, 16):.4f}, {np.percentile(vals, 84):.4f}]")

    # -- Save final summary ----------------------------------------------
    total_elapsed = time.time() - t_start
    summary = {
        'version': 13,
        'calibration_id': 'CAL-013',
        'method': 'Multi-objective DE+MCMC (stakes+geodetic+snowline) + area filter',
        'decision': 'D-028',
        'changes_from_v12': [
            'Snowline elevation chi2 added to MCMC likelihood (sigma=75m)',
            'Post-MCMC area evolution behavioral filter',
            'Manually digitized outlines (2000-2025, 5-yr intervals)',
        ],
        'snowline_config': {
            'sigma_m': SIGMA_SNOWLINE,
            'n_years': len(targets['snowline']),
        },
        'area_filter_config': {
            'n_candidates': n_area_candidates,
            'n_survivors': n_survived,
            'rmse_threshold_km2': AREA_RMSE_MAX,
            'checkpoints': {str(k): v for k, v in observed_areas.items()},
        },
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
    with open(OUTPUT_DIR / 'calibration_summary_v14.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n{'=' * 70}")
    print(f"CALIBRATION v13 (CAL-013) COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Total wall time: {total_elapsed:.0f}s ({total_elapsed/3600:.1f} hours)")
    print(f"  DE seeds: {N_SEEDS}, modes found: {len(modes)}")
    print(f"  MCMC chains: {len(modes)}, combined samples: {n_total}")
    print(f"  Snowline years in likelihood: {len(targets['snowline'])}")
    print(f"  Area filter: {n_area_candidates} → {n_survived} survivors")
    print(f"\n  Outputs saved to {OUTPUT_DIR}/ (v13)")
    print(f"\n  To project with filtered params:")
    print(f"    python run_projection.py --filtered-params "
          f"calibration_output/filtered_params_v14.json")
    print("Done!")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='CAL-013: Multi-objective calibration')
    parser.add_argument('--resume', action='store_true',
                        help='Skip DE phase, load saved optima from de_multistart_v14.json')
    args = parser.parse_args()
    main(resume=args.resume)
