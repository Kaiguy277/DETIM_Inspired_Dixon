"""
Validation analyses for Dixon Glacier DETIM — v13 posterior.

Three independent validation tasks:
  1. Sub-period geodetic comparison (2000-2010, 2010-2020 vs Hugonnet)
  2. Posterior predictive check by year (stake data, WY2023-2025)
  3. Sensitivity analysis of fixed parameters (lapse rate, r_ice/r_snow)

Uses the existing v13 posterior (filtered_params_v13.json) — no recalibration.
Results written to validation_output/.

References:
    Hugonnet et al. (2021) Nature — geodetic mass balance
    Gardner & Sharp (2009) J. Glaciol. — lapse rates
    Hock (1999) J. Glaciol. — radiation factors
"""
import sys
import os
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True)

import numpy as np
import pandas as pd
from pathlib import Path
import json
import time

# ── Paths ────────────────────────────────────────────────────────────
PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
DEM_PATH = PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif'
GLACIER_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
CLIMATE_PATH = PROJECT / 'data' / 'climate' / 'dixon_gap_filled_climate.csv'
STAKE_PATH = PROJECT / 'stake_observations_dixon.csv'
GEODETIC_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_hugonnet.csv'
BEST_PARAMS_PATH = PROJECT / 'calibration_output' / 'best_params_v13.json'
FILTERED_PARAMS_PATH = PROJECT / 'calibration_output' / 'filtered_params_v13.json'
OUTPUT_DIR = PROJECT / 'validation_output'
OUTPUT_DIR.mkdir(exist_ok=True)

GRID_RES = 100.0

# ── Fixed parameter values (baseline, D-017) ─────────────────────────
FIXED_LAPSE_RATE = -5.0e-3   # °C/m
FIXED_RICE_RATIO = 2.0       # r_ice / r_snow
FIXED_K_WIND = 0.0


# ── Helpers ──────────────────────────────────────────────────────────
def load_climate():
    df = pd.read_csv(CLIMATE_PATH, parse_dates=['date'], index_col='date')
    return df[['temperature', 'precipitation']]


def prepare_water_year_arrays(climate, wy_year):
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
    wy = climate.loc[start_date:end_date]
    if len(wy) < 30:
        return None
    T = wy['temperature'].values.astype(np.float64)
    P = wy['precipitation'].values.astype(np.float64)
    doy = np.array([d.timetuple().tm_yday for d in wy.index], dtype=np.int64)
    return T, P, doy


def _normalize_params(p):
    """Ensure param dict uses keys the model expects."""
    p = dict(p)
    if 'lapse_rate' in p and 'internal_lapse' not in p:
        p['internal_lapse'] = p.pop('lapse_rate')
    return p


def load_params():
    """Load MAP and posterior parameter sets."""
    best = _normalize_params(json.load(open(BEST_PARAMS_PATH)))
    filtered = json.load(open(FILTERED_PARAMS_PATH))
    posterior = [_normalize_params(p) for p in filtered['param_sets']]
    return best, posterior


def setup_model(grid_res=GRID_RES):
    """Prepare grid, ipot, and FastDETIM model."""
    from dixon_melt.terrain import prepare_grid
    from dixon_melt.model import precompute_ipot
    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config

    grid = prepare_grid(str(DEM_PATH), str(GLACIER_PATH), target_res=grid_res)
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
    return grid, fmodel


def run_annual_balance(fmodel, climate, wy_year, params):
    """Run model for one water year, return glacier-wide balance (m w.e.)."""
    arrays = prepare_water_year_arrays(climate, wy_year)
    if arrays is None:
        return np.nan
    T, P, doy = arrays
    result = fmodel.run(T, P, doy, params, 0.0)
    return result['glacier_wide_balance']


def run_stake_balance(fmodel, climate, wy_year, params):
    """Run model for one WY, return stake balances dict."""
    arrays = prepare_water_year_arrays(climate, wy_year)
    if arrays is None:
        return {}
    T, P, doy = arrays
    result = fmodel.run(T, P, doy, params, 0.0)
    return result['stake_balances']


