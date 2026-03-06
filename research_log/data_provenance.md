# Data Provenance — Dixon Glacier DETIM

Every dataset used in the model, its source, processing steps, known issues,
and quality assessment. This supports the Methods and Data sections of the thesis.

---

## 1. Digital Elevation Model

| Field | Value |
|-------|-------|
| File | `ifsar_2010/dixon_glacier_IFSAR_DTM_5m_full.tif` |
| Source | USGS IfSAR Alaska, acquired ~2010 |
| Native resolution | 5 m |
| CRS | WGS84 (EPSG:4326) |
| Model grid | Resampled to 50 m (analysis) or 100 m (calibration) via rasterio |
| Elevation range | 439–1637 m |
| Quality | High — IfSAR is survey-grade for Alaska. No voids in glacier area. |

**Processing:** Loaded with rasterio, reprojected to UTM 5N (EPSG:32605) for
metric grid operations. Slope and aspect computed via numpy gradient.
Code: `dixon_melt/terrain.py`.

**Limitation:** DEM is from 2010 — glacier surface has lowered since then
(Hugonnet: -0.95 to -1.26 m/yr thinning). For a 15-year-old DEM, cumulative
surface change could be 10–20 m in the ablation zone. This affects lapse rate
calculations and radiation geometry at low elevations.

---

## 2. Glacier Outline

| Field | Value |
|-------|-------|
| File | `geodedic_mb/dixon_glacier_outline_rgi7.geojson` |
| Source | Randolph Glacier Inventory v7.0 (RGI7) |
| RGI ID | RGI60-01.18059 |
| CRS | EPSG:4326 |
| Area | 39.86 km² (RGI), ~40.1 km² (gridded at 50m) |

**Processing:** Used to create glacier mask via rasterio.features.rasterize.
Code: `dixon_melt/terrain.py`.

---

## 3. Climate — Nuka SNOTEL (Primary Forcing)

| Field | Value |
|-------|-------|
| File | `data/climate/nuka_snotel_full.csv` |
| Station | Nuka Glacier SNOTEL, site 1037 |
| Location | 59.698°N, 150.712°W |
| Elevation | 1230 m |
| Distance to Dixon | ~20 km |
| Period | 1990-10-01 to present |
| Variables | TAVG, TMAX, TMIN (°F→°C), PREC cumulative (in→mm), SNWD (in→cm) |
| Source | NRCS Report Generator API |

### Coverage
| Variable | Coverage | Notes |
|----------|----------|-------|
| TAVG | 79% | Near-complete 1999+, gaps pre-1999 |
| TMAX/TMIN | 79% | Same pattern as TAVG |
| PREC | 93% | Cumulative, converted to daily increments |
| SNWD | 62% | Available since 2002 only |
| SWE | 0% | No SWE pillow installed at this site |

### Processing
1. Downloaded via NRCS API (automated script)
2. Temperature converted °F → °C
3. Precipitation: cumulative inches → daily increments in mm
4. Negative daily precip increments (gauge resets) flagged and set to 0
5. Temperature adjusted to Dixon glacier reference elevation (804 m) using
   calibrated lapse rate

### Known Issues
- **Undercatch:** SNOTEL gauges significantly underestimate solid precipitation
  in windy conditions. A precipitation correction factor (precip_corr) is
  calibrated to compensate. Typical values for maritime Alaska: 1.5–4.0×.
- **Distance:** 20 km from Dixon means precipitation events may differ in
  timing and magnitude. Orographic enhancement patterns differ.
- **No SWE pillow:** Cannot directly validate winter accumulation at station.

---

## 4. Climate — Dixon On-Glacier AWS

| Field | Value |
|-------|-------|
| Files | `Dixon24WX_RAW.csv`, `Dixon25_WX.csv` |
| Location | Near ABL stake, 804 m elevation |
| Type | Seasonal deployment (summer field seasons) |

### 2024 Season
| Field | Value |
|-------|-------|
| Period | 2024-04-30 to 2024-09-21 |
| Interval | Hourly |
| Variables | Temperature, precipitation |
| Quality | Clean — no significant data issues |

### 2025 Season
| Field | Value |
|-------|-------|
| Period | 2025-05-12 to 2025-10-10 |
| Interval | Hourly |
| Variables | Temperature, RH, precipitation |
| Quality | 968 bad temperature values flagged during QC |

### Processing
Hourly → daily aggregation. Used to validate SNOTEL-derived temperatures
during overlap periods. Stored in merged file:
`data/climate/dixon_model_climate.csv` (12,876 days, 81% T coverage).

---

## 5. Stake Mass Balance Observations

| Field | Value |
|-------|-------|
| File | `stake_observations_dixon.csv` |
| Stakes | ABL (804 m), ELA (1078 m), ACC (1293 m) |
| Period | 2023–2025 |
| Types | Annual, summer, winter balances |
| Uncertainty | ±0.10–0.15 m w.e. |

### Observations Summary
| Stake | Year | Annual (m w.e.) | Summer | Winter | Notes |
|-------|------|-----------------|--------|--------|-------|
| ABL | 2023 | -4.50 | -5.35 | +0.85 | Measured |
| ABL | 2024 | -2.63 | -4.56 | +1.93 | Measured |
| ELA | 2023 | +0.10 | -2.26 | +2.36 | Measured |
| ELA | 2024 | +0.10 | -2.50 | +2.60 | Measured |
| ACC | 2023 | +0.37 | -2.25 | +2.45 | Measured |
| ACC | 2024 | +1.46 | -1.55 | +3.01 | Measured |
| ELA | 2025 | +1.08 | -1.96 | +3.04 | Estimated |
| ACC | 2025 | +1.88 | -1.66 | +3.53 | Estimated |

**2025 observations** are estimates with inflated uncertainty (±0.30 m w.e.)
used in calibration with lower weight.

---

## 6. Geodetic Mass Balance (Hugonnet et al. 2021)

| Field | Value |
|-------|-------|
| File | `geodedic_mb/dixon_glacier_hugonnet.csv` |
| Source | Hugonnet et al. (2021), Nature |
| RGI ID | RGI60-01.18059 |

### Periods
| Period | dh/dt (m/yr) | dM/dt/A (m w.e./yr) | Uncertainty |
|--------|-------------|---------------------|-------------|
| 2000–2010 | -1.261 | -1.072 | ±0.225 |
| 2010–2020 | -0.948 | -0.806 | ±0.202 |
| 2000–2020 | -1.105 | -0.939 | ±0.122 |

**Reference:** Hugonnet, R., et al. (2021). Accelerated global glacier mass
loss in the early twenty-first century. Nature, 592, 726–731.

**Note:** Area-weighted, accounts for 99.5% of glacier area measured.
