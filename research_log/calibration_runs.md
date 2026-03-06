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
**ABORTED** at step 66 / 120 (eval ~7050, cost 15.87).

Same pathology as CAL-001: MF≈1.0 (bound), precip_corr≈6.0 (bound), lapse_rate≈-3.5 (bound).
SWE initialization was not the root cause. Root cause identified as temperature
reference elevation mismatch — see D-006.

### Output files
- `calibration_output/calibration_v2_stdout.log` (partial)
- No v2 JSON outputs (killed before completion)

---

## Run CAL-003: v3 Calibration (station_elev fix)

**Date:** 2026-03-06
**Script:** `run_calibration_full.py` (current, v3)
**Status:** RUNNING

### Fixes applied (cumulative)
1. (D-005) SWE=0 for Oct 1 starts, observed SWE for summer starts
2. (D-005) snow_redist removed
3. (D-006) station_elev corrected from 1230m → 804m to match merged climate data

### Configuration
Same DE settings as CAL-002 (120 maxiter, 15 popsize, 7 params).
Bounds unchanged — the temperature fix should allow parameters to find
physically reasonable values within existing bounds.

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
| Metric | Value |
|--------|-------|
| Final cost | 17.508 |
| Convergence | NO (hit maxiter) |
| Total evaluations | 13,737 |
| Wall time | 3,544 s (59.1 min) |

| Parameter | Best | At bound? |
|-----------|------|-----------|
| MF (mm/d/K) | 1.631 | Near lower |
| r_snow | 0.000026 | YES (lower) |
| r_ice | 0.00299 | YES (upper) |
| lapse_rate (°C/m) | -0.00350 | YES (upper) |
| precip_grad (frac/m) | 0.00598 | YES (upper) |
| precip_corr | 2.446 | No — mid-range |
| T0 (°C) | 0.502 | YES (lower) |

### Validation
| Target | Modeled | Observed | Residual |
|--------|---------|----------|----------|
| ABL 2023 annual | -4.07 | -4.50 | +0.43 |
| ABL 2024 annual | -1.67 | -2.63 | +0.96 |
| ELA 2023 annual | -1.55 | +0.10 | -1.65 |
| ELA 2024 annual | +0.36 | +0.10 | +0.26 |
| ACC 2023 annual | +0.66 | +0.37 | +0.29 |
| ACC 2024 annual | +2.33 | +1.46 | +0.87 |
| Geodetic 2000-2010 | -0.53 | -1.07 | +0.54 |
| Geodetic 2010-2020 | -1.62 | -0.81 | -0.82 |
| Geodetic 2000-2020 | -1.07 | -0.94 | -0.14 |

### Assessment
**IMPROVED but still problematic.** precip_corr moved off bounds (2.45, mid-range)
confirming D-006 fix was correct. But 4/7 params still at bounds:
- lapse_rate at -3.5°C/km (upper bound) — unrealistically shallow
- r_snow ≈ 0 and r_ice at max — extreme snow/ice melt contrast
- T0 = 0.5°C (lower) and precip_grad = 0.006 (upper) — maximizing snow
- ELA residuals large — model can't simultaneously fit ABL melt and ELA accumulation
- Geodetic decades flip-flopped: under-melts 2000-2010, over-melts 2010-2020

Root issue likely: model needs a way to differentiate elevation-dependent melt
beyond a single lapse rate. Or the climate data has non-stationarity issues.

### Output files
- `calibration_output/best_params_v3.json`
- `calibration_output/calibration_log_v3.csv`
- `calibration_output/calibration_summary_v3.json`
- `calibration_output/calibration_v3_stdout.log`

---

## Run CAL-004: v4 Calibration (statistical temp transfer + MF_grad)

**Date:** 2026-03-06
**Script:** `run_calibration_full.py` (v4)
**Status:** RUNNING

