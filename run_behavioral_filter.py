"""
Run multi-criteria behavioral filtering on MCMC posterior parameter sets.

Screens the top N parameter sets from the MCMC chain against:
  1. Observed snowline elevations (22 years, 1999-2024)
  2. Observed glacier area evolution (digitized outlines at ~5-yr intervals)

Survivors are saved for use in run_projection.py.

Usage:
    # Default: top 500 from chain, thresholds 150m snowline / 1.5 km² area
    python run_behavioral_filter.py

    # Custom thresholds
    python run_behavioral_filter.py --n-candidates 500 \
        --snowline-rmse 120 --area-rmse 1.0

    # Then project with filtered params:
    python run_projection.py --filtered-params calibration_output/filtered_params.json

Output:
    calibration_output/filtered_params.json — surviving parameter sets
    calibration_output/behavioral_filter_scores.csv — all scores
    calibration_output/behavioral_filter_summary.json — filter statistics
"""
import numpy as np
import pandas as pd
from pathlib import Path
import json
import time

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
DEM_PATH = PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif'
GLACIER_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
CLIMATE_PATH = PROJECT / 'data' / 'climate' / 'dixon_gap_filled_climate.csv'
SNOWLINE_DIR = PROJECT / 'snowlines_all'
OUTLINE_JSON = PROJECT / 'data' / 'glacier_outlines' / 'digitized_outline_summary.json'
FARINOTTI_PATH = PROJECT / 'data' / 'ice_thickness' / 'RGI60-01.18059_thickness.tif'
OUTPUT_DIR = PROJECT / 'calibration_output'

# Default filter thresholds
DEFAULT_N_CANDIDATES = 500
DEFAULT_SNOWLINE_RMSE = 150.0   # m
DEFAULT_AREA_RMSE = 1.5         # km²
DEFAULT_GRID_RES = 100.0        # m (same as projection)


