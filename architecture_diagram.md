# Dixon Glacier DETIM — Codebase Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                INPUT DATA                                        │
│                                                                                  │
│  ┌──────────────┐  ┌───────────────┐  ┌───────────────────┐  ┌───────────────┐  │
│  │ DEM (5m)     │  │ Glacier       │  │ Climate Stations  │  │ NEX-GDDP     │  │
│  │ IfSAR 2010   │  │ Outline RGI7  │  │                   │  │ CMIP6 (5 GCM)│  │
│  │              │  │               │  │ Nuka SNOTEL 375m  │  │ × 2 SSPs     │  │
│  │ Ice thick.   │  │ Stake obs.    │  │ MFB 1064    701m  │  │              │  │
│  │ Farinotti    │  │ ABL/ELA/ACC   │  │ McNeil 1003 411m  │  │ Bias-correct │  │
│  │ 2019         │  │               │  │ Anchor 1062 503m  │  │ via delta    │  │
│  │              │  │ Geodetic MB   │  │ LKC 1265    597m  │  │ method       │  │
│  │              │  │ Hugonnet      │  │ Kach. 1063  503m  │  │              │  │
│  │              │  │ 2000–2020     │  │                   │  │              │  │
│  │ Snowlines    │  │               │  │ Dixon AWS  1078m  │  │              │  │
│  │ 22 shp files │  │               │  │ (summer only)     │  │              │  │
│  │ 1999–2024    │  │               │  │                   │  │              │  │
│  └──────┬───────┘  └──────┬────────┘  └────────┬──────────┘  └──────┬────────┘  │
└─────────┼──────────────────┼───────────────────┼───────────────────┼────────────┘
          │                  │                   │                   │
          ▼                  ▼                   ▼                   ▼
┌─────────────────────────────────┐  ┌────────────────────┐  ┌──────────────────────┐
│        terrain.py               │  │    climate.py       │  │ climate_projections  │
│  ┌────────────────────────────┐ │  │                    │  │        .py           │
│  │ prepare_grid()             │ │  │ Gap-fill cascade   │  │                      │
│  │  ├─ load_and_reproject_dem │ │  │ (D-025):           │  │ load_cmip6_         │
│  │  ├─ compute_slope_aspect   │ │  │  Nuka (91.3%)     │  │  projections()       │
│  │  ├─ load_glacier_mask      │ │  │  → MFB (6.0%)     │  │                      │
│  │  └─ compute_wind_exposure  │ │  │  → McNeil (1.8%)  │  │ bias_correct_delta() │
│  └────────────────────────────┘ │  │  → Anchor (0.4%)  │  │  (additive T,        │
│                                 │  │  → interp (0.3%)  │  │   multiplicative P)  │
│                                 │  │  → DOY climo      │  │                      │
│                                 │  │                    │  │                      │
│                                 │  │ Monthly transfer   │  │                      │
│                                 │  │ coefficients for   │  │                      │
│                                 │  │ katabatic corr.    │  │                      │
└────────────┬────────────────────┘  └─────────┬──────────┘  └──────────┬───────────┘
             │                                 │                        │
             ▼                                 ▼                        │
  ┌─────────────────────┐       ┌───────────────────┐                  │
  │ Grid dict:          │       │ climate_df:       │                  │
  │  elevation [2D]     │       │  date (index)     │                  │
  │  slope [2D]         │       │  temperature (°C) │                  │
  │  aspect [2D]        │       │  precipitation    │                  │
  │  glacier_mask [2D]  │       │  (mm/day)         │                  │
  │  sx_norm [2D]       │       │  zero NaN (D-025) │                  │
  └──────────┬──────────┘       └─────────┬─────────┘                  │
             │                            │                            │
             ▼                            │                            │
  ┌─────────────────────┐                 │                            │
  │     solar.py        │                 │                            │
  │                     │                 │                            │
  │ precompute_ipot()   │                 │                            │
  │  → I_pot[365,r,c]   │                 │                            │
  │  (W/m², topo-       │                 │                            │
  │   corrected)        │                 │                            │
  └──────────┬──────────┘                 │                            │
             │                            │                            │
             ▼                            ▼                            │
