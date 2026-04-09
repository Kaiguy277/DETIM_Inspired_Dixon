"""
Future projection runner for Dixon Glacier.

Runs DETIM forward under CMIP6 emission scenarios (NEX-GDDP-CMIP6) with
evolving glacier geometry (delta-h, Huss et al. 2010) and discharge routing
(parallel linear reservoirs). Propagates both climate (multi-GCM) and
parameter (MCMC posterior) uncertainty through the full projection.

Tracks: mass balance, area, volume, mean thickness, discharge (m3/s),
and identifies "peak water" timing per scenario.

Usage:
    # Top 250 param sets from MCMC chain (default, cf. Geck 2020)
    python run_projection.py --scenario ssp245

    # Single parameter set (legacy)
    python run_projection.py --scenario ssp245 --params best_params_v10.json

    # Subset of GCMs
    python run_projection.py --scenario ssp245 --gcms ACCESS-CM2 MRI-ESM2-0

Requires:
    1. Posterior ensemble (calibration_output/posterior_params_v10.npy) or
       single parameter JSON (calibration_output/best_params_v10.json)
    2. CMIP6 climate CSVs in data/cmip6/ (from download_cmip6.py)
    3. Farinotti ice thickness in data/ice_thickness/

References:
    Huss et al. (2010) HESS 14, 815-829 (delta-h)
    Thrasher et al. (2022) NASA NEX-GDDP-CMIP6
    Hock & Jansson (2005) (linear reservoir routing)
"""
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import json
import time

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
DEM_PATH = PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif'
GLACIER_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
CLIMATE_PATH = PROJECT / 'data' / 'climate' / 'dixon_gap_filled_climate.csv'
CMIP6_DIR = PROJECT / 'data' / 'cmip6'
FARINOTTI_PATH = PROJECT / 'data' / 'ice_thickness' / 'RGI60-01.18059_thickness.tif'
OUTPUT_BASE = PROJECT / 'projection_output'


CHAIN_PATH = PROJECT / 'calibration_output' / 'mcmc_chain_v12_mode1.npy'
LOGPROB_PATH = PROJECT / 'calibration_output' / 'mcmc_logprob_v12_mode1.npy'
POSTERIOR_NAMES_PATH = PROJECT / 'calibration_output' / 'posterior_param_names_v10.json'

# Fixed parameters not in the posterior (held constant during calibration)
FIXED_PARAMS = {
    'internal_lapse': -0.005,
    'k_wind': 0.0,
}

# Number of top-performing parameter sets to use (cf. Geck 2020, Eklutna)
N_TOP = 250

# Burn-in: discard first half of chain (conservative)
BURNIN_FRACTION = 0.5

# Ensemble output percentiles
PERCENTILES = [5, 25, 50, 75, 95]

# Auto-incrementing run counter file
_RUN_COUNTER_FILE = OUTPUT_BASE / '.run_counter'

# Result keys to aggregate across ensemble members
RESULT_KEYS = [
    'glacier_wide_balance', 'area_km2', 'volume_km3', 'mean_thickness_m',
    'total_annual_runoff_mm', 'peak_daily_discharge_m3s',
    'mean_annual_discharge_m3s', 'total_annual_discharge_m3',
]


