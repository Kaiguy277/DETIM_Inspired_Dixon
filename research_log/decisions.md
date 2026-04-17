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

---

## D-028: Multi-Objective Calibration with Snowline in MCMC Likelihood

**Date:** 2026-03-18 (designed), 2026-03-19–23 (executed as CAL-013)

**Decision:** Add snowline elevation as a chi-squared term in the MCMC
log-likelihood, and apply glacier area evolution as a post-hoc behavioral
filter. This replaces the original plan of using snowlines as a post-hoc
filter (which proved ineffective — see analysis below).

**Pipeline:**
```
Phase 1: Multi-seed DE (stakes + geodetic + snowline in objective)
Phase 2: MCMC (stakes + geodetic + snowline in likelihood)
Phase 3: Combine posteriors
Phase 4: Post-hoc area evolution filter (top 1000 → RMSE ≤ 1.0 km²)
```

**Why snowlines moved INTO the likelihood (not post-hoc):**

Initial testing with the D-028 behavioral filter approach (top 1000 from
CAL-012, hard snowline RMSE threshold) revealed that snowline RMSE had
**zero discriminating power** as a post-hoc filter:
- All 1000 param sets scored RMSE 88–96m (std = 1.6m, range = 8m)
- Snowline RMSE uncorrelated with log-probability (r = 0.146)
- Systematic +30m positive bias (model snowline too high)
- At threshold ≤50m: 0/1000 pass; at ≤90m: 77/1000 pass
- No parameter combination within the CAL-012 posterior could improve
  snowline fit — the posterior was too tightly constrained by stakes+geodetic

This meant the stakes+geodetic objective was not "aware" of snowline
information, and the posterior it produced happened to be in a region of
parameter space with ~90m snowline RMSE regardless of parameter values.

By putting snowlines in the likelihood, the MCMC sampler explores regions
that jointly satisfy all three constraints, rather than calibrating on two
and hoping the third comes along.

**Structural snowline limitations identified:**
- Observed snowlines have high spatial spread (std 24–69m within a year)
  but the model produces near-contour-line snowlines (std 6–22m)
- Model over-amplifies interannual variability (std 129m vs obs 63m)
- Recent years (2019–2024) show persistent +88 to +178m bias
- These are structural DETIM limitations, not parameter-tunable

**Snowline uncertainty:** sigma = 75m (fixed), combining observed spatial
spread (~50–80m), model grid resolution (100m), and temporal mismatch.
Consistent with Rabatel et al. (2005).

**Area filter design:**
- 6 checkpoints at 5-year intervals (2000, 2005, 2010, 2015, 2020, 2025)
- Manually digitized outlines from historical satellite imagery
- Areas: 40.11, 40.11, 39.83, 39.26, 38.59, 38.34 km² (1.77 km² total retreat)
- RMSE threshold: 1.0 km² (tightened from original 1.5 km²)
- Area filter is post-hoc (too expensive for in-MCMC: 25 WY × delta-h per eval)

**Result:** All 1000 posterior samples passed the 1.0 km² area filter,
confirming the snowline-informed posterior is already consistent with
observed area retreat. The multi-objective calibration works.

**Rationale:**
- Snowline = spatial ELA constraint, directly informing the accumulation/
  ablation gradient the model must reproduce
- Area = integrated temporal constraint validating cumulative mass loss
  + delta-h geometry evolution over 25 years
- Follows Gabbi et al. (2012) multi-criteria philosophy but implements
  snowline as a likelihood term rather than post-hoc filter
- References: Rabatel et al. (2005), Beven & Binley (1992)

**Alternatives considered:**
- Post-hoc snowline filter (rejected: no discriminating power within
  the CAL-012 posterior, as demonstrated)
- Composite scoring (rejected: less principled than in-likelihood)
- Re-enabling k_wind to address spatial snowline structure (deferred:
  CAL-007 showed k_wind→0, would need new physics justification)

**Implementation:**
- `run_calibration_v13.py` — full DE+MCMC with snowline in likelihood +
  post-hoc area filter, with `--resume` and checkpoint support
- `dixon_melt/behavioral_filter.py` — area scoring module
- `run_behavioral_filter.py` — standalone filter runner (for reuse)
- `data/glacier_outlines/digitized/` — 6 manually digitized outlines
- `run_projection.py` updated with `--filtered-params` flag

## D-029: Validation Suite (Sub-period Geodetic, Stake Predictive Check, Sensitivity)

**Date:** 2026-04-08
**Decision:** Implement three independent validation analyses using the v13
posterior, without recalibration.

**Validation 1 — Sub-period geodetic comparison:**
Compare modeled glacier-wide balance to Hugonnet sub-periods (2000-2010,
2010-2020) that were withheld from calibration (D-016). Run 200 posterior
parameter sets through each decade independently.

Results:
| Period     | Observed (m w.e./yr) | Modeled median | Bias    | Within unc? |
|------------|----------------------|----------------|---------|-------------|
| 2000-2020  | -0.939 ± 0.122 (cal) | -0.765        | +0.174  | No          |
| 2000-2010  | -1.072 ± 0.225 (val) | -0.244        | +0.828  | No          |
| 2010-2020  | -0.806 ± 0.202 (val) | -1.287        | -0.481  | No          |

Interpretation: Model reverses the sub-period trend — underestimates mass
loss 2000-2010, overestimates 2010-2020. This is consistent with D-016:
Nuka SNOTEL shows cooler summers in 2001-2010 (9.07°C) vs 2011-2020
(10.00°C), so the model produces less melt in the first decade. But
Hugonnet shows MORE mass loss 2000-2010 than 2010-2020. The contradiction
is in the forcing, not the model — likely reflecting gap-filled climate
quality in early years (WY2001 77% T missing, WY2005 43%).

**Validation 2 — Posterior predictive check by year:**
Evaluate 200 posterior parameter sets against each stake year independently
to identify outliers.

Results (measured observations only):
| Year  | Site | Obs (m w.e.) | Mod median | Residual |
|-------|------|-------------|------------|----------|
| WY2023 | ABL | -4.50       | -4.12      | +0.38    |
| WY2023 | ACC | +0.37       | +0.42      | +0.05    |
| WY2023 | ELA | +0.10       | -1.31      | -1.41    |
| WY2024 | ABL | -2.63       | -4.24      | -1.61    |
| WY2024 | ACC | +1.46       | +0.21      | -1.25    |
| WY2024 | ELA | +0.10       | -1.42      | -1.52    |

