# Calibration Run Registry — Dixon Glacier DETIM

Every calibration run is logged here with full configuration, results, and assessment.
This is the authoritative record for reproducibility.

---

## Run CAL-001: Initial Full Calibration (v1)

**Date:** 2026-03-05
**Script:** `run_calibration_full_v1.py` (archived copy)
**Status:** COMPLETED

### Configuration
| Setting | Value |
|---------|-------|
| Grid resolution | 100 m |
| Method | scipy.optimize.differential_evolution |
| Population size | 15 per param (120 total) |
| Max iterations | 80 |
| Tolerance | 1e-4 |
| Mutation | (0.5, 1.0) |
| Recombination | 0.7 |
| Seed | 42 |
| Init | Latin hypercube |

### Parameters (8)
| Parameter | Lower | Upper | Best | At bound? |
|-----------|-------|-------|------|-----------|
| MF (mm/d/K) | 1.0 | 12.0 | 1.001 | YES (lower) |
| r_snow (mm m² W⁻¹ d⁻¹ K⁻¹) | 0.02e-3 | 1.5e-3 | 0.00002 | YES (lower) |
| r_ice | 0.05e-3 | 3.0e-3 | 0.003 | YES (upper) |
| lapse_rate (°C/m) | -8.5e-3 | -3.5e-3 | -4.51e-3 | no |
| precip_grad (frac/m) | 0.0002 | 0.006 | 0.00247 | no |
| precip_corr | 1.0 | 4.0 | 3.998 | YES (upper) |
| T0 (°C) | 0.5 | 3.0 | 3.000 | YES (upper) |
| snow_redist | 0.5 | 2.5 | 2.494 | YES (upper) |

### Results
| Metric | Value |
|--------|-------|
| Final cost | 15.016 |
| Convergence | NO (hit maxiter) |
| Total evaluations | 10,368 |
| Wall time | 3,158 s (52.6 min) |

### Objective weights
| Component | Weight |
|-----------|--------|
| w_stake_annual | 1.0 |
| w_stake_summer | 0.6 |
| w_geodetic | 0.4 |
| w_physics | 0.3 |

### Assessment
**FAILED** — 5 of 8 parameters at bounds. Cost of 15 indicates model cannot fit
observations. Root cause identified: winter SWE double-counting in annual runs
(initial SWE pre-loaded + daily precip accumulation). See Decision D-005.

### Output files
- `calibration_output/best_params.json`
- `calibration_output/calibration_log.csv` (10,368 rows)
- `calibration_output/calibration_summary.json`

---

## Run CAL-002: v2 Calibration (SWE fix + param reduction)

**Date:** 2026-03-06
**Script:** `run_calibration_full.py` (current)
**Status:** RUNNING

### Fixes applied (see D-005)
1. Annual/geodetic runs: winter_swe=0 at Oct 1 start
2. Summer runs: observed winter balance as initial SWE
3. snow_redist removed (redundant with precip_corr)

### Configuration
| Setting | Value |
|---------|-------|
| Grid resolution | 100 m |
| Method | differential_evolution |
| Population size | 15 per param (105 total) |
| Max iterations | 120 |
| Tolerance | 1e-4 |
| Mutation | (0.5, 1.0) |
| Recombination | 0.7 |
| Seed | 42 |

### Parameters (7)
| Parameter | Lower | Upper |
|-----------|-------|-------|
| MF (mm/d/K) | 1.0 | 12.0 |
| r_snow (mm m² W⁻¹ d⁻¹ K⁻¹) | 0.02e-3 | 1.5e-3 |
| r_ice | 0.05e-3 | 3.0e-3 |
| lapse_rate (°C/m) | -8.5e-3 | -3.5e-3 |
| precip_grad (frac/m) | 0.0002 | 0.006 |
| precip_corr | 1.0 | 6.0 |
| T0 (°C) | 0.5 | 3.0 |

### Results
*Pending — run in progress*

### Output files (expected)
- `calibration_output/best_params_v2.json`
- `calibration_output/calibration_log_v2.csv`
- `calibration_output/calibration_summary_v2.json`