┌═════════════════════════════════════════════════════════════════╪═════════════╗
║                    fast_model.py  (NUMBA-COMPILED CORE)        │             ║
║                    ─────────────────────────────────────        │             ║
║  FastDETIM.run(T_nuka, P_nuka, doy, params, winter_swe)        │             ║
║  Uses monthly temp transfer coefficients (slope/intercept)     │             ║
║                                                                │             ║
║  For each day:                                                 │             ║
║  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────┐  │             ║
║  │ temperature.py  │  │ precipitation.py │  │ I_pot lookup │  │             ║
║  │                 │  │                  │  │              │  │             ║
║  │ T_ref = α·T+β  │  │ P(z) = P·corr·  │  │ ipot[doy]    │  │             ║
║  │ (monthly coeff) │  │  (1+grad·dz)    │  │              │  │             ║
║  │ T(z) = T_ref + │  │                  │  │              │  │             ║
║  │  lapse·dz      │  │ snow/rain split  │  │              │  │             ║
║  │                 │  │ at T0 ± 1°C     │  │              │  │             ║
║  │                 │  │                  │  │              │  │             ║
║  │                 │  │ wind redist:     │  │              │  │             ║
║  │                 │  │ P *= 1+kw·sx    │  │              │  │             ║
║  └────────┬────────┘  └────────┬─────────┘  └──────┬───────┘  │             ║
║           │                    │                    │          │             ║
║           ▼                    ▼                    ▼          │             ║
║  ┌─────────────────────────────────────────────────────────┐   │             ║
║  │                      melt.py                            │   │             ║
║  │                                                         │   │             ║
║  │  M = (MF + MF_grad·dz + r·I_pot) × T⁺ × dt           │   │             ║
║  │       ↑                  ↑                              │   │             ║
║  │    elev-dependent    r_snow or r_ice                    │   │             ║
║  │    melt factor       (r_ice = 2×r_snow)                │   │             ║
║  └────────────────────────────┬────────────────────────────┘   │             ║
║                               │                                │             ║
║                               ▼                                │             ║
║  ┌─────────────────────────────────────────────────────────┐   │             ║
║  │                    snowpack.py                          │   │             ║
║  │                                                         │   │             ║
║  │  SWE += snowfall - melt                                │   │             ║
║  │  Surface: snow(1) / firn(2) / ice(3)                   │   │             ║
║  │  Tracks: ice_melt, snow_melt separately                │   │             ║
║  └────────────────────────────┬────────────────────────────┘   │             ║
║                               │                                │             ║
║                               ▼                                │             ║
║  ┌─────────────────────────────────────────────────────────┐   │             ║
║  │                   massbalance.py                        │   │             ║
║  │                                                         │   │             ║
║  │  glacier_wide_balance = mean(accum - melt) over mask   │   │             ║
║  │  stake_balance = extract at ABL/ELA/ACC elevations     │   │             ║
║  └────────────────────────────┬────────────────────────────┘   │             ║
║                               │                                │             ║
╚═══════════════════════════════╪════════════════════════════════╪═════════════╝
                                │                                │
        ┌───────────────────────┼────────────────────────────────┘
        │                       │
        ▼                       ▼
┌───────────────────┐  ┌────────────────────┐  ┌─────────────────────────────┐
│  calibration.py   │  │ run_projection.py  │  │ snowline_validation.py      │
│                   │  │                    │  │                             │
│ Phase 1: Multi-   │  │ 250 params ×      │  │ 22 yrs digitized snowlines  │
│  seed DE → modes  │  │ 5 GCMs ×          │  │ vs modeled net_balance=0    │
│ Phase 2: Multi-   │  │ 2 SSPs            │  │ contour                     │
│  chain MCMC per   │  │                    │  │                             │
│  mode (D-027)     │  │ ┌────────────────┐ │  │ Excluded: WY2000, WY2005   │
│ Phase 3: Combine  │  │ │glacier_dynamics│ │  │ (>30% NaN threshold)        │
│  → 250 posterior  │  │ │.py             │ │  │                             │
│                   │  │ │                │ │  │ Metrics: RMSE, bias,        │
│ 6 free params:    │  │ │ delta-h        │ │  │ spatial overlap             │
│  MF, MF_grad,     │  │ │ thinning       │ │  └─────────────────────────────┘
│  r_snow, precip   │  │ │ (Huss 2010)    │ │
│  _grad, precip    │  │ │                │ │
│  _corr, T0        │  │ │ Volume-area    │ │
│                   │  │ │ scaling        │ │
│ Fixed: lapse_rate │  │ │                │ │
│  r_ice=2×r_snow   │  │ │ Farinotti ice  │ │
│  k_wind=0.0       │  │ │ thickness      │ │
│                   │  │ └────────────────┘ │
└───────────────────┘  │                    │
                       │ ┌────────────────┐ │
                       │ │ routing.py     │ │
                       │ │                │ │
                       │ │ 3 linear       │ │
                       │ │ reservoirs:    │ │
                       │ │ fast/slow/gw   │ │
                       │ │ → Q (m³/s)     │ │
                       │ └────────────────┘ │
                       └─────────┬──────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              OUTPUTS                                        │
