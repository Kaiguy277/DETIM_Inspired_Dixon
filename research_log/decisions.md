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
