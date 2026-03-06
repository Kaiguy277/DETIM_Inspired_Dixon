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
