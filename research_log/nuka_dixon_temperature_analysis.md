# Nuka SNOTEL vs Dixon AWS Temperature Analysis

**Date:** 2026-03-06
**Referenced by:** D-007 in decisions.md

**CORRECTION (D-023, 2026-03-12):** The Dixon AWS is at the **ELA site
(1078 m)**, NOT the ABL site (804 m). The elevation difference to Nuka is
703 m, not 429 m. This eliminates most of the "katabatic residual" reported
below — the observed -5.1°C offset is explained by a standard -6.5 to
-7.3 °C/km lapse rate across 703 m, with only ~0–1°C true katabatic cooling.
The original analysis below is preserved for reference but its interpretation
of a "~3°C katabatic residual" is an artifact of the elevation error.

## Overview

Comparison of Nuka Glacier SNOTEL (**375 m** = 1230 ft; corrected D-013) with
Dixon Glacier on-glacier AWS (**1078 m**, at ELA site; corrected D-023) during
overlap periods (256 days, 2024-04-30 to 2025-09-23, summer seasons only).

**CORRECTION (D-013):** Nuka at 1230 feet = 375 m.
**CORRECTION (D-023):** Dixon AWS at 1078 m (ELA), not 804 m (ABL).

## Key Finding: Normal Lapse Rate — Minimal Katabatic Cooling

**Dixon (1078m) is 5.10°C colder than Nuka (375m), consistent with lapse-rate
cooling (703m × -6.5 to -7.3 C/km = -4.6 to -5.1°C). The katabatic residual
is ~0–1°C, much smaller than the ~3°C originally reported with wrong elevation.**

| Metric | Nuka (375m) | Dixon (1078m) |
|--------|-------------|---------------|
| Mean TAVG | 8.03°C | 2.93°C |
| ΔT (Dixon - Nuka) | — | -5.10°C |
| Expected ΔT at -6.5°C/km for +703m | — | -4.57°C |
| Expected ΔT at -7.3°C/km for +703m | — | -5.13°C |
| Katabatic residual (at -6.5 lapse) | — | **-0.53°C** |

With the corrected elevation (D-023), the observed offset is almost entirely
explained by a standard maritime lapse rate. Any remaining katabatic effect
is < 1°C, consistent with a station at the ELA where glacier surface
influence is moderate.

## Monthly Temperature Differences (corrected D-013)

With Nuka at 375m and Dixon at 1078m (dz = +703m; corrected D-023), a
-6.5 C/km lapse predicts -4.57°C. Residuals represent true katabatic cooling:

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