# =====================================================================
# 1. SUB-PERIOD GEODETIC COMPARISON
# =====================================================================
def validate_geodetic_subperiods(fmodel, climate, posterior, n_sample=200):
    """Compare modeled vs observed geodetic MB for three Hugonnet periods.

    Runs n_sample posterior parameter sets through each sub-period and
    reports bias, RMSE, and whether observed falls within uncertainty.
    """
    print("\n" + "=" * 70)
    print("VALIDATION 1: Sub-period geodetic comparison")
    print("=" * 70)

    geodetic = pd.read_csv(GEODETIC_PATH)
    periods = []
    for _, row in geodetic.iterrows():
        period_str = row['period']
        start_str, end_str = period_str.split('_')
        start_year = pd.Timestamp(start_str).year
        end_year = pd.Timestamp(end_str).year
        periods.append({
            'label': f'{start_year}-{end_year}',
            'start_year': start_year,
            'end_year': end_year,
            'obs_dmdtda': row['dmdtda'],
            'obs_err': row['err_dmdtda'],
            'calibrated': period_str == '2000-01-01_2020-01-01',
        })

    # Pre-compute climate arrays for all needed water years
    all_wy_arrays = {}
    for wy in range(2001, 2021):
        arr = prepare_water_year_arrays(climate, wy)
        if arr is not None:
            all_wy_arrays[wy] = arr

    # Sample from posterior
    idx = np.random.default_rng(42).choice(len(posterior), size=min(n_sample, len(posterior)), replace=False)
    sample_params = [posterior[i] for i in idx]

    results = []
    for period in periods:
        wy_range = range(period['start_year'] + 1, period['end_year'] + 1)
        usable_wys = [wy for wy in wy_range if wy in all_wy_arrays]
        n_years = len(usable_wys)

        print(f"\n  {period['label']}: {n_years} usable water years "
              f"({'CALIBRATION' if period['calibrated'] else 'VALIDATION'})")
        print(f"  Observed: {period['obs_dmdtda']:.4f} ± {period['obs_err']:.4f} m w.e./yr")

        modeled_means = []
        for pi, params in enumerate(sample_params):
            annual_bals = []
            for wy in usable_wys:
                T, P, doy = all_wy_arrays[wy]
                result = fmodel.run(T, P, doy, params, 0.0)
                annual_bals.append(result['glacier_wide_balance'])
            modeled_means.append(np.mean(annual_bals))

            if (pi + 1) % 50 == 0:
                print(f"    {pi+1}/{len(sample_params)} param sets done...")

        modeled_means = np.array(modeled_means)
        median_mod = np.median(modeled_means)
        p5, p95 = np.percentile(modeled_means, [5, 95])
        bias = median_mod - period['obs_dmdtda']
        within_unc = abs(bias) <= period['obs_err']

        print(f"  Modeled:  {median_mod:.4f} [{p5:.4f}, {p95:.4f}] m w.e./yr")
        print(f"  Bias:     {bias:+.4f} m w.e./yr  "
              f"({'within' if within_unc else 'OUTSIDE'} obs uncertainty)")

        results.append({
            'period': period['label'],
            'type': 'calibration' if period['calibrated'] else 'validation',
            'obs_dmdtda': period['obs_dmdtda'],
            'obs_err': period['obs_err'],
            'mod_median': median_mod,
            'mod_p5': p5,
            'mod_p95': p95,
            'bias': bias,
            'within_uncertainty': within_unc,
            'n_years': n_years,
            'n_param_sets': len(sample_params),
        })

    # Save
    df = pd.DataFrame(results)
    out_path = OUTPUT_DIR / 'geodetic_subperiod_validation.csv'
    df.to_csv(out_path, index=False, float_format='%.4f')
    print(f"\n  Saved: {out_path}")
    return df


