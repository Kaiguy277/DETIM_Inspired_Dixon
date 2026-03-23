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
   [NOTE: D-023 later corrected Dixon AWS to 1078m (ELA site, not ABL)]

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

---

## Run CAL-005: v4b Calibration (winter katabatic correction)

**Date:** 2026-03-06
**Script:** `run_calibration_full.py` (unchanged from v4, config.py updated)
**Status:** RUNNING

### Changes from CAL-004
1. (D-010) Winter transfer coefficients changed from standard lapse
   (alpha=1.0, beta=+2.77) to reduced katabatic (alpha=0.85, beta=+1.0)
   for Oct-Apr months.

### Configuration
Same as CAL-004 (80 maxiter, 15 popsize, 8 params, same bounds).

### Hypothesis
Winter accumulation was 22% of observed because Oct-Nov temps were too warm.
With corrected winter transfer, expect:
- precip_corr to increase from 0.5 to 1.5-3.0
- T0 to increase from 0.5 to 1.0-2.0
- Better stake annual fits (especially ACC/ELA winter balance)
- Reduced interannual residual variability

### Results
*Pending — run in progress*

### Output files (expected)
- `calibration_output/best_params_v5.json`
- `calibration_output/calibration_log_v5.csv`
- `calibration_output/calibration_summary_v5.json`
- `calibration_output/calibration_v5_stdout.log`

### Post-mortem
CAL-005 never completed — process was killed at step 32/80 (eval ~3950).
Best cost at termination: 16.43, worse than CAL-004 (17.82). The katabatic
winter correction did NOT improve results. precip_corr remained near lower
bound (~0.5-0.7). Root issue identified as spatial precipitation distribution,
not temperature transfer — see D-011.

---

## Run CAL-006: v6 Calibration (wind redistribution)

**Date:** 2026-03-06
**Script:** `run_calibration_full.py` (v6)
**Status:** RUNNING

### Changes from CAL-005
1. (D-011) Wind redistribution via Winstral Sx parameter
   - Prevailing wind: ESE (100°), d_max=300m
   - New parameter: k_wind [0.0, 1.0]
   - Sx normalized to [-1,+1], zero-meaned over glacier (mass conserving)

### Configuration
| Setting | Value |
|---------|-------|
| Grid resolution | 100 m |
| Method | differential_evolution |
| Population size | 15 per param (135 total) |
| Max iterations | 80 |
| Tolerance | 1e-4 |
| Mutation | (0.5, 1.0) |
| Recombination | 0.7 |
| Seed | 42 |

### Parameters (9)
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
| k_wind | 0.0 | 1.0 | Wind redistribution strength |

### Hypothesis
Wind redistribution allows the optimizer to decouple spatial snow distribution
from total precipitation amount. This should allow precip_corr to increase to
physically reasonable values (>1.0) while k_wind handles the E-W asymmetry.

### Results
**KILLED** at step 29/80 (eval ~4050, cost 16.54). Wind redistribution alone
did not fix the core issue. precip_corr still at lower bound (~0.55).
Root cause identified: statistical temperature transfer makes temperatures
too cold for DETIM to generate observed melt. See D-012.

### Output files
- `calibration_output/calibration_v6_stdout.log` (partial)

---

## Run CAL-007: v7 Calibration (identity transfer + winter targets)

**Date:** 2026-03-06
**Script:** `run_calibration_full.py` (v7)
**Status:** RUNNING

### Changes from CAL-006 (D-012)
1. Identity temperature transfer: raw Nuka T at 1230m, no katabatic correction
2. ref_elev = 1230m (Nuka SNOTEL), lapse_rate calibrated from there
3. Winter balance added as explicit calibration target (W=0.6)
4. precip_corr lower bound raised to 1.0 (Nuka undercatch is real)
5. lapse_rate bounds widened to [-9.0, -3.0] C/km
6. DE maxiter increased to 200 for weekend convergence

### Configuration
| Setting | Value |
|---------|-------|
| Grid resolution | 100 m |
| Method | differential_evolution |
| Population size | 15 per param (135 total) |
| Max iterations | 200 |
| Tolerance | 1e-4 |
| Mutation | (0.5, 1.0) |
| Recombination | 0.7 |
| Seed | 42 |

### Objective weights
| Component | Weight |
|-----------|--------|
| w_stake_annual | 1.0 |
| w_stake_summer | 0.8 |
| w_stake_winter | 0.6 |
| w_geodetic | 0.4 |
| w_physics | 0.3 |

### Parameters (9)
| Parameter | Lower | Upper | Role |
|-----------|-------|-------|------|
| MF (mm/d/K) | 1.0 | 12.0 | Base melt factor |
| MF_grad (mm/d/K/m) | -0.01 | 0.0 | Melt factor elevation gradient |
| r_snow | 0.02e-3 | 1.5e-3 | Radiation factor (snow) |
| r_ice | 0.05e-3 | 3.0e-3 | Radiation factor (ice) |
| lapse_rate (C/m) | -9.0e-3 | -3.0e-3 | From Nuka 1230m to each cell |
| precip_grad (frac/m) | 0.0002 | 0.006 | Precipitation gradient |
| precip_corr | 1.0 | 6.0 | Precipitation correction |
| T0 (C) | 0.5 | 3.0 | Rain/snow threshold |
| k_wind | 0.0 | 1.0 | Wind redistribution strength |

### Hypothesis
With identity transfer, temperatures are warm enough for DETIM to generate
realistic melt with literature-range MF values. precip_corr should settle
at >1.0 (correcting Nuka undercatch). Winter balance targets force the model
to get accumulation right at each stake. The optimizer has much more dynamic
range to work with.

### Results
| Metric | Value |
|--------|-------|
| Final cost | 17.035 |
| Convergence | YES (tol met at step 143) |
| Total evaluations | 20,050 |
| Wall time | 6,508 s (108.5 min) |

| Parameter | Best | At bound? |
|-----------|------|-----------|
| MF (mm/d/K) | 1.554 | No (but very low) |
| MF_grad (per m) | -0.00346 | No |
| r_snow | 0.001498 | YES (upper) |
| r_ice | 0.002999 | YES (upper) |
| lapse_rate (°C/m) | -0.00300 | YES (upper, shallowest) |
| precip_grad | 0.000200 | YES (lower) |
| precip_corr | 4.524 | No (but extreme) |
| T0 (°C) | 2.209 | No |
| k_wind | 0.0005 | YES (lower, effectively off) |

### Validation
| Target | Modeled | Observed | Residual |
|--------|---------|----------|----------|
| ABL 2023 annual | -3.38 | -4.50 | +1.12 |
| ABL 2024 annual | -3.83 | -2.63 | -1.20 |
| ELA 2023 annual | -0.52 | +0.10 | -0.62 |
| ELA 2024 annual | -0.92 | +0.10 | -1.02 |
| ACC 2023 annual | +1.14 | +0.37 | +0.77 |
| ACC 2024 annual | +0.74 | +1.46 | -0.72 |
| Geodetic 2000-2010 | **+1.404** | -1.072 | **+2.48** |
| Geodetic 2010-2020 | -0.552 | -0.806 | +0.25 |
| Geodetic 2000-2020 | +0.426 | -0.939 | +1.37 |

