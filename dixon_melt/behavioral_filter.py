"""
Multi-criteria behavioral filtering for DETIM parameter sets.

Screens MCMC posterior samples against independent observational
constraints that were NOT used in calibration:

  1. Snowline position — 22 years of digitized end-of-summer snowlines
     (elevation-based comparison, RMSE threshold)
  2. Glacier area evolution — digitized outlines at multi-year intervals
     (historical simulation with delta-h, area RMSE threshold)

Parameter sets that pass both filters are retained for projection,
ranked by their original MCMC log-probability. This follows the
"behavioral" or "multi-criteria" filtering approach of Gabbi et al.
(2014) and is analogous to GLUE-style informal likelihood weighting.

References
----------
Gabbi, J., Farinotti, D., Bauder, A., & Maurer, H. (2012). Ice volume
    distribution and implications on runoff projections in a
    glacierized catchment. HESS, 16, 4543-4556.
Beven, K. & Binley, A. (1992). The future of distributed models:
    model calibration and uncertainty prediction. Hydrol. Proc., 6, 279-298.
"""
import numpy as np
import pandas as pd
from pathlib import Path
import json
import time


# ── Snowline filter ──────────────────────────────────────────────────

def score_snowline(fmodel, climate, grid, params, snowline_dir):
    """Evaluate a single parameter set against all observed snowlines.

    Runs the model for each year with a valid snowline observation and
    compares modeled vs observed mean snowline elevation.

    Parameters
    ----------
    fmodel : FastDETIM instance
    climate : DataFrame with 'temperature', 'precipitation', DatetimeIndex
    grid : dict from prepare_grid
    params : dict of model parameters
    snowline_dir : str, path to directory with snowline shapefiles

    Returns
    -------
    dict with:
        rmse_m : float, RMSE of snowline elevation bias (m)
        mae_m : float, mean absolute error (m)
        mean_bias_m : float, mean signed bias (m)
        n_years : int, number of valid comparison years
        per_year : list of dicts with per-year results
        passed : bool (set later by apply_filter)
    """
    from .snowline_validation import (
        load_all_snowlines, validate_snowline_year,
    )

    dem_info = {
        'elevation': grid['elevation'],
        'glacier_mask': grid['glacier_mask'],
        'transform': grid['transform'],
        'cell_size': grid['cell_size'],
        'nrows': grid['elevation'].shape[0],
        'ncols': grid['elevation'].shape[1],
    }

    obs_list = load_all_snowlines(snowline_dir, dem_info)

    biases = []
    per_year = []
    for obs in obs_list:
        r = validate_snowline_year(fmodel, climate, grid, params, obs)
        if r is None or r == 'bad_climate':
            continue
        if np.isnan(r['elev_bias']):
            continue

        biases.append(r['elev_bias'])
        per_year.append({
            'year': r['year'],
            'obs_elev': r['obs_snowline_elev'],
            'mod_elev': r['modeled_snowline_elev'],
            'bias_m': r['elev_bias'],
        })

    if len(biases) == 0:
        return {
            'rmse_m': np.nan, 'mae_m': np.nan, 'mean_bias_m': np.nan,
            'n_years': 0, 'per_year': [],
        }

    biases = np.array(biases)
    return {
        'rmse_m': float(np.sqrt((biases ** 2).mean())),
        'mae_m': float(np.abs(biases).mean()),
        'mean_bias_m': float(biases.mean()),
        'n_years': len(biases),
        'per_year': per_year,
    }


# ── Glacier area filter ─────────────────────────────────────────────

def load_observed_areas(outline_json_path):
    """Load observed glacier areas from the digitized outline summary.

    Parameters
    ----------
    outline_json_path : str or Path, path to JSON file with format:
        [{"year": 2000, "area_km2": 40.12}, ...]

    Returns
    -------
    dict mapping year (int) → area_km2 (float), sorted by year
    """
    with open(outline_json_path) as f:
        records = json.load(f)

    # Sort by year, skip any without area
    areas = {}
    for rec in records:
        yr = int(rec['year'])
        a = rec.get('area_km2')
        if a is not None:
            areas[yr] = float(a)

    return dict(sorted(areas.items()))


