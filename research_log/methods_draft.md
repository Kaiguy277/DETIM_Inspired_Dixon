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

[TODO: Consider dynamic firn line based on multi-year accumulation.]

## 3.3 Input Data

### 3.3.1 Digital Elevation Model
[See data_provenance.md §1 — summarize here for thesis]

### 3.3.2 Climate Forcing
[See data_provenance.md §3–4 — summarize here for thesis]

### 3.3.3 Calibration and Validation Data
[See data_provenance.md §5–6 — summarize here for thesis]

## 3.4 Calibration

Model calibration follows a multi-objective approach using the SciPy
implementation of differential evolution (Storn & Price, 1997).

### 3.4.1 Calibrated Parameters

Seven parameters are calibrated simultaneously:

| Parameter | Symbol | Units | Bounds | Role |
|-----------|--------|-------|--------|------|
| Melt factor | MF | mm d⁻¹ K⁻¹ | [1, 12] | Temperature sensitivity |
| Radiation factor (snow) | r_snow | mm m² W⁻¹ d⁻¹ K⁻¹ | [0.02, 1.5]×10⁻³ | Solar melt on snow |
| Radiation factor (ice) | r_ice | mm m² W⁻¹ d⁻¹ K⁻¹ | [0.05, 3.0]×10⁻³ | Solar melt on ice |
| Lapse rate | λ | °C m⁻¹ | [-8.5, -3.5]×10⁻³ | Temperature extrapolation |
| Precipitation gradient | γ_p | m⁻¹ | [0.0002, 0.006] | Elevation scaling |
| Precipitation correction | C_p | — | [1, 6] | Undercatch + spatial transfer |
| Rain/snow threshold | T₀ | °C | [0.5, 3.0] | Phase partitioning |

### 3.4.2 Objective Function

The objective function combines three weighted components:

    J = w₁ × RMSE_annual + w₂ × RMSE_summer + w₃ × RMSE_geodetic + w₄ × P_phys

where RMSE values are computed from uncertainty-normalized residuals:

    ε_i = (modeled_i - observed_i) / σ_i

Weights: w₁ = 1.0 (stake annual), w₂ = 0.6 (stake summer),
w₃ = 0.4 (geodetic), w₄ = 0.3 (physical constraint r_ice > r_snow).

### 3.4.3 Initial Conditions

For water-year simulations (October 1 start), initial snow water equivalent
is set to zero — the snowpack accumulates naturally from daily precipitation
through the fall and winter months. For summer-only simulations (used for
summer balance calibration targets), initial SWE is set from observed winter
balance measurements at the ELA stake.

[TODO: Add calibration results when CAL-002 completes.]

## 3.5 Validation

[TODO: Cross-validation strategy, geodetic comparison, sensitivity analysis.]

## 3.6 Implementation

The model is implemented in Python 3.12 using NumPy for array operations
and Numba for just-in-time compilation of the simulation kernel. A single
JIT-compiled function (`run_simulation`) executes the full daily time-stepping
loop with parallel iteration over grid cells, achieving ~300 ms per water-year
simulation on a [TBD] grid. This enables the ~12,000 objective function
evaluations required by differential evolution to complete in approximately
one hour.

Spatial data handling uses rasterio for DEM and glacier outline operations.
All code is available at [repository TBD].
