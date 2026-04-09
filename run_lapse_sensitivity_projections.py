"""
Lapse rate sensitivity projections for Dixon Glacier DETIM.

Runs projections at three lapse rates (-4.5, -5.0, -5.5 °C/km) to bracket
the structural uncertainty from this fixed parameter choice. Uses the v13
posterior (50 param sets) × 5 GCMs × 2 SSPs.

The -5.0 baseline reproduces the standard projection; -4.5 and -5.5 span
the literature range for maritime Alaskan glaciers (Gardner & Sharp 2009,
Roth et al. 2023).

This is a scenario-based sensitivity analysis, not a recalibration — the
same posterior params are used at each lapse rate. The goal is to show
how the lapse rate choice affects projected glacier evolution.

References:
    Gardner & Sharp (2009) J. Glaciol. — -4.9 °C/km
    Roth et al. (2023) Juneau Icefield — -5.0 °C/km
    Schuster et al. (2023) Ann. Glaciol. — equifinality documentation
"""
import sys
import os
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout.reconfigure(line_buffering=True)

import json
import time
import copy
import numpy as np
from pathlib import Path

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
FILTERED_PARAMS_PATH = PROJECT / 'calibration_output' / 'filtered_params_v13.json'

# Lapse rates to test (°C/km → °C/m internally)
LAPSE_RATES_CKM = [-4.5, -5.0, -5.5]

# Use 250 param sets (matching baseline projections PROJ-009/011)
N_SAMPLES = 250

# SSP scenarios
SCENARIOS = ['ssp245', 'ssp585']


def load_and_subsample_params(n=N_SAMPLES, seed=42):
    """Load filtered params and subsample deterministically."""
    with open(FILTERED_PARAMS_PATH) as f:
        data = json.load(f)
    all_params = data['param_sets']
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(all_params), size=min(n, len(all_params)), replace=False)
    idx.sort()
    return [all_params[i] for i in idx]


def set_lapse_rate(param_sets, lapse_ckm):
    """Return a copy of param_sets with modified lapse rate."""
    lapse_cm = lapse_ckm / 1000.0  # °C/km → °C/m
    modified = []
    for p in param_sets:
        p2 = dict(p)
        p2['internal_lapse'] = lapse_cm
        if 'lapse_rate' in p2:
            p2['lapse_rate'] = lapse_cm
        modified.append(p2)
    return modified


def write_temp_params(param_sets, lapse_ckm):
    """Write param sets to a temp JSON file for the projection runner."""
    out_path = PROJECT / 'calibration_output' / f'_temp_lapse{lapse_ckm:.1f}_params.json'
    data = {
        'n_survivors': len(param_sets),
        'filter_config': {'note': f'lapse sensitivity {lapse_ckm} C/km'},
        'param_sets': param_sets,
    }
    with open(out_path, 'w') as f:
        json.dump(data, f)
    return out_path


def main():
    t_start = time.time()
    print("=" * 70)
    print("LAPSE RATE SENSITIVITY PROJECTIONS")
    print(f"Lapse rates: {LAPSE_RATES_CKM} °C/km")
    print(f"Scenarios: {SCENARIOS}")
    print(f"Param sets: {N_SAMPLES} (subsampled from v13 posterior)")
    print(f"Total projection runs: {len(LAPSE_RATES_CKM)} × {len(SCENARIOS)} "
          f"× {N_SAMPLES} params × 5 GCMs = "
          f"{len(LAPSE_RATES_CKM) * len(SCENARIOS) * N_SAMPLES * 5}")
    print("=" * 70)

    # Load and subsample params once
    base_params = load_and_subsample_params(N_SAMPLES)
    print(f"\nSubsampled {len(base_params)} param sets from posterior")

    from run_projection import run_projection, create_run_dir

    results_summary = []

    for lapse_ckm in LAPSE_RATES_CKM:
        # Modify lapse rate in all param sets
        modified_params = set_lapse_rate(base_params, lapse_ckm)
        temp_path = write_temp_params(modified_params, lapse_ckm)

        for scenario in SCENARIOS:
            label = f'lapse{lapse_ckm:.1f}_{scenario}'
            run_dir = create_run_dir(len(modified_params), [scenario], label=label)
            print(f"\n{'#' * 70}")
            print(f"# LAPSE = {lapse_ckm} °C/km, {scenario.upper()}")
            print(f"{'#' * 70}")

            result = run_projection(
                scenario=scenario,
                end_year=2100,
                grid_res=100.0,
                filtered_params_path=str(temp_path),
                output_dir=run_dir,
            )

            if result is not None:
                ens = result['ensemble_df']
                last = len(ens) - 1
                pw = result.get('peak_water', {})
                results_summary.append({
                    'lapse_rate_ckm': lapse_ckm,
                    'scenario': scenario,
                    'area_2100_p50': ens.loc[last, 'area_km2_p50'],
                    'area_2100_p05': ens.loc[last, 'area_km2_p05'],
                    'area_2100_p95': ens.loc[last, 'area_km2_p95'],
                    'volume_2100_p50': ens.loc[last, 'volume_km3_p50'],
                    'peak_water_year': pw.get('peak_year', None),
                    'peak_discharge_m3s': pw.get('peak_discharge_m3s', None),
                    'output_dir': str(result['output_dir']),
                })

        # Clean up temp file
        temp_path.unlink(missing_ok=True)

    # ── Cross-lapse comparison ────────────────────────────────────────
    elapsed = time.time() - t_start
    print(f"\n{'=' * 70}")
    print(f"LAPSE RATE SENSITIVITY — SUMMARY ({elapsed/3600:.1f} hours)")
    print(f"{'=' * 70}")

    print(f"\n  {'Lapse':>8s}  {'SSP':>6s}  {'Area 2100 (km²)':>20s}  "
          f"{'Peak Water':>12s}  {'Peak Q (m³/s)':>14s}")
    print(f"  {'-'*8}  {'-'*6}  {'-'*20}  {'-'*12}  {'-'*14}")

    for r in results_summary:
        area_str = (f"{r['area_2100_p50']:.1f} "
                    f"[{r['area_2100_p05']:.1f}-{r['area_2100_p95']:.1f}]")
        pw_str = f"WY{r['peak_water_year']}" if r['peak_water_year'] else "N/A"
        pq_str = f"{r['peak_discharge_m3s']:.2f}" if r['peak_discharge_m3s'] else "N/A"
        print(f"  {r['lapse_rate_ckm']:>+6.1f}    {r['scenario']:>6s}  "
              f"{area_str:>20s}  {pw_str:>12s}  {pq_str:>14s}")

    # Save summary
    import pandas as pd
    summary_path = PROJECT / 'validation_output' / 'lapse_sensitivity_projections.csv'
    pd.DataFrame(results_summary).to_csv(summary_path, index=False)
    print(f"\n  Summary saved: {summary_path}")
    print(f"  Individual runs in projection_output/PROJ-*_lapse*")


if __name__ == '__main__':
    main()