def create_run_dir(n_params, scenarios, label=None):
    """Create a numbered, descriptively-named run directory.

    Format: PROJ-{NNN}_{label}_{date}/
    Example: PROJ-003_top250_ssp245-ssp585_2026-03-11/

    Returns Path to the created directory.
    """
    OUTPUT_BASE.mkdir(exist_ok=True)

    # Auto-increment run number
    if _RUN_COUNTER_FILE.exists():
        counter = int(_RUN_COUNTER_FILE.read_text().strip()) + 1
    else:
        # Scan existing PROJ-### folders to find max
        existing = [d.name for d in OUTPUT_BASE.iterdir()
                    if d.is_dir() and d.name.startswith('PROJ-')]
        if existing:
            nums = []
            for name in existing:
                try:
                    nums.append(int(name.split('_')[0].split('-')[1]))
                except (IndexError, ValueError):
                    pass
            counter = max(nums) + 1 if nums else 1
        else:
            counter = 1
    _RUN_COUNTER_FILE.write_text(str(counter))

    date_str = datetime.now().strftime('%Y-%m-%d')
    ssp_str = '-'.join(s.replace('ssp', '') for s in scenarios)
    param_str = f'top{n_params}' if n_params > 1 else 'single-param'
    if label:
        name = f'PROJ-{counter:03d}_{label}_{date_str}'
    else:
        name = f'PROJ-{counter:03d}_{param_str}_ssp{ssp_str}_{date_str}'

    run_dir = OUTPUT_BASE / name
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def load_params(path):
    """Load a single parameter set from JSON."""
    with open(path) as f:
        params = json.load(f)
    if 'lapse_rate' in params and 'internal_lapse' not in params:
        params['internal_lapse'] = params['lapse_rate']
    return params


def load_filtered_params(path):
    """Load behaviorally-filtered parameter sets from JSON.

    These are produced by run_behavioral_filter.py and contain only
    parameter sets that passed both snowline and area filters.

    Parameters
    ----------
    path : str or Path, path to filtered_params.json

    Returns
    -------
    list of dicts, each a complete param set for FastDETIM.run()
    """
    with open(path) as f:
        data = json.load(f)

    param_sets = data['param_sets']
    config = data.get('filter_config', {})

    print(f"  Loaded {len(param_sets)} behaviorally-filtered parameter sets")
    if config:
        print(f"    Filter: {config.get('n_candidates', '?')} candidates → "
              f"{len(param_sets)} survivors")
        print(f"    Snowline RMSE ≤ {config.get('snowline_rmse_threshold_m', '?')} m, "
              f"Area RMSE ≤ {config.get('area_rmse_threshold_km2', '?')} km²")

    return param_sets


def load_top_param_sets(n_top=N_TOP, chain_path=None, logprob_path=None,
                        names_path=None):
    """Select the top-performing parameter sets from the MCMC chain.

    Ranks all post-burn-in samples by log-probability and returns the
    n_top best-performing unique parameter sets. Follows the approach
    of Geck (2020) on Eklutna Glacier.

    Parameters
    ----------
    n_top : int
        Number of top-performing sets to keep (default 250).
    chain_path : path to MCMC chain .npy (n_steps × n_walkers × n_params)
    logprob_path : path to log-probability .npy (n_steps × n_walkers)
    names_path : path to JSON with parameter names list

    Returns
    -------
    list of dicts, each a complete param set for FastDETIM.run(),
    ordered best-to-worst by log-probability.
    """
    chain_path = Path(chain_path or CHAIN_PATH)
    logprob_path = Path(logprob_path or LOGPROB_PATH)
    names_path = Path(names_path or POSTERIOR_NAMES_PATH)

    chain = np.load(chain_path)       # (n_steps, n_walkers, n_params)
    logprob = np.load(logprob_path)   # (n_steps, n_walkers)
    with open(names_path) as f:
        names = json.load(f)

    n_steps = chain.shape[0]
    burnin = int(n_steps * BURNIN_FRACTION)

    # Flatten post-burn-in chain
    flat_chain = chain[burnin:].reshape(-1, chain.shape[2])
    flat_logprob = logprob[burnin:].flatten()
    n_available = flat_chain.shape[0]

    # Rank by log-probability (highest = best fit)
    ranked_idx = np.argsort(flat_logprob)[::-1]

    # Take top n_top, removing exact duplicates
    seen = set()
    selected = []
    for idx in ranked_idx:
        key = tuple(flat_chain[idx])
        if key not in seen:
            seen.add(key)
            selected.append(idx)
        if len(selected) >= n_top:
            break

    samples = flat_chain[selected]
    lp = flat_logprob[selected]

    print(f"  Selected top {len(selected)} of {n_available} post-burn-in samples")
    print(f"  Log-prob range: {lp[-1]:.2f} to {lp[0]:.2f} "
          f"(best – worst in selection)")

    param_list = []
    for row in samples:
        p = {name: float(val) for name, val in zip(names, row)}
        p['r_ice'] = 2.0 * p['r_snow']
        p.update(FIXED_PARAMS)
        param_list.append(p)

    return param_list