# =====================================================================
# 2. POSTERIOR PREDICTIVE CHECK BY YEAR (STAKE DATA)
# =====================================================================
def validate_stakes_by_year(fmodel, climate, posterior, n_sample=200):
    """Evaluate posterior against each year's stake data independently.

    For each WY with stake observations, run n_sample posterior parameter
    sets and compare predicted vs observed balances at ABL, ELA, ACC.
    """
    print("\n" + "=" * 70)
    print("VALIDATION 2: Posterior predictive check — stake balance by year")
    print("=" * 70)

    stakes = pd.read_csv(STAKE_PATH, parse_dates=['date_start', 'date_end'])
    annual = stakes[stakes['period_type'] == 'annual'].copy()

    # Group by year
    years = sorted(annual['year'].unique())
    print(f"  Stake years: {years}")

    idx = np.random.default_rng(42).choice(len(posterior), size=min(n_sample, len(posterior)), replace=False)
    sample_params = [posterior[i] for i in idx]

    all_results = []
    for yr in years:
        yr_stakes = annual[annual['year'] == yr]
        arrays = prepare_water_year_arrays(climate, yr)
        if arrays is None:
            print(f"\n  WY{yr}: insufficient climate data, skipped")
            continue

        T, P, doy = arrays
        print(f"\n  WY{yr}:")

        # Observed
        obs_by_site = {}
        for _, row in yr_stakes.iterrows():
            obs_by_site[row['site_id']] = {
                'obs': row['mb_obs_mwe'],
                'unc': row['mb_obs_uncertainty_mwe'],
                'estimated': 'estimated' in str(row.get('notes', '')).lower(),
            }

        # Modeled (ensemble)
        mod_by_site = {site: [] for site in obs_by_site}
        for params in sample_params:
            result = fmodel.run(T, P, doy, params, 0.0)
            for site in obs_by_site:
                mod_val = result['stake_balances'].get(site, np.nan)
                mod_by_site[site].append(mod_val)

        for site in sorted(obs_by_site.keys()):
            obs = obs_by_site[site]['obs']
            unc = obs_by_site[site]['unc']
            est = obs_by_site[site]['estimated']
            mod_arr = np.array(mod_by_site[site])
            mod_arr = mod_arr[~np.isnan(mod_arr)]

            if len(mod_arr) == 0:
                print(f"    {site}: no valid model output")
                continue

            mod_med = np.median(mod_arr)
            mod_p5, mod_p95 = np.percentile(mod_arr, [5, 95])
            residual = mod_med - obs

            flag = " (estimated)" if est else ""
            print(f"    {site}: obs={obs:+.2f}±{unc:.2f}, "
                  f"mod={mod_med:+.2f} [{mod_p5:+.2f}, {mod_p95:+.2f}], "
                  f"residual={residual:+.2f}{flag}")

            all_results.append({
                'year': yr,
                'site': site,
                'elevation_m': yr_stakes[yr_stakes['site_id'] == site]['elevation_m'].iloc[0],
                'obs_mwe': obs,
                'obs_unc': unc,
                'estimated': est,
                'mod_median': mod_med,
                'mod_p5': mod_p5,
                'mod_p95': mod_p95,
                'residual': residual,
                'n_param_sets': len(mod_arr),
            })

    df = pd.DataFrame(all_results)

    # Summary statistics
    measured = df[~df['estimated']]
    if len(measured) > 0:
        rmse = np.sqrt(np.mean(measured['residual'] ** 2))
        mae = np.mean(np.abs(measured['residual']))
        mean_bias = np.mean(measured['residual'])
        print(f"\n  Summary (measured obs only, n={len(measured)}):")
        print(f"    RMSE:      {rmse:.3f} m w.e.")
        print(f"    MAE:       {mae:.3f} m w.e.")
        print(f"    Mean bias: {mean_bias:+.3f} m w.e.")

        # By site
        for site in sorted(measured['site'].unique()):
            site_df = measured[measured['site'] == site]
            site_rmse = np.sqrt(np.mean(site_df['residual'] ** 2))
            print(f"    {site} RMSE: {site_rmse:.3f} m w.e. (n={len(site_df)})")

    out_path = OUTPUT_DIR / 'stake_predictive_check.csv'
    df.to_csv(out_path, index=False, float_format='%.4f')
    print(f"\n  Saved: {out_path}")
    return df


