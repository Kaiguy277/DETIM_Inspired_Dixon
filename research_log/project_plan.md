# Dixon Glacier Modeling — Comprehensive Project Plan

**Date:** 2026-03-06
**Context:** MS Thesis, Alaska Pacific University
**Goal:** Model Dixon Glacier mass balance and meltwater discharge, including
future projections under glacier retreat scenarios.

---

## Current State Assessment

### What works
- DETIM core physics implemented and tested (solar, terrain, melt equation)
- Numba-compiled fast model achieves ~400 ms / water-year evaluation
- Calibration framework (differential_evolution) functional
- 35 years of climate data (Nuka SNOTEL 1990–present)
- 2 years of measured stake data, 20 years of geodetic constraint
- On-glacier AWS providing ground truth (2 summers)

### What doesn't work (UPDATED 2026-03-12)
- ~~Temperature transfer~~ — RESOLVED (D-012: identity transfer, D-023: elevation fix)
- ~~Calibration failures~~ — RESOLVED (CAL-010: Bayesian ensemble, cost 7.7)
- ~~No ice dynamics~~ — RESOLVED (D-018: delta-h parameterization)
- ~~No runoff routing~~ — RESOLVED (D-019: linear reservoir routing)
- ~~Climate data gaps~~ — RESOLVED (D-025: multi-station gap-filling)
- **PENDING:** Recalibrate (CAL-011) with gap-filled climate data
- **PENDING:** Re-run projections with recalibrated parameters
- **PENDING:** Snowline validation re-run (gap-filled data may allow WY2000/2005)

---

## Phase 1: Fix the Temperature Problem (CRITICAL PATH)

**This blocks everything else.** Without correct temperatures, no parameter
calibration or model output is meaningful.

### Option A: Statistical downscaling (Recommended)
Use the Nuka→Dixon regression to convert off-glacier temperatures to
on-glacier equivalents:

    T_glacier(z,t) = α(month) × T_nuka(t) + β(month) + λ_internal × (z - z_AWS)

Where:
- α, β are the monthly regression coefficients from Nuka→Dixon overlap
- λ_internal is an on-glacier lapse rate (estimated from Dixon AWS + stake
  elevations, or from literature: typically -4 to -6°C/km on-glacier)
- z_AWS = 1078m (Dixon AWS elevation at ELA site; D-023)

**Pros:** Empirically grounded, captures katabatic dampening.
**Cons:** Only validated for May–Sep. Winter relationship unknown.
**Key question:** What to do in winter? Options:
  a) Use standard lapse rate in winter (glacier may be snow-covered, less
     katabatic effect)
  b) Apply a reduced katabatic correction year-round
  c) Use the May regression for shoulder seasons, standard for Dec–Mar

### Option B: Temperature reduction factor
Apply a constant or elevation-dependent reduction to on-glacier cells:

    T_glacier = T_free_air - ΔT_katabatic(z)

Simpler but less physically grounded.

### Implementation plan
1. Add monthly α, β coefficients to config.py
2. Modify temperature.py to apply statistical transfer instead of simple lapse
3. Add an internal lapse rate parameter for on-glacier elevation distribution
4. Re-run calibration — expect dramatically different (better) results
5. Validate against Dixon AWS hold-out data (use 2024 for calibration,
   2025 for validation, or vice versa)

---

## Phase 2: Calibration & Validation

Once temperature transfer is fixed:

### 2a: Re-calibrate (CAL-004)
- 7 parameters: MF, r_snow, r_ice, internal_lapse_rate, precip_grad,
  precip_corr, T0
- Expect MF and radiation factors to land in literature-reasonable ranges
- May need to add α_scale or β_offset as calibration parameters if
  the regression doesn't transfer perfectly

### 2b: Validation strategy
- **Temporal split:** calibrate on WY2023, validate on WY2024 (or vice versa)
- **Leave-one-out:** fit all years, report jackknife errors
- **Spatial:** compare modeled vs observed snowline elevations
  (manual_snowline_elevations.csv)
- **Geodetic cross-check:** does the model reproduce Hugonnet 2000–2020?

### 2c: Sensitivity analysis
- Morris or Sobol sensitivity on all parameters
- Report parameter elasticities for the thesis

---

## Phase 3: Elevation-Dependent Melt

You're right that we already have elevation-dependent melt through:
1. Temperature lapse rate → less melt at higher elevations
2. Precipitation gradient → more accumulation at higher elevations
3. I_pot varies with slope/aspect (but not systematically with elevation)

What we're missing:
- **Albedo feedback:** Snow at high elevations stays cleaner and more reflective.
  Fresh snow has albedo ~0.85; dirty ice has ~0.3. The r_snow vs r_ice
  parameterization partially captures this, but within each category the
  radiation factor is constant.
- **Cloud cover:** Low-elevation zones may have more cloud-free days, increasing
  actual (vs potential) radiation receipt.

### Options for enhancement
1. **Elevation-dependent MF:** MF(z) = MF_0 + MF_grad × (z - z_ref). Adds 1
   parameter. Captures integrated effect of albedo, wind, humidity changes.
2. **Aspect-dependent radiation factor:** Different r values for south vs north
   facing. Already partially captured by I_pot but could be enhanced.
