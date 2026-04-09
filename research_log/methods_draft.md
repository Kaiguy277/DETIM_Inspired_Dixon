# Methods — Draft

Living draft of the Methods section for the MS thesis. Updated as modeling
decisions are finalized. Section numbers are provisional.

---

## 3.1 Study Site

Dixon Glacier (59.66°N, 150.88°W) is a large valley glacier on the Kenai
Peninsula, south-central Alaska, with an area of approximately 40 km² (RGI7).
The glacier spans 439 to 1637 m elevation and drains [direction/watershed TBD].
Mass balance observations have been collected at three stake sites since 2023:
an ablation zone stake (ABL, 804 m), an equilibrium line stake (ELA, 1078 m),
and an accumulation zone stake (ACC, 1293 m).

## 3.2 Model Description

We apply a Distributed Enhanced Temperature Index Model (DETIM) following
Method 2 of Hock (1999). Daily melt M (mm w.e. d⁻¹) at each grid cell is
computed as:

    M = (MF + r_snow/ice × I_pot) × T,  when T > 0°C
    M = 0,                                when T ≤ 0°C

where MF is a melt factor (mm d⁻¹ K⁻¹), r_snow and r_ice are radiation
factors for snow- and ice-covered surfaces respectively (mm m² W⁻¹ d⁻¹ K⁻¹),
I_pot is the potential clear-sky direct solar radiation (W m⁻²), and T is the
distributed air temperature (°C).

### 3.2.1 Temperature Distribution

Air temperature is extrapolated from the climate station to each grid cell
using a constant lapse rate:

    T_cell = T_station + λ × (z_cell - z_station)

where λ is the calibrated lapse rate (°C m⁻¹) and z denotes elevation (m).

### 3.2.2 Precipitation Distribution

Daily precipitation at each grid cell is computed as:

    P_cell = P_station × C_p × (1 + γ_p × Δz)

where C_p is a precipitation correction factor accounting for gauge undercatch
and spatial transfer, and γ_p is an elevation gradient (fraction m⁻¹).
Precipitation is partitioned into rain and snow using a linear transition
around threshold temperature T₀:

    f_snow = 1.0                    if T < T₀ - 1°C
    f_snow = 0.5 × (T₀ + 1 - T)   if T₀ - 1 ≤ T ≤ T₀ + 1°C
    f_snow = 0.0                    if T > T₀ + 1°C

### 3.2.3 Solar Radiation

Potential clear-sky direct radiation I_pot is computed for each grid cell
and day of year following Oke (1987) solar geometry with topographic
corrections for slope, aspect, and self-shading (Hock, 1999). The
atmospheric transmissivity is set to ψ_a = 0.75. Radiation values are
precomputed for all 365 days at 3-hour intervals and stored in a lookup
table for computational efficiency.

### 3.2.4 Snowpack and Surface Type

A snow water equivalent (SWE) layer is tracked at each grid cell. Surface
type determines which radiation factor is applied:
- Snow (SWE > 0): r_snow
- Firn (SWE = 0, elevation ≥ median glacier elevation): r_snow
- Ice (SWE = 0, below firn line): r_ice

The firn line is set at the median glacier elevation, a simplification that
avoids tracking multi-year accumulation history. This is consistent with
other DETIM implementations (Hock, 1999) and has minimal impact on
calibrated results because the radiation factor ratio (r_ice/r_snow = 2.0)
is the primary control on the snow-to-ice albedo feedback.

## 3.3 Input Data

### 3.3.1 Digital Elevation Model
[See data_provenance.md §1 — summarize here for thesis]

### 3.3.2 Climate Forcing

The primary climate station is the Nuka Glacier SNOTEL (site 1037, 375 m,
NRCS) located approximately 10 km northwest of Dixon Glacier. Daily mean air
temperature and precipitation are available from October 1990 to present,
though the record contains significant gaps in early years: WY2001 (77%
temperature missing), WY2005 (43%), and WY2000, WY2002–2004, WY2006–2008
(3–30%). A 192-day precipitation gap in WY2020 (November–June) resulted in
approximately 1,019 mm of unrecorded accumulation.

To produce a continuous forcing record for WY1999–WY2025, temperature and
precipitation gaps were filled using a multi-station cascade (D-025). Monthly
reverse regressions (T_nuka = slope × T_station + intercept) were computed
from overlapping valid days between Nuka and five nearby SNOTEL stations:
Middle Fork Bradley (1064, 701 m, 16 km), McNeil Canyon (1003, 411 m, 24 km),
Anchor River Divide (1062, 503 m, 34 km), Kachemak Creek (1063, 503 m,
14 km), and Lower Kachemak Creek (1265, 597 m, 13 km). For precipitation,
monthly ratios (P_nuka / P_mfb) were computed from wet-day pairs (both
> 0.5 mm d⁻¹).

