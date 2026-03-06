# Nuka SNOTEL vs Dixon AWS Temperature Analysis

**Date:** 2026-03-06
**Referenced by:** D-007 in decisions.md

## Overview

Comparison of Nuka Glacier SNOTEL (1230m, off-glacier) with Dixon Glacier
on-glacier AWS (804m, at ABL stake) during overlap periods (256 days,
2024-04-30 to 2025-09-23, summer seasons only).

## Key Finding: Inverted Temperature Profile

**Dixon (804m) is COLDER than Nuka (1230m) 100% of the time during summer.**

| Metric | Nuka (1230m) | Dixon (804m) |
|--------|-------------|-------------|
| Mean TAVG | 8.03°C | 2.93°C |
| ΔT (Dixon - Nuka) | — | -5.10°C |
| Expected ΔT at -6.5°C/km | — | +2.77°C |
| Actual bias | — | **+7.87°C too warm in model** |

This is the **katabatic cooling effect** — cold air draining off the glacier
ice surface creates a persistent temperature inversion in the boundary layer.

## Monthly Lapse Rates

All implied "lapse rates" are inverted (temperature decreases going downhill
onto the glacier):

| Month | Nuka °C | Dixon °C | ΔT | Implied lapse (°C/km) | n |
|-------|---------|----------|------|-----------------------|---|
| May | 3.27 | -0.59 | -3.86 | 9.06 | 51 |
| Jun | 8.34 | 3.18 | -5.16 | 12.11 | 59 |
| Jul | 9.90 | 4.39 | -5.51 | 12.92 | 44 |
| Aug | 10.33 | 4.59 | -5.74 | 13.47 | 57 |
| Sep | 8.41 | 3.12 | -5.29 | 12.41 | 44 |

The katabatic effect is **strongest in warmest months** (Aug: 13.5°C/km
inverted) when the temperature difference between ambient air and glacier
surface is greatest.

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
