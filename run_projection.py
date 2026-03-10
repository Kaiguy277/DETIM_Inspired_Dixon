"""
Future projection runner for Dixon Glacier.

Runs DETIM forward under CMIP6 emission scenarios (NEX-GDDP-CMIP6) with
evolving glacier geometry (delta-h, Huss et al. 2010) and discharge routing
(parallel linear reservoirs). Multi-GCM ensemble for uncertainty.

Tracks: mass balance, area, volume, mean thickness, discharge (m3/s),
and identifies "peak water" timing per scenario.

Usage:
    python run_projection.py --scenario ssp245
                             [--params calibration_output/best_params_v10.json]
                             [--end-year 2100]
                             [--gcms ACCESS-CM2 MRI-ESM2-0]

Requires:
    1. Calibrated parameters (from CAL-010 or similar)
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
import json
import time

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
DEM_PATH = PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif'
GLACIER_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
NUKA_PATH = PROJECT / 'data' / 'climate' / 'nuka_snotel_full.csv'
CMIP6_DIR = PROJECT / 'data' / 'cmip6'
FARINOTTI_PATH = PROJECT / 'data' / 'ice_thickness' / 'RGI60-01.18059_thickness.tif'
OUTPUT_DIR = PROJECT / 'projection_output'


def load_params(path):
    with open(path) as f:
        params = json.load(f)
    # Map param names: calibration saves 'lapse_rate', FastDETIM expects 'internal_lapse'
    if 'lapse_rate' in params and 'internal_lapse' not in params:
        params['internal_lapse'] = params['lapse_rate']
    return params


def run_single_gcm(fmodel, gcm_climate, ice_thickness_init, bedrock, grid,
                   params, routing_params, wy_start, wy_end, gcm_name=''):
    """Run projection for a single GCM forcing.

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