The gap-filling cascade applies stations in order of prediction skill: Nuka →
MFB → McNeil → Anchor → Kachemak → Lower Kachemak → linear interpolation
(≤3 days) → day-of-year climatology. Nuka provides 91.3% of temperature days
and 98.0% of precipitation days; fill stations contribute the remainder
(primarily MFB at 6.0% and McNeil at 1.8% for temperature). The resulting
record contains zero missing values across all 9,862 days. Transfer RMSE on
overlapping data ranges from 1.0–2.8°C depending on station and month.

[See data_provenance.md for full station details and transfer coefficients.]

### 3.3.3 Calibration and Validation Data
[See data_provenance.md §5–6 — summarize here for thesis]

## 3.4 Calibration

Model calibration employs a two-phase Bayesian approach following Rounce et al.
(2020): differential evolution (Storn & Price, 1997) identifies the maximum a
posteriori (MAP) parameter estimate, then Markov Chain Monte Carlo (MCMC)
sampling maps the posterior distribution to generate an ensemble of parameter
sets for projection uncertainty quantification.

### 3.4.1 Calibrated and Fixed Parameters

Six parameters are calibrated, with two physically constrained parameters
fixed from literature values:

**Calibrated parameters:**

| Parameter | Symbol | Units | Bounds | Prior |
|-----------|--------|-------|--------|-------|
| Melt factor | MF | mm d⁻¹ K⁻¹ | [1, 12] | N(5.0, 3.0) truncated |
| Melt factor gradient | MF_grad | mm d⁻¹ K⁻¹ m⁻¹ | [-0.01, 0] | Uniform |
| Radiation factor (snow) | r_snow | mm m² W⁻¹ d⁻¹ K⁻¹ | [0.02, 1.5]×10⁻³ | Uniform |
| Precipitation gradient | γ_p | m⁻¹ | [0.0002, 0.006] | Uniform |
| Precipitation correction | C_p | — | [1.2, 4.0] | Uniform |
| Rain/snow threshold | T₀ | °C | [0.5, 3.0] | N(1.5, 0.5) truncated |

**Fixed parameters:**

| Parameter | Value | Source |
|-----------|-------|--------|
| Lapse rate λ | -5.0 °C km⁻¹ | Gardner & Sharp (2009), Roth et al. (2023) |
| r_ice/r_snow ratio | 2.0 | Hock (1999) Table 4, mid-range of 1.5–3.0 |

The lapse rate is fixed to prevent equifinality with the precipitation
correction factor (see §3.4.4). The r_ice/r_snow ratio is fixed to preserve
the albedo feedback between snow- and ice-covered surfaces, which is critical
for projections as the firn line retreats under warming.

### 3.4.2 Calibration Targets

Calibration targets include point-scale stake observations and glacier-wide
geodetic mass balance:

- **Stake annual balance:** 8 observations at 3 elevations (ABL 804 m, ELA
  1078 m, ACC 1293 m), water years 2023–2025
- **Stake summer balance:** 8 observations (spring probe to fall measurement)
- **Stake winter balance:** 9 observations (October 1 to spring probe)
- **Geodetic mass balance:** Hugonnet et al. (2021) 2000–2020 mean:
  -0.939 ± 0.122 m w.e. yr⁻¹

The Hugonnet sub-periods (2000–2010, 2010–2020) are used for validation only,
as they are not statistically distinguishable (Z = 0.88, p > 0.30) and their
apparent trends contradict the Nuka SNOTEL forcing (see D-016).

### 3.4.3 Likelihood Function and Priors

The log-likelihood assumes independent Gaussian errors:

    ln L(θ) = -0.5 × Σᵢ [(mᵢ(θ) - oᵢ) / σᵢ]²

where mᵢ(θ) is the modeled value for parameter vector θ, oᵢ is the observed
value, and σᵢ is the reported measurement uncertainty. This inverse-variance
weighting naturally gives more weight to precise observations.

A geodetic hard penalty (λ = 50) is applied when the geodetic residual exceeds
its reported uncertainty, following D-014.

Prior distributions are either truncated normal (for parameters with
well-established literature ranges) or uniform (for parameters specific to
the study site). The posterior is proportional to the product of likelihood
and prior.

### 3.4.4 Calibration Procedure

**Phase 1 — MAP estimation:** The SciPy differential evolution optimizer
(population 15 × 6 = 90, Latin hypercube initialization, 200 maximum
iterations) identifies the parameter set that maximizes the posterior density.

**Phase 2 — MCMC sampling:** The emcee affine-invariant ensemble sampler
(Foreman-Mackey et al., 2013) is initialized with 24 walkers in a tight ball
around the MAP estimate. Each walker runs 10,000 steps. The first 2,000 steps
(or 2× the autocorrelation time, whichever is larger) are discarded as
burn-in, and samples are thinned by the autocorrelation time to yield
independent posterior samples. Convergence is assessed via the acceptance
fraction (target 0.2–0.5) and stability of the integrated autocorrelation time.

### 3.4.5 Initial Conditions

For water-year simulations (October 1 start), initial snow water equivalent
is set to zero — the snowpack accumulates naturally from daily precipitation
through the fall and winter months. For summer-only simulations (used for
summer balance calibration targets), initial SWE is set from observed winter
balance measurements at the ELA stake.