def run_single_gcm(fmodel, gcm_climate, ice_thickness_init, bedrock, grid,
                   params, routing_params, wy_start, wy_end, gcm_name='',
                   save_snapshots=False):
    """Run projection for a single GCM forcing.

    Parameters
    ----------
    save_snapshots : bool
        If True, store yearly spatial snapshots of glacier_mask and
        ice_thickness in results['snapshots']. Used for animations.

    Returns dict of annual results.
    """
    from dixon_melt.glacier_dynamics import apply_deltah, va_check, _select_size_class
    from dixon_melt.routing import route_linear_reservoirs

    cell_size = grid['cell_size']
    current_elev = grid['elevation'].copy()
    current_mask = grid['glacier_mask'].copy()
    ice_thickness = ice_thickness_init.copy()

    results = {
        'year': [], 'glacier_wide_balance': [], 'area_km2': [],
        'volume_km3': [], 'mean_thickness_m': [], 'cum_balance': [],
        'total_annual_runoff_mm': [], 'peak_daily_discharge_m3s': [],
        'mean_annual_discharge_m3s': [], 'total_annual_discharge_m3': [],
        'mean_summer_T': [], 'annual_precip_mm': [],
        'elev_min': [], 'elev_max': [], 'size_class': [],
    }

    if save_snapshots:
        results['snapshots'] = []

    cum_balance = 0.0

    for wy_year in range(wy_start, wy_end + 1):
        n_glacier = int(current_mask.sum())
        if n_glacier == 0:
            break

        area_km2 = n_glacier * cell_size**2 / 1e6
        area_m2 = n_glacier * cell_size**2
        glacier_elevs = current_elev[current_mask]
        glacier_thick = ice_thickness[current_mask]
        vol_km3 = glacier_thick.sum() * cell_size**2 / 1e9

        if save_snapshots:
            results['snapshots'].append({
                'year': wy_year,
                'mask': current_mask.copy(),
                'thickness': ice_thickness.copy(),
                'elevation': current_elev.copy(),
            })

        # Extract water year climate
        from dixon_melt.climate_projections import extract_water_year
        wy_climate = extract_water_year(gcm_climate, wy_year)
        if wy_climate is None:
            continue

        T = wy_climate['temperature'].values.astype(np.float64)
        P = wy_climate['precipitation'].values.astype(np.float64)
        doy = np.array(wy_climate.index.dayofyear, dtype=np.int64)

        # Update model geometry
        fmodel.update_geometry(current_elev, current_mask)

        # Run melt model
        r = fmodel.run(T, P, doy, params, 0.0)
        mb = r['glacier_wide_balance']
        cum_balance += mb

        # Route discharge
        Q_total, _, _, _ = route_linear_reservoirs(
            r['daily_runoff'], area_m2,
            routing_params['k_fast'], routing_params['k_slow'],
            routing_params['k_gw'], routing_params['f_fast'],
            routing_params['f_slow'],
        )

        # Summer temp (Jun-Aug, DOYs 152-243)
        summer_mask = (doy >= 152) & (doy <= 243)
        mean_summer_T = float(T[summer_mask].mean()) if summer_mask.any() else np.nan

        size_class = _select_size_class(area_km2)

        results['year'].append(wy_year)
        results['glacier_wide_balance'].append(mb)
        results['area_km2'].append(area_km2)
        results['volume_km3'].append(vol_km3)
        results['mean_thickness_m'].append(float(glacier_thick.mean()))
        results['cum_balance'].append(cum_balance)
        results['total_annual_runoff_mm'].append(float(r['daily_runoff'].sum()))
        results['peak_daily_discharge_m3s'].append(float(Q_total.max()))
        results['mean_annual_discharge_m3s'].append(float(Q_total.mean()))
        results['total_annual_discharge_m3'].append(float(Q_total.sum() * 86400))
        results['mean_summer_T'].append(mean_summer_T)
        results['annual_precip_mm'].append(float(P.sum()))
        results['elev_min'].append(float(glacier_elevs.min()))
        results['elev_max'].append(float(glacier_elevs.max()))
        results['size_class'].append(size_class)

        # Apply delta-h geometry update
        current_elev, current_mask, _ = apply_deltah(
            current_elev, current_mask, ice_thickness, bedrock,
            mb, cell_size,
        )

    return results


