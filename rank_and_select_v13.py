"""
Rank v13 posterior by snowline RMSE + area RMSE, select top 250.

Computes snowline RMSE for each of the 1000 filtered param sets,
combines with already-computed area RMSE, and saves the top 250
for projection.
"""
import sys, os
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True)

import numpy as np
import pandas as pd
from pathlib import Path
import json
import time

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
OUTPUT_DIR = PROJECT / 'calibration_output'
N_SELECT = 250

def main():
    t_start = time.time()

    # Load filtered params and area scores
    with open(OUTPUT_DIR / 'filtered_params_v13.json') as f:
        filtered = json.load(f)
    param_sets = filtered['param_sets']
    n_total = len(param_sets)

    area_df = pd.read_csv(OUTPUT_DIR / 'area_filter_v13_scores.csv')
    print(f"Loaded {n_total} param sets, {len(area_df)} area scores")

    # Set up model for snowline scoring
    from dixon_melt.terrain import prepare_grid
    from dixon_melt.model import precompute_ipot
    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config
    from dixon_melt.climate import load_gap_filled_climate
    from dixon_melt.behavioral_filter import score_snowline

    DEM_PATH = PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif'
    GLACIER_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
    CLIMATE_PATH = PROJECT / 'data' / 'climate' / 'dixon_gap_filled_climate.csv'
    SNOWLINE_DIR = PROJECT / 'snowlines_all'

    print("Preparing model...")
    grid = prepare_grid(str(DEM_PATH), str(GLACIER_PATH), target_res=100.0)
    ipot = precompute_ipot(grid, doy_range=range(1, 366), dt_hours=3.0)
    fmodel = FastDETIM(
        grid, ipot,
        transfer_alpha=config.TRANSFER_ALPHA,
        transfer_beta=config.TRANSFER_BETA,
        ref_elev=config.SNOTEL_ELEV,
        stake_names=config.STAKE_NAMES,
        stake_elevs=config.STAKE_ELEVS,
    )
    climate = load_gap_filled_climate(str(CLIMATE_PATH))
    climate = climate[['temperature', 'precipitation']]

    # JIT warm-up
    print("JIT warm-up...")
    fmodel.update_geometry(grid['elevation'], grid['glacier_mask'])
    _ = score_snowline(fmodel, climate, grid, param_sets[0], str(SNOWLINE_DIR))

    # Score snowlines for all 1000 param sets
    print(f"\nScoring snowlines for {n_total} param sets...")
    snowline_rmses = []
    t_score = time.time()

    for i, params in enumerate(param_sets):
        fmodel.update_geometry(grid['elevation'], grid['glacier_mask'])
        sl = score_snowline(fmodel, climate, grid, params, str(SNOWLINE_DIR))
        rmse = sl['rmse_m'] if not np.isnan(sl['rmse_m']) else 999.0
        snowline_rmses.append(rmse)

        if (i + 1) % 100 == 0 or i == 0:
            elapsed = time.time() - t_score
            rate = (i + 1) / elapsed
            eta = (n_total - i - 1) / rate
            print(f"  [{i+1:4d}/{n_total}] RMSE={rmse:.1f}m  ({rate:.1f}/s, ETA {eta/60:.1f}min)")

    snowline_rmses = np.array(snowline_rmses)
    area_rmses = area_df['area_rmse_km2'].values

    print(f"\nSnowline RMSE: min={snowline_rmses.min():.1f}, "
          f"median={np.median(snowline_rmses):.1f}, max={snowline_rmses.max():.1f}")
    print(f"Area RMSE:     min={area_rmses.min():.3f}, "
          f"median={np.median(area_rmses):.3f}, max={area_rmses.max():.3f}")

    # Normalize both to [0,1] so they contribute equally, then sum
    sl_min, sl_max = snowline_rmses.min(), snowline_rmses.max()
    ar_min, ar_max = area_rmses.min(), area_rmses.max()

    if sl_max > sl_min:
        sl_norm = (snowline_rmses - sl_min) / (sl_max - sl_min)
    else:
        sl_norm = np.zeros_like(snowline_rmses)

    if ar_max > ar_min:
        ar_norm = (area_rmses - ar_min) / (ar_max - ar_min)
    else:
        ar_norm = np.zeros_like(area_rmses)

    composite = sl_norm + ar_norm

    # Rank and select top N
    ranked_idx = np.argsort(composite)
    top_idx = ranked_idx[:N_SELECT]

    print(f"\nTop {N_SELECT} composite scores: "
          f"{composite[top_idx[0]]:.4f} to {composite[top_idx[-1]]:.4f}")
    print(f"Top {N_SELECT} snowline RMSE: "
          f"{snowline_rmses[top_idx].min():.1f} to {snowline_rmses[top_idx].max():.1f} m")
    print(f"Top {N_SELECT} area RMSE: "
          f"{area_rmses[top_idx].min():.3f} to {area_rmses[top_idx].max():.3f} km²")

    # Build output
    top_params = [param_sets[i] for i in top_idx]

    # Save ranked params (same format as filtered_params for run_projection.py)
    ranked_data = {
        'n_survivors': N_SELECT,
        'filter_config': {
            'source': 'CAL-013 (v13 multi-objective MCMC)',
            'method': 'ranked by normalized snowline_RMSE + area_RMSE, top 250',
            'n_candidates': n_total,
            'snowline_rmse_range_m': [float(snowline_rmses[top_idx].min()),
                                       float(snowline_rmses[top_idx].max())],
            'area_rmse_range_km2': [float(area_rmses[top_idx].min()),
                                     float(area_rmses[top_idx].max())],
        },
        'param_sets': top_params,
    }

    out_path = OUTPUT_DIR / 'ranked_params_v13_top250.json'
    with open(out_path, 'w') as f:
        json.dump(ranked_data, f, indent=2)
    print(f"\nSaved: {out_path.name}")

    # Also save full ranking table
    ranking_df = pd.DataFrame({
        'rank': range(n_total),
        'composite_score': composite[ranked_idx],
        'snowline_rmse_m': snowline_rmses[ranked_idx],
        'area_rmse_km2': area_rmses[ranked_idx],
        'log_prob': area_df['log_prob'].values[ranked_idx],
        'selected': [i < N_SELECT for i in range(n_total)],
    })
    for key in ['MF', 'MF_grad', 'r_snow', 'precip_grad', 'precip_corr', 'T0']:
        ranking_df[key] = [param_sets[ranked_idx[i]][key] for i in range(n_total)]

    rank_path = OUTPUT_DIR / 'ranking_v13_full.csv'
    ranking_df.to_csv(rank_path, index=False)
    print(f"Saved: {rank_path.name}")

    # Summary of selected params
    print(f"\nSelected top {N_SELECT} parameter summary:")
    for key in ['MF', 'MF_grad', 'r_snow', 'precip_grad', 'precip_corr', 'T0']:
        vals = [param_sets[i][key] for i in top_idx]
        print(f"  {key:12s}: median={np.median(vals):.4f}  "
              f"[{np.percentile(vals, 16):.4f}, {np.percentile(vals, 84):.4f}]")

    elapsed = time.time() - t_start
    print(f"\nDone in {elapsed/60:.1f} min")
    print(f"\nTo project:")
    print(f"  python run_projection.py --filtered-params {out_path}")


if __name__ == '__main__':
    main()