│                                                                             │
│  ┌──────────────────┐  ┌────────────────┐  ┌──────────────────────────┐    │
│  │ Calibration      │  │ Projections    │  │ Validation               │    │
│  │                  │  │                │  │                          │    │
│  │ mcmc_chain.npy   │  │ PROJ-###/      │  │ snowline_validation.csv  │    │
│  │ posterior_params  │  │  area/volume   │  │ spatial comparison grids │    │
│  │ corner plots     │  │  balance       │  │ scatter/timeseries plots │    │
│  │ traceplots       │  │  discharge     │  │                          │    │
│  │                  │  │  peak water    │  │                          │    │
│  │                  │  │  retreat anim  │  │                          │    │
│  └──────────────────┘  └────────────────┘  └──────────────────────────┘    │
│                                                                             │
│  Peak Water: SSP2-4.5 → WY2043  |  SSP5-8.5 → WY2058                      │
└─────────────────────────────────────────────────────────────────────────────┘
```


## Top-Level Scripts

```
                           ┌──────────────────────┐
                           │   Top-Level Scripts   │
                           └──────────┬───────────┘
                                      │
     ┌────────────────────┬───────────┼───────────┬────────────────────┐
     │                    │           │           │                    │
     ▼                    ▼           ▼           ▼                    ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ CALIBRATION  │  │ PROJECTION   │  │ VALIDATION   │  │ DATA/CLIMATE │  │ DIAGNOSTICS  │
├──────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────┤  ├──────────────┤
│run_calibra-  │  │run_          │  │run_snowline  │  │download_     │  │analyze_      │
│tion_v12.py * │  │projection.py │  │_validation   │  │cmip6.py      │  │snotel_       │
│              │  │              │  │.py           │  │              │  │stations.py   │
│run_calibra-  │  │animate_      │  │              │  │compute_      │  │              │
│tion_v11.py   │  │glacier_      │  │              │  │transfer_     │  │run_kwind_    │
│              │  │retreat.py    │  │              │  │coefficients  │  │gridsearch.py │
│run_calibra-  │  │              │  │              │  │.py           │  │              │
│tion_v10.py   │  │              │  │              │  │              │  │              │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │                 │                 │
       ▼                 ▼                 ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ PLOT SCRIPTS │  │              │  │              │  │              │  │              │
├──────────────┤  │plot_projec-  │  │plot_snowline │  │plot_climate  │  │plot_kwind_   │
│plot_calibra- │  │tion_         │  │_all_years.py │  │_inputs_      │  │comparison.py │
│tion_v10.py   │  │ensemble.py   │  │              │  │comparison.py │  │              │
│              │  │              │  │plot_snowline │  │              │  │plot_dixon_   │
│              │  │              │  │_with_climate │  │plot_climate  │  │vs_all.py     │
│              │  │              │  │.py           │  │_gap_fill_    │  │              │
│              │  │              │  │              │  │diagnostics   │  │              │
│              │  │              │  │              │  │.py           │  │              │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘

* = current calibration script (multi-seed DE + multi-chain MCMC, D-027)
```


## Module Dependency Graph

```
config.py ←──────── (imported by all modules)
    │
    ├── terrain.py ──────────────┐
    │     (DEM, slope, aspect,   │
    │      mask, wind exposure)  │
    │                            │
    ├── solar.py                 │
    │     (I_pot, topo-corrected │
    │      direct radiation)     │
    │                            ├──→ model.py (full-featured, dev/testing)
    ├── temperature.py           │         │
    │     (lapse rate distrib.)  ├──→ fast_model.py (numba core, production)
    │                            │         │
    ├── precipitation.py         │         ├──→ calibration.py
    │     (elev grad, rain/snow) │         │      (objective function for DE)
    │                            │         │
    ├── melt.py                  │         ├──→ run_calibration_v12.py
    │     (DETIM Method 2)       │         │      (DE + MCMC orchestration)
    │                            │         │
    ├── snowpack.py              │         ├──→ run_projection.py
    │     (SWE tracking)         │         │      + glacier_dynamics.py
    │                            │         │      + routing.py
    └── massbalance.py ──────────┘         │      + climate_projections.py
          (point + glacier-wide)           │
                                           └──→ snowline_validation.py
    climate.py ─────────────────────────────────→ (feeds all run_* scripts)
      (multi-station gap-fill cascade, D-025)