# =====================================================================
# 3. SENSITIVITY ANALYSIS OF FIXED PARAMETERS
# =====================================================================
def sensitivity_fixed_params(fmodel, climate, best_params):
    """Perturb fixed lapse rate and r_ice/r_snow ratio, evaluate impact.

    For each perturbation, re-run the model with MAP params (other free
    params unchanged) and report glacier-wide balance and stake RMSE.
    """
    print("\n" + "=" * 70)
    print("VALIDATION 3: Sensitivity of fixed parameters")
    print("=" * 70)

    stakes = pd.read_csv(STAKE_PATH, parse_dates=['date_start', 'date_end'])
    annual_measured = stakes[
        (stakes['period_type'] == 'annual') &
        ~stakes['notes'].str.contains('estimated', case=False, na=False)
    ]

    geodetic = pd.read_csv(GEODETIC_PATH)
    obs_geodetic = geodetic[geodetic['period'] == '2000-01-01_2020-01-01'].iloc[0]['dmdtda']

    # Pre-compute climate arrays
    wy_arrays = {}
    for wy in range(2001, 2021):
        arr = prepare_water_year_arrays(climate, wy)
        if arr is not None:
            wy_arrays[wy] = arr

    stake_years = sorted(annual_measured['year'].unique())
    stake_wy_arrays = {}
    for yr in stake_years:
        arr = prepare_water_year_arrays(climate, yr)
        if arr is not None:
            stake_wy_arrays[yr] = arr

    # ── Lapse rate sensitivity ──────────────────────────────────────
    lapse_values = np.array([-4.0, -4.5, -5.0, -5.5, -6.0, -6.5]) * 1e-3  # °C/m
    print(f"\n  Lapse rate sensitivity ({len(lapse_values)} values):")
    print(f"  Range: {lapse_values[0]*1000:.1f} to {lapse_values[-1]*1000:.1f} °C/km")

    lapse_results = []
    for lapse in lapse_values:
        params = dict(best_params)
        params['internal_lapse'] = lapse

        # Geodetic balance
        annual_bals = []
        for wy, (T, P, doy) in wy_arrays.items():
            result = fmodel.run(T, P, doy, params, 0.0)
            annual_bals.append(result['glacier_wide_balance'])
        geodetic_mod = np.mean(annual_bals)

        # Stake RMSE
        residuals = []
        for yr in stake_years:
            if yr not in stake_wy_arrays:
                continue
            T, P, doy = stake_wy_arrays[yr]
            result = fmodel.run(T, P, doy, params, 0.0)
            yr_obs = annual_measured[annual_measured['year'] == yr]
            for _, row in yr_obs.iterrows():
                mod = result['stake_balances'].get(row['site_id'], np.nan)
                if not np.isnan(mod):
                    residuals.append(mod - row['mb_obs_mwe'])
        stake_rmse = np.sqrt(np.mean(np.array(residuals) ** 2)) if residuals else np.nan

        print(f"    λ={lapse*1000:+.1f} °C/km: geodetic={geodetic_mod:+.4f} "
              f"(Δ={geodetic_mod - obs_geodetic:+.4f}), stake RMSE={stake_rmse:.3f}")

        lapse_results.append({
            'parameter': 'lapse_rate',
            'value': lapse * 1000,  # °C/km for readability
            'value_raw': lapse,
            'geodetic_mod': geodetic_mod,
            'geodetic_obs': obs_geodetic,
            'geodetic_bias': geodetic_mod - obs_geodetic,
            'stake_rmse': stake_rmse,
        })

    # ── r_ice/r_snow ratio sensitivity ──────────────────────────────
    ratio_values = [1.5, 1.75, 2.0, 2.25, 2.5, 3.0]
    print(f"\n  r_ice/r_snow ratio sensitivity ({len(ratio_values)} values):")

    ratio_results = []
    for ratio in ratio_values:
        params = dict(best_params)
        params['r_ice'] = ratio * params['r_snow']

        # Geodetic balance
        annual_bals = []
        for wy, (T, P, doy) in wy_arrays.items():
            result = fmodel.run(T, P, doy, params, 0.0)
            annual_bals.append(result['glacier_wide_balance'])
        geodetic_mod = np.mean(annual_bals)

        # Stake RMSE
        residuals = []
        for yr in stake_years:
            if yr not in stake_wy_arrays:
                continue
            T, P, doy = stake_wy_arrays[yr]
            result = fmodel.run(T, P, doy, params, 0.0)
            yr_obs = annual_measured[annual_measured['year'] == yr]
            for _, row in yr_obs.iterrows():
                mod = result['stake_balances'].get(row['site_id'], np.nan)
                if not np.isnan(mod):
                    residuals.append(mod - row['mb_obs_mwe'])
        stake_rmse = np.sqrt(np.mean(np.array(residuals) ** 2)) if residuals else np.nan

        print(f"    r_ice/r_snow={ratio:.2f}: geodetic={geodetic_mod:+.4f} "
              f"(Δ={geodetic_mod - obs_geodetic:+.4f}), stake RMSE={stake_rmse:.3f}")

        ratio_results.append({
            'parameter': 'rice_ratio',
            'value': ratio,
            'value_raw': ratio,
            'geodetic_mod': geodetic_mod,
            'geodetic_obs': obs_geodetic,
            'geodetic_bias': geodetic_mod - obs_geodetic,
            'stake_rmse': stake_rmse,
        })

    all_results = lapse_results + ratio_results
    df = pd.DataFrame(all_results)
    out_path = OUTPUT_DIR / 'sensitivity_fixed_params.csv'
    df.to_csv(out_path, index=False, float_format='%.4f')
    print(f"\n  Saved: {out_path}")

    # Summary
    print("\n  Sensitivity summary:")
    lapse_df = df[df['parameter'] == 'lapse_rate']
    ratio_df = df[df['parameter'] == 'rice_ratio']
    print(f"    Lapse rate: geodetic bias range {lapse_df['geodetic_bias'].min():+.4f} "
          f"to {lapse_df['geodetic_bias'].max():+.4f} m w.e./yr")
    print(f"    Lapse rate: stake RMSE range {lapse_df['stake_rmse'].min():.3f} "
          f"to {lapse_df['stake_rmse'].max():.3f} m w.e.")
    print(f"    r_ice/r_snow: geodetic bias range {ratio_df['geodetic_bias'].min():+.4f} "
          f"to {ratio_df['geodetic_bias'].max():+.4f} m w.e./yr")
    print(f"    r_ice/r_snow: stake RMSE range {ratio_df['stake_rmse'].min():.3f} "
          f"to {ratio_df['stake_rmse'].max():.3f} m w.e.")

    return df