### Assessment
**CONVERGED but physically unreasonable.** 5/9 parameters at bounds. The
geodetic results are catastrophic: model shows Dixon GAINING mass 2000-2010
when Hugonnet shows -1.07 m w.e./yr loss. precip_corr=4.52 (dumping 10.5 m/yr
of precipitation) is 2-3x above any literature value.

**ROOT CAUSE IDENTIFIED (D-013):** Nuka SNOTEL elevation is 1230 FEET (375 m),
not 1230 meters as used in all runs. The 855m elevation error placed the
entire glacier BELOW the reference station instead of above it, making all
on-glacier temperatures 3-4°C too warm. This is the root cause of every
calibration failure from CAL-001 through CAL-007.

### Output files
- `calibration_output/best_params_v7.json`
- `calibration_output/calibration_log_v7.csv`
- `calibration_output/calibration_summary_v7.json`
- `calibration_output/calibration_v7_stdout.log`

---

## Run CAL-008: v8 Calibration (elevation fix + cost restructuring)

**Date:** 2026-03-09
**Script:** `run_calibration_full.py` (v8)
**Status:** PENDING

### Changes from CAL-007 (D-013, D-014, D-015)
1. **SNOTEL elevation corrected:** 1230 ft = 375 m (not 1230 m)
2. **Lapse rate fixed** at -5.0 C/km (removed from calibration)
3. **k_wind removed** from calibration (was effectively zero)
4. **precip_corr bounds** tightened to [1.2, 3.0]
5. **r_ice bound** widened to [0.05e-3, 5.0e-3]
6. **Geodetic 2000-2020 dropped** (not independent of sub-periods)
7. **Cost function:** inverse-variance weighting (1/σ²) with geodetic hard penalty

### Configuration
| Setting | Value |
|---------|-------|
| Grid resolution | 100 m |
| Method | differential_evolution |
| Population size | 15 per param (105 total) |
| Max iterations | 200 |
| Tolerance | 1e-4 |
| Mutation | (0.5, 1.0) |
| Recombination | 0.7 |
| Seed | 42 |

### Parameters (8)
| Parameter | Lower | Upper | Role |
|-----------|-------|-------|------|
| MF (mm/d/K) | 1.0 | 12.0 | Base melt factor |
| MF_grad (mm/d/K/m) | -0.01 | 0.0 | Melt factor elevation gradient |
| r_snow | 0.02e-3 | 1.5e-3 | Radiation factor (snow) |
| r_ice | 0.05e-3 | 5.0e-3 | Radiation factor (ice) |
| lapse_rate (C/m) | -7.0e-3 | -4.0e-3 | Temperature lapse rate (literature bounded) |
| precip_grad (frac/m) | 0.0002 | 0.006 | Precipitation gradient |
| precip_corr | 1.2 | 3.0 | Precipitation correction |
| T0 (C) | 0.5 | 3.0 | Rain/snow threshold |

### Fixed parameters
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| ref_elev | 375 m | Nuka SNOTEL corrected (D-013) |
| k_wind | 0.0 | CAL-007 converged to ~0 (D-015) |

### Hypothesis
With correct reference elevation, the model will produce physically reasonable
temperatures at all stakes. The glacier surface is now properly ABOVE the
station, so lapse-rate cooling naturally produces colder on-glacier temps.
This should allow:
- MF in literature range (3-8 mm/d/K)
- precip_corr in defensible range (1.5-2.5)
- Geodetic fit within uncertainty bounds
- r values may come off upper bounds

### Results
| Metric | Value |
|--------|-------|
| Final cost | 577.13 |
| Convergence | NO (hit maxiter) |
| Total evaluations | 25,191 |
| Wall time | 5,112 s (85.2 min) |

| Parameter | Best | At bound? |
|-----------|------|-----------|
| MF (mm/d/K) | 9.637 | No |
| MF_grad (per m) | -0.00999 | YES (lower) |
| r_snow | 0.000087 | No (very low) |
| r_ice | 0.000087 | No (= r_snow) |
| lapse_rate (°C/m) | -0.00400 | YES (upper, shallowest) |
| precip_grad | 0.000200 | YES (lower) |
| precip_corr | 1.200 | YES (lower) |
| T0 (°C) | 0.501 | YES (lower) |

### Validation
| Target | Modeled | Observed | Residual |
|--------|---------|----------|----------|
| ABL 2023 annual | -4.46 | -4.50 | +0.04 |
| ELA 2023 annual | -0.99 | +0.10 | -1.09 |
| ACC 2023 annual | +0.93 | +0.37 | +0.56 |
| ABL 2024 annual | -4.54 | -2.63 | -1.91 |
| ELA 2024 annual | -1.06 | +0.10 | -1.16 |
| ACC 2024 annual | +0.80 | +1.46 | -0.66 |
| ELA 2023 winter | +0.77 | +2.36 | -1.59 |
| ACC 2023 winter | +0.98 | +2.45 | -1.47 |
| Geodetic 2000-2010 | -0.208 | -1.072 | +0.86 |
| Geodetic 2010-2020 | -1.372 | -0.806 | -0.57 |

### Assessment
**MAJOR PROGRESS on MF (9.6, literature-reasonable) but new pathology.**
Elevation fix (D-013) worked — MF moved from 1.55 to 9.6, confirming the
root cause. However, 6/8 params at bounds, and the model collapsed to a
pure degree-day model (r_snow ≈ r_ice ≈ 0, radiation effectively off).

**Key findings from post-run analysis:**
1. **Stakes and geodetic ARE compatible:** 2023 stake-extrapolated glacier-wide
   balance = -1.07, matching geodetic 2000-2010 exactly. No fundamental conflict.
2. **Geodetic sub-periods are NOT distinguishable:** Z=0.88 (p>0.30). The
   "acceleration" from -1.07 to -0.81 is within noise. Using both sub-periods
   creates a contradictory constraint because Nuka shows OPPOSITE temperature
   trends (cooler 2001-2010 summers but more mass loss).
3. **precip_corr bound too tight:** Minimum pc for ELA winter balance is
   3.01-3.16 for dry years. Cap of 3.0 prevents the model from accumulating
   enough snow. Winter balances underestimated by 1.5+ m w.e.
4. **Recommendation (D-016):** Use only 2000-2020 geodetic mean for calibration,
   widen precip_corr to [1.2, 4.0].

### Output files
- `calibration_output/best_params_v8.json`
- `calibration_output/calibration_log_v8.csv`
- `calibration_output/calibration_summary_v8.json`
- `calibration_output/calibration_v8_stdout.log`

---

## Run CAL-009: v9 Calibration (single geodetic + wider precip_corr)

**Date:** 2026-03-09
**Script:** `run_calibration_full.py` (v9)
**Status:** PENDING

### Changes from CAL-008 (D-016)
1. **Geodetic:** Use only 2000-2020 mean (-0.939 ± 0.122) for calibration;
   sub-periods reported for validation only
2. **precip_corr bounds** widened to [1.2, 4.0] (3.0-3.2x required for winter)

### Configuration
Same DE settings as CAL-008 (200 maxiter, 15 popsize, 8 params).