def score_area_evolution(fmodel, climate, grid, params, observed_areas,
                         ice_thickness_init, bedrock, wy_start=2000):
    """Run historical simulation with delta-h and compare area at checkpoints.

    Parameters
    ----------
    fmodel : FastDETIM instance
    climate : DataFrame with 'temperature', 'precipitation', DatetimeIndex
    grid : dict from prepare_grid
    params : dict of model parameters
    observed_areas : dict mapping year → area_km2
    ice_thickness_init : 2D array, initial ice thickness (m)
    bedrock : 2D array, bedrock elevation (m)
    wy_start : int, first water year to simulate

    Returns
    -------
    dict with:
        rmse_km2 : float, RMSE of area error at checkpoint years
        mae_km2 : float
        mean_bias_km2 : float
        max_abs_error_km2 : float
        n_checkpoints : int
        per_checkpoint : list of dicts
    """
    from .glacier_dynamics import apply_deltah
    from .climate_projections import extract_water_year

    checkpoint_years = sorted(observed_areas.keys())
    if not checkpoint_years:
        return {
            'rmse_km2': np.nan, 'mae_km2': np.nan, 'mean_bias_km2': np.nan,
            'max_abs_error_km2': np.nan, 'n_checkpoints': 0,
            'per_checkpoint': [],
        }

    wy_end = max(checkpoint_years)
    cell_size = grid['cell_size']

    # Initialize geometry from the DEM (which is 2010 IfSAR)
    current_elev = grid['elevation'].copy()
    current_mask = grid['glacier_mask'].copy()
    ice_thickness = ice_thickness_init.copy()

    per_checkpoint = []
    errors = []

    for wy_year in range(wy_start, wy_end + 1):
        n_glacier = int(current_mask.sum())
        if n_glacier == 0:
            break

        modeled_area = n_glacier * cell_size ** 2 / 1e6

        # Check if this is a checkpoint year
        if wy_year in observed_areas:
            obs_area = observed_areas[wy_year]
            error = modeled_area - obs_area
            errors.append(error)
            per_checkpoint.append({
                'year': wy_year,
                'obs_area_km2': obs_area,
                'mod_area_km2': modeled_area,
                'error_km2': error,
            })

        # Extract water year climate
        wy_climate = extract_water_year(climate, wy_year)
        if wy_climate is None:
            continue

        T = wy_climate['temperature'].values.astype(np.float64)
        P = wy_climate['precipitation'].values.astype(np.float64)
        doy = np.array(wy_climate.index.dayofyear, dtype=np.int64)

        # Handle NaN
        T = np.where(np.isnan(T), 0.0, T)
        P = np.where(np.isnan(P), 0.0, P)

        # Update model geometry and run
        fmodel.update_geometry(current_elev, current_mask)
        r = fmodel.run(T, P, doy, params, 0.0)
        mb = r['glacier_wide_balance']

        # Apply delta-h geometry update
        current_elev, current_mask, _ = apply_deltah(
            current_elev, current_mask, ice_thickness, bedrock,
            mb, cell_size,
        )

    if len(errors) == 0:
        return {
            'rmse_km2': np.nan, 'mae_km2': np.nan, 'mean_bias_km2': np.nan,
            'max_abs_error_km2': np.nan, 'n_checkpoints': 0,
            'per_checkpoint': [],
        }

    errors = np.array(errors)
    return {
        'rmse_km2': float(np.sqrt((errors ** 2).mean())),
        'mae_km2': float(np.abs(errors).mean()),
        'mean_bias_km2': float(errors.mean()),
        'max_abs_error_km2': float(np.abs(errors).max()),
        'n_checkpoints': len(errors),
        'per_checkpoint': per_checkpoint,
    }


# ── Combined filter ─────────────────────────────────────────────────