### Changes from CAL-003
1. (D-007) Statistical temperature transfer from raw Nuka SNOTEL
2. (D-008) Elevation-dependent melt factor (MF_grad parameter)
3. (D-009) Complete model architecture overhaul
4. Input is raw Nuka temperature at 1230m (not pre-adjusted)
5. internal_lapse replaces lapse_rate (on-glacier vertical gradient)

### Configuration
| Setting | Value |
|---------|-------|
| Grid resolution | 100 m |
| Method | differential_evolution |
| Population size | 15 per param (120 total) |
| Max iterations | 150 |
| Eval time | ~584 ms |
| Est. total time | ~176 min |

### Parameters (8)
| Parameter | Lower | Upper | Role |
|-----------|-------|-------|------|
| MF (mm/d/K) | 1.0 | 12.0 | Base melt factor |
| MF_grad (mm/d/K/m) | -0.01 | 0.0 | Melt factor elevation gradient |
| r_snow | 0.02e-3 | 1.5e-3 | Radiation factor (snow) |
| r_ice | 0.05e-3 | 3.0e-3 | Radiation factor (ice) |
| internal_lapse (C/m) | -8.0e-3 | -3.0e-3 | On-glacier lapse rate |
| precip_grad (frac/m) | 0.0002 | 0.006 | Precipitation gradient |
| precip_corr | 0.5 | 5.0 | Precipitation correction |
| T0 (C) | 0.5 | 3.0 | Rain/snow threshold |

### Results
| Metric | Value |
|--------|-------|
| Final cost | 17.823 |
| Convergence | NO (hit maxiter=80) |
| Total evaluations | 9,909 |
| Wall time | 3,545 s (59.1 min) |

| Parameter | Best | At bound? |
|-----------|------|-----------|
| MF (mm/d/K) | 4.123 | No |
| MF_grad (per m) | -0.00999 | YES (lower) |
| r_snow | 0.001496 | YES (upper) |
| r_ice | 0.001501 | Near r_snow |
| internal_lapse (°C/m) | -0.00798 | YES (lower) |
| precip_grad | 0.000383 | No |
| precip_corr | 0.505 | YES (lower) |
| T0 (°C) | 0.519 | YES (lower) |

### Validation
| Target | Modeled | Observed | Residual |
|--------|---------|----------|----------|
| ABL 2023 annual | -3.58 | -4.50 | +0.92 |
| ABL 2024 annual | -3.91 | -2.63 | -1.28 |
| ELA 2023 annual | -0.12 | +0.10 | -0.22 |
| ELA 2024 annual | -0.34 | +0.10 | -0.44 |
| ACC 2023 annual | +0.74 | +0.37 | +0.37 |
| ACC 2024 annual | +0.59 | +1.46 | -0.87 |
| Geodetic 2000-2010 | -0.68 | -1.07 | +0.40 |
| Geodetic 2010-2020 | -1.08 | -0.81 | -0.27 |
| Geodetic 2000-2020 | -0.88 | -0.94 | +0.06 |

### Assessment
**MAJOR PROGRESS on MF and geodetic fit.** MF=4.1 is literature-reasonable.
Geodetic 2000-2020 modeled (-0.88) closely matches observed (-0.94).
Statistical temperature transfer (D-007) is working.

**Remaining problems:**
- 4/8 params at bounds (MF_grad, internal_lapse, precip_corr, T0)
- precip_corr=0.5 → model wants LESS precip than Nuka (unusual)
- r_snow ≈ r_ice → no snow/ice melt contrast
- Year-to-year residuals are large and flip sign (ABL: +0.92 in 2023, -1.28 in 2024)
- ELA/ACC systematically too negative in 2024-2025

**Root issue:** The model improves glacier-wide and long-term fit but can't capture
interannual variability. The winter temperature transfer (standard lapse for Oct-Apr)
may be a major error source — winter accumulation drives year-to-year differences.

### Output files
- `calibration_output/best_params_v4.json`
- `calibration_output/calibration_log_v4.csv`
- `calibration_output/calibration_summary_v4.json`
- `calibration_output/calibration_v4_stdout.log`