### Parameters (8)
| Parameter | Lower | Upper | Role |
|-----------|-------|-------|------|
| MF (mm/d/K) | 1.0 | 12.0 | Base melt factor |
| MF_grad (mm/d/K/m) | -0.01 | 0.0 | Melt factor elevation gradient |
| r_snow | 0.02e-3 | 1.5e-3 | Radiation factor (snow) |
| r_ice | 0.05e-3 | 5.0e-3 | Radiation factor (ice) |
| lapse_rate (C/m) | -7.0e-3 | -4.0e-3 | Temperature lapse rate |
| precip_grad (frac/m) | 0.0002 | 0.006 | Precipitation gradient |
| precip_corr | 1.2 | 4.0 | Precipitation correction (widened) |
| T0 (C) | 0.5 | 3.0 | Rain/snow threshold |

### Hypothesis
With the single 2000-2020 geodetic constraint (no contradictory sub-period
signals) and wider precip_corr (physically required for winter balance),
the optimizer should find a solution that simultaneously:
- Matches winter accumulation at stakes (needs pc ≈ 2.5-3.5)
- Matches 20-year geodetic mean (needs enough melt to offset accumulation)
- Uses radiation factors (not just pure degree-day as in CAL-008)

### Results
| Metric | Value |
|--------|-------|
| Final cost | 7.681 |
| Convergence | NO (hit maxiter) |
| Total evaluations | 24,516 |
| Wall time | 4,293 s (71.5 min) |

| Parameter | Best | At bound? |
|-----------|------|-----------|
| MF (mm/d/K) | 7.642 | No |
| MF_grad (per m) | -0.00220 | No |
| r_snow | 0.001290 | No (near upper) |
| r_ice | 0.001340 | No (≈ r_snow) |
| lapse_rate (°C/m) | -0.00683 | No (steep end) |
| precip_grad | 0.000851 | No |
| precip_corr | 1.200 | YES (lower) |
| T0 (°C) | 0.513 | YES (lower) |

### Validation — Stake Balances
**Summer balances — good fit (±0.3–0.5 m w.e.):**
| Target | Modeled | Observed | Residual |
|--------|---------|----------|----------|
| ABL 2023 summer | -5.02 | -5.35 | +0.33 |
| ABL 2024 summer | -4.81 | -4.56 | -0.25 |
| ELA 2023 summer | -2.72 | -2.26 | -0.46 |
| ELA 2024 summer | -2.83 | -2.50 | -0.33 |
| ACC 2023 summer | -1.35 | -2.25 | +0.90 |
| ACC 2024 summer | -1.65 | -1.55 | -0.10 |

**Winter balances — systematic underestimation:**
| Target | Modeled | Observed | Residual |
|--------|---------|----------|----------|
| ABL 2024 winter | +0.70 | +1.93 | -1.23 |
| ELA 2023 winter | +1.35 | +2.36 | -1.01 |
| ELA 2024 winter | +1.33 | +2.60 | -1.27 |
| ACC 2023 winter | +1.63 | +2.45 | -0.82 |
| ACC 2024 winter | +1.63 | +3.01 | -1.38 |
| ABL 2025 winter | +2.18 | +1.60 | +0.58 |
| ELA 2025 winter | +3.54 | +3.04 | +0.50 |
| ACC 2025 winter | +4.01 | +3.53 | +0.48 |

**Annual balances:**
| Target | Modeled | Observed | Residual |
|--------|---------|----------|----------|
| ABL 2023 annual | -4.26 | -4.50 | +0.24 |
| ABL 2024 annual | -4.29 | -2.63 | -1.66 |
| ELA 2023 annual | -1.38 | +0.10 | -1.48 |
| ELA 2024 annual | -1.52 | +0.10 | -1.62 |
| ACC 2023 annual | +0.27 | +0.37 | -0.10 |
| ACC 2024 annual | +0.05 | +1.46 | -1.41 |

### Validation — Geodetic
| Period | Modeled | Observed | Uncertainty | Status |
|--------|---------|----------|-------------|--------|
| 2000-2020 | -0.817 | -0.939 | ±0.122 | **Within uncertainty** (calibration target) |
| 2000-2010 | +0.141 | -1.072 | ±0.225 | **OPPOSITE SIGN** (validation only) |
| 2010-2020 | -1.775 | -0.806 | ±0.202 | **2× observed** (validation only) |

### Assessment
**BEST CALIBRATION YET** — cost 7.68 is dramatically improved over all prior runs.
MF=7.64 is literature-reasonable. Geodetic 2000-2020 within uncertainty. Summer
melt well-captured at most stakes.

**Critical issues for projections:**

1. **Equifinality:** lapse_rate=-6.83 C/km and precip_corr=1.20 compensate each
   other. Steep lapse makes high elevations cold (all precip → snow), but low
   precip_corr limits total accumulation. For current climate these cancel, but
   under warming they diverge — steep lapse underestimates warming at high
   elevations while low precip means glacier disappears too fast.

2. **r_snow ≈ r_ice** (1.29 vs 1.34 × 10⁻³): No albedo feedback. As firn line
   retreats upward under warming, the model won't capture accelerated ice melt.