def run_behavioral_filter(
    param_sets,
    fmodel, climate, grid,
    snowline_dir,
    observed_areas,
    ice_thickness_init, bedrock,
    snowline_rmse_max=150.0,
    area_rmse_max=1.5,
    wy_start=2000,
    verbose=True,
):
    """Screen parameter sets against snowline and area observations.

    Parameters
    ----------
    param_sets : list of dicts, candidate parameter sets (from MCMC)
    fmodel : FastDETIM instance
    climate : DataFrame
    grid : dict
    snowline_dir : str, path to snowline shapefiles
    observed_areas : dict, year → area_km2
    ice_thickness_init : 2D array
    bedrock : 2D array
    snowline_rmse_max : float, max allowed snowline RMSE (m) to pass
    area_rmse_max : float, max allowed area RMSE (km²) to pass
    wy_start : int, start year for area evolution simulation
    verbose : bool

    Returns
    -------
    dict with:
        survivors : list of dicts (param sets that passed both filters)
        survivor_indices : list of int (indices into original param_sets)
        all_scores : list of dicts (full scoring for every param set)
        summary : dict with filter statistics
    """
    n_total = len(param_sets)
    all_scores = []
    survivors = []
    survivor_indices = []

    t_start = time.time()

    if verbose:
        print(f"\n{'=' * 70}")
        print(f"BEHAVIORAL FILTER — {n_total} candidate parameter sets")
        print(f"  Snowline RMSE threshold: {snowline_rmse_max:.0f} m")
        print(f"  Area RMSE threshold:     {area_rmse_max:.1f} km²")
        print(f"  Area checkpoints:        {sorted(observed_areas.keys())}")
        print(f"{'=' * 70}")

    # --- Phase 1: Snowline filter (faster, do first to cull early) ---
    if verbose:
        print(f"\n  Phase 1: Snowline filter ({n_total} param sets)...")

    snowline_passed_idx = []

    for i, params in enumerate(param_sets):
        # Reset geometry to original for each param set
        fmodel.update_geometry(grid['elevation'], grid['glacier_mask'])

        sl_score = score_snowline(fmodel, climate, grid, params, snowline_dir)
        sl_pass = (not np.isnan(sl_score['rmse_m'])
                   and sl_score['rmse_m'] <= snowline_rmse_max)

        score_entry = {
            'param_index': i,
            'snowline_rmse_m': sl_score['rmse_m'],
            'snowline_mae_m': sl_score['mae_m'],
            'snowline_bias_m': sl_score['mean_bias_m'],
            'snowline_n_years': sl_score['n_years'],
            'snowline_passed': sl_pass,
            'area_rmse_km2': np.nan,
            'area_mae_km2': np.nan,
            'area_bias_km2': np.nan,
            'area_n_checkpoints': 0,
            'area_passed': False,
            'passed_both': False,
        }
        all_scores.append(score_entry)

        if sl_pass:
            snowline_passed_idx.append(i)

        if verbose and ((i + 1) % max(1, n_total // 10) == 0 or i == 0):
            status = "PASS" if sl_pass else "FAIL"
            print(f"    [{i+1}/{n_total}] snowline RMSE={sl_score['rmse_m']:.0f}m "
                  f"bias={sl_score['mean_bias_m']:+.0f}m → {status}")

    n_sl_pass = len(snowline_passed_idx)
    if verbose:
        print(f"\n  Snowline filter: {n_sl_pass}/{n_total} passed "
              f"({100 * n_sl_pass / max(n_total, 1):.0f}%)")

    # --- Phase 2: Area filter (only on snowline survivors) ---
    if verbose:
        print(f"\n  Phase 2: Area evolution filter ({n_sl_pass} param sets)...")

    for count, i in enumerate(snowline_passed_idx):
        params = param_sets[i]

        # Reset geometry for each run
        fmodel.update_geometry(grid['elevation'], grid['glacier_mask'])

        area_score = score_area_evolution(
            fmodel, climate, grid, params, observed_areas,
            ice_thickness_init, bedrock, wy_start=wy_start,
        )

        area_pass = (not np.isnan(area_score['rmse_km2'])
                     and area_score['rmse_km2'] <= area_rmse_max)

        all_scores[i]['area_rmse_km2'] = area_score['rmse_km2']
        all_scores[i]['area_mae_km2'] = area_score['mae_km2']
        all_scores[i]['area_bias_km2'] = area_score['mean_bias_km2']
        all_scores[i]['area_n_checkpoints'] = area_score['n_checkpoints']
        all_scores[i]['area_passed'] = area_pass
        all_scores[i]['passed_both'] = area_pass  # already passed snowline

        if area_pass:
            survivors.append(params)
            survivor_indices.append(i)

        if verbose and ((count + 1) % max(1, n_sl_pass // 10) == 0 or count == 0):
            status = "PASS" if area_pass else "FAIL"
            print(f"    [{count+1}/{n_sl_pass}] param {i}: "
                  f"area RMSE={area_score['rmse_km2']:.2f} km² "
                  f"bias={area_score['mean_bias_km2']:+.2f} km² → {status}")

    elapsed = time.time() - t_start
    n_survived = len(survivors)

    summary = {
        'n_candidates': n_total,
        'n_passed_snowline': n_sl_pass,
        'n_passed_area': n_survived,
        'n_survivors': n_survived,
        'survival_rate': n_survived / max(n_total, 1),
        'snowline_rmse_threshold_m': snowline_rmse_max,
        'area_rmse_threshold_km2': area_rmse_max,
        'elapsed_seconds': elapsed,
        'snowline_rmse_distribution': {
            'min': float(np.nanmin([s['snowline_rmse_m'] for s in all_scores])),
            'median': float(np.nanmedian([s['snowline_rmse_m'] for s in all_scores])),
            'max': float(np.nanmax([s['snowline_rmse_m'] for s in all_scores])),
        },
    }

    if n_sl_pass > 0:
        area_rmses = [all_scores[i]['area_rmse_km2'] for i in snowline_passed_idx
                      if not np.isnan(all_scores[i]['area_rmse_km2'])]
        if area_rmses:
            summary['area_rmse_distribution'] = {
                'min': float(np.min(area_rmses)),
                'median': float(np.median(area_rmses)),
                'max': float(np.max(area_rmses)),
            }

    if verbose:
        print(f"\n  Area filter: {n_survived}/{n_sl_pass} passed")
        print(f"\n{'=' * 70}")
        print(f"BEHAVIORAL FILTER RESULT")
        print(f"  {n_total} candidates → {n_sl_pass} passed snowline "
              f"→ {n_survived} passed area")
        print(f"  Survival rate: {100 * summary['survival_rate']:.1f}%")
        print(f"  Elapsed: {elapsed:.0f}s "
              f"({elapsed / max(n_total, 1):.1f}s per candidate)")
        print(f"{'=' * 70}")

    return {
        'survivors': survivors,
        'survivor_indices': survivor_indices,
        'all_scores': all_scores,
        'summary': summary,
    }