def run_projection(params_path, scenario='ssp245', end_year=2100,
                   grid_res=100.0, gcms=None):
    """Run full ensemble projection for one SSP scenario.

    Returns dict with ensemble results.
    """
    t_start = time.time()

    from dixon_melt.climate_projections import (
        GCMS as DEFAULT_GCMS, SCENARIOS, prepare_gcm_ensemble,
    )

    if gcms is None:
        gcms = DEFAULT_GCMS

    scenario_label = SCENARIOS.get(scenario, scenario)

    print("=" * 70)
    print(f"DIXON GLACIER PROJECTION — {scenario_label}")
    print(f"Period: WY2026 to WY{end_year}")
    print(f"GCMs: {gcms}")
    print("=" * 70)

    params = load_params(params_path)
    print(f"\n  Parameters from: {params_path}")

    # ── Prepare grid & model ──────────────────────────────────────────
    from dixon_melt.terrain import prepare_grid
    grid = prepare_grid(str(DEM_PATH), str(GLACIER_PATH), target_res=grid_res)

    from dixon_melt.model import precompute_ipot
    print("  Precomputing I_pot table...")
    ipot_table = precompute_ipot(grid, doy_range=range(1, 366), dt_hours=3.0)

    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config
    from dixon_melt.glacier_dynamics import (
        initialize_ice_thickness, compute_bedrock, va_check,
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
        str(CMIP6_DIR), str(NUKA_PATH), scenario, gcms=gcms)

    if len(ensemble) == 0:
        print("  ERROR: No GCM data available. Run download_cmip6.py first.")
        return None

    print(f"  Loaded {len(ensemble)} GCMs: {list(ensemble.keys())}")

    # ── Routing parameters ────────────────────────────────────────────
    routing_params = config.DEFAULT_ROUTING

    # ── Run each GCM ──────────────────────────────────────────────────
    all_results = {}
    for gcm_name, gcm_climate in ensemble.items():
        print(f"\n  --- {gcm_name} ---")
        t_gcm = time.time()

        r = run_single_gcm(
            fmodel, gcm_climate, ice_thickness, bedrock, grid,
            params, routing_params, 2026, end_year, gcm_name,
        )

        n_years = len(r['year'])
        if n_years > 0:
            final_area = r['area_km2'][-1]
            final_vol = r['volume_km3'][-1]
            print(f"    {n_years} years, final: {final_area:.1f} km2, "
                  f"{final_vol:.3f} km3 "
                  f"({100 * final_area / area_init:.0f}% area, "
                  f"{100 * final_vol / max(vol_init, 1e-9):.0f}% vol), "
                  f"{time.time() - t_gcm:.0f}s")
        all_results[gcm_name] = r

    # ── Ensemble summary ──────────────────────────────────────────────
    elapsed = time.time() - t_start
    print(f"\n{'=' * 70}")
    print(f"ENSEMBLE SUMMARY — {scenario_label} ({elapsed:.0f}s)")
    print(f"{'=' * 70}")

    # Peak water
    results_list = list(all_results.values())
    pw = peak_water_analysis(results_list, scenario)
    if pw:
        print(f"\n  PEAK WATER: ~WY{pw['peak_year']} "
              f"({pw['peak_discharge_m3s']:.2f} m3/s, "
              f"{pw['window_years']}-yr smoothed)")
        print(f"    GCM range: {pw['gcm_min']:.2f}–{pw['gcm_max']:.2f} m3/s")

    # End-of-century summary
    print(f"\n  End-of-century ({end_year}):")
    for gcm_name, r in all_results.items():
        if len(r['year']) > 0:
            print(f"    {gcm_name}: area={r['area_km2'][-1]:.1f} km2, "
                  f"vol={r['volume_km3'][-1]:.3f} km3, "
                  f"cum_MB={r['cum_balance'][-1]:+.1f} m w.e.")

    # ── Save results ──────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(exist_ok=True)

    for gcm_name, r in all_results.items():
        df = pd.DataFrame(r)
        outfile = OUTPUT_DIR / f'projection_{scenario}_{gcm_name}_{end_year}.csv'
        df.to_csv(outfile, index=False)

    # Save ensemble mean
    if len(results_list) > 0:
        years = results_list[0]['year']
        ens_df = pd.DataFrame({'year': years})

        for key in ['glacier_wide_balance', 'area_km2', 'volume_km3',
                    'mean_thickness_m', 'total_annual_runoff_mm',
                    'mean_annual_discharge_m3s', 'peak_daily_discharge_m3s']:
            vals = []
            for r in results_list:
                yr_to_val = dict(zip(r['year'], r[key]))
                vals.append([yr_to_val.get(y, np.nan) for y in years])
            arr = np.array(vals)
            ens_df[f'{key}_mean'] = np.nanmean(arr, axis=0)
            ens_df[f'{key}_std'] = np.nanstd(arr, axis=0)
            ens_df[f'{key}_min'] = np.nanmin(arr, axis=0)
            ens_df[f'{key}_max'] = np.nanmax(arr, axis=0)

        ens_file = OUTPUT_DIR / f'projection_{scenario}_ensemble_{end_year}.csv'
        ens_df.to_csv(ens_file, index=False)
        print(f"\n  Ensemble summary: {ens_file.name}")

    if pw:
        pw_file = OUTPUT_DIR / f'peak_water_{scenario}.json'
        with open(pw_file, 'w') as f:
            json.dump(pw, f, indent=2)

    print(f"  All results saved to {OUTPUT_DIR}/")

    return {
        'scenario': scenario,
        'gcm_results': all_results,
        'peak_water': pw,
        'initial_area_km2': area_init,
        'initial_volume_km3': vol_init,
    }


def run_all_scenarios(params_path, end_year=2100, grid_res=100.0, gcms=None):
    """Run projections for all three SSP scenarios."""
    from dixon_melt.climate_projections import SCENARIOS

    all_projections = {}
    for scenario in SCENARIOS:
        result = run_projection(
            params_path, scenario, end_year, grid_res, gcms)
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
            gcm_areas = [r['area_km2'][-1] for r in res['gcm_results'].values()
                         if len(r['area_km2']) > 0]
            mean_area = np.mean(gcm_areas) if gcm_areas else 0
            print(f"  {sc}: peak water {pw_str}, "
                  f"final area {mean_area:.1f} km2 "
                  f"({100 * mean_area / res['initial_area_km2']:.0f}%)")

    return all_projections


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Run Dixon Glacier future projections')
    parser.add_argument('--scenario', default=None,
                        choices=['ssp126', 'ssp245', 'ssp585', 'all'],
                        help='SSP scenario (default: all)')
    parser.add_argument('--end-year', type=int, default=2100)
    parser.add_argument('--params',
                        default='calibration_output/best_params_v10.json')
    parser.add_argument('--gcms', nargs='+', default=None,
                        help='GCMs to use (default: 5-model ensemble)')
    parser.add_argument('--grid-res', type=float, default=100.0)
    args = parser.parse_args()

    if args.scenario is None or args.scenario == 'all':
        run_all_scenarios(args.params, args.end_year, args.grid_res, args.gcms)
    else:
        run_projection(args.params, args.scenario, args.end_year,
                       args.grid_res, args.gcms)