def main(n_candidates=DEFAULT_N_CANDIDATES,
         snowline_rmse_max=DEFAULT_SNOWLINE_RMSE,
         area_rmse_max=DEFAULT_AREA_RMSE,
         grid_res=DEFAULT_GRID_RES):

    from run_projection import load_top_param_sets
    from dixon_melt.terrain import prepare_grid
    from dixon_melt.model import precompute_ipot
    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config
    from dixon_melt.climate import load_gap_filled_climate
    from dixon_melt.glacier_dynamics import initialize_ice_thickness, compute_bedrock
    from dixon_melt.behavioral_filter import (
        run_behavioral_filter, load_observed_areas,
    )

    t_start = time.time()
    print("=" * 70)
    print("BEHAVIORAL FILTER — Dixon Glacier DETIM")
    print(f"  Candidates:      top {n_candidates} from MCMC chain")
    print(f"  Snowline RMSE:   ≤ {snowline_rmse_max:.0f} m")
    print(f"  Area RMSE:       ≤ {area_rmse_max:.1f} km²")
    print(f"  Grid resolution: {grid_res:.0f} m")
    print("=" * 70)

    # ── Load parameter candidates ──────────────────────────────────
    print("\n  Loading MCMC posterior...")
    param_sets = load_top_param_sets(n_top=n_candidates)
    print(f"  Loaded {len(param_sets)} candidate parameter sets")

    # ── Prepare grid and model ─────────────────────────────────────
    print("\n  Preparing grid...")
    grid = prepare_grid(str(DEM_PATH), str(GLACIER_PATH), target_res=grid_res)

    print("  Precomputing I_pot...")
    ipot_table = precompute_ipot(grid, doy_range=range(1, 366), dt_hours=3.0)

    fmodel = FastDETIM(
        grid, ipot_table,
        transfer_alpha=config.TRANSFER_ALPHA,
        transfer_beta=config.TRANSFER_BETA,
        ref_elev=config.SNOTEL_ELEV,
        stake_names=config.STAKE_NAMES,
        stake_elevs=config.STAKE_ELEVS,
    )

    # ── Initialize ice thickness ───────────────────────────────────
    farinotti = str(FARINOTTI_PATH) if FARINOTTI_PATH.exists() else None
    ice_thickness, thickness_source = initialize_ice_thickness(
        grid, farinotti_path=farinotti)
    bedrock = compute_bedrock(grid['elevation'], ice_thickness)
    print(f"  Ice thickness: {thickness_source}")

    # ── Load climate ───────────────────────────────────────────────
    print("  Loading gap-filled climate (D-025)...")
    climate = load_gap_filled_climate(str(CLIMATE_PATH))
    climate = climate[['temperature', 'precipitation']]

    # ── Load observed areas ────────────────────────────────────────
    observed_areas = load_observed_areas(str(OUTLINE_JSON))
    print(f"  Observed area checkpoints: {observed_areas}")

    # ── Run the filter ─────────────────────────────────────────────
    result = run_behavioral_filter(
        param_sets=param_sets,
        fmodel=fmodel,
        climate=climate,
        grid=grid,
        snowline_dir=str(SNOWLINE_DIR),
        observed_areas=observed_areas,
        ice_thickness_init=ice_thickness,
        bedrock=bedrock,
        snowline_rmse_max=snowline_rmse_max,
        area_rmse_max=area_rmse_max,
        wy_start=min(observed_areas.keys()),
        verbose=True,
    )

    survivors = result['survivors']
    summary = result['summary']
    all_scores = result['all_scores']

    # ── Save results ───────────────────────────────────────────────
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 1. Filtered parameter sets (for run_projection.py)
    filtered_path = OUTPUT_DIR / 'filtered_params.json'
    filtered_data = {
        'n_survivors': len(survivors),
        'filter_config': {
            'n_candidates': n_candidates,
            'snowline_rmse_threshold_m': snowline_rmse_max,
            'area_rmse_threshold_km2': area_rmse_max,
            'area_checkpoints': observed_areas,
        },
        'param_sets': survivors,
    }
    with open(filtered_path, 'w') as f:
        json.dump(filtered_data, f, indent=2)
    print(f"\n  Filtered params saved: {filtered_path.name} "
          f"({len(survivors)} sets)")

    # 2. Full scores table
    scores_path = OUTPUT_DIR / 'behavioral_filter_scores.csv'
    scores_df = pd.DataFrame(all_scores)
    # Add parameter values for analysis
    for i, params in enumerate(param_sets):
        for key in ['MF', 'r_snow', 'r_ice', 'MF_grad', 'precip_corr',
                     'precip_grad', 'T0', 'internal_lapse']:
            if key in params:
                scores_df.loc[i, key] = params[key]
    scores_df.to_csv(scores_path, index=False)
    print(f"  Scores saved: {scores_path.name}")

    # 3. Summary JSON
    summary_path = OUTPUT_DIR / 'behavioral_filter_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"  Summary saved: {summary_path.name}")

    elapsed = time.time() - t_start
    print(f"\n  Total elapsed: {elapsed / 60:.1f} min")

    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Run behavioral filter on MCMC posterior')
    parser.add_argument('--n-candidates', type=int, default=DEFAULT_N_CANDIDATES,
                        help=f'Number of top MCMC samples to screen '
                             f'(default: {DEFAULT_N_CANDIDATES})')
    parser.add_argument('--snowline-rmse', type=float, default=DEFAULT_SNOWLINE_RMSE,
                        help=f'Max snowline RMSE to pass, in meters '
                             f'(default: {DEFAULT_SNOWLINE_RMSE})')
    parser.add_argument('--area-rmse', type=float, default=DEFAULT_AREA_RMSE,
                        help=f'Max area RMSE to pass, in km² '
                             f'(default: {DEFAULT_AREA_RMSE})')
    parser.add_argument('--grid-res', type=float, default=DEFAULT_GRID_RES,
                        help=f'Model grid resolution in meters '
                             f'(default: {DEFAULT_GRID_RES})')
    args = parser.parse_args()

    main(
        n_candidates=args.n_candidates,
        snowline_rmse_max=args.snowline_rmse,
        area_rmse_max=args.area_rmse,
        grid_res=args.grid_res,
    )