Overall RMSE: 1.20 m w.e. (measured only, n=6). WY2024 is a clear outlier
— the model over-predicts melt at all three sites. WY2023 fits ABL and ACC
well but misses ELA by -1.4 m w.e. The ELA site may have a systematic
issue (both years show ~-1.4 to -1.5 residual), possibly related to
local accumulation effects not captured by the lapse-based precipitation
distribution.

**Validation 3 — Sensitivity of fixed parameters:**
Perturb lapse rate (-4.0 to -6.5 °C/km) and r_ice/r_snow ratio (1.5 to
3.0) with MAP params held fixed. Report geodetic balance and stake RMSE.

Results — lapse rate:
| λ (°C/km) | Geodetic mod | Bias    | Stake RMSE |
|-----------|-------------|---------|------------|
| -4.0      | -1.631      | -0.692  | 1.800      |
| -4.5      | -1.216      | -0.277  | 1.497      |
| -5.0      | -0.817      | +0.122  | 1.227      |
| -5.5      | -0.434      | +0.505  | 1.005      |
| -6.0      | -0.063      | +0.876  | 0.850      |
| -6.5      | +0.296      | +1.235  | 0.781      |

Results — r_ice/r_snow:
| Ratio | Geodetic mod | Bias    | Stake RMSE |
|-------|-------------|---------|------------|
| 1.50  | -0.773      | +0.166  | 1.188      |
| 2.00  | -0.817      | +0.122  | 1.227      |
| 3.00  | -0.906      | +0.033  | 1.318      |

Key finding: Lapse rate sensitivity is ~10× larger than r_ice/r_snow.
Geodetic bias swings 1.9 m w.e./yr across the lapse range vs 0.13 for
the ratio. The -5.0 °C/km choice sits near the minimum geodetic bias,
confirming it is well-centered within the literature range.

**Rationale for not recalibrating lapse rate:**
Despite high sensitivity, freeing the lapse rate would re-introduce the
equifinality documented in CAL-009 (D-017): lapse_rate=-6.83 with
precip_corr=1.20 fits current observations via compensating errors that
diverge under warming. With only 3 years of stakes and 20 years of geodetic,
the observation network cannot independently constrain both lapse rate
and precipitation correction. Literature convergence on -5.0 °C/km for
maritime Alaskan glaciers (Gardner & Sharp 2009, Roth et al. 2023) provides
a stronger constraint than the calibration data.

**Implementation:**
- `run_validation.py` — all three analyses in one script (~1.6 min runtime)
- Output in `validation_output/` (3 CSVs)
- Methods draft §3.6 updated (replaced TODO with full methodology text)

## D-030: Lapse Rate Sensitivity Projections

**Date:** 2026-04-08
**Decision:** Run projections at three lapse rates (-4.5, -5.0, -5.5 °C/km)
to bracket the structural uncertainty from the fixed lapse rate choice.

**Rationale:** D-029 showed lapse rate is the dominant fixed-parameter
sensitivity. Rather than recalibrating (which re-introduces equifinality),
we run scenario-based sensitivity projections: the same v13 posterior
params at each lapse rate, for both SSP2-4.5 and SSP5-8.5. This shows
readers the projection envelope attributable to lapse rate uncertainty.

**Design:**
- Lapse rates: -4.5, -5.0, -5.5 °C/km (literature range, Gardner & Sharp
  2009; Roth et al. 2023)
- Param sets: 250 (subsampled from 1000 posterior, matching baseline PROJ-009/011)
- GCMs: all 5 (ACCESS-CM2, EC-Earth3, MPI-ESM1-2-HR, MRI-ESM2-0, NorESM2-MM)
- Scenarios: SSP2-4.5, SSP5-8.5
- Total: 3 × 2 × 250 × 5 = 7,500 simulations (~1.5 hours)

**Alternatives considered:**
- Recalibrate at each lapse rate (rejected: re-introduces equifinality,
  ~120 hr compute, and not standard practice for fixed-parameter sensitivity)
- Full 1000-param ensemble at each lapse rate (rejected: unnecessary,
  250 matches baseline projections and captures parameter uncertainty)
- Single MAP param at each lapse rate (rejected: loses parameter uncertainty)

**Implementation:**
- `run_lapse_sensitivity_projections.py` — wrapper around run_projection.py
- Output: 6 projection runs in `projection_output/PROJ-*_lapse*`
- Summary CSV in `validation_output/lapse_sensitivity_projections.csv`

## D-031: ELA Stake Bias — Wind Redistribution Representativity

**Date:** 2026-04-09
**Decision:** Accept the persistent -1.4 m w.e. bias at the ELA stake
(1078 m) as a measurement representativity issue, not a calibration failure.
Document rather than recalibrate.

**Evidence — the bias is spatial, not temporal:**
- ELA residual: -1.41 (WY2023), -1.52 (WY2024) — nearly identical both years
- ABL residual: +0.38 (WY2023), same elevation band on main trunk → good fit
- ACC residual: +0.05 (WY2023) → excellent fit
- The model predicts -1.3 m w.e. as the *average* across all 814 glacier cells
  at 1028-1128 m (20.3% of glacier area). The observation is from ONE location
  on the southern branch.

**Physical explanation — wind redistribution to southern branch:**
- Digitized snowlines show systematically lower snowlines (more accumulation)
  on the southern branch where the ELA stake is located
- Wind exposure (Sx): 70% of glacier cells are in sheltered (deposition)
  zones, 30% exposed (erosion). The southern branch is a deposition zone.
- The ELA stake site receives preferential wind-loaded accumulation that is
  not representative of the elevation-band average
- A constant precip_grad cannot capture this spatial variability

**Why recalibration won't help:**
- k_wind was tested in CAL-007 and converged to ~0 — the observation network
  (3 stakes + geodetic) cannot constrain a wind redistribution parameter
- Forcing the model to match +0.1 m w.e. at ELA would require over-
  accumulating at ALL cells in that elevation band, breaking the geodetic
  fit (-0.939 ± 0.122) and the ABL/ACC stakes
- The model's glacier-wide balance is within 2σ of geodetic (bias +0.17).
  The ELA bias (+1.4 × ~20% area ≈ +0.28 m w.e.) is consistent with the
  geodetic bias being partly caused by the same unmodeled wind effect.

**Why this is acceptable for projections:**
- Projections use glacier-wide metrics (area, volume, discharge), not point
  balances. The glacier-wide fit is constrained by the geodetic observation.
- The lapse rate sensitivity bracket (D-030: -4.5 to -5.5 °C/km) spans a
  wider projection uncertainty (9 km² by 2100) than the ELA bias would cause.