### 3.4.6 Equifinality and Parameter Constraints

Preliminary calibration (CAL-001 through CAL-009) revealed persistent
equifinality between the lapse rate and precipitation correction factor:
a steep lapse rate with low precipitation correction can produce similar
current-climate mass balance as a moderate lapse rate with higher precipitation.
However, these parameter sets diverge under warming — the steep-lapse solution
underestimates warming at high elevations while the low-precipitation solution
causes the glacier to disappear too rapidly.

Fixing the lapse rate at the literature value (-5.0 °C km⁻¹) and deriving
r_ice from r_snow eliminates the two primary equifinality axes while
maintaining sufficient flexibility in the remaining six parameters to fit
all calibration targets.

## 3.5 Projection Ensemble

Projections of glacier mass balance, area, and discharge under climate
scenarios are run with 250 parameter sets drawn from the MCMC posterior
distribution. For each parameter set, the model is forced with bias-corrected
daily output from five CMIP6 GCMs (ACCESS-CM2, EC-Earth3, MPI-ESM1-2-HR,
MRI-ESM2-0, NorESM2-MM) from the NEX-GDDP-CMIP6 archive (Thrasher et al.,
2022) under SSP2-4.5 and SSP5-8.5 to WY2100. Results are reported as the
median with 5th and 95th percentile credible intervals, capturing
uncertainty from both parameter equifinality and climate forcing.

To bracket structural uncertainty from the fixed lapse rate, projections are
additionally run at -4.5 and -5.5 °C km⁻¹ (spanning the literature range
for maritime Alaskan glaciers) using 250 posterior parameter sets. This
scenario-based sensitivity analysis uses the same calibrated parameters at
each lapse rate, isolating the effect of the lapse rate assumption on
projected glacier evolution.

## 3.6 Validation

Model validation employs three independent approaches targeting different
aspects of model performance.

### 3.6.1 Sub-period Geodetic Comparison

The Hugonnet et al. (2021) geodetic record provides independent sub-period
estimates for 2000–2010 (-1.072 ± 0.225 m w.e. yr⁻¹) and 2010–2020
(-0.806 ± 0.202 m w.e. yr⁻¹). Only the full 2000–2020 period is used for
calibration; the sub-periods serve as validation targets. For 200 posterior
parameter sets, the model is run through each sub-period independently and
the ensemble median compared to the observed value.

### 3.6.2 Posterior Predictive Check by Year

Rather than full leave-one-year-out cross-validation (which would require
three complete recalibrations), we evaluate the posterior ensemble against
each stake year independently. For each water year with stake observations
(WY2023–2025), 200 posterior parameter sets are run and predicted balances
compared to observed values at all three stake elevations (ABL, ELA, ACC).
This identifies whether any single year dominates the calibration fit or
whether the posterior generalizes across the observation period.

### 3.6.3 Known Spatial Bias at ELA

The ELA stake (1078 m) exhibits a persistent negative bias of approximately
-1.4 m w.e. in both WY2023 and WY2024, while ABL and ACC residuals are
small (+0.38, +0.05 m w.e. in WY2023). This bias is attributed to wind
redistribution: digitized snowlines show systematically greater accumulation
on the southern branch of the glacier where the ELA stake is located,
consistent with preferential wind-loading in this sheltered zone. The model
distributes precipitation uniformly by elevation and predicts the *average*
balance across all 814 cells at 1028–1128 m (20.3% of glacier area), whereas
the stake observation represents a single point in a locally favored
accumulation zone. The glacier-wide geodetic constraint (within 2σ of
Hugonnet et al., 2021) confirms that the integrated mass balance is
well-captured; the ELA discrepancy reflects a measurement representativity
limitation rather than a model calibration failure.

### 3.6.4 Sensitivity of Fixed Parameters

Two parameters are fixed from literature rather than calibrated: the lapse
rate (λ = -5.0 °C km⁻¹) and the r_ice/r_snow ratio (2.0). To quantify
the impact of these choices, each fixed parameter is perturbed across its
plausible range while holding all other parameters at their MAP values.
Lapse rate is varied from -4.0 to -6.5 °C km⁻¹ (Gardner & Sharp, 2009;
Roth et al., 2023) and the r_ice/r_snow ratio from 1.5 to 3.0 (Hock, 1999,
Table 4). For each perturbation, the 2000–2020 geodetic mass balance and
stake RMSE are recomputed to quantify sensitivity.

## 3.7 Implementation

The model is implemented in Python 3.12 using NumPy for array operations
and Numba for just-in-time compilation of the simulation kernel. A single
JIT-compiled function (`run_simulation`) executes the full daily time-stepping
loop with parallel iteration over grid cells, achieving ~240 ms per water-year
simulation on a 100 m grid (289 × 117, 4011 glacier cells). MCMC sampling
uses the emcee package (Foreman-Mackey et al., 2013). Corner plots are
generated with the corner package (Foreman-Mackey, 2016).

Spatial data handling uses rasterio for DEM and glacier outline operations.
All code is available at [repository TBD].