```


## Two-Tier Model Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  model.py — DETIMModel class                                         │
│    Full-featured, pure-Python loop                                   │
│    Used for: development, testing, debugging                         │
│                                                                       │
│  fast_model.py — FastDETIM class                                     │
│    Numba-compiled monolithic kernel (~5× faster)                     │
│    Monthly temp transfer coefficients (statistical katabatic corr.)  │
│    Used for: calibration (1000s of runs), projections, validation    │
│                                                                       │
│  Both implement identical physics:                                   │
│    temp → precip → melt → snowpack → mass balance                   │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```


## Parameter Flow

```
┌─────────────────────────────────────────────┐
│            Calibrated Parameters             │
│                                              │
│  FREE (6):                                   │
│   MF .............. melt factor (mm/d/K)     │
│   MF_grad ........ elev. gradient of MF      │
│   r_snow ......... radiation factor, snow    │
│   precip_grad .... precip elev. gradient     │
│   precip_corr .... gauge undercatch corr.    │
│   T0 ............. rain/snow threshold (°C)  │
│                                              │
│  FIXED:                                      │
│   lapse_rate = -5.0 °C/km (D-015)           │
│   r_ice = 2 × r_snow  (Hock 1999)           │
│   k_wind = 0.0        (CAL-007)             │
│                                              │
│  DERIVED:                                    │
│   250 posterior sets → projections           │
│   MAP estimate → validation                  │
└─────────────────────────────────────────────┘
```


## Climate Gap-Fill Pipeline (D-025)

```
┌───────────────────────────────────────────────────────────────────┐
│                   Multi-Station Gap-Fill Cascade                  │
│                                                                   │
│  Primary: Nuka SNOTEL (375m) ──────────── 91.3% of days         │
│       ↓ (gaps)                                                    │
│  Fill 1: Middle Fork Bradley (701m) ───── 6.0%  (best T, r=.88) │
│       ↓ (gaps)                                                    │
│  Fill 2: McNeil Canyon (411m) ─────────── 1.8%  (WY2001 gaps)   │
│       ↓ (gaps)                                                    │
│  Fill 3: Anchor River Divide (503m) ───── 0.4%  (longest record)│
│       ↓ (gaps)                                                    │
│  Fill 4: Interpolation ───────────────── 0.3%                   │
│       ↓ (gaps)                                                    │
│  Fill 5: DOY climatology ──────────────── remainder              │
│                                                                   │
│  Each fill uses monthly reverse regression coefficients           │
│  (compute_transfer_coefficients.py) to adjust for elevation       │
│  and local effects.                                               │
│                                                                   │
│  Output: dixon_gap_filled_climate.csv (9,862 days, zero NaN)     │
└───────────────────────────────────────────────────────────────────┘
```


## Data Directory Structure

```
data/
├── climate/
│   ├── nuka_snotel_full.csv          (12,876 days, 1990–2024)
│   ├── dixon_gap_filled_climate.csv  (9,862 days, zero NaN, D-025)
│   └── snotel_stations/             (5 nearby SNOTEL CSVs)
├── cmip6/                            (5 GCMs × 2 SSPs = 10 CSVs)
└── ice_thickness/                    (Farinotti 2019 consensus)

ifsar_2010/
├── dixon_glacier_IFSAR_DTM_5m_full.tif
└── dixon_glacier_IFSAR_DSM_5m_full.tif

geodedic_mb/
├── dixon_glacier_outline_rgi7.geojson
├── dixon_glacier_hugonnet.csv
└── stake_observations_dixon.csv

dixon_observed_raw/                   (Dixon AWS, summer only)
snowlines_all/                        (22 shapefiles, 1999–2024)

calibration_output/                   (v1–v12 iterations)
projection_output/
├── PROJ-001_single-param_2025-03-10/
└── PROJ-002_top250-params_2026-03-11/
```
