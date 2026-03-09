# Nuka SNOTEL vs Dixon AWS Temperature Analysis

**Date:** 2026-03-06
**Referenced by:** D-007 in decisions.md

## Overview

Comparison of Nuka Glacier SNOTEL (**375 m** = 1230 ft; corrected D-013) with
Dixon Glacier on-glacier AWS (804m, at ABL stake) during overlap periods
(256 days, 2024-04-30 to 2025-09-23, summer seasons only).

**CORRECTION (D-013):** The original analysis assumed Nuka at 1230 m. The
NRCS lists Nuka at 1230 feet = 375 m. Dixon AWS (804 m) is 429 m ABOVE
Nuka, not 426 m below. The "inverted temperature profile" was an artifact
of the units error.

## Key Finding: Normal Lapse + Modest Katabatic Cooling

**Dixon (804m) is 5.10°C colder than Nuka (375m), consistent with lapse-rate
cooling (429m × -5.0 C/km = -2.15°C) plus ~3°C of real katabatic cooling.**

| Metric | Nuka (375m) | Dixon (804m) |
|--------|-------------|-------------|
| Mean TAVG | 8.03°C | 2.93°C |
| ΔT (Dixon - Nuka) | — | -5.10°C |
| Expected ΔT at -5.0°C/km for +429m | — | -2.15°C |
| Katabatic residual | — | **-2.95°C** |

The katabatic effect is real but modest (~3°C, not ~8°C as originally
reported). This is consistent with on-glacier cooling measured at other
maritime glaciers (Gardner & Sharp 2009). In the DETIM framework, this
cooling is implicitly absorbed by the calibrated melt factor (Hock 1999).

## Monthly Temperature Differences (corrected D-013)

With Nuka at 375m and Dixon at 804m (dz = +429m), a -5.0 C/km lapse
predicts -2.15°C. Residuals represent true katabatic cooling:

| Month | Nuka °C | Dixon °C | ΔT | Lapse pred | Katabatic residual | n |
|-------|---------|----------|------|-----------|-------------------|---|
| May | 3.27 | -0.59 | -3.86 | +1.12 | -1.71 | 51 |
| Jun | 8.34 | 3.18 | -5.16 | +6.20 | -3.02 | 59 |
| Jul | 9.90 | 4.39 | -5.51 | +7.76 | -3.37 | 44 |
| Aug | 10.33 | 4.59 | -5.74 | +8.19 | -3.60 | 57 |
| Sep | 8.41 | 3.12 | -5.29 | +6.27 | -3.15 | 44 |

The katabatic residual (1.7-3.6°C) is consistent with other maritime glaciers.
It is strongest in warmest months when the glacier surface–air temperature
gradient is greatest, as expected from katabatic wind theory.

## Linear Regression

    T_dixon = 0.695 × T_nuka + (-2.650)
    R² = 0.696, RMSE = 1.45°C

The slope of 0.695 means Dixon temperature variability is **dampened** relative
to Nuka — the glacier buffers temperature extremes. This is NOT a simple
elevation offset; a lapse rate model cannot capture this relationship.

### Monthly regression slopes

| Month | Slope | Intercept | Interpretation |
|-------|-------|-----------|----------------|
| May | 0.667 | -2.77 | Moderate coupling |
| Jun | 0.534 | -1.27 | Dampened — glacier cooling onset |
| Jul | 0.574 | -1.29 | Dampened — peak glacier influence |
| Aug | 0.391 | +0.56 | Most dampened — maximum katabatic |
| Sep | 1.211 | -7.06 | Enhanced — early season transition |

## Implications for DETIM

### Why all calibrations failed
The merged climate data applies a -6.5°C/km lapse rate to adjust Nuka temps
to Dixon elevation (804m), adding +2.77°C. But the true Dixon temperature is
5.10°C COLDER than Nuka. The merged climate is therefore **+7.87°C too warm**
at the glacier surface during summer. This dwarfs the D-006 fix (+2.8°C).

### What this means
1. **A standard lapse rate cannot represent Nuka→glacier temperature transfer.**
   The free-air lapse rate breaks down over glacier surfaces due to katabatic winds.
2. **The DETIM formulation (T_cell = T_station + λ×Δz) needs modification**
   for an off-glacier driving station.
3. **The dampened slope (0.695) means positive degree-days at the glacier are
   much fewer than the raw station data implies.**

### Caveat
This analysis uses only summer overlap data (May–Sep). Winter temperatures
may have a different relationship. The Dixon AWS is deployed seasonally, so
we cannot validate the winter transfer.

## Literature Context
Katabatic cooling on glacier surfaces is well-documented:
- Greuell & Böhm (1998): boundary layer cooling on Pasterze Glacier
- Shea & Moore (2010): temperature distribution on glaciers in BC
- Petersen & Pellicciotti (2011): glacier-surface temperature parameterizations

The standard approach is either:
1. A temperature offset/reduction factor applied to on-glacier cells
2. A modified lapse rate that accounts for boundary layer cooling
3. A statistical downscaling from free-air to glacier surface temperature