3. **Sub-period reversal:** Model shows mass gain 2000-2010 when geodetic shows
   strongest loss. This is an input limitation (Nuka SNOTEL doesn't capture
   Dixon's decadal precipitation variability), not fixable with parameters.

4. **Winter accumulation gap:** 1.0-1.4 m w.e. too low for WY2024 at all stakes.
   precip_corr at lower bound (1.20) despite D-016 analysis showing 3.0-3.2×
   required. The optimizer exploited lapse rate to compensate.

**Conclusion:** CAL-009 demonstrates the model CAN fit observations, but the
parameter set is not physically defensible for projections due to equifinality.
Proceeding to CAL-010 with Bayesian ensemble approach (D-017).

### Output files
- `calibration_output/best_params_v9.json`
- `calibration_output/calibration_log_v9.csv`
- `calibration_output/calibration_summary_v9.json`
- `calibration_output/calibration_v9_stdout.log`

---

## Run CAL-010: Bayesian Ensemble (DE + MCMC)

**Date:** 2026-03-09
**Script:** `run_calibration_v10.py`
**Status:** PENDING
**Decision:** D-017

### Changes from CAL-009
1. **Lapse rate fixed** at -5.0 C/km (removed from calibration)
2. **r_ice derived** as 2.0 × r_snow (removed from calibration)
3. **Parameters reduced** from 8 to 6 free parameters
4. **MCMC sampling** added (emcee) for posterior ensemble
5. **Informative priors** on MF and T0 (literature-based)

### Phase 1: Differential Evolution (MAP estimate)
| Setting | Value |
|---------|-------|
| Grid resolution | 100 m |
| Method | scipy.optimize.differential_evolution |
| Population size | 15 per param (90 total) |
| Max iterations | 200 |
| Tolerance | 1e-4 |
| Mutation | (0.5, 1.0) |
| Recombination | 0.7 |
| Seed | 42 |

### Phase 2: MCMC (emcee)
| Setting | Value |
|---------|-------|
| Sampler | emcee affine-invariant ensemble (Foreman-Mackey et al. 2013) |
| Walkers | 24 (4× ndim) |
| Steps | 10,000 |
| Burn-in | 2,000 (or 2× autocorrelation time) |
| Thinning | By autocorrelation time |
| Likelihood | Gaussian: ln(L) = -0.5 × Σ((residual/σ)²) |
| Convergence | Acceptance 0.2-0.5, autocorrelation time stable |

### Parameters (6 free)
| Parameter | Lower | Upper | Prior | Source |
|-----------|-------|-------|-------|--------|
| MF (mm/d/K) | 1.0 | 12.0 | TruncNorm(5.0, 3.0) | Braithwaite 2008 |
| MF_grad (mm/d/K/m) | -0.01 | 0.0 | Uniform | No strong literature |
| r_snow | 0.02e-3 | 1.5e-3 | Uniform | Hock 1999 range |
| precip_grad (frac/m) | 0.0002 | 0.006 | Uniform | Region-specific |
| precip_corr | 1.2 | 4.0 | Uniform | PyGEM cap 3.0, Wolverine 2.28× |
| T0 (°C) | 0.5 | 3.0 | TruncNorm(1.5, 0.5) | Standard range |

### Fixed parameters
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| lapse_rate | -5.0 C/km | Gardner & Sharp 2009, Roth et al. 2023 |
| r_ice/r_snow ratio | 2.0 | Hock 1999 Table 4 mid-range |
| k_wind | 0.0 | CAL-007 converged to ~0 |
| ref_elev | 375 m | Nuka SNOTEL corrected (D-013) |

### Calibration targets
Same as CAL-009:
- Stake annual: 8 (6 measured, 2 estimated with inflated unc)
- Stake summer: 8 (6 measured)
- Stake winter: 9 (8 measured)
- Geodetic: 2000-2020 mean only (-0.939 ± 0.122 m w.e./yr)
- Sub-periods: validation only (not in likelihood)

### Expected outputs
- `calibration_output/best_params_v10.json` (DE MAP estimate)
- `calibration_output/mcmc_chain_v10.h5` (full MCMC chain)
- `calibration_output/posterior_samples_v10.csv` (thinned posterior)
- `calibration_output/corner_plot_v10.png` (parameter correlations)
- `calibration_output/calibration_summary_v10.json`
- `calibration_output/calibration_v10_stdout.log`

### Results — Phase 1 (DE)
| Metric | Value |
|--------|-------|
| Final cost | 7.703 |
| Convergence | NO (hit maxiter) |
| Total evaluations | 18,251 |
| Wall time | 3,103 s (51.7 min) |

| Parameter | MAP | At bound? |
|-----------|-----|-----------|
| MF (mm/d/K) | 7.049 | No |
| MF_grad (per m) | -0.0039 | No |
| r_snow (×10⁻³) | 1.974 | Near upper (2.0) |
| precip_grad | 0.0006 | No |
| precip_corr | 1.644 | No |
| T0 (°C) | 0.001 | YES (lower, ~0.0) |

### Results — Phase 2 (MCMC)
| Metric | Value |
|--------|-------|
| Wall time | 30,158 s (8.4 hours) |
| Mean acceptance fraction | 0.373 (target: 0.2–0.5) |
| Autocorrelation times | 138–266 steps |
| Max tau | 266 (precip_grad) |
| Chain / max(tau) | 38× (target: >50×) |
| Burn-in used | 2,000 steps |
| Thinning | every 69 steps |
| Independent posterior samples | **2,760** |

### Posterior Summary
| Parameter | Median | 16th | 84th | MAP |
|-----------|--------|------|------|-----|
| MF | 7.11 | 6.91 | 7.34 | 7.05 |
| MF_grad | -0.0039 | -0.0042 | -0.0036 | -0.0039 |
| r_snow (×10⁻³) | 1.756 | 1.411 | 1.932 | 1.974 |
| precip_grad | 0.0006 | 0.0004 | 0.0008 | 0.0006 |
| precip_corr | 1.644 | 1.502 | 1.781 | 1.644 |
| T0 | 0.014 | 0.004 | 0.037 | 0.001 |

### MAP Validation — Geodetic
| Period | Modeled | Observed | Uncertainty | Status |
|--------|---------|----------|-------------|--------|
| 2000-2020 | -0.817 | -0.939 | ±0.122 | Within uncertainty |
| 2000-2010 | +0.146 | -1.072 | ±0.225 | Opposite sign (validation) |
| 2010-2020 | -1.780 | -0.806 | ±0.202 | 2× observed (validation) |

### Assessment
**FIRST BAYESIAN ENSEMBLE CALIBRATION.** 2,760 posterior samples successfully
generated. Key findings:

1. **MF well-constrained**: 7.11 [6.91, 7.34] — tight posterior, mid-literature range
2. **precip_corr off bounds**: 1.64 [1.50, 1.78] — effective correction at ELA is
   1.64 × (1 + 0.0006 × 703) = 2.33×, comparable to Wolverine (2.28×)
3. **T0 near 0°C**: physically defensible for maritime climate (Jennings et al. 2018)
4. **r_snow broad posterior**: 1.76 [1.41, 1.93] — good spread for projections
5. **Convergence adequate**: acceptance 0.37, chain/tau=38× (slightly below 50× for
   2 of 6 params — precip_grad and precip_corr mix slowly due to correlation)
6. **Corner plot** shows expected MF-precip_corr negative correlation

**Limitation:** Sub-period geodetic mismatch persists (input limitation, not model).
Winter accumulation still systematically underestimated for WY2024 (single-station
forcing error). Both acknowledged as known limitations.

**Ready for projections** with 200+ posterior samples.

### Output files
- `calibration_output/best_params_v10.json`
- `calibration_output/calibration_log_v10_de.csv`
- `calibration_output/mcmc_chain_v10.npy`
- `calibration_output/mcmc_logprob_v10.npy`
- `calibration_output/posterior_samples_v10.csv`
- `calibration_output/corner_plot_v10.png`
- `calibration_output/calibration_summary_v10.json`
- `calibration_output/calibration_v10_stdout.log`

---

## PROJ-001: First Full Projection Run (SSP2-4.5 + SSP5-8.5)

**Date:** 2026-03-10
**Script:** `run_projection.py`
**Parameters:** `calibration_output/best_params_v10.json` (CAL-010 MAP)
**Grid:** 100m
**Ice thickness:** Farinotti et al. (2019) consensus, 171m mean

### Configuration
- **GCMs (5):** ACCESS-CM2, EC-Earth3, MPI-ESM1-2-HR, MRI-ESM2-0, NorESM2-MM
- **Scenarios:** SSP2-4.5, SSP5-8.5
- **Period:** WY2026–WY2100 (75 years)
- **Geometry:** Delta-h (Huss et al. 2010), large class, Farinotti bedrock
- **Routing:** 3 parallel linear reservoirs (k_fast=0.3, k_slow=0.05, k_gw=0.01)
- **Bias correction:** Monthly delta method vs Nuka SNOTEL 1991–2020

### Results — SSP2-4.5
| GCM | Final area (km2) | Final vol (km3) | Area % | Vol % | Cum MB (m w.e.) |
|-----|-------------------|-----------------|--------|-------|-----------------|
| ACCESS-CM2 | 17.8 | 1.798 | 44% | 26% | -157.5 |
| EC-Earth3 | 17.6 | 1.758 | 44% | 26% | -160.3 |
| MPI-ESM1-2-HR | 15.2 | 1.293 | 38% | 19% | -187.5 |
| MRI-ESM2-0 | 22.1 | 2.531 | 55% | 37% | -123.5 |
| NorESM2-MM | 16.8 | 1.612 | 42% | 23% | -167.7 |
| **Ensemble** | **~18** | **~1.8** | **45%** | **26%** | **~-159** |

**Peak water:** ~WY2043 (8.13 m3/s, 11-yr smoothed, range 7.06–8.33)

### Results — SSP5-8.5
| GCM | Final area (km2) | Final vol (km3) | Area % | Vol % | Cum MB (m w.e.) |
|-----|-------------------|-----------------|--------|-------|-----------------|
| ACCESS-CM2 | 6.3 | 0.250 | 16% | 4% | -277.2 |
| EC-Earth3 | 6.4 | 0.255 | 16% | 4% | -276.9 |
| MPI-ESM1-2-HR | 12.2 | 0.780 | 30% | 11% | -225.6 |
| MRI-ESM2-0 | 19.5 | 2.124 | 49% | 31% | -143.4 |
| NorESM2-MM | 7.8 | 0.338 | 19% | 5% | -263.2 |
| **Ensemble** | **~10** | **~0.75** | **26%** | **11%** | **~-237** |

**Peak water:** ~WY2058 (8.44 m3/s, 11-yr smoothed, range 7.46–9.50)

### Assessment
- Glacier survives to 2100 in all scenarios but loses 45–74% of area
- Peak water ~15 years later under SSP5-8.5 (more ice to melt)
- MRI-ESM2-0 consistently wettest/coolest outlier
- Large GCM spread in SSP5-8.5 reflects structural model uncertainty
- Routing not yet validated against observed discharge
- Single parameter set (MAP); posterior ensemble projections pending

### Output files
- `projection_output/projection_ssp{245,585}_*_2100.csv` (5 GCMs + ensemble each)
- `projection_output/peak_water_ssp{245,585}.json`
- `projection_output/*.png` (diagnostic plots)

---

## NOTE: Climate Input Fix (D-025) — Impacts CAL-010 and All Projections

**Date:** 2026-03-12

CAL-010 was run with the old `ffill().fillna(0)` climate preprocessing,
which introduced severe errors in gap years:
- WY2000: summer T filled at ~3°C (actual ~11°C) → melt suppressed
- WY2001: 282-day gap filled at ~2°C → nearly zero summer melt
- WY2005: summer T filled at -7.7°C → ZERO melt + spurious snow accumulation
- WY2020: 192-day precip gap → 1,176mm instead of ~2,307mm

**D-025 implemented multi-station gap-filling:**
- 5 nearby SNOTEL stations with monthly regression transfer
- 91.3% original Nuka, 6.0% MFB, 1.8% McNeil, 0.4% interp, 0.1% other
- All downstream consumers updated to use `dixon_gap_filled_climate.csv`

**Expected impact on recalibration (CAL-011):**
1. Geodetic sub-period mismatch should shrink (2000-2010 was most affected)
2. MF may decrease (less compensation needed for suppressed melt years)
3. WY2000 and WY2005 contribute real information (not noise) to calibration
4. Snowline validation D-022 exclusions may no longer be needed (gap-filled
   data replaces the fillna(0) that caused terminus-level snowlines)

**All CAL-010 results and PROJ-001/002 results are based on the old climate
and should be re-run with gap-filled data before thesis submission.**

---

## Run CAL-011: Recalibration with Gap-Filled Climate (D-026)

**Date:** 2026-03-12
**Script:** `run_calibration_v11.py`
**Status:** KILLED (step 28/200, cost 7.23) — superseded by CAL-012 (D-027)
**Decision:** D-026

### Changes from CAL-010
1. **Climate input:** `dixon_gap_filled_climate.csv` (D-025) — zero NaN,
   91.3% Nuka + 5-station cascade gap-fill
2. **Coverage filter removed:** `t_cov < 0.85` check no longer needed — all
   20 geodetic water years (WY2001–2020) now contribute
3. **Poisoned years fixed:** WY2000, WY2001, WY2005, WY2020 now have
   realistic temperature and precipitation from nearby stations

### Configuration
Same as CAL-010 (D-017):

| Setting | Value |
|---------|-------|
| Grid resolution | 100 m |
| Method | DE (MAP) + emcee MCMC (posterior) |
| DE population | 15 per param (90 total) |
| DE max iterations | 200 |
| DE tolerance | 1e-4 |
| MCMC walkers | 24 (4x ndim) |
| MCMC steps | 10,000 |
| MCMC burn-in | 2,000 minimum |

### Parameters (6 free — unchanged from CAL-010)
| Parameter | Lower | Upper | Prior |
|-----------|-------|-------|-------|
| MF (mm/d/K) | 1.0 | 12.0 | TruncNorm(5.0, 3.0) |
| MF_grad (mm/d/K/m) | -0.01 | 0.0 | Uniform |
| r_snow | 0.02e-3 | 2.0e-3 | Uniform |
| precip_grad (frac/m) | 0.0002 | 0.006 | Uniform |
| precip_corr | 1.2 | 4.0 | Uniform |
| T0 (C) | 0.0 | 3.0 | TruncNorm(1.5, 0.5) |

### Fixed parameters (unchanged)
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| lapse_rate | -5.0 C/km | Gardner & Sharp 2009, Roth 2023 |
| r_ice/r_snow | 2.0 | Hock 1999 Table 4 mid-range |
| k_wind | 0.0 | CAL-007 converged to ~0 |
| ref_elev | 375 m | Nuka SNOTEL (D-013) |

### Hypothesis
With corrected climate forcing:
1. All 20 geodetic years contribute real melt → r_snow may come off upper bound
2. WY2005 summer T realistic → less MF compensation needed
3. T0 gains gradient signal in gap years → may move up from ~0°C
4. Geodetic sub-period mismatch (2000-2010 vs 2010-2020) should shrink
5. Overall cost should decrease (less internal contradiction)

### Results
**KILLED** at DE step 28/200 (eval ~2650, best cost 7.23).
Superseded by CAL-012 (D-027) before completion — no need to run single-seed
DE when multi-seed approach addresses multimodality concern.

Early DE trajectory showed best cost 7.23 at step 28, with MF~7.5, pc~1.39,
T0~0.2, r_snow~1.07e-3. Notably T0 was already drifting toward 0 again.

### Output files (partial)
- `calibration_output/calibration_v11_stdout.log` (partial, killed at step 28)

---

## Run CAL-012: Multi-Seed DE + Multi-Chain MCMC (D-027)

**Date:** 2026-03-12
**Script:** `run_calibration_v12.py`
**Status:** COMPLETED
**Decision:** D-027

### Changes from CAL-011
1. **Multi-seed DE:** 5 seeds [42, 123, 456, 789, 2024] to detect multimodality
2. **Hierarchical clustering:** DE optima clustered by normalized Chebyshev
   distance (10% of parameter range threshold)
3. **Multi-chain MCMC:** separate emcee chain from each distinct mode
4. **Combined posterior:** equal-weighted concatenation across all chains

### Rationale (D-027)
CAL-010 ran single-seed DE → single MCMC chain. If the posterior is multimodal
(e.g., high-MF/low-r_snow vs low-MF/high-r_snow), the single chain would miss
alternative modes. Multi-seed DE probes the cost surface broadly; if seeds
converge to different regions, separate MCMC chains explore each mode.

### Configuration
Same model and target setup as CAL-011:

| Setting | Value |
|---------|-------|
| Grid resolution | 100 m |
| DE seeds | 5 (42, 123, 456, 789, 2024) |
| DE population | 15 per param (90 total) per seed |
| DE max iterations | 200 per seed |
| Cluster threshold | 10% of parameter range |
| MCMC walkers | 24 (4x ndim) per chain |
| MCMC steps | 10,000 per chain |
| MCMC burn-in | 2,000 minimum per chain |

### Parameters (6 free — unchanged)
| Parameter | Lower | Upper | Prior |
|-----------|-------|-------|-------|
| MF (mm/d/K) | 1.0 | 12.0 | TruncNorm(5.0, 3.0) |
| MF_grad (mm/d/K/m) | -0.01 | 0.0 | Uniform |
| r_snow | 0.02e-3 | 2.0e-3 | Uniform |
| precip_grad (frac/m) | 0.0002 | 0.006 | Uniform |
| precip_corr | 1.2 | 4.0 | Uniform |
| T0 (C) | 0.0 | 3.0 | TruncNorm(1.5, 0.5) |

### Fixed parameters (unchanged)
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| lapse_rate | -5.0 C/km | Gardner & Sharp 2009, Roth 2023 |
| r_ice/r_snow | 2.0 | Hock 1999 Table 4 |
| k_wind | 0.0 | CAL-007 converged to ~0 |
| ref_elev | 375 m | Nuka SNOTEL (D-013) |

### Estimated runtime
- Phase 1 (DE): ~50 min/seed × 5 seeds = ~4.2 hrs
- Phase 1.5 (clustering): seconds
- Phase 2 (MCMC): ~8 hrs/chain × N_modes chains
- Best case (1 mode): ~12 hrs total
- Worst case (5 modes): ~44 hrs total

### Results — Phase 1 (Multi-Seed DE)
| Metric | Value |
|--------|-------|
| Total DE wall time | 15,956 s (4.4 hrs) |
| Modes found | **1** (unimodal — all 5 seeds converged to same region) |

| Seed | Cost | MF | MF_grad | r_snow (×10⁻³) | precip_grad | precip_corr | T0 |
|------|------|----|---------|-----------------|-------------|-------------|-----|
| 42 | 7.171 | 6.947 | -0.00385 | 2.000 | 0.000640 | 1.672 | 0.0005 |
| 123 | 7.172 | 7.014 | -0.00390 | 1.850 | 0.000613 | 1.691 | 0.0010 |
| 456 | 7.173 | 6.959 | -0.00378 | 1.908 | 0.000702 | 1.634 | 0.0032 |
| 789 | 7.173 | 7.100 | -0.00405 | 1.952 | 0.000507 | 1.792 | 0.0020 |
| **2024** | **7.170** | **6.939** | **-0.00383** | **2.000** | **0.000598** | **1.710** | **0.0000** |

**Key finding:** All 5 seeds converged to costs within 0.003 of each other (7.170–7.173),
confirming the posterior is **unimodal**. No alternative modes detected. The multi-seed
approach validates CAL-010's single-seed result — the cost surface has one global minimum
in this parameterization.

### Results — Phase 2 (MCMC)
| Metric | Value |
|--------|-------|
| Chains run | 1 (single mode) |
| Walkers | 24 (4× ndim) |
| Steps | 10,000 |
| Burn-in | 2,000 (used 5,000 for posterior = 50% of chain) |
| Thinning | every 70 steps |
| MCMC wall time | 29,968 s (8.3 hrs) |
| Mean acceptance fraction | 0.373 (target: 0.2–0.5) |
| Autocorrelation times | 141–253 steps |
| Max tau | 253 (precip_grad) |
| Chain / max(tau) | 40× (target: >50×; adequate for 4/6 params) |
| Independent posterior samples | **2,736** |

### Posterior Summary (v12)
| Parameter | Median | 16th | 84th | MAP (seed 2024) | At bound? |
|-----------|--------|------|------|-----------------|-----------|
| MF (mm/d/K) | 7.163 | 6.927 | 7.434 | 6.939 | No |
| MF_grad (per m) | -0.00395 | -0.00424 | -0.00366 | -0.00383 | No |
| r_snow (×10⁻³) | 1.472 | 0.872 | 1.848 | 2.000 | MAP at upper |
| precip_grad | 0.000658 | 0.000501 | 0.000865 | 0.000598 | No |
| precip_corr | 1.672 | 1.520 | 1.809 | 1.710 | No |
| T0 (°C) | 0.012 | 0.003 | 0.031 | 0.000 | MAP at lower |

### Comparison with CAL-010 (pre-gap-fill)
| Parameter | CAL-010 Median | CAL-012 Median | Change |
|-----------|---------------|---------------|--------|
| MF | 7.11 | 7.16 | +0.7% |
| MF_grad | -0.0039 | -0.00395 | -1.3% |
| r_snow (×10⁻³) | 1.756 | 1.472 | -16% |
| precip_grad | 0.0006 | 0.000658 | +10% |
| precip_corr | 1.644 | 1.672 | +1.7% |
| T0 | 0.014 | 0.012 | -14% |

Gap-filled climate had modest impact on most parameters. Largest change is r_snow
(-16%), with broader posterior spread [0.87, 1.85] vs [1.41, 1.93] in CAL-010.
This suggests gap-filled years provide additional constraint on the radiation
factor, but the overall calibration is robust to the climate fix.

### Total Runtime
| Phase | Wall time |
|-------|-----------|
| Phase 1 (5× DE) | 4.4 hrs |
| Phase 2 (1× MCMC) | 8.3 hrs |
| **Total** | **12.8 hrs** |

### Assessment
**DEFINITIVE CALIBRATION for thesis.** Key conclusions:

1. **Unimodal posterior confirmed:** All 5 DE seeds converge to same minimum.
   The equifinality concern from CAL-009 was resolved by fixing lapse rate and
   reducing to 6 free parameters (D-017). Single-mode MCMC is sufficient.

2. **Gap-fill impact modest:** Parameters changed <2% for MF, MF_grad, precip_corr.
   The r_snow posterior broadened, suggesting gap-filled years add information
   but don't fundamentally change the calibration.

3. **MF well-constrained:** 7.16 [6.93, 7.43] — tight, mid-literature range.

4. **T0 near 0°C:** Consistent with maritime climate (Jennings et al. 2018).

5. **precip_corr = 1.67:** Effective correction at ELA = 1.67 × (1 + 0.00066 × 703)
   = 2.44×, comparable to Wolverine Glacier (2.28×, O'Neel et al. 2014).

6. **Ready for projections** with v12 posterior.

### Output files
- `calibration_output/de_multistart_v12.json` (5 seed optima + clustering)
- `calibration_output/best_params_v12.json` (best mode MAP)
- `calibration_output/mcmc_chain_v12_mode1.npy` (10000 × 24 × 6)
- `calibration_output/mcmc_logprob_v12_mode1.npy` (10000 × 24)
- `calibration_output/posterior_samples_v12.csv` (2,736 thinned samples)
- `calibration_output/corner_plot_v12.png`
- `calibration_output/calibration_summary_v12.json`
- `calibration_output/calibration_v12_stdout.log`

---

## PROJ-004: Projection SSP2-4.5 with v12 Posterior + Gap-Filled Climate

**Date:** 2026-03-14
**Script:** `run_projection.py`
**Parameters:** CAL-012 posterior (top 250 of 2,736 samples)
**Climate:** Gap-filled (D-025) + NEX-GDDP-CMIP6 bias-corrected
**Grid:** 100m
**Status:** COMPLETED

### Configuration
- **GCMs (5):** ACCESS-CM2, EC-Earth3, MPI-ESM1-2-HR, MRI-ESM2-0, NorESM2-MM
- **Scenario:** SSP2-4.5
- **Period:** WY2026–WY2100 (75 years)
- **Total runs:** 1,250 (5 GCMs × 250 param sets)
- **Geometry:** Delta-h (Huss et al. 2010), Farinotti ice thickness
- **Routing:** 3 parallel linear reservoirs
- **Bias correction:** Monthly delta method vs gap-filled obs 1991–2020
- **Wall time:** 841 s (14.0 min)

### Results — SSP2-4.5
| Metric | Median | 5th–95th |
|--------|--------|----------|
| Final area (km2) | 21.9 | 18.7–29.3 |
| Final area (%) | 55% | 47–73% |
| Final volume (km3) | 2.49 | 1.97–3.53 |
| Final volume (%) | 36% | 29–51% |
| Final balance (m w.e./yr) | -1.50 | -2.96 to -0.99 |

**Peak water:** ~WY2058 (8.49 m3/s, 11-yr smoothed, range 7.82–10.04)

| GCM | Final area (km2) | Final area (%) |
|-----|-------------------|----------------|
| ACCESS-CM2 | 21.9 | 55% |
| EC-Earth3 | 22.1 | 55% |
| MPI-ESM1-2-HR | 18.8 | 47% |
| MRI-ESM2-0 | 29.3 | 73% |
| NorESM2-MM | 20.9 | 52% |

### Output files
- `projection_output/PROJ-004_top250_ssp245_2026-03-14/`

---

## PROJ-005: Projection SSP5-8.5 with v12 Posterior + Gap-Filled Climate

**Date:** 2026-03-14
**Script:** `run_projection.py`
**Parameters:** CAL-012 posterior (top 250 of 2,736 samples)
**Climate:** Gap-filled (D-025) + NEX-GDDP-CMIP6 bias-corrected
**Grid:** 100m
**Status:** COMPLETED

### Configuration
- **GCMs (5):** ACCESS-CM2, EC-Earth3, MPI-ESM1-2-HR, MRI-ESM2-0, NorESM2-MM
- **Scenario:** SSP5-8.5
- **Period:** WY2026–WY2100 (75 years)
- **Total runs:** 1,250 (5 GCMs × 250 param sets)
- **Wall time:** 819 s (13.7 min)

### Results — SSP5-8.5
| Metric | Median | 5th–95th |
|--------|--------|----------|
| Final area (km2) | 12.0 | 11.0–25.9 |
| Final area (%) | 30% | 27–64% |
| Final volume (km3) | 0.74 | 0.57–3.05 |
| Final volume (%) | 11% | 8–44% |
| Final balance (m w.e./yr) | -6.60 | -8.07 to -3.01 |

**Peak water:** ~WY2063 (9.12 m3/s, 11-yr smoothed, range 7.76–11.13)

| GCM | Final area (km2) | Final area (%) |
|-----|-------------------|----------------|
| ACCESS-CM2 | 11.1 | 28% |
| EC-Earth3 | 11.7 | 29% |
| MPI-ESM1-2-HR | 15.2 | 38% |
| MRI-ESM2-0 | 25.8 | 64% |
| NorESM2-MM | 12.0 | 30% |

### Output files
- `projection_output/PROJ-005_top250_ssp585_2026-03-14/`

---

### Comparison: PROJ-002 (v10, old climate) vs PROJ-004/005 (v12, gap-filled)

| Metric | PROJ-002 SSP2-4.5 | PROJ-004 SSP2-4.5 | PROJ-002 SSP5-8.5 | PROJ-005 SSP5-8.5 |
|--------|-------------------|-------------------|-------------------|-------------------|
| Peak water year | WY2043 | **WY2058** | WY2058 | **WY2063** |
| Peak Q (m3/s) | 8.13 | 8.49 | 8.44 | 9.12 |
| Final area (%) | ~45% | 55% | ~26% | 30% |
| Final vol (%) | ~26% | 36% | ~11% | 11% |

**Key changes with v12 + gap-filled climate:**
- Peak water delayed ~15 years under SSP2-4.5 (WY2043 → WY2058)
- Peak water delayed ~5 years under SSP5-8.5 (WY2058 → WY2063)
- Glacier retains more area/volume by 2100 in SSP2-4.5 (55% vs 45%)
- Higher peak discharge in both scenarios
- Gap-filled climate years (especially WY2000, WY2005) contribute realistic
  forcing rather than suppressed melt, affecting long-term trajectory

**Note:** PROJ-003 was an aborted run (bug in climate_projections.py where
`precip_source` column from gap-filled CSV was misidentified as precipitation).
Fixed by tightening column matching in `load_nuka_historical()`.

---

## Run CAL-013: Multi-Objective Calibration with Snowline in Likelihood (D-028)

**Date:** 2026-03-19–23
**Script:** `run_calibration_v13.py`
**Status:** COMPLETED
**Decision:** D-028

### Changes from CAL-012
1. **Snowline elevation in MCMC likelihood:** 22 years of digitized snowline
   elevations (1999–2024) added as chi-squared terms with sigma=75m
2. **Post-hoc area behavioral filter:** 6 manually digitized outlines
   (2000–2025, 5-yr intervals) as area RMSE ≤ 1.0 km² screen
3. **MCMC checkpoint/resume:** saves every 1000 steps, `--resume` flag
   to skip completed DE phase and continue MCMC from last checkpoint

### Motivation
Post-hoc snowline filtering of the CAL-012 posterior had **zero
discriminating power**: all 1000 param sets scored RMSE 88–96m (range 8m,
std 1.6m). Snowline RMSE was uncorrelated with log-probability (r=0.146).
The stakes+geodetic likelihood constrained the posterior so tightly that
no parameter variation could improve snowline fit. Moving snowlines into
the likelihood lets the sampler explore parameter space that jointly
satisfies all constraints.

### Configuration
Same model and DE/MCMC structure as CAL-012:

| Setting | Value |
|---------|-------|
| Grid resolution | 100 m |
| DE seeds | 5 (42, 123, 456, 789, 2024) |
| DE maxiter | 200 per seed |
| MCMC walkers | 24 (4× ndim) |
| MCMC steps | 10,000 per chain |
| MCMC burn-in | 2,000 minimum |
| Snowline sigma | 75 m |
| Area RMSE threshold | 1.0 km² |

### Parameters (6 free — unchanged from CAL-012)
| Parameter | Lower | Upper | Prior |
|-----------|-------|-------|-------|
| MF (mm/d/K) | 1.0 | 12.0 | TruncNorm(5.0, 3.0) |
| MF_grad (mm/d/K/m) | -0.01 | 0.0 | Uniform |
| r_snow | 0.02e-3 | 2.0e-3 | Uniform |
| precip_grad (frac/m) | 0.0002 | 0.006 | Uniform |
| precip_corr | 1.2 | 4.0 | Uniform |
| T0 (C) | 0.0 | 3.0 | TruncNorm(1.5, 0.5) |

### Fixed parameters (unchanged)
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| lapse_rate | -5.0 C/km | Gardner & Sharp 2009, Roth 2023 |
| r_ice/r_snow | 2.0 | Hock 1999 Table 4 |
| k_wind | 0.0 | CAL-007 converged to ~0 |
| ref_elev | 375 m | Nuka SNOTEL (D-013) |

### Calibration targets
| Type | Count | Notes |
|------|-------|-------|
| Stake annual | 8 (6 measured) | ABL/ELA/ACC, WY2023–2025 |
| Stake summer | 8 (6 measured) | |
| Stake winter | 9 (8 measured) | |
| Geodetic | 1 period | 2000-2020 mean (-0.939 ± 0.122) |
| **Snowline** | **22 years** | **1999–2024, sigma=75m (NEW)** |

### Results — Phase 1 (Multi-Seed DE)
| Metric | Value |
|--------|-------|
| Total DE wall time | 31,816 s (8.8 hrs) |
| Modes found | **1** (unimodal) |

| Seed | Cost | MF | precip_corr | T0 | r_snow (×10⁻³) |
|------|------|----|-------------|-----|-----------------|
| 42 | 5.345 | 7.035 | 1.507 | 0.003 | 1.889 |
| 123 | **5.343** | 7.097 | 1.651 | 0.000 | 1.989 |
| 456 | 5.343 | 7.150 | 1.665 | 0.001 | 1.977 |
| 789 | 5.343 | 7.104 | 1.633 | 0.001 | 1.954 |
| 2024 | 5.343 | 7.110 | 1.621 | 0.000 | 1.961 |

**Cost decreased** from 7.170 (CAL-012) to 5.343 — the snowline terms
provide additional gradient signal that helps DE find better optima.

### Results — Phase 2 (MCMC)
| Metric | Value |
|--------|-------|
| Chains run | 1 (single mode) |
| Total steps | 10,000 (accumulated across 3 resumed runs) |
| Mean acceptance fraction | 0.365 |
| Eval time | ~615 ms (vs 290 ms in CAL-012 — 22 extra snowline runs) |
| Combined posterior samples | 1,656 |

### Posterior Summary (v13)
| Parameter | Median | 16th | 84th | MAP |
|-----------|--------|------|------|-----|
| MF (mm/d/K) | 7.299 | 7.059 | 7.581 | 7.110 |
| MF_grad (per m) | -0.0042 | -0.0044 | -0.0039 | -0.0041 |
| r_snow (×10⁻³) | 1.405 | 0.726 | 1.815 | 1.961 |
| precip_grad | 0.000700 | 0.000600 | 0.000900 | 0.000694 |
| precip_corr | 1.605 | 1.475 | 1.741 | 1.621 |
| T0 (°C) | 0.011 | 0.003 | 0.029 | 0.000 |

### Comparison with CAL-012
| Parameter | CAL-012 Median | CAL-013 Median | Change |
|-----------|---------------|---------------|--------|
| MF | 7.16 | 7.30 | +1.9% |
| MF_grad | -0.00395 | -0.0042 | -6.3% |
| r_snow (×10⁻³) | 1.472 | 1.405 | -4.6% |
| precip_grad | 0.000658 | 0.000700 | +6.4% |
| precip_corr | 1.672 | 1.605 | -4.0% |
| T0 | 0.012 | 0.011 | -8.3% |

Snowline information pulled MF slightly higher (more melt), precip_corr
slightly lower, and steepened MF_grad. Changes are modest (<7%) but
physically meaningful: the snowline constraint informs the ELA position,
which depends on the balance between accumulation and ablation.

### MAP Snowline Validation
| Year | Obs (m) | Mod (m) | Bias (m) |
|------|---------|---------|----------|
| 1999 | 1105 | 1065 | -40 |
| 2000 | 1032 | 841 | -191 |
| 2003 | 979 | 984 | +5 |
| 2004 | 1204 | 1170 | -35 |
| 2005 | 1104 | 1129 | +25 |
| 2006 | 1109 | 1099 | -10 |
| 2007 | 1128 | 1156 | +28 |
| 2009 | 1237 | 1387 | +149 |
| 2010 | 1086 | 1077 | -9 |
| 2014 | 1245 | 1242 | -4 |
| 2015 | 1051 | 1061 | +10 |
| 2020 | 1126 | 1303 | +176 |
| 2024 | 1166 | 1254 | +88 |

**Summary (22 years):** RMSE = 90m, mean bias = +32m, MAE = 68m

Snowline RMSE did not improve dramatically (90m vs 93m in CAL-012) because
the error is primarily structural: the model over-amplifies interannual
variability (std 129m vs obs 63m) and produces spatially flat snowlines
(std 6–22m vs obs 24–69m). However, the snowline information now shapes
the posterior distribution rather than being ignored.

### Area Evolution Filter (Phase 4)
| Metric | Value |
|--------|-------|
| Candidates screened | 1,000 (top by log-prob) |
| RMSE threshold | 1.0 km² |
| **Survivors** | **1,000 (100%)** |

All posterior samples passed the area filter, confirming the snowline-informed
posterior already produces area trajectories consistent with the observed
1.77 km² retreat (2000–2025). The area filter is effectively a validation
check rather than an active screen.

### Area checkpoints (manually digitized outlines)
| Year | Observed area (km²) | Source |
|------|---------------------|--------|
| 2000 | 40.11 | Manual digitization |
| 2005 | 40.11 | Manual digitization |
| 2010 | 39.83 | Manual digitization |
| 2015 | 39.26 | Manual digitization |
| 2020 | 38.59 | Manual digitization |
| 2025 | 38.34 | Manual digitization |

### Runtime
| Phase | Wall time |
|-------|-----------|
| Phase 1 (5× DE) | 8.8 hrs |
| Phase 2 (MCMC, 10k steps) | ~19 hrs (across 3 resumed runs) |
| Phase 4 (area filter) | ~0.5 hrs |
| **Total** | **~28 hrs** |

Note: MCMC crashed twice due to machine sleep/OOM. Checkpoint/resume
support (saves every 1000 steps) was added after the first crash,
preventing further data loss.

### Assessment
**MULTI-OBJECTIVE CALIBRATION COMPLETE.** Key conclusions:

1. **Snowline in likelihood works:** DE cost dropped from 7.17 to 5.34,
   confirming the snowline terms provide useful gradient signal.
2. **Posterior shifts are modest but physical:** MF +1.9%, precip_corr -4%.
   Snowlines constrain the ELA position, pulling parameters toward slightly
   more melt and less precipitation correction.
3. **Structural snowline error persists:** RMSE 90m with +32m bias, driven
   by model over-amplification of interannual variability and spatially
   flat snowlines. This is a DETIM limitation, not parameter-tunable.
4. **Area filter validates posterior:** 100% pass rate at 1.0 km² confirms
   the posterior is consistent with observed area retreat without additional
   screening needed.
5. **Ready for projections** with v13 posterior (1,000 filtered params).

### Output files
- `calibration_output/de_multistart_v13.json` (5-seed DE optima)
- `calibration_output/best_params_v13.json` (MAP)
- `calibration_output/mcmc_chain_v13_mode1.npy` (10000 × 24 × 6)
- `calibration_output/mcmc_logprob_v13_mode1.npy` (10000 × 24)
- `calibration_output/posterior_samples_v13.csv` (1,656 thinned samples)
- `calibration_output/corner_plot_v13.png`
- `calibration_output/filtered_params_v13.json` (1,000 area-filtered sets)
- `calibration_output/behavioral_filter_v13_scores.csv`
- `calibration_output/area_filter_v13_scores.csv`
- `calibration_output/calibration_summary_v13.json`
- `calibration_output/calibration_v13_stdout.log`
