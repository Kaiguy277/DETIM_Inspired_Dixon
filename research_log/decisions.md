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
Dixon), supplemented by on-glacier AWS at ELA site (1078m; D-023, was 804m) for 2024–2025 summers.
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
**[NOTE: D-023 later corrected Dixon AWS elevation to 1078m (ELA site). The
logic of this decision remains valid — the ref_elev should match the merged
climate data's target elevation — but the actual elevation was wrong.]**
**Rationale:** The merged climate file (`dixon_model_climate.csv`) contains
temperatures already lapse-rate adjusted from Nuka SNOTEL (1230m) down to
Dixon AWS elevation (804m; later corrected to 1078m in D-023) — see
`climate.py:merge_climate_data()` line 154–157.
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

**Key finding:** Dixon AWS is **5.10°C colder** than Nuka SNOTEL during summer
overlap (n=256 days).
**[NOTE (D-023): This analysis assumed Dixon at 804m and Nuka at 1230m — BOTH
were wrong. With corrected elevations (Dixon=1078m ELA, Nuka=375m), the 703m
elevation difference at -6.5 to -7.3 C/km fully explains the -5.1°C offset.
There is NO katabatic inversion — the cooling is a normal lapse rate. The
"dampened slope" (0.695) includes real on-glacier boundary layer effects but
the large constant offset is simply elevation.]**

**Quantified bias (original, partially superseded by D-013 and D-023):**
The merged climate data uses -6.5°C/km to adjust Nuka to Dixon elevation,
adding +2.77°C. True relationship is -5.10°C. Net bias:
**+7.87°C too warm** at glacier surface during summer.

**Regression:** T_dixon = 0.695 × T_nuka + (-2.650), R²=0.696
- Slope < 1 → glacier dampens temperature variability
- Relationship varies by month (Aug most dampened: slope=0.39)

**Plan:** Implement monthly statistical transfer in temperature.py, re-calibrate.
See `research_log/project_plan.md` Phase 1 for implementation details.

## D-008: Elevation-Dependent Melt Factor

**Date:** 2026-03-06
**Decision:** Add MF_grad parameter: MF(z) = MF + MF_grad * (z - z_ref).
**Rationale:** A single MF cannot capture the ABL-to-ACC mass balance gradient.
Even with correct temperatures, integrated effects of albedo, wind, humidity,
and cloud cover cause melt efficiency to decrease with elevation. MF_grad adds
one parameter to capture this. Negative MF_grad = less melt at higher elevations.
**Bounds:** [-0.01, 0.0] mm d-1 K-1 per m. Floor at 0.1 mm d-1 K-1.

## D-009: Model Architecture Overhaul — v4

**Date:** 2026-03-06
**Decision:** Comprehensive model update implementing Phases 1-6 of project plan.
**Changes:**
  1. fast_model.py rewritten: statistical temp transfer, MF_grad, daily runoff tracking
  2. config.py: monthly transfer coefficients, stake config, routing/dynamics defaults
  3. glacier_dynamics.py: delta-h parameterization (Huss et al. 2010)
  4. routing.py: parallel linear reservoir discharge model
  5. run_projection.py: future projection framework with peak water analysis
  6. run_calibration_full.py: v4 using raw Nuka input, 8 params
**Parameter set (8):** MF, MF_grad, r_snow, r_ice, internal_lapse, precip_grad,
  precip_corr, T0

## D-010: Winter Katabatic Correction for Temperature Transfer

**Date:** 2026-03-06
**Decision:** Apply reduced katabatic correction for Oct-Apr months in the
Nuka→Dixon temperature transfer, replacing the standard lapse assumption.
**Rationale:** CAL-004 diagnosis (see `cal004_diagnosis.md`) revealed that the
standard lapse transfer for winter months (+2.77°C at 804m) makes October and
November too warm, causing precipitation to fall as rain instead of snow.
The model accumulated only 22% of observed winter balance at ELA/ACC.
This forced precip_corr to 0.5 (compensating for rain damage) and T0 to 0.5°C.

**Winter coefficients changed:**
  - Old (standard lapse): alpha=1.0, beta=+2.77 for Oct-Apr
  - New (reduced katabatic): alpha=0.85, beta=+1.0 for Oct-Apr

**Physical basis:** Katabatic cooling operates year-round because the glacier
surface remains below ambient air temperature even in winter. The correction
is smaller than summer (-1.8°C vs -5.1°C) because the ambient-surface
temperature gradient is smaller when both are cold.

**Expected effect:** More Oct-Nov precipitation falls as snow, allowing
precip_corr and T0 to find physically reasonable values. Winter accumulation
at ELA/ACC should increase dramatically.

**Limitation:** These winter coefficients are estimated, not measured. Year-round
on-glacier temperature sensors should be recommended in the thesis as critical
future work.

## D-011: Wind Redistribution of Snow (Winstral Sx)

**Date:** 2026-03-06
**Decision:** Add spatially distributed wind redistribution of snowfall using
the Winstral et al. (2002) Sx parameter, with prevailing wind from ESE (100°).

**Rationale:** CAL-004/005 showed precip_corr stuck at 0.5 (lower bound) and
the model unable to capture spatial variability in mass balance. Analysis of
22 years of digitized snowlines (9,295 sample points) revealed:
  - Western side of glacier has snowline **100m lower** than eastern side
    (every year, E-W diff +17 to +111m)
  - NW-facing slopes: mean snowline 1061m; S-facing: 1175m
  - Detrended correlation r(easting, Z_anomaly) = +0.59

Combined with regional climatology:
  - Gulf of Alaska storms approach from SSE with E/SE surface winds
  - Synoptic wind during precipitation: ~100° (ESE)
  - Empirical snowline asymmetry confirms ESE wind deposits on W/NW lee side

**Implementation:**
  - `terrain.py`: `compute_wind_exposure()` computes Sx along upwind direction
    (d_max=300m), normalized to [-1,+1] and zero-meaned over glacier
  - `fast_model.py`: `P_cell *= (1 + k_wind * sx_norm[i,j])`
  - New calibration parameter: `k_wind` [0.0, 1.0]
  - Mass-conserving: mean(D_wind) = 1.0 over glacier surface

**Sensitivity test (WY2023, k_wind 0→1):**
  - ABL: -1.56 → -1.62 (more exposed, less snow)
  - ACC: +3.21 → +3.47 (more sheltered, more snow deposited)
  - Glacier-wide: ~+1.30 (nearly unchanged — mass conserving)

**Reference:** Winstral, A., Elder, K., & Davis, R. E. (2002). Spatial snow
modeling of wind-redistributed snow using terrain-based parameters. J.
Hydrometeorol., 3(5), 524-538.

## D-012: Revert to Identity Temperature Transfer

**Date:** 2026-03-06
**Decision:** Remove statistical katabatic temperature transfer (D-007, D-010).
Use raw Nuka SNOTEL temperature at 1230m with a calibrated lapse rate.

**Rationale:** Comprehensive diagnostic of CAL-004/005/006 revealed that the
statistical transfer made on-glacier temperatures too cold for DETIM to generate
observed summer melt:
  - ABL summer mean T = 2.4°C after transfer (vs ~10°C with standard lapse)
  - Required MF > 19 mm/d/K to match ABL summer melt of -5.35 m w.e.
  - Literature MF for ice: 6-12 mm/d/K; for the whole DETIM equation: 2-8
  - With standard lapse: ABL ~10°C → MF ~3.5 (perfectly reasonable)

**Physical explanation:** DETIM was designed as an empirical index model. The
temperature input is not meant to be the literal on-glacier surface temperature
— it's an index that, when multiplied by MF, produces the right melt rate.
The katabatic cooling is real (measured: -5.1°C at ABL, R²=0.70) but is
implicitly absorbed by the MF parameter in the standard DETIM framework.

**Additional changes:**
  1. ref_elev changed from 804m (Dixon AWS) to 1230m (Nuka SNOTEL)
  2. lapse_rate replaces internal_lapse (now from 1230m, not 804m)
  3. Winter balance added as explicit calibration target (W=0.6)
  4. precip_corr lower bound raised from 0.5 to 1.0 (Nuka undercatch)
  5. lapse_rate upper bound widened to -9.0 C/km
  6. DE maxiter increased to 200 for weekend convergence

**Validation with hand-picked params (MF=1.0, pc=3.5, lapse=-6.5):**
  - ABL 2023: -4.46 (obs -4.50) — excellent
  - ACC 2023: +1.43 (obs +0.37) — optimizer has room to improve
  - ELA 2023: -0.85 (obs +0.10) — needs more accumulation at ELA

**The katabatic analysis (D-007) remains valid** for thesis discussion — it
quantifies the real 5°C on-glacier cooling effect and supports the recommendation
for year-round temperature sensors as future work.

## D-013: Nuka SNOTEL Elevation Units Error — 1230 ft, Not 1230 m

**Date:** 2026-03-09
**Decision:** Correct Nuka SNOTEL reference elevation from 1230 m to 375 m
(1230 ft × 0.3048 = 374.9 m). Rebuild model around correct geometry.

**Discovery:** The NRCS website (wcc.sc.egov.usda.gov/nwcc/site?sitenum=1037)
lists Nuka Glacier SNOTEL (site 1037) elevation as "1230" in feet, the standard
unit for all US SNOTEL stations. The value was recorded as 1230 m in
`data_provenance.md` and `config.py`, introducing an 855 m elevation error that
propagated through every calibration run (CAL-001 through CAL-007).

**Impact — this is the root cause of all calibration failures:**
  - All glacier cells were positioned BELOW the reference station instead of
    ABOVE it (ABL at 804m is 429m above Nuka at 375m, not 426m below at 1230m)
  - With lapse applied in the wrong direction, ABL was ~3-4°C too warm
  - Excess warmth → too much melt → optimizer suppressed MF to 1.55
  - Excess warmth → too much rain (not snow) → optimizer inflated precip_corr to 4.5
  - The D-007 "katabatic paradox" (Dixon 5.1°C colder despite being lower) was
    never a paradox — Dixon at 804m IS higher than Nuka at 375m. Expected
    lapse-rate cooling at -5.0 C/km = 2.15°C, plus ~2.95°C of real (modest)
    katabatic cooling = 5.10°C total.
  - D-007 through D-012 were all attempts to work around this geometry error

**Corrected temperature geometry (summer mean Nuka T = 8.0°C, lapse -5.0 C/km):**
| Stake | dz from 375m | T (corrected) | T (v7 wrong) |
|-------|-------------|---------------|--------------|
| ABL (804m) | +429m | 5.9°C | 9.3°C |
| ELA (1078m) | +703m | 4.5°C | 8.5°C |
| ACC (1293m) | +918m | 3.4°C | 7.8°C |

**Changes required:**
  1. `config.py`: SNOTEL_ELEV = 375.0
  2. Lapse rate fixed at -5.0 C/km (remove from calibration), citing Gardner &
     Sharp (2009) ablation-season mean -4.9 C/km, Roth et al. (2023) Juneau
     Icefield calibrated -5.0 C/km
  3. precip_corr bounds tightened to [1.2, 3.0], citing PyGEM cap of 3.0,
     Wolverine Glacier analog of 2.28x
  4. Identity transfer (D-012) remains correct — DETIM uses index temperatures,
     and MF absorbs the ~3°C katabatic effect implicitly (Hock 1999)
  5. The katabatic analysis (D-007) is reinterpreted: the real on-glacier
     cooling is ~3°C (not 8°C), consistent with literature values

**References:**
  - NRCS: https://wcc.sc.egov.usda.gov/nwcc/site?sitenum=1037
  - Gardner & Sharp (2009), J. Climate: Arctic on-glacier lapse rate -4.9 C/km
  - Roth et al. (2023), J. Glaciol.: Juneau Icefield calibrated -5.0 C/km
  - Rounce et al. (2020), PyGEM: precip_corr cap of 3.0

## D-014: Cost Function Restructuring — Inverse-Variance + Geodetic Hard Constraint

**Date:** 2026-03-09
**Decision:** Replace arbitrary-weight cost function with inverse-variance
weighting and a hard geodetic constraint.

**Rationale:** Literature review of OGGM (Zekollari et al. 2023), PyGEM
(Rounce et al. 2020), and Huss et al. (2009) shows that all major glacier
models treat geodetic mass balance as the PRIMARY calibration constraint,
not a minor soft penalty. The v7 cost function gave geodetic weight 0.4 vs
combined stake weight 2.4 (annual=1.0, summer=0.8, winter=0.6), allowing
the optimizer to ignore the 20-year geodetic signal.

Additionally, using all 3 Hugonnet periods (2000-2010, 2010-2020, 2000-2020)
is statistically improper — the 20-year period is derived from the sub-periods
and is not independent. This gave triple weight to the same data.

**Changes:**
  1. Drop 2000-2020 geodetic period; use only 2000-2010 and 2010-2020
  2. Replace weighted sum with inverse-variance (1/σ²) weighting for all
     observations — geodetic uncertainties (0.12-0.22) naturally weight them
     appropriately relative to stake uncertainties (0.10-0.15)
  3. Add geodetic hard penalty: λ=50 for exceeding reported uncertainty bounds

**References:**
  - Zekollari et al. (2023), Ann. Glaciol.: OGGM calibration strategy
  - Rounce et al. (2020), J. Glaciol.: PyGEM Bayesian calibration
  - Zemp et al. (2013), The Cryosphere: reanalysing glacier mass balance

## D-015: Remove Lapse Rate and k_wind from Calibration

**Date:** 2026-03-09
**Decision:** Fix lapse rate at -5.0 C/km and remove k_wind, reducing free
parameters from 9 to 7.

**Lapse rate rationale:** The optimizer consistently exploits lapse rate to
compensate for other model deficiencies. Literature values for maritime
glaciers converge on -4.5 to -5.5 C/km (Gardner & Sharp 2009: -4.9;
Roth et al. 2023 Juneau Icefield: -5.0). Fixing it eliminates a major
source of equifinality with MF and precip parameters.

**k_wind rationale:** CAL-007 converged to k_wind ≈ 0 (effectively off).
The wind redistribution concept (D-011) is physically sound but adds a
parameter that the current observation network cannot constrain. Removing
it reduces dimensionality without information loss. Can be revisited if
snowline validation reveals spatial bias.

**Lapse rate update:** Initially fixed at -5.0 C/km, but with the corrected
elevation (D-013) the optimizer should no longer exploit this parameter.
Re-included with tight literature bounds [-7.0, -4.0] C/km to allow the
model some flexibility while preventing physically unreasonable values.

**Calibrated parameters (8):** MF, MF_grad, r_snow, r_ice, lapse_rate,
precip_grad, precip_corr, T0

## D-016: Use Only 2000-2020 Geodetic Mean + Widen precip_corr

**Date:** 2026-03-09
**Decision:** Revert to single 2000-2020 geodetic constraint and widen
precip_corr upper bound from 3.0 to 4.0.

**Rationale — geodetic sub-periods:**
CAL-008 post-analysis revealed that the two geodetic sub-periods (2000-2010
and 2010-2020) create a contradictory constraint. Nuka SNOTEL shows cooler
summers in 2001-2010 (9.07°C) than 2011-2020 (10.00°C), so the model
produces less melt in the first decade. But Hugonnet shows MORE mass loss
in 2001-2010 (-1.07) than 2010-2020 (-0.81). This is opposite to what
the Nuka forcing predicts, and a single parameter set cannot satisfy both.

Statistical test: the sub-periods are NOT distinguishable (Z=0.88, p>0.30).
The "acceleration" is within reported uncertainty (±0.22-0.23 m w.e./yr).

Solution: use ONLY the 2000-2020 mean (-0.939 ± 0.122 m w.e./yr) for
calibration. It has tighter uncertainty and integrates over the full period.
Sub-periods become validation targets (reported but not optimized against).

**Rationale — precip_corr bound:**
Back-calculation from ELA observed winter balance shows minimum required
precip_corr of 3.01 (WY2023) and 3.16 (WY2024). The 3.0 upper bound in
CAL-008 was slightly too tight — the model could not physically produce
enough snow. With the corrected elevation, higher precip_corr is needed
because on-glacier temperatures are now colder (more rain→snow conversion
efficiency), but total precipitation still needs to be adequate.

New bound [1.2, 4.0] allows the optimizer to reach the physically required
range while staying well below the absurd 4.52 of CAL-007.

**Compatibility check (key finding):**
Extrapolating 2023 stake observations across the glacier hypsometry gives
a glacier-wide balance of -1.07 m w.e., matching the 2000-2010 geodetic
exactly (-1.072). The stakes and geodetic are NOT in conflict — the model
should be able to fit both with a single parameter set.

**Changes:**
  1. Restore 2000-2020 geodetic period as sole geodetic constraint
  2. Drop 2000-2010 and 2010-2020 from calibration (validation only)
  3. Widen precip_corr upper bound from 3.0 to 4.0

## D-017: Bayesian Ensemble Calibration (DE + MCMC)

**Date:** 2026-03-09
**Decision:** Replace single-optimum calibration with a two-phase Bayesian
ensemble approach: differential evolution to find the MAP estimate, then
MCMC sampling to generate a posterior distribution of parameter sets for
projection uncertainty quantification.

**Rationale — why single DE is insufficient for projections:**
CAL-009 demonstrated the core equifinality problem: lapse_rate=-6.83 C/km
with precip_corr=1.20 fits current observations but has compensating errors
that diverge under warming. A single "best" parameter set cannot capture
the structural uncertainty in how warming propagates across the glacier.

For peak water projections under emission scenarios, we need not one parameter
set but a **population of parameter sets** that are all consistent with
observations. The spread in projections across this ensemble represents genuine
uncertainty about the glacier's temperature sensitivity, accumulation rate,
and rain/snow partitioning under future warming.

**Literature precedent:**
  - PyGEM (Rounce et al. 2020, J. Glaciol.): MCMC with PyMC, 10,000 steps,
    informative priors on 2 parameters, ~100-200 posterior samples for projections
  - Rounce et al. (2023, Science): Same approach scaled to 215,000 glaciers
  - Schuster et al. (2023, Ann. Glaciol.): Documented equifinality in TI models;
    recommended ensemble approaches for projection credibility
  - Foreman-Mackey et al. (2013): emcee affine-invariant ensemble sampler

**Method:**

Phase 1 — Differential Evolution (MAP estimate):
  - Find best-fit parameter set as starting point for MCMC
  - Same DE settings as CAL-009 but with reduced parameter space

Phase 2 — MCMC (emcee):
  - 24 walkers initialized in tight ball around DE optimum
  - 10,000 steps per walker (~240,000 evaluations)
  - Log-likelihood: L = -0.5 × Σ((residual/σ)²) with same inverse-variance
    structure as DE cost function
  - Burn-in: first 2,000 steps discarded
  - Thinning: by autocorrelation time for independent samples
  - Convergence: acceptance fraction 0.2-0.5, Gelman-Rubin < 1.1

**Parameter changes from CAL-009:**

1. **Lapse rate fixed at -5.0 C/km** (removed from calibration). This is the
   single most important change — eliminates the lapse/precip equifinality.
   With lapse free, the optimizer exploited it to -6.83 (CAL-009). Literature:
   Gardner & Sharp (2009) -4.9, Roth et al. (2023) -5.0 C/km. For projections,
   the lapse rate determines how warming distributes across the 439-1637m
   elevation range — it MUST be physically correct.

2. **r_ice derived as 2.0 × r_snow** (removed from calibration). Hock (1999)
   Table 4 shows r_ice/r_snow ratios of 1.5-3.0. CAL-009 converged to near-
   equality (1.29 vs 1.34), eliminating the albedo feedback critical for
   projections. Fixed ratio of 2.0 is mid-range of literature.

3. **6 free parameters** (reduced from 8): MF, MF_grad, r_snow, precip_grad,
   precip_corr, T0. Lower dimensionality improves MCMC convergence and reduces
   equifinality.

4. **Priors:**
   - MF: Truncated Normal(5.0, 3.0) on [1, 12] — Braithwaite (2008)
   - T0: Truncated Normal(1.5, 0.5) on [0.5, 3.0] — standard range
   - All others: Uniform within bounds

**Compute estimate:**
  - Phase 1 (DE): ~60 min (fewer params → faster convergence)
  - Phase 2 (MCMC, 8 cores): ~2-4 hours (emcee parallelizes across walkers)
  - Projections (200 samples × 4 scenarios × 80 years): ~4 hours

**Expected output:**
  - ~200-500 independent posterior samples (parameter sets)
  - Corner plot showing parameter correlations and marginal distributions
  - Each sample physically defensible for projections
  - Projection uncertainty envelope on peak water timing

**References:**
  - Rounce, D.R. et al. (2020). J. Glaciol., 66(255), 175-187.
  - Rounce, D.R. et al. (2023). Science, 379(6627), 78-83.
  - Schuster, L. et al. (2023). Ann. Glaciol., 1-16.
  - Foreman-Mackey, D. et al. (2013). PASP, 125(925), 306.
  - Gardner, A.S. & Sharp, M.J. (2009). J. Climate, 22(2), 372-392.
  - Hock, R. (1999). J. Glaciol., 45(149), 101-111.
  - Braithwaite, R.J. (2008). J. Glaciol., 54(185), 349-354.

## D-018: Glacier Dynamics Overhaul — Correct Delta-h + Ice Thickness

**Date:** 2026-03-10
**Decision:** Complete rewrite of `glacier_dynamics.py` to fix three
compounding bugs and add ice thickness tracking for physically-based
glacier retreat.

**Bugs fixed:**
  1. **Wrong size class:** Used small-glacier coefficients (a=-0.30,
     b=0.60, c=0.09) with large-glacier exponent (gamma=6). Dixon at
     ~40 km2 is a *large* glacier (>20 km2 threshold).
  2. **Wrong h_r convention:** Code used z_norm = (z - z_min)/range
     (0=terminus, 1=headwall) but the Huss equation expects h_r =
     (z_max - z)/range (0=headwall, 1=terminus). This produced maximum
     thinning at the headwall instead of the terminus — physically backwards.
  3. **No ice thickness tracking:** Retreat criterion was heuristic
     (single-year dh > 5m in bottom 10% of elevation range). Cells
     losing 4m/yr for 10 years were never removed.

**New implementation:**
  1. All three Huss et al. (2010) size classes with correct coefficients:
     - Large (A > 20 km2): gamma=6, a=-0.02, b=0.12, c=0.00
     - Medium (5 < A < 20): gamma=4, a=-0.05, b=0.19, c=0.01
     - Small (A < 5 km2): gamma=2, a=-0.30, b=0.60, c=0.09
  2. Dynamic size class switching as glacier shrinks (hard switch at
     area thresholds, following OGGM convention).
  3. Ice thickness initialization: Farinotti et al. (2019) consensus
     GeoTIFF if available (RGI60-01.18059), otherwise Bahr et al. (1997)
     V-A scaling (V = 0.0340 * A^1.36, km3/km2) with parabolic
     hypsometric distribution.
  4. Bedrock DEM computed once (surface - thickness); cells deglaciate
     when ice_thickness < 1m (exposed bedrock replaces surface).
  5. Volume-area consistency check at each time step; warning if
     modeled volume deviates > 3x from V-A prediction.
  6. Full tracking: area, volume, mean thickness, size class, V-A ratio,
     cells removed per year.

**Validation (synthetic glacier tests):**
  - V-A ratio = 1.000 at initialization (by construction)
  - At -0.5 m w.e./yr, 4 km2 glacier loses 10% area in 20 years
  - At -1.0 m w.e./yr, 34 km2 glacier transitions large→medium at ~75 yr
  - Terminus cells deglaciate first (correct spatial pattern)

**Files modified:**
  - `dixon_melt/glacier_dynamics.py` — complete rewrite
  - `dixon_melt/config.py` — added DELTAH_PARAMS dict, VA_C, VA_GAMMA, RGI IDs
  - `run_projection.py` — updated for new API (ice thickness, bedrock, volume tracking)

**Data needed:** Farinotti et al. (2019) consensus thickness for Dixon
  (composite_thickness_RGI60-01.zip from ETH Zurich Research Collection,
  DOI: 10.3929/ethz-b-000315707). Until downloaded, V-A scaling fallback
  is used.

**References:**
  - Huss, M. et al. (2010). HESS, 14(5), 815-829.
  - Bahr, D. B. et al. (1997). J. Geophys. Res., 102(B9), 20355-20362.
  - Chen, J. & Ohmura, A. (1990). Ann. Glaciol., 14, 85-89.
  - Farinotti, D. et al. (2019). Nature Geosci., 12, 168-173.
  - Bahr, D. B. et al. (2015). Rev. Geophys., 53, 95-140.

## D-019: CMIP6 Projection Pipeline with Discharge Routing

**Date:** 2026-03-10
**Decision:** Replace placeholder future climate (linear delta method) with
real CMIP6 projections from NASA NEX-GDDP-CMIP6. Wire discharge routing
into projection pipeline. Implement multi-GCM ensemble for uncertainty.

**Climate data — NEX-GDDP-CMIP6:**
  - Source: NASA, hosted on AWS S3 (no authentication)
  - Resolution: 0.25° (~25 km), daily, bias-corrected against observations
  - Scenarios: SSP1-2.6, SSP2-4.5, SSP5-8.5 (SSP3-7.0 not available)
  - Period: 2015-2100 (historical: 1950-2014)
  - Extraction: single pixel nearest to Dixon (59.62°N, 150.88°W)
  - Bias correction: monthly delta method against Nuka SNOTEL 1991-2020
    climatology (additive for T, multiplicative for P)

**GCM ensemble (5 models):**
  1. ACCESS-CM2 (Australian, good Arctic performance)
  2. EC-Earth3 (European, high resolution)
  3. MPI-ESM1-2-HR (German, high resolution)
  4. MRI-ESM2-0 (Japanese, good precip)
  5. NorESM2-MM (Norwegian, high-latitude design)

  Selection rationale: representative subset following Rounce et al. (2023),
  covering multiple modeling centers and good high-latitude performance.

**Discharge routing — wired into projection pipeline:**
  - Parallel linear reservoirs (Hock & Jansson 2005): fast (supraglacial),
    slow (subglacial), groundwater
  - Default parameters from config.py (k_fast=0.3, k_slow=0.05, k_gw=0.01)
  - Output: daily discharge (m3/s), peak daily, mean annual, total annual

**Peak water analysis:**
  - 11-year running mean of ensemble-mean annual discharge
  - Peak year with GCM uncertainty range
  - Computed per scenario

**New files:**
  - `download_cmip6.py` — download + single-pixel extraction from S3
  - `dixon_melt/climate_projections.py` — bias correction, ensemble loading
  - `run_projection.py` — complete rewrite for multi-GCM, multi-SSP ensemble

**Workflow:**
  1. `python download_cmip6.py` — downloads ~5 GCMs × 3 SSPs × 76 years × 2 vars
  2. `python run_projection.py --scenario ssp245` — one scenario
  3. `python run_projection.py --scenario all` — all scenarios with comparison

**References:**
  - Thrasher, B. et al. (2022). NASA NEX-GDDP-CMIP6.
  - Rounce, D. R. et al. (2023). Science, 379(6627), 78-83.
  - Hock, R. & Jansson, P. (2005). In: Anderson & McDonnell (eds),
    Encyclopedia of Hydrological Sciences.
  - Maraun, D. & Widmann, M. (2018). Statistical Downscaling and Bias
    Correction for Climate Research. Cambridge University Press.

## D-020: Posterior Ensemble Projections (Top 250 Parameter Sets)

**Date:** 2026-03-11
**Decision:** Replace single-parameter projections with ensemble projections
using the top 250 performing parameter sets from the MCMC chain, following
Geck (2020) on Eklutna Glacier. This propagates both climate uncertainty
(5 GCMs) and parameter uncertainty (250 param sets) through the projection.

**Method:**
  - Rank all post-burn-in MCMC samples (120,000) by log-probability
  - Select top 250 unique parameter sets (best-performing)
  - Run each (GCM, param_set) pair independently with its own geometry
    evolution trajectory via delta-h
  - Total: 250 × 5 GCMs = 1,250 runs per scenario
  - Aggregate with percentiles (p05, p25, p50, p75, p95) across full ensemble

**Output structure:**
  - Auto-numbered run directories: `projection_output/PROJ-{NNN}_{label}_{date}/`
  - Per-scenario ensemble CSV with percentile bands
  - Per-GCM aggregated CSV (over param samples)
  - Metadata JSON, peak water JSON
  - Plotting: `plot_projection_ensemble.py` and `animate_glacier_retreat.py`

**PROJ-002 Results (top 250, SSP2-4.5 & SSP5-8.5):**
  - SSP2-4.5: Peak water ~WY2043 (8.17 m³/s), 2100 area 18.1 km² (45%)
  - SSP5-8.5: Peak water ~WY2058 (8.54 m³/s), 2100 area 8.6 km² (21%)
  - Parameter uncertainty is relatively small; GCM spread dominates
  - MRI-ESM2-0 is outlier (most conservative retreat)

**Files modified:**
  - `run_projection.py` — complete rewrite: `load_top_param_sets()`,
    `aggregate_ensemble()`, auto-numbered `PROJ-###` output dirs
  - `plot_projection_ensemble.py` — new, 5 plot types with uncertainty bands
  - `animate_glacier_retreat.py` — new, side-by-side MP4/GIF glacier retreat

**References:**
  - Geck, J. (2020). MS Thesis, Alaska Pacific University. (Eklutna Glacier)

## D-021: Snowline Validation (Independent Spatial Check)

**Date:** 2026-03-11
**Decision:** Implement independent validation of DETIM against 22 years
(1999–2024) of digitized snowline observations. These were never used in
calibration, providing a true out-of-sample spatial check.

**Method:**
  - Load observed snowline shapefiles (LineString, UTM 5N) and rasterize
    onto the 100m model grid
  - For each year, run the model from Oct 1 to the snowline observation date
  - Extract modeled snowline as the contour where net balance (accum − melt) = 0
  - Compare: (a) mean snowline elevation (observed vs modeled), (b) net balance
    sampled at observed snowline locations (should be ~0)

**Metrics:**
  - Elevation comparison: obs vs modeled mean snowline altitude per year
  - Balance at observed snowline: mean m w.e. at obs positions (ideal = 0)
  - Spatial overlap: fraction of observed snowline in modeled snow vs ice zones

**Results (MAP parameters, 21 valid years → 19 after D-022 exclusions):**
  - Mean bias: +6 m (near zero — model not systematically biased)
  - RMSE: 189 m
  - MAE: 122 m
  - Correlation: r = 0.52
  - Mean balance at observed snowline: −0.38 m w.e.
  - WY2000 and WY2005 excluded per D-022 (insufficient SNOTEL data)
  - Post-2017 persistent positive bias (~100–175m) suggests model melts
    slightly too aggressively in recent years

**Files added:**
  - `dixon_melt/snowline_validation.py` — validation module
  - `run_snowline_validation.py` — runner script with 3 plot types
  - `calibration_output/snowline_validation.csv` — per-year results
  - `calibration_output/snowline_scatter.png` — obs vs mod scatter
  - `calibration_output/snowline_timeseries.png` — elevation time series
  - `calibration_output/snowline_spatial_examples.png` — spatial maps

**References:**
  - Rabatel, A. et al. (2005). J. Glaciol., 51(172), 539-546.
  - Hock, R. (1999). J. Glaciol., 45(149), 101-111.

## D-022: Exclude Snowline Years with Insufficient SNOTEL Data

**Date:** 2026-03-11
**Decision:** Automatically exclude snowline validation years where >30% of
melt-season (May–Sep) temperature data is missing from Nuka SNOTEL.

**Rationale:** WY2000 and WY2005 showed extreme negative snowline bias
(−600m and −660m) with the model placing the snowline at the glacier
terminus (~430m). Investigation revealed the root cause is massive NaN
gaps in Nuka SNOTEL temperature during the melt season:
  - WY2000: 56 of 153 days missing (37%), including a 53-day streak
    from June 19 to August 10
  - WY2005: 132 of 153 days missing (86%), with two streaks spanning
    nearly all of May through August

The validation code (D-021) replaced NaN temperatures with 0°C before
running the model. This effectively eliminated melt on those days,
producing unrealistically high SWE and snowlines at the glacier terminus.
Including these years inflated RMSE and degraded the correlation.

**Threshold:** 30% of May–Sep temperatures missing. This catches WY2000
(37%) and WY2005 (86%) while retaining years like WY2003 (21%, gap in
late September after melt season) that validate well despite some missing
data.

**Implementation:** Added a NaN fraction check in
`snowline_validation.py:validate_snowline_year()`. Years exceeding the
threshold return `'bad_climate'` and are logged as skipped.

**Effect on validation statistics (expected):**
  - n: 21 → 19 years
  - RMSE, MAE should decrease substantially
  - Correlation should improve (2000 and 2005 were major outliers)

**Alternatives considered:**
  - Climatological gap-filling (daily DOY means): More data-preserving
    but introduces synthetic forcing. Could be revisited for thesis
    sensitivity analysis.
  - Hardcoded exclusion list: Less principled; the threshold approach
    is automatic and self-documenting.

**Files modified:**
  - `dixon_melt/snowline_validation.py` — added melt-season NaN check

---

## D-023: Correct Dixon AWS Elevation from 804m to 1078m

**Date:** 2026-03-12
**Status:** CONFIRMED

**Problem:** The Dixon on-glacier AWS was recorded at 804 m (ABL stake
elevation) in config.py, climate.py, fast_model.py, and all research log
files. This is incorrect — the weather station was deployed at the ELA
stake site (1078 m), not the ABL site.

**Evidence:** Temperature comparison of Dixon AWS (2024–2025 summer data)
vs Nuka SNOTEL (375 m) shows a mean daily offset of -4.6°C (2024) to
-5.6°C (2025). At a -6.5 °C/km lapse rate:
  - **1078 m predicts -4.6°C offset** — exact match (2024)
  - 804 m predicts -2.8°C offset — 1.8°C too warm, even before katabatic

Monthly breakdown (2024 summer, Dixon minus Nuka):
  May: -3.6°C, Jun: -4.7°C, Jul: -5.2°C, Aug: -5.0°C, Sep: -4.7°C

Cross-validated against Middle Fork Bradley SNOTEL (701 m, 16 km away):
Dixon is 4.2°C colder than MFB despite only 377 m elevation difference,
again consistent with 1078 m + standard lapse, not 804 m.

**Parallel to D-013:** Same class of error — incorrect elevation metadata.
D-013 corrected Nuka from 1230 m → 375 m (feet vs meters). D-023 corrects
Dixon AWS from 804 m → 1078 m (ABL vs ELA site).

**Impact on model:** The Dixon AWS is currently used only for summer
gap-filling (climate.py:merge_climate_data) with limited overlap days.
The fast_model.py ref_elev parameter (used in the statistical temperature
transfer) was already set from calibration, not from DIXON_AWS_ELEV.
However, correcting this is essential for:
  1. Accurate temperature merge when Dixon AWS data is available
  2. Correct interpretation of on-glacier precipitation observations
  3. Future multi-station gap-filling using Dixon AWS

**Files modified:**
  - `dixon_melt/config.py` — DIXON_AWS_ELEV: 804.0 → 1078.0
  - `dixon_melt/climate.py` — DIXON_AWS_ELEV: 804.0 → 1078.0, updated comments
  - `dixon_melt/fast_model.py` — updated ref_elev comments
  - `research_log/data_provenance.md` — corrected AWS location/elevation
  - `research_log/decisions.md` — this entry

---

## D-024: Multi-Station Climate Analysis — Dixon AWS as Ground Truth

**Date:** 2026-03-12
**Status:** ANALYSIS COMPLETE

**Motivation:** The model predicts conditions on the glacier, so all station
transfer relationships should be evaluated against Dixon AWS (1078m, ELA site),
not against each other. Previous analysis compared SNOTEL stations to Nuka;
this reframes everything around Dixon as ground truth.

**Data sources evaluated (7 total):**

| Station | Site | Elev | Dist | Record | T corr vs Dixon | T RMSE |
|---------|------|------|------|--------|-----------------|--------|
| Dixon AWS | — | 1078m | 0km | 2024–25 summers | — | — |
| Nuka Glacier SNOTEL | 1037 | 375m | 10km | 1990– | r=0.863 | 5.3°C |
| Mid Fork Bradley SNOTEL | 1064 | 701m | 16km | 1990– | **r=0.877** | **4.8°C** |
| McNeil Canyon SNOTEL | 1003 | 411m | 24km | 1986– | r=0.872 | 5.9°C |
| Anchor River Div SNOTEL | 1062 | 503m | 34km | 1980– | r=0.851 | 5.9°C |
| Lower Kachemak Ck SNOTEL | 1265 | 597m | 13km | 2015– | r=0.869 | 5.0°C |
| Kachemak Creek SNOTEL | 1063 | 503m | 14km | 2003–2019 | — | — |

**Key findings — Temperature:**

1. **MFB is the best single predictor of Dixon temperature** (r=0.877,
   RMSE=4.8°C). Closest in elevation (+377m) and same mountain group.
2. All transfer slopes are 0.3–0.8 — the glacier dampens temperature
   variability (real boundary layer physics, not an artifact).
3. **August is the hardest month** to predict: slopes drop to 0.3–0.5,
   r² drops to 0.15–0.37. Peak melt season = maximum glacier-surface
   decoupling from free-air temperature.
4. May and September have the best transfers (r² ~0.55–0.60).
5. A simple lapse rate consistently overpredicts Dixon temperature —
   regression transfer is required.

**Monthly transfer coefficients (T_dixon = slope × T_station + intercept):**

MFB → Dixon:
  May: 0.745x - 2.84  (r²=0.60)
  Jun: 0.559x - 1.30  (r²=0.75)
  Jul: 0.591x - 1.11  (r²=0.52)
  Aug: 0.318x + 1.53  (r²=0.26)
  Sep: 0.453x + 0.19  (r²=0.58)

Nuka → Dixon:
  May: 0.666x - 2.81  (r²=0.57)
  Jun: 0.534x - 1.27  (r²=0.50)
  Jul: 0.611x - 1.55  (r²=0.37)
  Aug: 0.391x + 0.56  (r²=0.14)
  Sep: 0.770x - 2.98  (r²=0.57)

**Key findings — Precipitation:**

1. **Nuka has the best precip correlation with Dixon** (r=0.75 on wet
   days), despite 703m elevation difference — same orographic regime.
2. Dixon receives ~0.78× Nuka precip but ~1.7× MFB precip.
3. Event detection hit rate: Nuka and MFB both ~80% (when it rains on
   Dixon, those stations also record rain).
4. Precip ratios vary seasonally (peaks Aug/Sep).

**Implications for gap-filling strategy:**
- **Temperature:** Use MFB as primary gap-fill source (best RMSE), with
  McNeil as backup. Apply monthly regression transfer, not simple lapse.
- **Precipitation:** Use Nuka as primary (best correlation with Dixon),
  with MFB ratio-scaling for WY2020 gap.
- The existing fast_model.py monthly transfer (alpha/beta) approach is
  validated — but coefficients should be refit against the full Dixon
  record, not just the pre-D-023 analysis.

**Caveat:** Dixon AWS covers summer only (May–Sep/Oct). Winter transfer
relationships are extrapolated — we cannot validate them. The dampening
effect (slope < 1) may be weaker or absent in winter when the glacier
surface is snow-covered and katabatic winds are reduced.

**Scripts:** `plot_dixon_vs_all.py`, `analyze_snotel_stations.py`
**Plots:** `calibration_output/dixon_vs_all_*.png`


---

## D-025: Multi-Station Climate Gap-Filling Pipeline

**Date:** 2026-03-12

**Decision:** Replace `ffill().fillna(0)` gap handling with a multi-station
cascade that transfers nearby SNOTEL observations into Nuka-equivalent values
using monthly regression coefficients.

**Problem:**
Nuka SNOTEL has severe data gaps that poisoned calibration:
- Temperature: WY2000 (56d), WY2001 (282d), WY2002 (102d), WY2005 (157d)
- Precipitation: WY2020 (192d, 1,019mm of real precip lost)
- `ffill().fillna(0)` set summer T to 0°C, killing melt in early years
- Model compensated by cranking up MF, over-melting in clean years

**Method:**
1. Compute monthly reverse regressions: T_nuka = slope × T_other + intercept
   for each fill station, using all overlapping valid days.
2. Compute monthly precipitation ratios: P_nuka / P_mfb on wet-day pairs.
3. Temperature cascade: Nuka → MFB → McNeil → Anchor → Kachemak → Lower Kach
   → linear interp (≤3d) → DOY climatology.
4. Precipitation cascade: Nuka → MFB (monthly ratio) → DOY climatology.
5. Output: `data/climate/dixon_gap_filled_climate.csv` — zero NaN, 9,862 days.

**Results:**
- 91.3% of days use original Nuka data (target was >90%)
- Fill stations: MFB 6.0%, McNeil 1.8%, interp 0.4%, anchor 0.3%, clim 0.1%
- WY2005 Jun-Aug mean T: 8.5°C (was ~0°C with old approach)
- WY2020 total precip: 2,307mm (was ~1,176mm with old approach)
- Transfer RMSE: 1-3°C depending on station and month

**Alternatives considered:**
- ERA5 reanalysis: coarser, introduces different biases
- Single-station (MFB only): doesn't cover all gap years
- Dixon AWS for forcing: summer-only, too short, wrong purpose (validation)

**Downstream changes:**
- `run_calibration_v10.py`: loads gap-filled CSV, asserts no NaN
- `run_snowline_validation.py`: loads gap-filled CSV
- `run_projection.py`: gap-filled CSV for bias correction reference
- All plotting scripts: updated to use gap-filled CSV

**Next steps:** Recalibrate (CAL-011) with gap-filled climate → expect
MF to decrease (less compensation needed) and geodetic sub-period mismatch
to shrink.

**Scripts:** `compute_transfer_coefficients.py`, `plot_climate_gap_fill_diagnostics.py`
**Plots:** `calibration_output/climate_gap_fill_diagnostics.png`,
  `calibration_output/climate_gap_fill_by_wy.png`,
  `calibration_output/transfer_validation_scatter.png`

---

## D-026: Recalibrate with Gap-Filled Climate (CAL-011)

**Date:** 2026-03-12
**Decision:** Re-run the CAL-010 Bayesian ensemble calibration (DE + MCMC)
with the multi-station gap-filled climate data from D-025, keeping the same
6 free parameters, bounds, priors, and fixed parameters.

**Rationale:**
CAL-010 was run with the old `ffill().fillna(0)` climate preprocessing,
which introduced severe errors in gap years (WY2000, WY2001, WY2005, WY2020).
D-025 replaced this with a 5-station cascade gap-fill producing zero-NaN
forcing data. The calibration must be re-run before any results can be used
in the thesis.

**What changed from CAL-010:**
1. Climate input: `dixon_gap_filled_climate.csv` (D-025) — zero NaN, 91.3% Nuka
2. Coverage filter removed: the `t_cov < 0.85` filter in `build_calibration_targets()`
   excluded years with poor temperature coverage. With gap-filled data (zero NaN),
   all 20 geodetic water years (WY2001–2020) now contribute to calibration.
3. Previously poisoned years now provide real information:
   - WY2000: summer T was ~3°C (fillna), now ~11°C
   - WY2001: 282-day gap filled at ~2°C, now realistic seasonal cycle
   - WY2005: summer T was -7.7°C → ZERO melt, now 8.5°C mean
   - WY2020: precip was 1,176mm (gap), now 2,307mm

**What stayed the same:**
- 6 free parameters: MF, MF_grad, r_snow, precip_grad, precip_corr, T0
- All bounds unchanged
- Priors: MF~TN(5,3), T0~TN(1.5,0.5)
- Fixed: lapse_rate=-5.0 C/km, r_ice=2×r_snow, k_wind=0
- DE config: 200 maxiter, 15 popsize, seed 42
- MCMC config: 24 walkers, 10,000 steps, 2,000 min burn-in
- Geodetic target: 2000-2020 mean only (sub-periods for validation)

**Expected outcomes:**
1. Geodetic sub-period mismatch should shrink (2000-2010 was most affected)
2. MF may decrease (less compensation needed for suppressed melt years)
3. r_snow may come off upper bound (melt budget spread across more real years)
4. T0 may move up from ~0°C (rain/snow partition now matters in gap years)
5. Cost function value may decrease (less internal contradiction in targets)

**Alternatives considered:**
- Adjusting bounds or priors: deferred — want to see the data effect first
- Freeing lapse rate: would re-introduce equifinality seen in CAL-009
- Freeing r_ice/r_snow ratio: revisit if r_snow still hits upper bound

**Script:** `run_calibration_v11.py`
**Output prefix:** v11

**Post-mortem:** CAL-011 killed at DE step 28/200 (cost 7.23) — superseded
by CAL-012 (D-027) before completion.

---

## D-027: Multi-Seed Calibration to Address Posterior Multimodality (CAL-012)

**Date:** 2026-03-12
**Decision:** Replace single-seed DE + single MCMC chain with multi-seed DE
(5 seeds) + separate MCMC chains from each distinct mode, then combine
posterior samples. This is "Option A" from Rounce et al. (2020), adapted.

**Problem:**
CAL-010 and CAL-011 used a single DE seed (42) to find one MAP estimate, then
initialized all MCMC walkers tightly around it (0.1% spread). If the posterior
has multiple modes — distinct parameter combinations that fit the data
similarly well — this approach would:
1. Only find whichever mode the DE seed happens to land in
2. Never explore alternative modes during MCMC (walkers can't cross
   low-probability valleys in 10,000 steps)
3. Underestimate parameter uncertainty for projections

The concern is real for DETIM: known trade-offs (MF vs r_snow, precip_corr
vs precip_grad) create ridges in parameter space that could harbor distinct
local optima.

**Method:**
1. **Phase 1 — Multi-seed DE:** Run DE with 5 seeds [42, 123, 456, 789, 2024].
   Each seed initializes a different Latin hypercube population, exploring the
   cost surface from different starting regions. ~50 min per seed.
2. **Phase 1.5 — Clustering:** Normalize DE optima to [0,1] by parameter range,
   compute pairwise Chebyshev distance, hierarchically cluster with 10% threshold.
   Two optima within 10% of each parameter's range → same mode.
3. **Phase 2 — Per-mode MCMC:** Run separate emcee chains (24 walkers × 10,000
   steps) from each distinct mode. Each chain explores its local posterior.
4. **Phase 3 — Combine:** Concatenate posterior samples from all chains with
   equal weighting (conservative; BIC-weighting is an alternative if modes
   have very different likelihoods).

**Possible outcomes:**
- **All 5 seeds → 1 mode:** Posterior is unimodal. Combined posterior ≈
  single-chain posterior but with higher confidence. ~12 hrs total.
- **2-3 modes:** Real multimodality. Combined posterior captures the full
  uncertainty. Each mode gets documented with its physical interpretation.
  ~20-28 hrs total.
- **5 distinct modes:** Extreme equifinality. May indicate the model is
  under-constrained. Would motivate tighter priors or additional constraints.
  ~44 hrs total.

**What stayed the same (vs CAL-011):**
- Gap-filled climate (D-025), all 20 geodetic years
- 6 free parameters, same bounds, priors, fixed params
- DE config per seed (200 maxiter, 15 popsize)
- MCMC config per chain (24 walkers, 10,000 steps)

**Script:** `run_calibration_v12.py`
**Output prefix:** v12