def peak_water_analysis(results_list, scenario_name):
    """Compute peak water year from ensemble of GCM results.

    Returns dict with peak year, discharge, and confidence interval.
    """
    # Collect annual discharge from all GCMs into a 2D array
    all_years = set()
    for r in results_list:
        all_years.update(r['year'])
    years = sorted(all_years)

    if len(years) < 10:
        return None

    # Build discharge matrix (n_gcms x n_years)
    discharge_matrix = []
    for r in results_list:
        yr_to_q = dict(zip(r['year'], r['mean_annual_discharge_m3s']))
        row = [yr_to_q.get(y, np.nan) for y in years]
        discharge_matrix.append(row)

    Q = np.array(discharge_matrix)
    Q_mean = np.nanmean(Q, axis=0)

    # 11-year running mean for robust peak detection
    window = min(11, len(years) // 3)
    if window < 3:
        window = 3
    kernel = np.ones(window) / window
    smoothed = np.convolve(Q_mean, kernel, mode='valid')
    offset = window // 2
    peak_idx = np.argmax(smoothed)
    peak_year = years[peak_idx + offset]
    peak_q = smoothed[peak_idx]

    # GCM spread at peak
    peak_yr_idx = years.index(peak_year) if peak_year in years else peak_idx + offset
    gcm_peaks = Q[:, peak_yr_idx]
    gcm_peaks = gcm_peaks[~np.isnan(gcm_peaks)]

    return {
        'peak_year': peak_year,
        'peak_discharge_m3s': peak_q,
        'gcm_min': float(np.min(gcm_peaks)) if len(gcm_peaks) > 0 else np.nan,
        'gcm_max': float(np.max(gcm_peaks)) if len(gcm_peaks) > 0 else np.nan,
        'window_years': window,
    }


def aggregate_ensemble(all_runs, years):
    """Aggregate results across all ensemble members (GCM × param samples).

    Parameters
    ----------
    all_runs : list of result dicts from run_single_gcm
    years : sorted list of water years

    Returns
    -------
    DataFrame with columns: year, {key}_mean, {key}_std, {key}_p05..p95
    """
    ens_df = pd.DataFrame({'year': years})
    n_years = len(years)

    for key in RESULT_KEYS:
        # Build matrix (n_members × n_years), aligning on year
        vals = []
        for r in all_runs:
            yr_to_val = dict(zip(r['year'], r[key]))
            vals.append([yr_to_val.get(y, np.nan) for y in years])
        arr = np.array(vals)

        ens_df[f'{key}_mean'] = np.nanmean(arr, axis=0)
        ens_df[f'{key}_std'] = np.nanstd(arr, axis=0)
        for pct in PERCENTILES:
            ens_df[f'{key}_p{pct:02d}'] = np.nanpercentile(arr, pct, axis=0)

    return ens_df


def run_projection(params_path=None, scenario='ssp245', end_year=2100,
                   grid_res=100.0, gcms=None, n_samples=None,
                   output_dir=None, filtered_params_path=None):
    """Run full ensemble projection for one SSP scenario.

    Propagates both climate uncertainty (multi-GCM) and parameter uncertainty
    (MCMC posterior samples). Each (GCM, param_sample) pair runs an independent
    simulation with its own geometry evolution trajectory.

    Parameters
    ----------
    params_path : str or None
        Path to single-param JSON (legacy mode). If None, uses posterior
        ensemble from calibration_output/.
    scenario : str
        SSP scenario identifier (ssp126, ssp245, ssp585).
    end_year : int
        Final water year of projection.
    grid_res : float
        Model grid resolution in meters.
    gcms : list of str or None
        GCM names to include; None = all 5.
    n_samples : int or None
        Number of top-performing param sets to use. None = 250
        (following Geck 2020). Ignored when params_path is a JSON.
    output_dir : Path or None
        Directory for output files. If None, auto-creates a PROJ-### folder.
    filtered_params_path : str or None
        Path to behaviorally-filtered params JSON from run_behavioral_filter.py.
        If provided, overrides params_path and n_samples.

    Returns
    -------
    dict with scenario, ensemble results, peak water analysis.
    """
    t_start = time.time()

    from dixon_melt.climate_projections import (
        GCMS as DEFAULT_GCMS, SCENARIOS, prepare_gcm_ensemble,
    )

    if gcms is None:
        gcms = DEFAULT_GCMS

    scenario_label = SCENARIOS.get(scenario, scenario)

    # ── Load parameters ───────────────────────────────────────────────
    if filtered_params_path is not None:
        param_sets = load_filtered_params(filtered_params_path)
        param_source = f"behavioral filter: {len(param_sets)} survivors"
    elif params_path is not None and params_path.endswith('.json'):
        param_sets = [load_params(params_path)]
        param_source = f"single: {params_path}"
    else:
        param_sets = load_top_param_sets(n_top=n_samples or N_TOP)
        param_source = f"top {len(param_sets)} from MCMC chain"

    n_params = len(param_sets)

    # ── Create output directory ────────────────────────────────────────
    if output_dir is None:
        output_dir = create_run_dir(n_params, [scenario])
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"DIXON GLACIER PROJECTION — {scenario_label}")
    print(f"Period: WY2026 to WY{end_year}")
    print(f"GCMs ({len(gcms)}): {gcms}")
    print(f"Parameter sets: {param_source}")
    print(f"Total runs: {len(gcms)} GCMs × {n_params} param sets"
          f" = {len(gcms) * n_params}")
    print(f"Output: {output_dir.name}/")
    print("=" * 70)

    # ── Prepare grid & model ──────────────────────────────────────────
    from dixon_melt.terrain import prepare_grid
    grid = prepare_grid(str(DEM_PATH), str(GLACIER_PATH), target_res=grid_res)

    from dixon_melt.model import precompute_ipot
    print("  Precomputing I_pot table...")
    ipot_table = precompute_ipot(grid, doy_range=range(1, 366), dt_hours=3.0)

    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config
    from dixon_melt.glacier_dynamics import (
        initialize_ice_thickness, compute_bedrock,
    )

    fmodel = FastDETIM(
        grid, ipot_table,
        transfer_alpha=config.TRANSFER_ALPHA,
        transfer_beta=config.TRANSFER_BETA,
        ref_elev=config.SNOTEL_ELEV,
        stake_names=config.STAKE_NAMES,
        stake_elevs=config.STAKE_ELEVS,
    )

    # ── Initialize ice thickness & bedrock ────────────────────────────
    farinotti = str(FARINOTTI_PATH) if FARINOTTI_PATH.exists() else None
    ice_thickness, thickness_source = initialize_ice_thickness(
        grid, farinotti_path=farinotti)
    bedrock = compute_bedrock(grid['elevation'], ice_thickness)
    cell_size = grid['cell_size']

    n_init = int(grid['glacier_mask'].sum())
    area_init = n_init * cell_size**2 / 1e6
    vol_init = ice_thickness[grid['glacier_mask']].sum() * cell_size**2 / 1e9

    print(f"\n  Ice thickness: {thickness_source}")
    print(f"  Initial: {area_init:.1f} km2, {vol_init:.3f} km3, "
          f"H_mean={ice_thickness[grid['glacier_mask']].mean():.0f} m")

    # ── Load & bias-correct CMIP6 ensemble ────────────────────────────
    print(f"\n  Loading CMIP6 ensemble for {scenario}...")
    ensemble = prepare_gcm_ensemble(
        str(CMIP6_DIR), str(CLIMATE_PATH), scenario, gcms=gcms)

    if len(ensemble) == 0:
        print("  ERROR: No GCM data available. Run download_cmip6.py first.")
        return None

    print(f"  Loaded {len(ensemble)} GCMs: {list(ensemble.keys())}")

    # ── Prepend historical climate (2000-2025) to each GCM ───────────
    # This ensures continuous glacier evolution from the initial DEM geometry
    # through the historical period and into the projection.
    historical = pd.read_csv(CLIMATE_PATH, parse_dates=['date'], index_col='date')
    historical = historical[['temperature', 'precipitation']]
    # Trim to historical period (before GCM data starts)
    hist_end = '2025-09-30'
    historical = historical.loc[:hist_end]
    print(f"  Historical climate: {len(historical)} days "
          f"({historical.index.min().date()} to {historical.index.max().date()})")

    for gcm_name in list(ensemble.keys()):
        gcm_df = ensemble[gcm_name]
        # Remove any GCM data that overlaps with historical period
        gcm_df = gcm_df.loc['2025-10-01':]
        # Concatenate: historical then GCM
        combined = pd.concat([historical, gcm_df])
        combined = combined[~combined.index.duplicated(keep='first')]
        combined = combined.sort_index()
        ensemble[gcm_name] = combined

    wy_start = 2001  # Start from WY2001 (Oct 2000 - Sep 2001)
    print(f"  Running WY{wy_start} to WY{end_year} "
          f"(historical 2001-2025 + projection 2026-{end_year})")

    # ── Routing parameters ────────────────────────────────────────────
    routing_params = config.DEFAULT_ROUTING

    # ── Run all (GCM × param) combinations ────────────────────────────
    all_runs = []          # flat list of every run result
    gcm_results = {}       # keyed by gcm_name → list of runs (one per param)
    run_count = 0
    total_runs = len(ensemble) * n_params

    for gcm_name, gcm_climate in ensemble.items():
        gcm_runs = []
        print(f"\n  --- {gcm_name} ({n_params} param sets) ---")
        t_gcm = time.time()

        for pi, params in enumerate(param_sets):
            run_count += 1
            r = run_single_gcm(
                fmodel, gcm_climate, ice_thickness, bedrock, grid,
                params, routing_params, wy_start, end_year, gcm_name,
            )
            gcm_runs.append(r)
            all_runs.append(r)

            if n_params <= 5 or (pi + 1) % max(1, n_params // 5) == 0:
                n_yr = len(r['year'])
                area_end = r['area_km2'][-1] if n_yr > 0 else 0
                print(f"    [{run_count}/{total_runs}] param {pi+1}/{n_params}"
                      f"  final area={area_end:.1f} km2")

        dt_gcm = time.time() - t_gcm
        print(f"    {gcm_name} done: {dt_gcm:.0f}s "
              f"({dt_gcm / max(n_params, 1):.1f}s/run)")
        gcm_results[gcm_name] = gcm_runs

    # ── Ensemble aggregation ──────────────────────────────────────────
    elapsed = time.time() - t_start
    print(f"\n{'=' * 70}")
    print(f"ENSEMBLE SUMMARY — {scenario_label} ({elapsed:.0f}s)")
    print(f"  {total_runs} total runs "
          f"({len(ensemble)} GCMs × {n_params} param sets)")
    print(f"{'=' * 70}")

    # Determine common year range
    all_years = set()
    for r in all_runs:
        all_years.update(r['year'])
    years = sorted(all_years)

    # Full ensemble aggregation (GCM × param)
    ens_df = aggregate_ensemble(all_runs, years)

    # Per-GCM median (aggregated over param samples)
    gcm_medians = {}
    for gcm_name, runs in gcm_results.items():
        gcm_df = aggregate_ensemble(runs, years)
        gcm_medians[gcm_name] = gcm_df

    # Peak water (using all runs for full uncertainty)
    pw = peak_water_analysis(all_runs, scenario)
    if pw:
        print(f"\n  PEAK WATER: ~WY{pw['peak_year']} "
              f"({pw['peak_discharge_m3s']:.2f} m3/s, "
              f"{pw['window_years']}-yr smoothed)")
        print(f"    Range: {pw['gcm_min']:.2f}–{pw['gcm_max']:.2f} m3/s")

    # End-of-century summary
    if years:
        last_yr = years[-1]
        last_idx = years.index(last_yr)
        print(f"\n  End-of-century (WY{last_yr}):")
        print(f"    Area:   {ens_df.loc[last_idx, 'area_km2_p50']:.1f} km2 "
              f"[{ens_df.loc[last_idx, 'area_km2_p05']:.1f}–"
              f"{ens_df.loc[last_idx, 'area_km2_p95']:.1f}]"
              f"  ({100 * ens_df.loc[last_idx, 'area_km2_p50'] / area_init:.0f}%)")
        print(f"    Volume: {ens_df.loc[last_idx, 'volume_km3_p50']:.4f} km3 "
              f"[{ens_df.loc[last_idx, 'volume_km3_p05']:.4f}–"
              f"{ens_df.loc[last_idx, 'volume_km3_p95']:.4f}]"
              f"  ({100 * ens_df.loc[last_idx, 'volume_km3_p50'] / max(vol_init, 1e-9):.0f}%)")
        print(f"    Bal:    {ens_df.loc[last_idx, 'glacier_wide_balance_p50']:+.2f}"
              f" m w.e./yr "
              f"[{ens_df.loc[last_idx, 'glacier_wide_balance_p05']:+.2f} to "
              f"{ens_df.loc[last_idx, 'glacier_wide_balance_p95']:+.2f}]")

        # Per-GCM breakdown
        print(f"\n  Per-GCM median end-of-century area:")
        for gcm_name, gcm_df in gcm_medians.items():
            a = gcm_df.loc[last_idx, 'area_km2_p50']
            print(f"    {gcm_name:20s}: {a:.1f} km2 "
                  f"({100 * a / area_init:.0f}%)")

    # ── Save results ──────────────────────────────────────────────────
    output_dir.mkdir(exist_ok=True)

    # Full ensemble percentiles
    ens_file = output_dir / f'projection_{scenario}_ensemble_{end_year}.csv'
    ens_df.to_csv(ens_file, index=False)
    print(f"\n  Ensemble summary: {ens_file.name}")

    # Per-GCM aggregated results
    for gcm_name, gcm_df in gcm_medians.items():
        gcm_file = output_dir / f'projection_{scenario}_{gcm_name}_{end_year}.csv'
        gcm_df.to_csv(gcm_file, index=False)

    # Peak water
    if pw:
        pw['n_param_samples'] = n_params
        pw['n_gcms'] = len(ensemble)
        pw['n_total_runs'] = total_runs
        pw_file = output_dir / f'peak_water_{scenario}.json'
        with open(pw_file, 'w') as f:
            json.dump(pw, f, indent=2)

    # Save ensemble metadata
    meta = {
        'scenario': scenario,
        'end_year': end_year,
        'grid_res_m': grid_res,
        'n_param_samples': n_params,
        'gcms': list(ensemble.keys()),
        'n_total_runs': total_runs,
        'initial_area_km2': area_init,
        'initial_volume_km3': vol_init,
        'thickness_source': thickness_source,
        'elapsed_seconds': elapsed,
        'percentiles': PERCENTILES,
    }
    meta_file = output_dir / f'projection_{scenario}_meta_{end_year}.json'
    with open(meta_file, 'w') as f:
        json.dump(meta, f, indent=2)

    print(f"  All results saved to {output_dir}/")

    return {
        'scenario': scenario,
        'ensemble_df': ens_df,
        'gcm_medians': gcm_medians,
        'peak_water': pw,
        'initial_area_km2': area_init,
        'initial_volume_km3': vol_init,
        'output_dir': output_dir,
    }


def run_all_scenarios(params_path=None, end_year=2100, grid_res=100.0,
                      gcms=None, n_samples=None, label=None,
                      filtered_params_path=None):
    """Run projections for all three SSP scenarios."""
    from dixon_melt.climate_projections import SCENARIOS

    # Determine n_params for folder naming
    if filtered_params_path is not None:
        with open(filtered_params_path) as f:
            n_p = len(json.load(f)['param_sets'])
        if label is None:
            label = f'filtered{n_p}'
    elif params_path is not None and params_path.endswith('.json'):
        n_p = 1
    else:
        n_p = n_samples or N_TOP

    # One shared folder for all scenarios in this run
    run_dir = create_run_dir(n_p, list(SCENARIOS.keys()), label=label)
    print(f"\n  Run directory: {run_dir.name}/\n")

    all_projections = {}
    for scenario in SCENARIOS:
        result = run_projection(
            params_path, scenario, end_year, grid_res, gcms, n_samples,
            output_dir=run_dir, filtered_params_path=filtered_params_path)
        if result is not None:
            all_projections[scenario] = result

    # Cross-scenario comparison
    if len(all_projections) > 1:
        print("\n" + "=" * 70)
        print("CROSS-SCENARIO COMPARISON")
        print("=" * 70)
        for sc, res in all_projections.items():
            pw = res.get('peak_water')
            pw_str = f"WY{pw['peak_year']}" if pw else "N/A"
            ens = res['ensemble_df']
            last = len(ens) - 1
            area_med = ens.loc[last, 'area_km2_p50']
            print(f"  {sc}: peak water {pw_str}, "
                  f"final area {area_med:.1f} km2 "
                  f"[{ens.loc[last, 'area_km2_p05']:.1f}–"
                  f"{ens.loc[last, 'area_km2_p95']:.1f}] "
                  f"({100 * area_med / res['initial_area_km2']:.0f}%)")

    return all_projections


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Run Dixon Glacier future projections')
    parser.add_argument('--scenario', default=None,
                        choices=['ssp126', 'ssp245', 'ssp585', 'all'],
                        help='SSP scenario (default: all)')
    parser.add_argument('--end-year', type=int, default=2100)
    parser.add_argument('--params', default=None,
                        help='Path to single-param JSON (legacy) or posterior '
                             '.npy. Default: use posterior ensemble.')
    parser.add_argument('--n-samples', type=int, default=None,
                        help='Number of top-performing param sets '
                             '(default: 250, cf. Geck 2020)')
    parser.add_argument('--gcms', nargs='+', default=None,
                        help='GCMs to use (default: 5-model ensemble)')
    parser.add_argument('--grid-res', type=float, default=100.0)
    parser.add_argument('--label', default=None,
                        help='Custom label for the run folder name')
    parser.add_argument('--filtered-params', default=None,
                        help='Path to behaviorally-filtered params JSON '
                             '(from run_behavioral_filter.py). Overrides '
                             '--params and --n-samples.')
    args = parser.parse_args()

    if args.scenario is None or args.scenario == 'all':
        run_all_scenarios(args.params, args.end_year, args.grid_res,
                          args.gcms, args.n_samples, args.label,
                          args.filtered_params)
    else:
        run_projection(args.params, args.scenario, args.end_year,
                       args.grid_res, args.gcms, args.n_samples,
                       filtered_params_path=args.filtered_params)