- ABL and ACC — which ARE representative of their elevation bands — validate
  well in WY2023 (0.38, 0.05 m w.e. residuals).

**WY2024 forcing limitation (separate issue):**
WY2024 shows large residuals at all sites (not just ELA). Root cause: Nuka
SNOTEL recorded 912 mm winter precip (similar to WY2023's 864 mm), but
observed winter balance at Dixon was dramatically higher (ABL: 0.85 → 1.93,
+127%). The off-glacier forcing station missed a local accumulation event.
This is a forcing data limitation, not a model deficiency. The precipitation
gradient also flattened from 38%/100m (WY2023) to 11%/100m (WY2024),
confirming the interannual variability that a single precip_grad cannot
capture.

**Alternatives considered:**
- Increase ELA uncertainty to ~0.5 m w.e. and recalibrate (deferred: would
  improve formal statistics but not change the physical model. Current
  calibration already weights ELA correctly given its stated uncertainty.)
- Re-enable k_wind with snowlines as constraint (rejected: snowline
  validation showed model spatial std 6-22m vs observed 24-69m — the model
  cannot resolve the spatial structure that wind creates)
- Exclude ELA from calibration entirely (rejected: still provides useful
  gradient constraint even if biased; removing it would lose information)

**References:**
- Geck et al. (2021) documented similar spatial representativity issues
  at Eklutna, noting snowline over-prediction at end of season
- Hock (1999): DETIM distributes precipitation by elevation only;
  wind redistribution requires explicit parameterization

---

## D-032: IceBoost v2.0 Ice Thickness Cross-Check

**Date:** 2026-04-13

**Context:** The projection pipeline uses Farinotti et al. (2019) thickness
(`data/ice_thickness/RGI60-01.18059_thickness.tif`, 25 m, EPSG:32605) for
initial ice volume and Δh-parameterization retreat. Farinotti is a consensus
of 5 models, ±30% typical error. Maffezzoli et al. (2025, GMD)'s IceBoost v2.0
(XGBoost+CatBoost ensemble, GlaThiDa-trained) reports ~30% RMSE improvement
over Farinotti globally. Zenodo deposit 17724512 publishes pre-computed
per-glacier thickness rasters — downloaded RGI62_rgi1.zip (396 MB) and
extracted `RGI60-01.18059.tif` (100 m, 5 bands: thickness, thickness_err,
jensen_gap, h_wgs84, n_geoid) into `data/ice_thickness/iceboost/`.

**Comparison (see `compare_iceboost_farinotti.py` and plots in
`data/ice_thickness/iceboost/comparison/`):**

| Metric              | Farinotti 2019 | IceBoost v2.0        |
|---------------------|----------------|----------------------|
| Resolution          | 25 m           | 100 m                |
| Mean thickness      | 161 m          | 219 m                |
| Max thickness       | 415 m          | 501 m                |
| Glacier area        | 42.8 km²       | 39.9 km² (meta)      |
| Ice volume          | 6.90 km³       | 9.07 ± 1.55 km³      |

Pixel-wise (100 m common grid, n=4,281):
- IceBoost − Farinotti: mean **+59 m**, median +51 m, RMS 94 m
- Pearson r = 0.75
- IceBoost volume is **+37% larger** than Farinotti on the common mask
  (within IceBoost's reported ±17% error bar)

**Elevation-banded bias (IceBoost thicker at every band, worst in upper glacier):**
- 800–900 m: essentially equal (−2 m)
- 1000–1100 m: +47 m
- 1200–1300 m: **+125 m** (near ELA / accumulation zone, n=650)
- 1300–1500 m: +83 to +108 m

**Interpretation:**
- Both products are modelled (no in-situ GPR at Dixon), so neither is ground
  truth. The 37% divergence is consistent with Farinotti's own stated error.
- The spatial pattern — agreement in the low ablation zone, large positive
  IceBoost bias in the upper basin — matches published findings that
  Farinotti under-estimates thickness in mass-balance-dominated accumulation
  zones and over-estimates in steep margins.
- **Implication for this thesis:** initial volume affects how long the
  glacier survives under each SSP, not when meltwater peaks.
  A +37% initial volume would push simulated disappearance dates later
  by roughly +37% of the remaining lifetime (order: ~20-30 years for RCP 8.5,
  ~100+ years for RCP 2.6). Peak meltwater timing is nearly unchanged.

**Decision:** Keep Farinotti 2019 as the primary input for this thesis to
preserve consistency with the calibrated Δh-parameterization and published
Alaska volume budgets. Treat IceBoost as an independent upper-bound
sensitivity check. Add one appendix-level projection run that initialises
with IceBoost thickness (scaled 1.37× globally, or pixel-remapped) and
report the divergence in disappearance date and cumulative runoff. This
is a single additional calibration-independent run, not a recalibration.

**Next steps:**
- (deferred) Add a `--thickness-source iceboost` flag to `run_projection.py`
  that swaps the thickness raster at initialisation.
- (deferred) Report volume trajectory spread with both products in the
  thesis appendix.

**Files:**
- `data/ice_thickness/iceboost/RGI60-01.18059.tif` (IceBoost raster)
- `data/ice_thickness/iceboost/comparison/iceboost_vs_farinotti.png`
- `compare_iceboost_farinotti.py`
- Zenodo: https://doi.org/10.5281/zenodo.17724512
- Paper: Maffezzoli et al., GMD 18, 2545 (2025)

---

## D-033: North-Branch-Only Snowline Comparison
**Date:** 2026-04-14
**Status:** Implemented (diagnostic; not in calibration likelihood)

**Motivation:** Advisor meeting (Granola notes, ref [[1]](https://notes.granola.ai/d/d58629ca-f663-4cc6-af28-79711979b29f))
flagged that whole-glacier snowline comparison is confounded by the high
cross-glacier spatial variability DETIM cannot reproduce (D-028 structural
finding: observed spatial std 24–69 m, modelled 6–22 m). Advisor suggested
breaking the glacier into sub-branches (north / middle / south). As a first
cut we compare only the NORTH BRANCH — the upper NE tributary — where the
observed snowline is spatially more coherent.

**Definition (revised 2026-04-15, 2D mask with X extended west to 621000):**
- Dixon's aspect is NW; a Y-only cut bleeds into the central-upper glacier.
  Revised mask uses BOTH a northing and easting threshold:
  north branch = glacier cells with UTM 5N Y > 6615000 m AND X > 621000 m.
- X threshold chosen after two iterations: initial X=622000 dropped the
  ELA-entry zone (15.7% mask, r=0.16); extending west to X=621000 keeps
  the NE tributary saddle while still excluding central-body snowlines
  (which cluster near x ≈ 619000–620000).
- Mask covers 898/4011 glacier cells (22.4 %) — essentially the
  accumulation zone and ELA region of the NE tributary.
- Both observed snowline rasterisation and modelled B=0 boundary cells
  are filtered to this identical mask before computing mean elevation.

**Results (revised 2D mask X=621000, MAP params, CAL-013, 100 m grid):**
- n = 18 years with both obs and modelled boundary inside the mask.
  Skipped: 2000, 2009, 2012, 2014 (no observed line in branch).
- Mean bias: +17 m (modelled higher than observed)
- RMSE: 85 m
- MAE:  73 m
- Correlation r = 0.51 — intermediate between the Y-only (0.70) and
  tight-2D (0.16) sensitivity bounds. Informative: the diagnostic
  depends on where you draw the box, which is itself a finding.
- Temporal pattern preserved: pre-2017 mostly negative bias (−14 to −123 m);
  2017-onwards strongly positive (+12 to +176 m). 2019–2024 all ≥ +71 m.

**Mask-definition sensitivity (report alongside bias):**
| Mask | % glacier | n | bias | RMSE | r |
|------|-----------|---|------|------|---|
| Y > 6615000 only             | 53.2 % | 19 | +17 m | 88 m | 0.70 |
| Y > 6615000 AND X > 621000   | 22.4 % | 18 | +17 m | 85 m | 0.51 |
| Y > 6615000 AND X > 622000   | 15.7 % | 15 | +26 m | 86 m | 0.16 |

The bias is remarkably robust across the three masks (+17 to +26 m); RMSE
is also stable (85–88 m). Correlation is sensitive to the mask because the
elevation range of the observed line shrinks as the mask tightens.

---

### Rev.3 — 2026-04-15: Manually-digitized branch polygons

Bounding-box masks abandoned in favour of manually-digitized branch polygons
(Dixon's NW aspect makes orthogonal cuts awkward). Polygons at
`data/glacier_outlines/branches/dixon_{north,middle,south}_branch.shp`;
middle built as `glacier − (north ∪ south)` to guarantee non-overlap.

Runner: `run_snowline_branches.py` (supersedes `run_snowline_north_branch.py`).
Snowlines are effectively split at branch boundaries via raster intersection —
each line pixel is attributed to exactly one branch by `(line_raster & branch_mask)`.

**Per-branch areas (total 40.11 km², union = RGI7 outline):**
- North:  11.38 km² (28.4 %)
- Middle:  8.52 km² (21.2 %)
- South:  20.21 km² (50.4 %)

**Results (MAP params CAL-013, 100 m grid):**
| Branch | n | bias | RMSE | MAE | r |
|--------|---|------|------|-----|---|
| North  | 16 | +19.3 m | 86.6 m | 73.3 m | 0.57 |
| Middle |  5 | −65.3 m |123.8 m | 91.2 m | 0.41 |
| South  | 22 | +37.5 m | 91.6 m | 71.4 m | 0.80 |

**Findings:**
- South branch has every year represented (observed lines always draw through
  it) and the strongest interannual signal (r=0.80). This is now the cleanest
  test of the model's snowline reproduction.
- North branch: r=0.57, intermediate dynamic range. Bias +19 m, RMSE 87 m —
  consistent with the bounding-box rev.2 result (+17 m / 85 m), confirming
  the bounding-box was a reasonable approximation of the hand-digitized branch.
- Middle branch: only 5 years have a digitized line passing through it — the
  digitizer usually didn't draw through the middle cirque. The −65 m mean bias
  and 124 m RMSE are dominated by 2000 (−254 m) and 2012 (−67 m). Too few
  points for a robust summary; flag as a digitization-coverage issue rather
  than a model finding.
- 2020 gives near-identical bias on north (+178) and south (+177) — the
  warm-year over-prediction is glacier-wide, not branch-specific.

**Files:**
- `run_snowline_branches.py` — main analysis
- `data/glacier_outlines/branches/*.shp` — the three digitized polygons
- `calibration_output/snowline_branches.csv` — 66 rows (22 yr × 3 branches)
- `calibration_output/snowline_branches_summary.json`
- `calibration_output/snowline_branches_{scatter,timeseries,bias}.png`
- `_workbench_snowline_north/` — interactive workbench (3-branch view)

**Interpretation (revised):**
- The restricted 2D mask isolates the NE tributary cleanly. Mean bias
  (+26 m) and RMSE (86 m) remain on the order of whole-glacier figures,
  so the branch split does not by itself reveal a radically different
  error structure — the recent-warming positive-bias drift is the
  dominant signal on this tributary as it is glacier-wide.
- The r=0.16 correlation on the revised mask should not be over-interpreted:
  obs elevations cluster in a narrow 1021–1185 m band on the tip (obs σ
  across years ≈ 49 m), so even well-behaved model error (σ ≈ 84 m)
  swamps interannual signal. The time-series plot and bias bar chart
  are more informative than r for this mask.
- Two years (2003, 2016) have obs line present in the mask but zero
  modelled boundary cells — the modelled net balance is entirely positive
  or entirely negative on the NE tributary at the observation date.
  This is a qualitative disagreement worth flagging: the model puts the
  snowline outside the NE-arm box on those dates while observations show
  it crossing the box.

**Scope:** Diagnostic only — NOT added to the calibration likelihood. The
CAL-013 posterior already uses whole-glacier snowline in the likelihood
(D-028). Adding the branch split would require rerunning the multi-objective
calibration and is deferred pending discussion with the advisor.

**Files:**
- `run_snowline_north_branch.py` — standalone runner
- `calibration_output/snowline_north_branch.csv` — per-year obs/mod/bias
- `calibration_output/snowline_north_branch_summary.json` — aggregate stats
- `calibration_output/snowline_north_branch_scatter.png`
- `calibration_output/snowline_north_branch_timeseries.png`

**Next steps:**
- (deferred) Repeat for middle / south branches and compare bias patterns.
- (deferred) Discuss with advisor whether to fold branch-resolved snowline
  residuals into a reweighted likelihood for CAL-014.

## D-034: Free Lapse Rate in Calibration (CAL-014)

**Date:** 2026-04-14
**Decision:** Stop fixing the lapse rate at -5.0 °C km⁻¹. Include it as a
7th calibrated parameter in CAL-014, with truncated-normal prior
N(μ=-4.5, σ=1.0) on bounds [-6.5, -2.0] °C km⁻¹.

**Rationale:**

Post-audit literature review (`litreview/literature_review_2026-04-14.md`,
2026-04-14) found that our fixed value of -5.0 is NOT a consensus choice:

- **Geck et al. (2021)** on Eklutna Glacier (our advisor's paper, verified
  directly from local PDF p. 913): *"The temperature lapse rate among the
  best parameter sets ranged from -0.6 to -0.2 °C (100 m)⁻¹ with a mean
  of -0.3 °C (100 m)⁻¹ and a mode of -0.2 °C (100 m)⁻¹."*
  That is -2 to -6 °C km⁻¹, mean -3, mode -2. Geck **calibrated** lapse
  rate rather than fixing it, and got substantially shallower values than
  our -5.0.
- **Schuster, Rounce & Maussion (2023, Ann. Glaciol.,
  DOI:10.1017/aog.2023.57)** verified from local PDF p. 295: constant
  lapse rate reference is **-6.5 K km⁻¹** (OGGM default), with an
  alternative of monthly-variable lapse rates derived from ERA5 pressure
  levels. *"Neither their constant nor variable approach uses -5.0"*.
- **Petersen, Beven, Klok, Haberkorn & Brock (2013, Ann. Glaciol.,
  DOI:10.3189/2013aog63a477)** verified from PDF: calibrated a constant
  lapse rate of -3.2 °C km⁻¹ on Haut Glacier d'Arolla — much shallower
  than our -5.0.
- **Gardner & Sharp (2009, Ann. Glaciol.,
  DOI:10.3189/172756409787769663)** verified from PDF: showed that melt
  factor (MF) silently compensates for lapse-rate bias — which is exactly
  the symptom we observe (our calibrated MF=7.30 is at the high end of
  Geck's mode 5.75-6.00).

**Evidence of compensation in our CAL-013:**
- MF posterior median 7.30 [7.06, 7.58] is high relative to literature
  (Hock 2003 range 1.5-11.6, Braithwaite 2008 typical 3-7)
- Geck (2021) mode MF = 5.75-6.00
- Trüssel et al. (2015) Yakutat: MF calibrated much lower
- The elevated MF suggests the fixed -5.0 lapse is too steep, producing
  too-cold on-glacier temperatures that the optimizer compensates for
  by inflating MF.

**Prior choice rationale:**
- Mean -4.5 °C km⁻¹: centered between Geck's mean (-3) and OGGM default (-6.5)
- Sigma 1.0 °C km⁻¹: allows ±1σ of [-5.5, -3.5], covering literature range
- Truncated at [-6.5, -2.0]: literature extremes

**Why NOT follow Geck exactly and use -3.0 fixed:**
- Dixon is not Eklutna — different hypsometry, precipitation regime
- Different data constrains different values
- Better to let the data speak via calibration than hard-code a value
  from a neighboring (but different) glacier

**Alternatives considered:**
- Fix at -5.0 (current approach): rejected — not defensible after lit review
- Fix at -3.0 (Geck's mean): rejected — site-specific, shouldn't be
  assumed to transfer
- Monthly variable from ERA5 (Schuster 2023 option): deferred — requires
  ERA5 download and significant refactor; free-scalar is a reasonable
  first step
- Follow Gardner & Sharp (2009) "seasonal" rates: deferred — requires
  sub-annual stake data we don't have

**Implementation:**
- Add `lapse_rate` to `PARAM_NAMES` in `run_calibration_v14.py`
- Bounds: [-6.5e-3, -2.0e-3] (°C/m internally)
- Prior: truncated normal mean -4.5e-3, sigma 1.0e-3
- Remove `FIXED_LAPSE_RATE` constant; add as calibrated

**Risk (equifinality):**
- CAL-009 with free lapse went to -6.83 (extreme) with precip_corr=1.20
  (low), both at/near bounds — physically unrealistic
- CAL-014 mitigations:
  1. Tighter lapse bounds [-6.5, -2.0] (was [-7.0, -3.0])
  2. Informative truncated-normal prior (was uniform)
  3. Multi-seed DE (5 seeds) to detect multimodality
  4. 25 stake obs + geodetic + snowlines in likelihood (we had fewer
     constraints in CAL-009)
  5. Post-hoc area filter

**Literature References (directly quoted from verified PDFs in `papers_verified/`):**

- **Geck et al. (2021)** J. Glaciol. — Geck_2021_Eklutna.pdf, p. 913:
  *"The temperature lapse rate among the best parameter sets ranged from
  -0.6 to -0.2 °C (100 m)⁻¹ with a mean of -0.3 °C (100 m)⁻¹ and a mode of
  -0.2 °C (100 m)⁻¹."*
  → -2 to -6 °C/km, mean -3, mode -2. Eklutna was CALIBRATED, not fixed.

- **Gardner et al. (2009)** J. Climate — Gardner_2009_Arctic_lapse_JClimate.pdf,
  p. 4288 (§4b):
  *"All other mean summer and winter lapse rates lay within the ranges
  4.9° ± 0.4°C km⁻¹ and 3.2° ± 0.5°C km⁻¹, respectively."*
  → Canadian Arctic glaciers. Summer (ablation) -4.9; winter -3.2; annual ~-4.
  Paper argues for VARIABLE rather than fixed rates (Abstract, p. 4281).

- **Schuster et al. (2023)** Ann. Glaciol. — Schuster_2023_TI_calibration.pdf,
  p. 295: OGGM reference constant value is -6.5 K/km (MALR); alternative is
  monthly variable from ERA5.

- **Petersen et al. (2013)** Ann. Glaciol. — Petersen_2013_constant_lapse.pdf:
  calibrated -3.2 °C/km on Haut Glacier d'Arolla.

- **Gardner & Sharp (2009)** Ann. Glaciol. (DOI:10.3189/172756409787769663)
  — Gardner_Sharp_2009_sensitivity.pdf: shows MF silently compensates for
  lapse rate bias in degree-day modeling.

- **Trüssel et al. (2015)** J. Glaciol. — Trussel_2015_Yakutat.pdf: Yakutat
  Glacier DETIM application, Alaska maritime.

**Prior choice (N(-4.5e-3, 1.0e-3)) spans:**
- Midway between Geck's annual mean (-3) and Gardner's summer (-5)
- Consistent with Gardner's implied annual mean (~-4 °C/km)
- Bounds [-6.5, -2.0] capture full literature range (OGGM MALR to Geck mode)


## D-035: Decouple r_ice from r_snow in Calibration (CAL-014)

**Date:** 2026-04-14
**Decision:** Stop deriving r_ice = 2.0 × r_snow. Calibrate r_ice as an
independent 8th parameter with truncated-normal prior N(μ=0.004, σ=0.002)
on bounds [0.02e-3, 10.0e-3] mm m² W⁻¹ d⁻¹ K⁻¹.

**Rationale:**

Post-audit literature review revealed our fixed ratio of 2.0 is NOT the
consensus:

- **Geck et al. (2021)** verified from PDF (p. 914, Fig. 6 caption):
  r_ice = 0.0414 and r_snow = 0.0098, giving ratio = **4.22**. Geck
  calibrated both independently. Our claimed "ratio of 2.0 follows Geck's
  approach" was incorrect — Geck does not use a fixed ratio.
- **Trüssel et al. (2015)** verified from PDF: calibrated both r_ice
  and r_snow independently; reported ratio ~1.83 for Yakutat Glacier.
- **Huss & Hock (2015)** verified from PDF Section 3.1.2: uses
  classical degree-day model with separate f_snow and f_ice factors,
  NOT a radiation-index model. Our earlier claim that they fix ratio
  at 2.0 was wrong.
- **Sjursen et al. (2023) J. Glaciol., DOI:10.1017/jog.2023.62**:
  Bayesian parameter estimation treats MF_snow and MF_ice as
  independent parameters.

**Physics rationale:**
- Snow albedo ~0.7 (fresh) to ~0.5 (aged)
- Ice albedo ~0.3 (clean) to ~0.1 (debris-covered)
- The ratio of absorbed shortwave radiation is 2-7× higher for ice
- Fixing ratio at 2.0 is too conservative — likely underestimates
  albedo feedback
- Under warming, exposed ice fraction grows → ratio matters more for
  projections than for current-climate fit (which stays dominantly
  snow-covered)

**Albedo feedback argument (critical for projections):**
- The ONLY part of the model that differentiates snow from ice melt is
  this ratio. If ratio is fixed artificially low, the albedo feedback
  (exposed ice melts faster as firn retreats) is dampened.
- Projections under warming increasingly depend on bare-ice physics
- Sjursen (2023) showed that separate calibration of snow and ice DDFs
  matters for uncertainty envelope of projections

**Prior choice rationale:**
- Mean 0.004 mm m² W⁻¹ d⁻¹ K⁻¹: approximately 2× our current r_snow
  MAP, matching current default but allowing flexibility
- Sigma 0.002: permits ratio range ~1.5-4 based on r_snow posterior
- Upper bound 10e-3: Geck's upper bound (0.0414 in his units) converted

**Unit conversion check (user should verify with advisor):**
Our units: mm m² W⁻¹ d⁻¹ K⁻¹
Geck's units: m² mm d⁻¹ °C⁻¹
These should be equivalent (W⁻¹ d⁻¹ vs d⁻¹ with implicit W/m² = 1)
but dimensional analysis should be confirmed before committing posterior
to projection runs.

**Alternatives considered:**
- Keep ratio fixed at 2.0 (current): rejected after lit review — not
  supported by closest analog (Geck Eklutna)
- Fix ratio at Geck's 4.22: rejected — site-specific, shouldn't transfer
- Use separate degree-day factors (MF_snow, MF_ice) without radiation:
  rejected — DETIM Method 2 with radiation is our chosen framework

**Risk (equifinality):**
- r_snow, r_ice, MF all influence summer melt → potential 3-way trade-off
- Mitigations:
  1. Informative priors on all three (from Hock 1999 literature ranges)
  2. Snowlines in likelihood provide spatial constraint on snow vs ice
     melt distinction (snowline elevation depends on ratio)
  3. Multi-seed DE for mode detection

**Implementation:**
- Add `r_ice` to `PARAM_NAMES` in `run_calibration_v14.py`
- Bounds: [0.02e-3, 10.0e-3]
- Prior: truncated normal mean 4.0e-3, sigma 2.0e-3
- Remove `FIXED_RICE_RATIO` constant; r_ice no longer derived

**Literature References (directly quoted from verified PDFs in `papers_verified/`):**

- **Geck et al. (2021)** J. Glaciol. — Geck_2021_Eklutna.pdf, p. 914
  (Fig. 6 caption): *"γ = −0.2°C (100 m)⁻¹, fm = 5.5 mm °C⁻¹ d⁻¹,
  **r_ice = 0.0414**, **r_snow = 0.0098** m² mm d⁻¹ °C⁻¹, pcor = 15%
  and pgrad = 25% (100 m)⁻¹"*
  → Geck's best-fit r_ice/r_snow = 0.0414/0.0098 = **4.22**. He
  calibrated both parameters independently.

- **Hock (1999)** J. Glaciol. — Hock_1999_DETIM.pdf, p. 106 Table 1:
  Storglaciären best-fit values:
  - Model 2: r_ice = 0.8×10⁻³, r_snow = 0.6×10⁻³ → ratio = **1.33**
  - Model 3: r_ice = 1.0×10⁻³, r_snow = 0.7×10⁻³ → ratio = **1.43**
  → **Hock's actual calibrated values give ratio ~1.4, NOT 2.0.**
  → Previously-claimed "Hock Table 4 range 1.5-3.0" was fabricated.
  → Table 3 DDF (not radiation factor) values: *"tend to vary from
  2 to 7 mm d⁻¹ °C⁻¹ over snow and 5 to 11 mm d⁻¹ °C⁻¹ over ice
  surfaces"* → DDF ratio 1.5-2.5, still not 3.0.

- **Rounce et al. (2020)** PyGEM J. Glaciol. — Rounce_2020_PyGEM.pdf,
  p. 176: *"the degree-day factor of snow is assumed to be **70% of
  the degree-day factor of ice**"*
  → f_ice/f_snow = 1/0.7 = **1.43**, NOT 2.0. PyGEM fixes this ratio
  but at 1.43, not 2.0.

- **Trüssel et al. (2015)** J. Glaciol. — Trussel_2015_Yakutat.pdf:
  calibrated r_ice and r_snow independently; reported ratio ~1.83
  for Yakutat Glacier.

- **Huss & Hock (2015)** Front. Earth Sci. — huss_hock_2015.pdf, §3.1.2:
  uses classical degree-day model with separate f_snow and f_ice
  factors (NOT a radiation-index model — ratio claim does not apply).

- **Sjursen et al. (2023)** J. Glaciol. — Sjursen_2023_Bayesian_mass_balance.pdf:
  Bayesian calibration with independent MF_snow and MF_ice.

**CORRECTED understanding of literature ratios:**
Previously claimed *"Hock Table 4 range 1.5-3.0, our 2.0 is mid-range"*
was not supported by Hock 1999 itself. Actual values:
- Hock (1999) Storglaciären: 1.33-1.43 (from Table 1, Models 2-3)
- Rounce (2020) PyGEM: 1.43 (fixed assumption)
- Geck (2021) Eklutna: 4.22 (calibrated)
- Trüssel (2015) Yakutat: ~1.83 (calibrated)

Our chosen prior TN(4.0e-3, 2.0e-3) centered at ratio ~2-3 given
typical r_snow ~1-2e-3. This encompasses both Hock/Rounce (~1.4) and
Geck (~4.2) endpoints.

**Next steps:**
- Implement `run_calibration_v14.py` with both D-034 and D-035 changes
- 8 free parameters total (was 6)
- Same DE + MCMC structure as CAL-013 (emcee, 5 seeds, multi-objective)
- Expected runtime: ~30-35 hours (slightly longer than CAL-013 due to
  extra params)
- Register as CAL-014 in `calibration_runs.md`


## D-036: Branch-Resolved Snowline Likelihood (CAL-014)

**Date:** 2026-04-14
**Decision:** Replace whole-glacier snowline likelihood term with per-branch
(north / middle / south) residuals using manually-digitized branch
polygons. Also revised per-parameter Options B after literature prior
validation:

1. **Keep r_ice/r_snow RATIO fixed** (at 2.5, up from 2.0) rather than
   freeing it (supersedes earlier D-035 which freed it).
2. **Tighten lapse_rate prior σ from 1.0e-3 to 0.6e-3** (D-034 revised).
3. **Raise σ_snowline from 75m to 90m** (match measured structural RMSE
   from CAL-013).
4. **Branch-resolved snowline likelihood**: ~43 residuals across 3
   branches vs 22 whole-glacier.

**Motivation:**

Second-round literature review (`litreview/cal014_prior_validation_2026-04-14.md`)
identified three serious issues with the originally-proposed 8-parameter
CAL-014:

a) **r_ice upper bound excluded Geck's range.** Geck 2021 best-fit
   r_ice = 0.0414 in same units as ours. Our proposed upper bound of
   10e-3 would have capped r_ice at 24% of Geck's best value. Either
   raise bounds or (preferred) use fixed ratio.

b) **Over-parameterization risk.** Only Geck 2021 among verified
   maritime Alaska precedents frees both lapse AND r_ice, and Geck
   explicitly acknowledges *"the model is overparameterized, it is not
   possible to determine a single best model run"* (p. 913). McNeil
   2020 (Taku/Lemon Creek, Juneau Icefield), Ziemen 2016 (Juneau),
   and O'Neel 2019 (Wolverine) all FIX the lapse rate. Rounce 2020
   PyGEM, Sjursen 2023, Huss & Hock 2015 all FIX the r_ice/r_snow
   ratio and calibrate only r_snow.

c) **Lapse σ=1.0e-3 on bounds [-6.5, -2.0] was too loose.** Sjursen
   2023 (p. 833, verified quote): *"precarious due to compensating
   effects between Tcorr and [MF]"*. With σ=1.0, the prior has
   meaningful mass across nearly the full bound range, reopening the
   equifinality loop CAL-013 closed.

**Resolution (Option B from lit review):**

7 free parameters (MF, MF_grad, r_snow, precip_grad, precip_corr, T0,
lapse_rate). r_ice derived as 2.5 × r_snow (fixed ratio). This:
- Tests the lapse hypothesis (is our CAL-013 MF=7.30 a compensation?)
- Avoids Geck's acknowledged over-param
- Uses mid-range literature ratio (between PyGEM 1.43 and Geck 4.22)

**Branch-resolved snowline implementation:**

Per-branch snowline analysis already performed in D-033 using manually-
digitized polygons in `data/glacier_outlines/branches/`:
- North branch (11.4 km²): 16 years, bias +19m, RMSE 87m, r=0.57
- Middle branch (8.5 km²): 5 years, bias −65m, RMSE 124m, r=0.41
- South branch (20.2 km²): 22 years, bias +38m, RMSE 92m, r=0.80

Adding these as branch-specific likelihood terms:
- Increases snowline constraints from 22 → 43 residuals
- Captures spatial variability (addresses ELA bias from D-031)
- Uses σ_snowline = 90m uniformly (all branches have similar RMSE)

**Alternatives considered:**

- Option A (6 params, fix lapse at -5.0): rejected — lapse hypothesis
  worth testing; the prior validation showed -5.0 wasn't consensus anyway
- Option C (8 params, free both lapse and r_ice): rejected — repeats
  Geck's overparameterization warning
- Branch-specific σ_snowline: deferred — branches have similar RMSEs
  (87-124m), uniform 90m is good enough

**Risk mitigations:**

1. Multi-seed DE (5 seeds) for mode detection
2. Posterior correlation matrix diagnostics
3. Prior-vs-posterior width check per parameter (Sjursen 2023 line 452:
   if posterior σ ≈ prior σ, parameter is unidentified → drop it)
4. Gelman-Rubin R̂ across chains; require < 1.1
5. Fall-back plan: if lapse_rate posterior is indistinguishable from
   prior, fix it at CAL-013 value and rerun as 6-param CAL-014a

**Literature References (directly quoted from verified PDFs):**

- Sjursen et al. (2023) J. Glaciol. — Sjursen_2023_Bayesian_mass_balance.pdf,
  p. 833: *"precarious due to compensating effects between Tcorr and
  [MF]"*; p. 775: *"Increasing the number of unknown parameters... makes
  equifinality worse"*.
- Geck et al. (2021) J. Glaciol. — Geck_2021_Eklutna.pdf, p. 913:
  acknowledges overparameterization *"it is not possible to determine
  a single best model run"*.
- McNeil et al. (2020) J. Glaciol. — McNeil_2020_Taku_LemonCreek.pdf:
  fixes lapse at -5.0 for Taku/Lemon Creek (Juneau Icefield).
- Rounce et al. (2020) PyGEM — Rounce_2020_PyGEM.pdf, p. 176:
  *"the degree-day factor of snow is assumed to be 70% of the degree-
  day factor of ice"* (fixed ratio 1.43).
- Racoviteanu et al. (2019) — Racoviteanu_2019_automated_snowline.pdf:
  snowline altitude uncertainties of ±70m per observation.

**Implementation:**

- `run_calibration_v14.py` — updated for 7 params, ratio 2.5, branch-resolved snowlines
- `RICE_RATIO = 2.5` constant (replaces the old FIXED_RICE_RATIO=2.0)
- `SIGMA_SNOWLINE = 90.0` (up from 75.0)
- New `_load_branch_masks()` function reads branch polygons
- `build_snowline_targets()` now produces branch-resolved targets
- `compute_chi2_terms()` loops over (year, branch) pairs, running model
  once per year (efficient) and extracting per-branch modeled snowlines
- Expected MCMC runtime: ~25-28 hours (7 params × 32 walkers × 10,000
  steps × 5 seeds; slightly longer than CAL-013 due to more snowline
  terms but fewer params than originally-proposed 8-param CAL-014)


## D-037: CAL-015 — Free r_ice Independently, Widen Bounds

**Date:** 2026-04-17
**Decision:** Run CAL-015 with 8 free parameters (adding independent r_ice),
widened bounds on parameters that hit limits in CAL-014 (lapse_rate,
r_snow, precip_corr), and fresh literature-based priors (not informed by
CAL-014 posterior).

**Motivation:**

1. **CAL-014 posterior hit bounds on two parameters:**
   - `lapse_rate`: pegged at prior upper bound of -2.0e-3 (posterior
     median -2.2e-3). Data wants shallower than prior allowed.
   - `r_snow`: pegged at prior upper bound of 2.0e-3 (posterior median
     ~2.0e-3). Data wants higher than prior allowed.

2. **Advisor (Dr. Jason Geck) explicitly requested independent r_ice
   calibration** in April 10, 2026 meeting (Granola notes):
   *"Ice/snow radiation factor ratio questionable. Currently using 2:1
   fixed ratio. Should calibrate ice and snow factors independently.
   Ice dominates in summer when glacier is exposed."*

3. **Geck's own Eklutna paper (2021)** calibrated both r_snow and r_ice
   independently and got:
   - r_snow = 0.0098 m² mm W⁻¹ d⁻¹ °C⁻¹
   - r_ice = 0.0414 m² mm W⁻¹ d⁻¹ °C⁻¹
   - ratio = 4.22
   Our fixed ratio of 2.5 in CAL-014 was not supported by the closest
   analog study.

4. **CAL-014 MF (6.57) and precip_corr (2.70) trade-off** with the
   bound-capped r_snow suggests a parameterization artifact. Freeing
   r_ice and widening r_snow bounds should allow the data to find a
   more physical combination.

**Bound changes from CAL-014:**

| Parameter  | CAL-014 bounds         | CAL-015 bounds         | Rationale              |
|-----------|------------------------|------------------------|------------------------|
| r_snow    | [0.02e-3, 2.0e-3]      | [0.02e-3, 30e-3]       | CAL-014 hit upper; cover Geck 9.8e-3 |
| r_ice     | derived (2.5 × r_snow) | [0.02e-3, 60e-3] FREE  | Advisor request; cover Geck 41e-3    |
| lapse     | [-6.5e-3, -2.0e-3]     | [-6.5e-3, -0.5e-3]     | CAL-014 hit upper; cover Geck mode -2|
| precip_corr | [1.2, 4.0]           | [1.0, 5.0]             | CAL-014 hit 2.70; widen    |
| MF, MF_grad, precip_grad, T0 | unchanged |                         |                        |

**Fresh-start priors (NOT CAL-014 informed):**

| Parameter  | Prior (CAL-015)                        | Rationale                                        |
|-----------|-----------------------------------------|--------------------------------------------------|
| MF        | TN(5.0, 3.0) on [1, 12]                 | Braithwaite 2008; Hock 2003 range               |
| T0        | TN(1.5, 0.5) on [0, 3]                  | Standard rain/snow threshold                    |
| r_snow    | TN(5e-3, 10e-3) on [0.02e-3, 30e-3]    | Center allows Hock (0.7e-3) or Geck (9.8e-3)   |
| r_ice     | TN(12e-3, 15e-3) on [0.02e-3, 60e-3]   | Wide σ allows ratio 1.4 (Hock) or 4.2 (Geck)   |
| lapse_rate| TN(-4.0e-3, 1.5e-3) on [-6.5e-3, -0.5e-3] | Covers Geck mode -2, Gardner summer -5, MALR -6.5 |
| MF_grad, precip_grad, precip_corr | Uniform in bounds | Let data speak                        |

**Over-parameterization concern (flagged, mitigated):**

Prior lit review (`litreview/cal014_prior_validation_2026-04-14.md`) warned
against 8 parameters. Mitigations in CAL-015:
1. Fresh priors prevent CAL-014 bias from dictating posterior
2. Multi-seed DE (5 seeds) will detect multimodality
3. Branch-resolved snowlines (43 residuals) + geodetic + 25 stakes + area
   filter = substantial data constraint
4. Post-MCMC diagnostics planned: R̂, autocorr τ, posterior correlations
5. Falsification: if posterior std / prior std > 0.9 for any parameter,
   that parameter is unidentified and will be fixed for CAL-015a

**Branch-resolved snowlines kept (D-036):**
- 43 residuals across north (16), middle (5), south (22) branches
- σ_snowline = 90m (matches CAL-013 structural RMSE)

**Expected runtime:** ~28-32 hours (8 params vs CAL-014's 7; 32 MCMC
walkers × 10,000 steps).

**Falsification criteria:**
- Each parameter's posterior should be well inside bounds (not pegged)
- r_ice/r_snow ratio posterior median should fall in literature range
  (1.3-5.0); if outside, flag
- Snowline RMSE should improve vs CAL-014 (was 112m branch-resolved)
- MCMC acceptance in [0.2, 0.5]; autocorr τ < 200

**Literature References (all from verified PDFs in papers_verified/):**
- Geck et al. (2021) J. Glaciol., p. 914: r_ice=0.0414, r_snow=0.0098
- Hock (1999) J. Glaciol., p. 106 Table 1: r_ice=0.8-1e-3, r_snow=0.6-0.7e-3
- Rounce et al. (2020) PyGEM, p. 176: fixed ratio 1.43 for global model
- Gardner et al. (2009) J. Climate, p. 4288: summer lapse -4.9±0.4, winter -3.2±0.5
- Granola notes 2026-04-10: advisor request for independent r_ice

**Implementation:**
- `run_calibration_v15.py` (copied from v14, modified)
- 8 free params; RICE_RATIO constant removed
- All output filenames use `_v15` suffix
- Branch-resolved snowlines unchanged from CAL-014