3. **Albedo parameterization:** Track snow age, compute time-varying albedo.
   More physical but adds complexity and parameters.

**Recommendation:** Start with elevation-dependent MF. It's the simplest and
most impactful for fitting the ABL-to-ACC gradient. Can be done as:

    MF_cell = MF × (1 + MF_grad × (z_cell - z_ref))

One additional parameter (MF_grad). If MF_grad < 0, melt factor decreases
with elevation (expected physically).

---

## Phase 4: Discharge Routing

For peak meltwater flow forecasting, need to convert distributed melt to
basin outlet discharge.

### 4a: Simple linear reservoir
Each grid cell's melt is routed through 2–3 parallel linear reservoirs
(fast/slow/groundwater) with characteristic response times:

    Q(t) = Σ k_i × S_i(t)
    dS_i/dt = input_i - k_i × S_i

Where fast reservoir captures supraglacial/englacial routing (~hours),
slow captures subglacial (~days), and groundwater captures proglacial
storage (~weeks).

**Parameters:** 3 reservoir coefficients, 2 partitioning fractions = 5 new params.
**Calibration data needed:** Stream gauge / discharge observations.

### 4b: More sophisticated options
- Distributed flow routing (D8/D-infinity) with travel time
- Snow/ice melt vs rain separation in routing
- Seasonal evolution of drainage system efficiency

**Recommendation:** Start with the linear reservoir model. It's standard
in glaciohydrological studies (Hock & Jansson, 2005) and doesn't require
spatially distributed routing.

**Data need:** Do you have any discharge measurements at the glacier outlet?
This is critical for calibrating the routing.

---

## Phase 5: Ice Dynamics & Glacier Retreat

For future projections, the glacier geometry must evolve as mass is lost.

### 5a: Volume-Area scaling (simplest)
    V = c × A^γ  (Bahr et al., 1997)

Redistribute mass loss geometrically: terminus retreats, surface lowers.
Fast to compute but physically crude.

### 5b: Δh parameterization (recommended)
Use empirical elevation-change patterns from Huss et al. (2010):

    Δh(z) = Δh_max × f(z_normalized)

Where f is a normalized curve showing that thinning is greatest at the terminus
and decreases with elevation. Apply to the DEM each year to update geometry.

**Pros:** Captures observed pattern of glacier thinning. Validated globally.
Only needs total mass balance as input (which we already compute).
**Cons:** Doesn't capture dynamic feedbacks (surging, calving, flow acceleration).

### 5c: Shallow ice approximation (most physical)
Solve the ice flow equations:

    ∂H/∂t = -∇·(HŪ) + ḃ

Where H is ice thickness, Ū is depth-averaged velocity, ḃ is mass balance.
Requires ice thickness data (could estimate from Farinotti et al. 2019 consensus).

**Recommendation:** Use the Δh parameterization (5b) for the thesis. It's
well-established, computationally cheap, and appropriate for a mass-balance-focused
study. Mention the shallow ice approach as future work.

### 5d: Future climate forcing
- UAF SNAP downscaled projections for Alaska (CMIP6)
- Multiple emissions scenarios (SSP2-4.5, SSP5-8.5)
- Bias-correct against Nuka SNOTEL historical record

---

## Phase 6: Future Projections & Peak Flow Analysis

### 6a: Projection runs
- Run DETIM with Δh geometry updates under multiple climate scenarios
- Track: annual mass balance, ELA, AAR, glacier area, total volume
- Run to glacier disappearance or 2100 (whichever comes first)

### 6b: Peak flow analysis
- Identify annual peak meltwater discharge timing and magnitude
- Track how peak flow evolves as glacier shrinks:
  - Initially: more melt (warmer → more exposed ice → more melt)
  - Peak: maximum meltwater ("peak water")
  - Decline: glacier too small to sustain high melt rates
- Report timing and magnitude of "peak water" for Dixon Glacier
- This is the key thesis result for water resources implications

---

## Recommended Priority Order

```
Phase 1: Temperature transfer fix     ← BLOCKING, do now
Phase 2: Calibration & validation     ← Follows immediately
Phase 3: Elevation-dependent MF       ← If calibration still needs help
Phase 4: Discharge routing            ← Needs discharge data
Phase 5: Glacier retreat (Δh method)  ← Can develop in parallel with Phase 4
Phase 6: Future projections           ← Final analysis
```

### Minimum viable thesis
Phases 1 + 2 + 5 + 6 (skip 3 and 4 if time-limited). The core thesis
question "when does Dixon Glacier reach peak water?" can be answered without
discharge routing (report as specific melt rate, not volumetric discharge)
and may not need elevation-dependent MF if the temperature fix resolves
the calibration issues.

---

## Data Gaps to Address

| Gap | Impact | Possible source |
|-----|--------|----------------|
| Winter Nuka↔Dixon temperature | Can't validate winter transfer | Deploy year-round sensor? |
| Ice thickness | Needed for Δh method | Farinotti et al. 2019 consensus |
| Discharge | Needed for routing | USGS gauge? Field deployment? |
| Future climate | Needed for projections | UAF SNAP / CMIP6 downscaled |
| On-glacier lapse rate (with elevation) | Internal temp distribution | Multi-level AWS? Literature |