# =====================================================================
# MAIN
# =====================================================================
def main():
    t_start = time.time()
    print("=" * 70)
    print("DIXON GLACIER DETIM — VALIDATION SUITE (v13 posterior)")
    print("=" * 70)

    # ── Setup ────────────────────────────────────────────────────────
    print("\nLoading climate data...")
    climate = load_climate()
    print(f"  {len(climate)} days ({climate.index.min().date()} to {climate.index.max().date()})")

    print("\nLoading parameters...")
    best_params, posterior = load_params()
    print(f"  MAP params loaded")
    print(f"  Posterior: {len(posterior)} parameter sets")

    print("\nPreparing grid and model...")
    grid, fmodel = setup_model()
    n_glacier = grid['glacier_mask'].sum()
    print(f"  Grid: {grid['elevation'].shape}, {n_glacier} glacier cells")

    # ── Run validations ──────────────────────────────────────────────
    # Warm up numba
    print("\nWarming up numba JIT...")
    arrays = prepare_water_year_arrays(climate, 2020)
    if arrays:
        T, P, doy = arrays
        _ = fmodel.run(T, P, doy, best_params, 0.0)
    print("  Done.")

    geodetic_df = validate_geodetic_subperiods(fmodel, climate, posterior, n_sample=200)
    stakes_df = validate_stakes_by_year(fmodel, climate, posterior, n_sample=200)
    sensitivity_df = sensitivity_fixed_params(fmodel, climate, best_params)

    # ── Summary ──────────────────────────────────────────────────────
    elapsed = time.time() - t_start
    print(f"\n{'=' * 70}")
    print(f"VALIDATION COMPLETE — {elapsed/60:.1f} minutes")
    print(f"Output: {OUTPUT_DIR}/")
    print(f"  geodetic_subperiod_validation.csv")
    print(f"  stake_predictive_check.csv")
    print(f"  sensitivity_fixed_params.csv")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
