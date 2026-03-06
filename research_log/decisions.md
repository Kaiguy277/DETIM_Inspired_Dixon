# Decision Log — Dixon Glacier DETIM

Numbered record of modeling decisions. Each entry captures what was decided,
why, what alternatives were considered, and any caveats.

---

## D-001: Model Selection — DETIM Method 2 (Hock 1999)

**Date:** Prior sessions (pre-2026-03-06)
**Decision:** Use Distributed Enhanced Temperature Index Model, Method 2:
  M = (MF + r_snow/ice * I_pot) * T, where T > 0
**Rationale:** Balances physical realism (radiation + temperature) against data
availability. Dixon Glacier lacks the full energy balance data needed for DEBAM.
Method 2 adds spatially distributed potential clear-sky radiation to a basic
degree-day model, capturing topographic shading and aspect effects.
**Alternatives considered:**
- Classical degree-day (Method 1): Too simple for a 40 km² glacier with
  significant topographic variability (439–1637m).
- Full energy balance (DEBAM): Requires wind, humidity, albedo, cloud cover
  at grid scale — not available.
**Reference:** Hock, R. (1999). A distributed temperature-index ice- and
snowmelt model including potential direct solar radiation. J. Glaciol., 45(149).

## D-002: Climate Data Source — Nuka SNOTEL + On-Glacier AWS

**Date:** Prior sessions
**Decision:** Primary forcing from Nuka SNOTEL (site 1037, 1230m, ~20 km from
Dixon), supplemented by on-glacier AWS at ABL stake (804m) for 2024–2025 summers.
**Rationale:** Nuka SNOTEL is the nearest long-record station with daily T and P
going back to 1990. On-glacier AWS provides ground truth for lapse rate validation
during summer field seasons.
**Known issues:**
- SNOTEL precipitation is cumulative and prone to undercatch (esp. wind-affected snow).
- No SWE pillow at Nuka — cannot directly validate winter accumulation.
- 20 km distance introduces spatial uncertainty in precipitation patterns.
- Temperature lapse rate from SNOTEL to glacier assumed constant (calibrated).

## D-003: Calibration Targets — Stakes + Geodetic

**Date:** Prior sessions
**Decision:** Multi-objective calibration against:
  1. Stake mass balance at 3 elevations (ABL 804m, ELA 1078m, ACC 1293m), 2023–2025
  2. Geodetic mass balance from Hugonnet et al. (2021), 2000–2020
**Rationale:** Stakes provide point-scale seasonal resolution (annual + summer).
Geodetic provides glacier-wide decadal constraint. Together they constrain both
the spatial pattern and long-term magnitude of mass balance.
**Uncertainties:**
- Stake obs: ±0.12 m w.e. (measured), ±0.30 m w.e. (2025 estimated)
- Geodetic: ±0.20–0.22 m w.e./yr (Hugonnet et al.)

## D-004: Numba JIT Compilation for Calibration Speed

**Date:** Prior sessions
**Decision:** Implement core simulation loop as a single Numba @njit(parallel=True)
function (FastDETIM) for calibration, separate from the Pandas-based orchestrator
(DETIMModel) used for analysis.
**Rationale:** Differential evolution requires ~10,000+ objective evaluations.
Each evaluation runs 365-day simulations on a 578×233 grid. JIT compilation
reduces per-evaluation time from seconds to ~300 ms.
**Trade-off:** Two code paths for the same physics — must keep them in sync.

## D-005: Fix SWE Double-Counting in Calibration v2

**Date:** 2026-03-06
**Decision:** Three fixes to calibration objective function:
  1. Annual runs (Oct 1 start): Set initial SWE = 0. Snowpack accumulates
     naturally from daily precipitation during Oct–Apr.
  2. Summer runs (~May start): Use observed winter balance at ELA as initial SWE.
  3. Remove snow_redist parameter (was multiplicatively redundant with precip_corr).
**Rationale:** v1 calibration initialized annual runs with observed winter SWE
AND accumulated snow from daily precipitation — double-counting winter snowpack.
The optimizer compensated by pushing MF to lower bound (1.0), r_snow to ~0,
and precip_corr/snow_redist/T0 to upper bounds. 5 of 8 parameters hit bounds;
final cost = 15.0 (very poor).
**Evidence:**
- v1 best params: MF=1.0 (bound), r_snow≈0 (bound), precip_corr=4.0 (bound),
  T0=3.0 (bound), snow_redist=2.5 (bound)
- Pattern: maximize accumulation + suppress melt = compensating for double-count
**Files modified:** `run_calibration_full.py` (v1 backed up as `_v1.py`)
**Parameter count:** 8 → 7 (snow_redist removed, precip_corr bounds widened to [1,6])

## D-006: Fix Temperature Reference Elevation Mismatch

**Date:** 2026-03-06
**Decision:** Change model station_elev from 1230m (SNOTEL) to 804m (Dixon AWS)
to match the merged climate data's actual reference elevation.
**Rationale:** The merged climate file (`dixon_model_climate.csv`) contains
temperatures already lapse-rate adjusted from Nuka SNOTEL (1230m) down to
Dixon AWS elevation (804m) — see `climate.py:merge_climate_data()` line 154–157.
But `FastDETIM` was initialized with `config.SNOTEL_ELEV = 1230m`, causing the
model to apply the lapse rate from the wrong base elevation.

**Impact:** Every grid cell was +2.8°C too warm (assuming -6.5°C/km lapse rate
over the 426m discrepancy). This caused:
- Massive over-melting, forcing MF → lower bound (1.0)
- Far too little snow accumulation (rain instead), forcing precip_corr → upper bound
- Both CAL-001 and CAL-002 affected — explains why cost stayed at ~15 despite fixes
- The lapse_rate parameter partially compensated but couldn't fix a constant offset

**Fix:** Set `CLIMATE_REF_ELEV = 804.0` in config.py and pass it (not SNOTEL_ELEV)
to FastDETIM. This is a one-line change in `run_calibration_full.py`.
**Evidence:** v2 calibration mid-run still shows MF≈1.0, precip_corr≈6.0, cost≈15.87

## D-007: Nuka→Dixon Temperature Transfer Is Invalid

**Date:** 2026-03-06
**Decision:** Replace simple lapse rate temperature transfer with statistical
downscaling based on empirical Nuka↔Dixon relationship.
**Analysis:** See `research_log/nuka_dixon_temperature_analysis.md` for full details.

**Key finding:** Dixon AWS (804m, on-glacier) is **5.10°C colder** than Nuka
SNOTEL (1230m, off-glacier) during summer overlap (n=256 days). Dixon is colder
100% of the time despite being 426m lower in elevation. This is katabatic
cooling — cold glacier surface air draining downslope creates a persistent
temperature inversion.

**Quantified bias:** The merged climate data uses -6.5°C/km to adjust Nuka to
Dixon elevation, adding +2.77°C. True relationship is -5.10°C. Net bias:
**+7.87°C too warm** at glacier surface during summer. This is the actual root
cause of all calibration failures (not D-005 or D-006, though both were also bugs).

**Regression:** T_dixon = 0.695 × T_nuka + (-2.650), R²=0.696
- Slope < 1 → glacier dampens temperature variability
- Relationship varies by month (Aug most dampened: slope=0.39)

**Plan:** Implement monthly statistical transfer in temperature.py, re-calibrate.
See `research_log/project_plan.md` Phase 1 for implementation details.
