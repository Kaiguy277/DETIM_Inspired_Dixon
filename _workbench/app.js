/* ===================================================================
   Dixon Glacier DETIM -- Interactive Model Workbench
   All data embedded. Safe DOM only: createElement, textContent, appendChild.
   =================================================================== */

// ── DOM helper ──────────────────────────────────────────────────────
function el(tag, attrs, children) {
  var node = document.createElement(tag);
  if (attrs) {
    Object.keys(attrs).forEach(function(k) {
      if (k === 'className') node.className = attrs[k];
      else if (k === 'textContent') node.textContent = attrs[k];
      else if (k === 'htmlFor') node.htmlFor = attrs[k];
      else if (k.indexOf('on') === 0) node.addEventListener(k.slice(2).toLowerCase(), attrs[k]);
      else if (k === 'style' && typeof attrs[k] === 'object') {
        Object.keys(attrs[k]).forEach(function(s) { node.style[s] = attrs[k][s]; });
      } else node.setAttribute(k, attrs[k]);
    });
  }
  if (children) {
    if (!Array.isArray(children)) children = [children];
    children.forEach(function(c) {
      if (c == null) return;
      if (typeof c === 'string' || typeof c === 'number') {
        node.appendChild(document.createTextNode(String(c)));
      } else {
        node.appendChild(c);
      }
    });
  }
  return node;
}

// ── DATA ────────────────────────────────────────────────────────────

var DATA = {};

DATA.stakes = [
  {site:"ABL",period:"annual",year:2023,start:"2022-10-01",end:"2023-10-03",mb:-4.5,unc:0.12,elev:804},
  {site:"ABL",period:"summer",year:2023,start:"2023-05-02",end:"2023-10-03",mb:-5.35,unc:0.12,elev:804},
  {site:"ABL",period:"winter",year:2023,start:"2022-10-01",end:"2023-05-02",mb:0.85,unc:0.10,elev:804},
  {site:"ABL",period:"annual",year:2024,start:"2023-10-01",end:"2024-09-20",mb:-2.63,unc:0.12,elev:804},
  {site:"ABL",period:"summer",year:2024,start:"2024-04-29",end:"2024-09-20",mb:-4.56,unc:0.12,elev:804},
  {site:"ABL",period:"winter",year:2024,start:"2023-10-01",end:"2024-04-29",mb:1.93,unc:0.10,elev:804},
  {site:"ABL",period:"winter",year:2025,start:"2024-10-01",end:"2025-05-11",mb:1.6,unc:0.10,elev:804},
  {site:"ACC",period:"annual",year:2023,start:"2022-10-01",end:"2023-10-03",mb:0.37,unc:0.12,elev:1293},
  {site:"ACC",period:"summer",year:2023,start:"2023-05-02",end:"2023-10-03",mb:-2.25,unc:0.12,elev:1293},
  {site:"ACC",period:"winter",year:2023,start:"2022-10-01",end:"2023-05-02",mb:2.45,unc:0.10,elev:1293},
  {site:"ACC",period:"annual",year:2024,start:"2023-10-01",end:"2024-09-20",mb:1.46,unc:0.12,elev:1293},
  {site:"ACC",period:"summer",year:2024,start:"2024-04-29",end:"2024-09-20",mb:-1.55,unc:0.12,elev:1293},
  {site:"ACC",period:"winter",year:2024,start:"2023-10-01",end:"2024-04-29",mb:3.01,unc:0.10,elev:1293},
  {site:"ACC",period:"winter",year:2025,start:"2024-10-01",end:"2025-05-11",mb:3.53,unc:0.15,elev:1293},
  {site:"ACC",period:"annual",year:2025,start:"2024-10-01",end:"2025-10-01",mb:1.875,unc:0.15,elev:1293},
  {site:"ACC",period:"summer",year:2025,start:"2025-05-11",end:"2025-10-01",mb:-1.655,unc:0.15,elev:1293},
  {site:"ELA",period:"annual",year:2023,start:"2022-10-01",end:"2023-10-03",mb:0.1,unc:0.12,elev:1078},
  {site:"ELA",period:"summer",year:2023,start:"2023-05-02",end:"2023-10-03",mb:-2.26,unc:0.12,elev:1078},
  {site:"ELA",period:"winter",year:2023,start:"2022-10-01",end:"2023-05-02",mb:2.36,unc:0.10,elev:1078},
  {site:"ELA",period:"annual",year:2024,start:"2023-10-01",end:"2024-09-20",mb:0.1,unc:0.12,elev:1078},
  {site:"ELA",period:"summer",year:2024,start:"2024-04-29",end:"2024-09-20",mb:-2.5,unc:0.12,elev:1078},
  {site:"ELA",period:"winter",year:2024,start:"2023-10-01",end:"2024-04-29",mb:2.6,unc:0.10,elev:1078},
  {site:"ELA",period:"winter",year:2025,start:"2024-10-01",end:"2025-05-11",mb:3.04,unc:0.10,elev:1078},
  {site:"ELA",period:"annual",year:2025,start:"2024-10-01",end:"2025-10-01",mb:1.08,unc:0.12,elev:1078},
  {site:"ELA",period:"summer",year:2025,start:"2025-05-11",end:"2025-10-01",mb:-1.96,unc:0.12,elev:1078}
];

DATA.geodetic = [
  {period:"2000-2010",area_m2:39858000,dhdt:-1.2613,err:0.246,dmdtda:-1.0721,err_dm:0.2248},
  {period:"2010-2020",area_m2:39858000,dhdt:-0.9481,err:0.2257,dmdtda:-0.8059,err_dm:0.2017},
  {period:"2000-2020",area_m2:39858000,dhdt:-1.1047,err:0.115,dmdtda:-0.939,err_dm:0.1216}
];

DATA.snowlines = [
  {year:1995,date:"1995-08-20",source:"landsat-5",mean:1027.3,median:1030.8,min:926.2,max:1155.9,std:55.0,n:780},
  {year:1999,date:"1999-09-08",source:"landsat-7",mean:1107.4,median:1086.6,min:1040.8,max:1297.0,std:58.3,n:975},
  {year:2000,date:"2000-08-09",source:"landsat-7",mean:1036.2,median:1021.9,min:960.8,max:1201.4,std:56.1,n:578},
  {year:2003,date:"2003-08-02",source:"landsat-7",mean:984.3,median:984.8,min:929.6,max:1029.3,std:23.9,n:666},
  {year:2004,date:"2004-08-29",source:"landsat-7",mean:1203.8,median:1197.2,min:1130.5,max:1340.9,std:50.7,n:752},
  {year:2005,date:"2005-09-08",source:"landsat-7",mean:1106.7,median:1096.8,min:1046.9,max:1183.9,std:37.6,n:755},
  {year:2006,date:"2006-09-19",source:"landsat-5",mean:1110.0,median:1108.0,min:1029.6,max:1203.3,std:41.9,n:1002},
  {year:2007,date:"2007-09-06",source:"landsat-5",mean:1128.9,median:1126.9,min:1036.6,max:1327.0,std:67.3,n:988},
  {year:2009,date:"2009-09-19",source:"landsat-7",mean:1232.3,median:1224.7,min:1190.9,max:1282.9,std:22.5,n:524},
  {year:2010,date:"2010-09-15",source:"landsat-7",mean:1086.5,median:1083.5,min:956.1,max:1224.0,std:61.0,n:1139},
  {year:2011,date:"2011-09-18",source:"landsat-7",mean:1064.8,median:1052.5,min:1013.9,max:1159.1,std:34.4,n:476},
  {year:2012,date:"2012-10-06",source:"landsat-7",mean:1079.8,median:1071.2,min:1017.6,max:1165.6,std:40.8,n:566},
  {year:2013,date:"2013-09-15",source:"landsat-8",mean:1158.3,median:1157.6,min:1045.9,max:1311.7,std:57.0,n:2225},
  {year:2014,date:"2014-09-25",source:"landsat-8",mean:1238.2,median:1250.6,min:1159.2,max:1292.1,std:38.7,n:674},
  {year:2015,date:"2015-08-27",source:"unknown",mean:1054.6,median:1057.3,min:961.4,max:1132.7,std:48.9,n:915},
  {year:2016,date:"2016-08-29",source:"landsat-8",mean:1073.8,median:1056.6,min:968.6,max:1193.0,std:55.5,n:799},
  {year:2017,date:"2017-09-30",source:"sentinel-2",mean:1161.3,median:1161.9,min:1044.4,max:1306.6,std:59.3,n:1744},
  {year:2018,date:"2018-10-05",source:"sentinel-2",mean:1170.4,median:1171.8,min:1070.5,max:1243.2,std:44.8,n:1456},
  {year:2019,date:"2019-09-17",source:"sentinel-2",mean:1159.6,median:1152.1,min:1054.1,max:1355.5,std:61.5,n:2420},
  {year:2020,date:"2020-10-06",source:"sentinel-2",mean:1126.3,median:1124.9,min:1067.4,max:1221.4,std:33.9,n:1045},
  {year:2021,date:"2021-09-19",source:"sentinel-2",mean:1088.3,median:1076.7,min:1018.4,max:1189.7,std:40.3,n:853},
  {year:2023,date:"2023-09-29",source:"sentinel-2",mean:1124.8,median:1110.6,min:1065.0,max:1264.6,std:48.7,n:939},
  {year:2024,date:"2024-09-20",source:"sentinel-2",mean:1166.4,median:1177.9,min:1007.8,max:1338.1,std:69.7,n:1712}
];

DATA.areas = [
  {year:2000,area:40.11,source:"manual_digitization"},
  {year:2005,area:40.11,source:"manual_digitization"},
  {year:2010,area:39.83,source:"manual_digitization"},
  {year:2015,area:39.26,source:"manual_digitization"},
  {year:2020,area:38.59,source:"manual_digitization"},
  {year:2025,area:38.34,source:"manual_digitization"}
];

DATA.sensitivity = [
  {param:"lapse_rate",value:-4.0,geod_mod:-1.631,geod_obs:-0.939,bias:-0.692,stake_rmse:1.800},
  {param:"lapse_rate",value:-4.5,geod_mod:-1.216,geod_obs:-0.939,bias:-0.277,stake_rmse:1.497},
  {param:"lapse_rate",value:-5.0,geod_mod:-0.817,geod_obs:-0.939,bias:0.122,stake_rmse:1.227},
  {param:"lapse_rate",value:-5.5,geod_mod:-0.434,geod_obs:-0.939,bias:0.505,stake_rmse:1.005},
  {param:"lapse_rate",value:-6.0,geod_mod:-0.063,geod_obs:-0.939,bias:0.876,stake_rmse:0.850},
  {param:"lapse_rate",value:-6.5,geod_mod:0.296,geod_obs:-0.939,bias:1.235,stake_rmse:0.781},
  {param:"rice_ratio",value:1.50,geod_mod:-0.773,geod_obs:-0.939,bias:0.166,stake_rmse:1.188},
  {param:"rice_ratio",value:1.75,geod_mod:-0.795,geod_obs:-0.939,bias:0.144,stake_rmse:1.207},
  {param:"rice_ratio",value:2.00,geod_mod:-0.817,geod_obs:-0.939,bias:0.122,stake_rmse:1.227},
  {param:"rice_ratio",value:2.25,geod_mod:-0.839,geod_obs:-0.939,bias:0.100,stake_rmse:1.248},
  {param:"rice_ratio",value:2.50,geod_mod:-0.862,geod_obs:-0.939,bias:0.077,stake_rmse:1.271},
  {param:"rice_ratio",value:3.00,geod_mod:-0.906,geod_obs:-0.939,bias:0.033,stake_rmse:1.318}
];

DATA.lapseProjections = [
  {lapse:-4.5,scenario:"ssp126",area_p50:19.67,area_p05:17.46,area_p95:26.59,vol_p50:2.168,peak_year:2017,peak_q:8.857},
  {lapse:-4.5,scenario:"ssp245",area_p50:15.78,area_p05:13.37,area_p95:20.17,vol_p50:1.410,peak_year:2017,peak_q:8.857},
  {lapse:-4.5,scenario:"ssp585",area_p50:5.41,area_p05:3.88,area_p95:18.35,vol_p50:0.192,peak_year:2017,peak_q:8.857},
  {lapse:-5.0,scenario:"ssp126",area_p50:25.00,area_p05:21.76,area_p95:32.64,vol_p50:2.914,peak_year:2017,peak_q:8.490},
  {lapse:-5.0,scenario:"ssp245",area_p50:19.60,area_p05:17.04,area_p95:25.53,vol_p50:2.157,peak_year:2017,peak_q:8.490},
  {lapse:-5.0,scenario:"ssp585",area_p50:10.49,area_p05:8.79,area_p95:22.57,vol_p50:0.516,peak_year:2017,peak_q:8.490},
  {lapse:-5.5,scenario:"ssp126",area_p50:31.67,area_p05:28.13,area_p95:37.37,vol_p50:4.020,peak_year:2018,peak_q:8.100},
  {lapse:-5.5,scenario:"ssp245",area_p50:25.17,area_p05:21.07,area_p95:32.06,vol_p50:2.937,peak_year:2018,peak_q:8.100},
  {lapse:-5.5,scenario:"ssp585",area_p50:13.91,area_p05:13.30,area_p95:29.23,vol_p50:1.073,peak_year:2065,peak_q:8.726}
];

DATA.bestParams = {
  MF:7.110,MF_grad:-0.00411,r_snow:0.00196,r_ice:0.00392,
  precip_grad:0.000694,precip_corr:1.621,T0:0.000254,
  lapse_rate:-5.0,k_wind:0.0
};

DATA.calSummary = {
  version:13,id:"CAL-013",method:"Multi-objective DE+MCMC (stakes+geodetic+snowline) + area filter",
  decision:"D-028",n_samples:1656,acceptance:0.368,
  wall_time_h:11.2,de_seeds:[42,123,456,789,2024],n_modes:1,
  de_best_cost:5.343,
  posteriorRanges:{MF:[7.06,7.58],precip_corr:[1.47,1.74],MF_grad:[-0.0045,-0.0038],
    r_snow:[0.0017,0.0022],precip_grad:[0.0004,0.0010],T0:[0.0,0.01]}
};

DATA.constants = {
  LATITUDE:59.66,LONGITUDE:-150.88,ELEV_MIN:439,ELEV_MAX:1637,
  GLACIER_AREA:40.1,SNOTEL_ELEV:375,DIXON_AWS_ELEV:1078,
  SOLAR_CONSTANT:1368,PSI_A:0.75,ICE_DENSITY:900,WATER_DENSITY:1000,
  TARGET_RESOLUTION:50,WIND_AZIMUTH:100,WIND_SEARCH_DIST:300,
  VA_C:0.0340,VA_GAMMA:1.36
};

// ── MODULES ─────────────────────────────────────────────────────────

DATA.modules = [
  {name:"config.py",path:"dixon_melt/config.py",lines:193,category:"Core",
   deps:[],decisions:["D-013","D-015","D-017","D-023"],
   description:"Site-specific configuration and physical constants for Dixon Glacier. Contains all elevation references, station metadata, temperature transfer coefficients, gap-filling parameters, default model parameters, physical constants, delta-h coefficients, and routing defaults.\n\nThis file is the single source of truth for every number in the model that is not a calibrated parameter. Every correction to elevation data (D-013: Nuka from 1230m to 375m; D-023: Dixon AWS from 804m to 1078m) propagated through config.py first. The multi-station gap-filling coefficients (D-025) live here as monthly slope/intercept arrays computed from overlapping SNOTEL records.\n\nThe default parameters serve as initial guesses for calibration and as the parameter set used when running the model outside calibration. The fixed parameters (lapse_rate = -5.0 C/km, r_ice = 2x r_snow, k_wind = 0) were deliberately removed from calibration (D-015, D-017) to prevent equifinality.\n\nIf any constant here were wrong, the entire model would be silently miscalibrated. The Nuka elevation error (D-013) is the clearest example: 855m of wrong elevation caused every calibration from CAL-001 through CAL-007 to fail, and the error was invisible until someone checked the NRCS website and noticed the units were feet, not meters.",
   equations:["All constants: see parameter table"],
   params:[
     {name:"SNOTEL_ELEV",val:"375.0 m",desc:"Nuka SNOTEL elevation (1230 ft converted)"},
     {name:"DIXON_AWS_ELEV",val:"1078.0 m",desc:"On-glacier AWS at ELA site"},
     {name:"PSI_A",val:"0.75",desc:"Clear-sky atmospheric transmissivity"},
     {name:"TARGET_RESOLUTION",val:"50.0 m",desc:"Model grid cell size"},
     {name:"VA_C / VA_GAMMA",val:"0.034 / 1.36",desc:"Volume-area scaling (Bahr et al. 1997)"}
   ]},

  {name:"fast_model.py",path:"dixon_melt/fast_model.py",lines:369,category:"Core",
   deps:["config.py"],decisions:["D-004","D-007","D-009","D-012","D-013"],
   description:"The Numba-compiled simulation kernel -- the computational heart of the model. This single @njit(parallel=True) function runs the full DETIM physics for an arbitrary time period on the entire glacier grid, returning cumulative melt, accumulation, daily runoff, stake balances, glacier-wide balance, and end-of-run SWE.\n\nPhysically, fast_model.py implements the daily loop that every glacier model needs: for each day, distribute temperature from the reference station to every grid cell using a lapse rate, partition precipitation into rain and snow using a threshold temperature with a 2-degree transition zone, compute potential melt using the DETIM equation (MF + r_surface * I_pot) * T+, track snowpack evolution, and accumulate mass balance. The elevation-dependent melt factor (MF_grad) reduces melt efficiency at higher elevations, capturing the integrated effects of lower temperatures, higher albedo, and less absorbed longwave radiation.\n\nThe function takes raw Nuka SNOTEL temperature at 375m and applies identity transfer (alpha=1, beta=0 for all months, per D-012) followed by the calibrated lapse rate to reach each grid cell. This design means the melt factor MF implicitly absorbs the ~3C katabatic cooling that exists between free-air and on-glacier temperatures -- exactly as Hock (1999) intended for DETIM.\n\nPerformance matters because calibration requires ~250,000 evaluations (5 DE seeds x 200 iterations x 250 population + MCMC). Each evaluation runs the model for 1-25 water years on a 578x233 grid. Numba JIT compilation plus parallel=True across grid cells reduces per-evaluation time from several seconds to ~300ms, making the full calibration feasible in ~20 hours.\n\nIf this function had a bug in temperature distribution, the entire mass balance would be wrong. The elevation reference error (D-006, D-013) is the clearest example: setting ref_elev to 1230m instead of 375m reversed the sign of the lapse correction, making every cell ~3-4C too warm.",
   equations:["M = (MF + r \\cdot I_{pot}) \\cdot T^+","T_{cell} = T_{nuka} + \\lambda \\cdot (z_{cell} - z_{ref})","P_{cell} = P_{nuka} \\cdot c_p \\cdot (1 + p_g \\cdot (z_{cell} - z_{ref}))"],
   params:[
     {name:"MF",val:"7.11 mm/d/K",desc:"Melt factor (MAP from CAL-013)"},
     {name:"MF_grad",val:"-0.0041 mm/d/K/m",desc:"Elevation gradient of melt factor"},
     {name:"r_snow",val:"0.00196 mm m2/W/d/K",desc:"Radiation factor for snow"},
     {name:"r_ice",val:"0.00392 mm m2/W/d/K",desc:"Radiation factor for ice (2x r_snow)"},
     {name:"lapse_rate",val:"-5.0 C/km",desc:"Fixed temperature lapse rate"},
     {name:"precip_corr",val:"1.621",desc:"Precipitation correction factor"},
     {name:"T0",val:"~0.0 C",desc:"Rain/snow threshold temperature"}
   ]},

  {name:"calibration.py",path:"dixon_melt/calibration.py",lines:169,category:"Core",
   deps:["model.py","massbalance.py","fast_model.py"],decisions:["D-003","D-005","D-014","D-017","D-028"],
   description:"The objective function builder for differential evolution calibration. This module defines the mathematical cost function that tells the optimizer how well a given parameter set reproduces observations. It is the bridge between physical measurements (stake mass balance, geodetic mass balance, snowline elevations) and abstract parameter optimization.\n\nThe cost function uses inverse-variance weighting (D-014): each observation contributes (residual / sigma)^2, where sigma is the reported measurement uncertainty. This means the geodetic mass balance (-0.939 +/- 0.122 m w.e./yr over 2000-2020), with its tight uncertainty, naturally dominates the cost function compared to individual stake measurements (+/- 0.10-0.15 m w.e.). A hard penalty (lambda=50) is added when the geodetic residual exceeds the reported uncertainty bounds, preventing the optimizer from sacrificing the 20-year integrated constraint to chase individual stake years.\n\nFor CAL-013 (D-028), snowline elevations were added as a chi-squared term in the MCMC log-likelihood with sigma=75m, combining observed spatial spread, model resolution, and temporal mismatch. This was necessary because post-hoc snowline filtering had zero discriminating power -- all 1000 posterior samples from CAL-012 scored within an 8m RMSE range.\n\nThe function runs the model for each calibration target period (annual Oct-Oct, summer May-Sep, geodetic 2000-2020) and extracts the relevant output. Annual runs start with SWE=0; summer runs initialize with observed winter balance at ELA. This two-initialization approach was a critical fix (D-005) that resolved the SWE double-counting that caused all v1 parameters to hit their bounds.",
   equations:["\\mathcal{L} = -\\frac{1}{2} \\sum_i \\left(\\frac{y_i - \\hat{y}_i}{\\sigma_i}\\right)^2"],
   params:[
     {name:"sigma_stakes",val:"0.10-0.15 m w.e.",desc:"Stake measurement uncertainty"},
     {name:"sigma_geodetic",val:"0.122 m w.e./yr",desc:"Hugonnet 2000-2020 uncertainty"},
     {name:"sigma_snowline",val:"75 m",desc:"Combined snowline uncertainty"},
     {name:"lambda_penalty",val:"50",desc:"Hard geodetic penalty multiplier"}
   ]},

  {name:"climate.py",path:"dixon_melt/climate.py",lines:606,category:"Data",
   deps:["config.py"],decisions:["D-002","D-025"],
   description:"Climate data ingestion, quality control, and multi-station gap-filling. This is the largest module (606 lines) because getting the input forcing right is the most important -- and historically most problematic -- part of the model.\n\nThe module loads Nuka SNOTEL daily data (temperature and precipitation since 1990), converts from imperial to metric (F to C, inches to mm), and fills gaps using a cascade of 5 nearby SNOTEL stations. The gap-filling cascade (D-025) replaced the original ffill().fillna(0) approach that had been silently poisoning calibration: when Nuka had multi-month temperature gaps (e.g., WY2005: 132 of 153 melt-season days missing), fillna(0) set summer temperatures to 0C, killing all melt in those years. The model compensated by cranking up the melt factor to over-melt in clean years.\n\nEach fill station has monthly regression coefficients (T_nuka = slope * T_other + intercept) computed from overlapping valid days, stored in config.py. The cascade fills 91.3% of days from original Nuka data, 6.0% from Middle Fork Bradley, 1.8% from McNeil Canyon, with the remainder from interpolation and climatology. Precipitation uses monthly ratios (Nuka/MFB) for gap periods, most critically WY2020 where 192 days of precipitation were missing, losing 1,019mm of real accumulation.\n\nThe module also handles Dixon AWS data loading for validation, and provides utilities for extracting water-year subsets and computing climatologies. The output is a zero-NaN daily climate file that all downstream components (calibration, snowline validation, projections) consume.\n\nIf the gap-filling were wrong, the geodetic sub-period comparison would fail: the model would produce incorrect decadal mass balances because gap years cluster in 2000-2005.",
   equations:["T_{nuka} = \\alpha_m \\cdot T_{station} + \\beta_m","P_{nuka} = r_m \\cdot P_{mfb}"],
   params:[
     {name:"TEMP_FILL_ORDER",val:"mfb, mcneil, anchor, kachemak, lower_kach",desc:"Station cascade priority"},
     {name:"Coverage",val:"91.3% Nuka, 6.0% MFB, 1.8% McNeil",desc:"Gap-fill source breakdown"}
   ]},

  {name:"glacier_dynamics.py",path:"dixon_melt/glacier_dynamics.py",lines:451,category:"Core",
   deps:["config.py"],decisions:["D-018"],
   description:"Glacier geometry evolution using the delta-h parameterization of Huss et al. (2010). This module answers the question: as the glacier loses mass, WHERE does it thin, and WHEN do cells deglaciate?\n\nThe delta-h method is an empirical parameterization that distributes a glacier-wide mass change across the elevation profile. The key insight is that glaciers thin most at the terminus and least at the headwall, following a power-law shape that depends on glacier size. For Dixon (~40 km2, a 'large' glacier), the exponent gamma=6 produces a very steep terminus-weighted thinning pattern: the lowest cells receive ~12x more thinning than cells near the headwall.\n\nThe module tracks ice thickness for every grid cell, initialized from the Farinotti et al. (2019) consensus thickness estimate. Each year, the glacier-wide mass balance is converted to a volume change, distributed via delta-h, and subtracted from ice thickness. Cells where ice thickness drops below 1m are removed from the glacier mask -- they have deglaciated, exposing bedrock. The surface DEM is updated each year: thinning cells lower the surface, deglaciated cells snap to bedrock elevation.\n\nDynamic size-class switching is critical for long projections: as Dixon shrinks below 20 km2 (expected mid-century under SSP5-8.5), it transitions to 'medium' glacier coefficients with a less terminus-concentrated thinning pattern. This feedback means retreat accelerates as the glacier enters a different dynamical regime.\n\nThree bugs in the original implementation (D-018) produced qualitatively wrong retreat patterns: wrong size class coefficients, inverted h_r convention (maximum thinning at headwall instead of terminus), and no ice thickness tracking (cells losing 4m/yr for a decade were never removed).",
   equations:["\\Delta h = (h_r + a)^\\gamma + b(h_r + a) + c","V = c_V \\cdot A^{\\gamma_V}","h_r = \\frac{z_{max} - z}{z_{max} - z_{min}}"],
   params:[
     {name:"gamma (large)",val:"6",desc:"Thinning concentration exponent, A > 20 km2"},
     {name:"a, b, c (large)",val:"-0.02, 0.12, 0.00",desc:"Huss et al. (2010) coefficients"},
     {name:"VA_C / VA_GAMMA",val:"0.034 / 1.36",desc:"Volume-area scaling"},
     {name:"ice_min",val:"1 m",desc:"Deglaciation threshold"}
   ]},

  {name:"snowline_validation.py",path:"dixon_melt/snowline_validation.py",lines:328,category:"Validation",
   deps:["fast_model.py","config.py","terrain.py"],decisions:["D-021","D-022","D-028"],
   description:"Independent validation of the model against 22 years of digitized snowline observations (1995-2024). These snowlines were derived from Landsat and Sentinel-2 imagery by manually tracing the snow/ice boundary, then extracting elevations from the IfSAR DEM. They were NEVER used in calibration until D-028 added them to the MCMC likelihood.\n\nFor each observation year, the module runs the model from October 1 to the satellite acquisition date, then extracts the modeled snowline as the contour where net balance (accumulation minus melt) equals zero. The comparison metrics include mean elevation bias, RMSE, correlation, and the balance at observed snowline locations (ideally zero if the model correctly identifies the ELA).\n\nThe structural limitation analysis (D-028) revealed that DETIM produces snowlines that are too spatially uniform: observed snowlines have within-year spatial standard deviations of 24-69m (reflecting wind redistribution, aspect effects, and local topography), while modeled snowlines have standard deviations of only 6-22m (essentially following elevation contours). The model also over-amplifies interannual variability (std 129m vs observed 63m). These limitations are inherent to DETIM's elevation-only precipitation distribution and cannot be resolved by parameter tuning.\n\nYears with >30% missing melt-season temperature data (D-022) are automatically excluded, catching WY2000 and WY2005 where the original fillna(0) approach would have produced unrealistically low snowlines.",
   equations:["RMSE_{snowline} = \\sqrt{\\frac{1}{N}\\sum(z_{mod} - z_{obs})^2}"],
   params:[
     {name:"sigma_snowline",val:"75 m",desc:"Total uncertainty for likelihood"},
     {name:"nan_threshold",val:"30%",desc:"Max missing melt-season T for inclusion"},
     {name:"n_years",val:"22 (19 valid after D-022)",desc:"Observation coverage"}
   ]},

  {name:"behavioral_filter.py",path:"dixon_melt/behavioral_filter.py",lines:418,category:"Validation",
   deps:["glacier_dynamics.py","fast_model.py","config.py"],decisions:["D-028"],
   description:"Post-hoc screening of posterior parameter sets against observed glacier area evolution. The behavioral filter runs each candidate parameter set through the full glacier dynamics simulation (2000-2025) and compares modeled area at 6 checkpoint years against manually digitized glacier outlines.\n\nThe filter implements the GLUE (Generalized Likelihood Uncertainty Estimation) philosophy of Beven and Binley (1992): not all parameter sets that fit the calibration data are 'behavioral' -- some produce unrealistic glacier retreat patterns despite matching stake and geodetic mass balance. The area checkpoints add a temporal constraint that the calibration targets lack: the geodetic mass balance only constrains the 20-year MEAN, while area evolution constrains the TRAJECTORY.\n\nFor CAL-013, all 1000 posterior samples passed the 1.0 km2 RMSE threshold, demonstrating that the snowline-informed likelihood (D-028) had already pushed the posterior into a region consistent with observed retreat. This is actually the ideal outcome: it means the in-likelihood constraints are sufficient and the post-hoc filter is not discarding good samples. The filter remains valuable as a safety check for future calibrations.\n\nThe 6 digitized outlines span 2000-2025 at 5-year intervals, showing Dixon retreating from 40.11 km2 to 38.34 km2 (a loss of 1.77 km2 or 4.4%). The retreat is concentrated at the terminus and along thin marginal ice, consistent with the delta-h thinning pattern.",
   equations:["RMSE_{area} = \\sqrt{\\frac{1}{N}\\sum(A_{mod}(t_i) - A_{obs}(t_i))^2}"],
   params:[
     {name:"RMSE threshold",val:"1.0 km2",desc:"Maximum allowed area RMSE"},
     {name:"Checkpoints",val:"2000, 2005, 2010, 2015, 2020, 2025",desc:"5-year intervals"},
     {name:"Pass rate (CAL-013)",val:"1000/1000 (100%)",desc:"All samples behavioral"}
   ]},

  {name:"solar.py",path:"dixon_melt/solar.py",lines:187,category:"Physics",
   deps:["config.py"],decisions:["D-001"],
   description:"Computation of potential clear-sky direct solar radiation (I_pot) for every grid cell on every day of the year. This is the 'enhanced' in 'Enhanced Temperature Index' -- what separates DETIM Method 2 from a basic degree-day model.\n\nThe module computes the sun's position (declination, hour angle, zenith, azimuth) for Dixon's latitude (59.66N) at sub-hourly resolution, then traces the solar beam path to determine whether each grid cell is illuminated or shaded by surrounding topography. The result is a 365 x nrows x ncols lookup table of daily integrated radiation in W/m2, precomputed once and reused for every model run.\n\nAt Dixon's high latitude, solar geometry creates dramatic spatial variability: south-facing slopes at the terminus receive 3-4x more radiation than north-facing headwall slopes. In midsummer (DOY 172), the sun is above the horizon for ~19 hours, but much of the glacier's northern aspect receives only oblique illumination. The shading calculation uses the terrain module's horizon angles to block direct beam when the sun is below the local horizon.\n\nThe radiation factors r_snow and r_ice multiply I_pot in the melt equation, allowing the model to differentiate melt rates between snow-covered and ice-exposed surfaces at the same temperature. The ratio r_ice/r_snow (fixed at 2.0) captures the albedo feedback: bare ice absorbs roughly twice as much shortwave radiation as snow.",
   equations:["I_{pot} = S_0 \\cdot \\psi_a^{P/(P_0 \\cos\\theta_z)} \\cdot \\cos\\theta_i","\\cos\\theta_i = \\cos\\theta_z\\cos\\beta + \\sin\\theta_z\\sin\\beta\\cos(\\phi_s - \\phi_n)"],
   params:[
     {name:"S_0",val:"1368 W/m2",desc:"Solar constant"},
     {name:"PSI_A",val:"0.75",desc:"Atmospheric transmissivity"},
     {name:"Resolution",val:"Sub-hourly integration",desc:"Temporal resolution for solar geometry"}
   ]},

  {name:"terrain.py",path:"dixon_melt/terrain.py",lines:238,category:"Data",
   deps:["config.py"],decisions:["D-011"],
   description:"DEM loading, reprojection, slope/aspect computation, horizon angle calculation, and wind exposure (Sx) mapping. This module transforms the raw 5m IfSAR DEM into all the terrain derivatives the model needs.\n\nThe DEM is resampled from 5m to the model resolution (50m for calibration, finer for visualization). Slope and aspect are computed using standard finite differences, then used by the solar module to calculate incident radiation angles. Horizon angles are computed along 72 azimuth directions to enable topographic shading.\n\nThe Winstral Sx parameter (D-011) quantifies wind exposure: for each cell, a search along the prevailing wind direction (100 degrees, ESE) finds the maximum upward angle to the horizon within 300m upwind. Positive Sx means the cell is sheltered (in the lee), negative means exposed (on the windward side). The Sx field is normalized to [-1, +1] and zero-meaned over the glacier so that wind redistribution conserves mass.\n\nAlthough k_wind was set to zero in calibration (CAL-007 converged to k_wind~0), the Sx field remains computed and stored because the snowline validation revealed systematic spatial patterns (western/southern branch snowlines 100m lower than eastern) that match the expected wind deposition pattern. The Sx field is available for future work if additional constraints become available.",
   equations:["S_x = \\max\\left(\\arctan\\frac{z_{upwind} - z_{cell}}{d}\\right)","P_{cell} = P_{base} \\cdot (1 + k_{wind} \\cdot S_x)"],
   params:[
     {name:"WIND_AZIMUTH",val:"100 deg (ESE)",desc:"Prevailing wind during precipitation"},
     {name:"WIND_SEARCH_DIST",val:"300 m",desc:"Maximum upwind search distance"},
     {name:"DEM source",val:"IfSAR 2010, 5m",desc:"Input DEM for all terrain products"}
   ]},

  {name:"model.py",path:"dixon_melt/model.py",lines:264,category:"Core",
   deps:["config.py","solar.py","terrain.py","fast_model.py"],decisions:["D-009"],
   description:"The Pandas-based orchestrator that wraps the Numba kernel for analysis runs. While fast_model.py handles the computation, model.py manages I/O, parameter setting, grid initialization, and output formatting. It provides a clean DETIMModel class interface for scripts that need more than raw arrays.\n\nThe DETIMModel class loads the DEM, computes all terrain derivatives (slope, aspect, horizon angles, Sx), builds the 365-day solar radiation lookup table, and provides methods like run_period(), set_params(), and reset(). It produces DataFrame outputs with dates, spatial maps, and summary statistics that are more convenient for analysis and plotting than the raw Numba arrays.\n\nThis module exists because Numba functions cannot handle Pandas DataFrames, file I/O, or complex object-oriented patterns. The two-code-path trade-off (D-004) means any physics change must be implemented in BOTH fast_model.py and model.py to keep them in sync.",
   equations:["Same as fast_model.py"],
   params:[]},

  {name:"climate_projections.py",path:"dixon_melt/climate_projections.py",lines:235,category:"Projection",
   deps:["config.py","climate.py"],decisions:["D-019"],
   description:"CMIP6 climate scenario loading and bias correction for glacier projections. This module bridges the gap between global climate model output (0.25-degree, daily, raw) and the glacier-specific forcing the DETIM model needs.\n\nBias correction uses the monthly delta method against Nuka SNOTEL 1991-2020 climatology: for temperature, the GCM's monthly mean bias is subtracted (additive correction); for precipitation, the ratio of observed to GCM monthly totals is applied (multiplicative correction). This preserves the GCM's interannual variability and trend while anchoring the climatology to local observations.\n\nThe module loads 5 GCMs (ACCESS-CM2, EC-Earth3, MPI-ESM1-2-HR, MRI-ESM2-0, NorESM2-MM) across 3 SSP scenarios. The GCM selection follows Rounce et al. (2023), choosing models with good high-latitude performance from diverse modeling centers to span the climate model structural uncertainty.\n\nEach GCM provides 2015-2100 daily temperature and precipitation at the nearest 0.25-degree pixel to Dixon Glacier. The bias-corrected output feeds directly into run_projection.py for ensemble glacier simulations.",
   equations:["T_{corr}(d) = T_{gcm}(d) - (\\overline{T}_{gcm,m} - \\overline{T}_{obs,m})","P_{corr}(d) = P_{gcm}(d) \\cdot \\frac{\\overline{P}_{obs,m}}{\\overline{P}_{gcm,m}}"],
   params:[
     {name:"Reference period",val:"1991-2020",desc:"Nuka SNOTEL climatology for bias correction"},
     {name:"GCMs",val:"5 (ACCESS-CM2, EC-Earth3, MPI, MRI, NorESM2)",desc:"CMIP6 model ensemble"}
   ]},

  {name:"temperature.py",path:"dixon_melt/temperature.py",lines:46,category:"Physics",
   deps:["config.py"],decisions:["D-007","D-012"],
   description:"Temperature distribution utilities, including the statistical transfer from off-glacier stations to on-glacier temperatures. Currently implements identity transfer (D-012): the raw Nuka SNOTEL temperature is used directly, and the calibrated lapse rate in fast_model.py handles elevation adjustment.\n\nThis module's history illustrates a key lesson: DETIM is designed for off-glacier index temperatures, not literal on-glacier surface temperatures. The statistical katabatic transfer (D-007, D-010) made temperatures too cold, requiring physically unreasonable melt factors (>19 mm/d/K). Reverting to identity transfer (D-012) allowed MF to settle at ~7 mm/d/K, well within the Braithwaite (2008) literature range.",
   equations:["T_{ref} = \\alpha_m \\cdot T_{nuka} + \\beta_m"],
   params:[
     {name:"alpha",val:"1.0 (all months)",desc:"Identity transfer slope"},
     {name:"beta",val:"0.0 (all months)",desc:"Identity transfer intercept"}
   ]},

  {name:"precipitation.py",path:"dixon_melt/precipitation.py",lines:67,category:"Physics",
   deps:["config.py"],decisions:["D-013","D-016"],
   description:"Precipitation distribution from the reference station to glacier grid cells. Applies a precipitation correction factor (precip_corr) for gauge undercatch and spatial transfer, plus an elevation-dependent gradient (precip_grad) that increases precipitation with altitude.\n\nThe correction factor (1.621 from CAL-013) accounts for three effects: (1) SNOTEL gauge undercatch of snow (typically 10-30%), (2) orographic enhancement between Nuka (375m, coastal foothills) and Dixon (439-1637m, deep in the Kenai Mountains), and (3) any systematic precipitation difference between the SNOTEL site and the glacier catchment. The value is well within the literature range (PyGEM caps at 3.0, Wolverine Glacier analog is 2.28x).\n\nThe elevation gradient (0.000694 per meter from CAL-013) means precipitation increases by ~7% per 100m of elevation gain, adding about 50% more precipitation at the headwall (1637m) compared to the terminus (439m). This gradient, combined with the temperature-dependent rain/snow partition, creates the accumulation pattern that determines the equilibrium line altitude.",
   equations:["P_{cell} = P_{nuka} \\cdot c_p \\cdot (1 + p_g \\cdot (z_{cell} - z_{ref}))"],
   params:[
     {name:"precip_corr",val:"1.621",desc:"Gauge undercatch + spatial transfer"},
     {name:"precip_grad",val:"0.000694 /m",desc:"Elevation gradient (~7%/100m)"}
   ]},

  {name:"melt.py",path:"dixon_melt/melt.py",lines:70,category:"Physics",
   deps:["config.py","solar.py"],decisions:["D-001","D-008"],
   description:"The DETIM melt calculation: M = (MF + r * I_pot) * T+ where T+ = max(T, 0). This is the core equation from Hock (1999) Method 2 that gives the model its name.\n\nThe melt factor MF captures all non-radiative energy fluxes (sensible heat, latent heat, longwave radiation) as a single empirical parameter. The radiation factors r_snow and r_ice add spatial structure by modulating melt based on clear-sky incoming solar radiation. On a south-facing slope receiving 300 W/m2 of potential radiation, r_ice = 0.00392 adds 1.18 mm/d/K to the base melt factor -- a significant enhancement.\n\nThe elevation-dependent melt factor (D-008) MF(z) = MF + MF_grad * (z - z_ref) decreases melt efficiency at higher elevations. With MF_grad = -0.0041 mm/d/K/m, the melt factor drops from ~9.0 at the terminus (439m) to ~4.0 at the headwall (1637m), capturing the integrated effects of lower air density, higher albedo, and stronger re-radiation at altitude.",
   equations:["M = (MF + r_{snow/ice} \\cdot I_{pot}) \\cdot T^+","MF(z) = MF + MF_{grad} \\cdot (z - z_{ref})"],
   params:[
     {name:"MF",val:"7.11 mm/d/K",desc:"Base melt factor at reference elevation"},
     {name:"r_snow",val:"0.00196 mm m2/W/d/K",desc:"Snow radiation factor"},
     {name:"r_ice",val:"0.00392 mm m2/W/d/K",desc:"Ice radiation factor (2x r_snow)"},
     {name:"MF_grad",val:"-0.0041 mm/d/K/m",desc:"Elevation gradient"}
   ]},

  {name:"snowpack.py",path:"dixon_melt/snowpack.py",lines:98,category:"Physics",
   deps:[],decisions:["D-005"],
   description:"Snow water equivalent (SWE) tracking and the firn/ice surface-type switch. Each grid cell maintains a SWE state that accumulates from snowfall and depletes from melt. When SWE reaches zero, the surface transitions from snow to ice, switching the radiation factor from r_snow to r_ice (doubling the radiation-driven melt component).\n\nThe initial SWE state is critical for calibration (D-005): annual runs (Oct 1 start) initialize with SWE=0 and accumulate naturally, while summer runs (May start) use observed winter balance. The v1 calibration double-counted winter accumulation by initializing annual runs with observed SWE AND accumulating from daily precipitation, forcing MF to its lower bound to compensate.",
   equations:["SWE(t+1) = SWE(t) + S(t) - M_{snow}(t)"],
   params:[
     {name:"SWE init (annual)",val:"0.0 mm",desc:"Oct 1 start, accumulates naturally"},
     {name:"SWE init (summer)",val:"Observed winter balance",desc:"From ELA stake measurement"}
   ]},

  {name:"massbalance.py",path:"dixon_melt/massbalance.py",lines:62,category:"Core",
   deps:[],decisions:["D-003"],
   description:"Mass balance computation utilities: loading stake observations, computing glacier-wide specific balance, and formatting output. The glacier-wide balance is computed as the area-weighted mean of all grid cell balances (accumulation minus melt, converted to meters water equivalent).\n\nStake observations are loaded from CSV with site ID, period type (annual/summer/winter), year, dates, observed mass balance, uncertainty, and elevation. The 27 rows span 3 sites (ABL, ELA, ACC) across 3 water years (2023-2025), providing the point-scale calibration targets.",
   equations:["\\bar{B} = \\frac{1}{A}\\sum_{i} b_i \\cdot \\Delta A_i"],
   params:[]},

  {name:"routing.py",path:"dixon_melt/routing.py",lines:112,category:"Physics",
   deps:["config.py"],decisions:["D-019"],
   description:"Parallel linear reservoir discharge model (Hock and Jansson 2005) that converts daily glacier melt and rainfall into a hydrograph. Three reservoirs -- fast (supraglacial/ice surface), slow (subglacial), and groundwater -- each with characteristic recession times, combine to produce the delayed and attenuated discharge response.\n\nMelt and rain-on-glacier are partitioned into the three reservoirs (60% fast, 30% slow, 10% groundwater by default). Each reservoir drains exponentially: Q = k * S, where S is storage and k is the recession coefficient. The fast reservoir (k=0.3/day) responds within 1-3 days, the slow reservoir (k=0.05/day) integrates over weeks, and the groundwater reservoir (k=0.01/day) maintains baseflow through winter.\n\nRouting is primarily used in projections to compute peak water timing and magnitude -- the year when glacier melt contribution to downstream discharge reaches its maximum before declining as the glacier shrinks.",
   equations:["Q_i(t) = k_i \\cdot S_i(t)","S_i(t+1) = S_i(t) + f_i \\cdot R(t) - Q_i(t)"],
   params:[
     {name:"k_fast",val:"0.3 /day",desc:"Fast reservoir recession"},
     {name:"k_slow",val:"0.05 /day",desc:"Slow reservoir recession"},
     {name:"k_gw",val:"0.01 /day",desc:"Groundwater recession"},
     {name:"f_fast / f_slow",val:"0.6 / 0.3",desc:"Partitioning fractions"}
   ]}
];

// ── DECISIONS ───────────────────────────────────────────────────────

DATA.decisions = [
  {id:"D-001",title:"Model Selection -- DETIM Method 2 (Hock 1999)",date:"Pre-2026-03-06",
   tags:["design"],
   text:"Use Distributed Enhanced Temperature Index Model, Method 2: M = (MF + r_snow/ice * I_pot) * T, where T > 0. Balances physical realism (radiation + temperature) against data availability. Dixon Glacier lacks the full energy balance data needed for DEBAM. Method 2 adds spatially distributed potential clear-sky radiation to a basic degree-day model, capturing topographic shading and aspect effects.",
   alternatives:"Classical degree-day (Method 1): Too simple for a 40 km2 glacier with significant topographic variability (439-1637m). Full energy balance (DEBAM): Requires wind, humidity, albedo, cloud cover at grid scale -- not available.",
   why:"DETIM Method 2 occupies the sweet spot for Dixon: it captures the first-order spatial physics (topographic shading, aspect-dependent radiation) that matter on a 40 km2 glacier spanning 1200m of elevation, without requiring the meteorological inputs that simply do not exist for this remote site. The key insight from Hock (1999) is that potential clear-sky radiation, which can be computed from topography alone, correlates strongly enough with actual energy inputs that adding it to a temperature index substantially improves spatial melt patterns. For Dixon, south-facing terminus slopes receive 3-4x more radiation than north-facing headwall slopes -- a difference that a basic degree-day model would completely miss."},

  {id:"D-002",title:"Climate Data Source -- Nuka SNOTEL + On-Glacier AWS",date:"Pre-2026-03-06",
   tags:["data"],
   text:"Primary forcing from Nuka SNOTEL (site 1037, 375m, ~20 km from Dixon), supplemented by on-glacier AWS at ELA site (1078m; D-023 corrected from 804m) for 2024-2025 summers. Nuka SNOTEL is the nearest long-record station with daily T and P going back to 1990. On-glacier AWS provides ground truth for lapse rate validation during summer field seasons.",
   alternatives:"ERA5 reanalysis (coarser, different biases), other SNOTEL stations (tested in D-024, Nuka best for precip).",
   why:"Nuka is the only station within 20km that has both temperature and precipitation records spanning the full geodetic calibration period (2000-2020). While Middle Fork Bradley proved to be a better temperature predictor for Dixon (D-024), it lacks the precipitation correlation. Using Nuka as primary forcing with multi-station gap-filling (D-025) gives the best combination of record length, proximity, and data completeness."},

  {id:"D-003",title:"Calibration Targets -- Stakes + Geodetic",date:"Pre-2026-03-06",
   tags:["cal"],
   text:"Multi-objective calibration against: (1) Stake mass balance at 3 elevations (ABL 804m, ELA 1078m, ACC 1293m), 2023-2025, and (2) Geodetic mass balance from Hugonnet et al. (2021), 2000-2020. Stakes provide point-scale seasonal resolution. Geodetic provides glacier-wide decadal constraint. Together they constrain both the spatial pattern and long-term magnitude of mass balance.",
   alternatives:"Stakes only (insufficient temporal constraint), geodetic only (no spatial constraint), degree-day factor literature values (not site-specific).",
   why:"The complementarity is the key: stakes tell you the model gets the elevation gradient right (ABL should melt ~5x more than ACC), while geodetic tells you the glacier-wide total is correct over 20 years. Neither alone is sufficient -- a model could match all three stakes perfectly while getting the glacier-wide balance wrong by distributing melt incorrectly across the 36,000 grid cells between stake sites."},

  {id:"D-004",title:"Numba JIT Compilation for Calibration Speed",date:"Pre-2026-03-06",
   tags:["design"],
   text:"Implement core simulation loop as a single Numba @njit(parallel=True) function (FastDETIM) for calibration, separate from the Pandas-based orchestrator (DETIMModel) used for analysis. Differential evolution requires ~10,000+ objective evaluations. Each evaluation runs 365-day simulations on a 578x233 grid. JIT compilation reduces per-evaluation time from seconds to ~300 ms.",
   alternatives:"Pure Python (too slow for calibration), Cython (less portable), Fortran (less maintainable), coarser grid (loses spatial resolution).",
   why:"The full DE+MCMC calibration (CAL-013) required ~250,000 model evaluations. At 300ms each, that is ~20 hours -- already a weekend-long computation. At the original Python speed of ~3 seconds per evaluation, it would have taken 200+ hours, making iterative calibration design impossible. The trade-off of maintaining two code paths (fast_model.py for calibration, model.py for analysis) is worth the 10x speedup."},

  {id:"D-005",title:"Fix SWE Double-Counting in Calibration v2",date:"2026-03-06",
   tags:["fix"],
   text:"Three fixes to calibration objective function: (1) Annual runs (Oct 1 start): Set initial SWE = 0, snowpack accumulates naturally from daily precipitation during Oct-Apr. (2) Summer runs (~May start): Use observed winter balance at ELA as initial SWE. (3) Remove snow_redist parameter (multiplicatively redundant with precip_corr). v1 calibration initialized annual runs with observed winter SWE AND accumulated snow from daily precipitation -- double-counting winter snowpack. The optimizer compensated by pushing MF to lower bound (1.0), r_snow to ~0, and precip_corr/snow_redist/T0 to upper bounds. 5 of 8 parameters hit bounds.",
   alternatives:"None -- this was a bug, not a design choice.",
   why:"When you double-count winter accumulation, the model sees roughly 2x the correct snow input. The only way the optimizer can compensate is to suppress melt (MF to minimum) and suppress additional accumulation (precip parameters to extremes). This is the clearest example of how a single initialization bug can corrupt the entire parameter set, producing values that are internally consistent with the bug but physically meaningless. The diagnostic clue was that 5 of 8 parameters hit their bounds -- a strong signal that the model physics are fighting the data."},

  {id:"D-006",title:"Fix Temperature Reference Elevation Mismatch",date:"2026-03-06",
   tags:["fix"],
   text:"Change model station_elev from 1230m (SNOTEL) to 804m (Dixon AWS) to match the merged climate data's actual reference elevation. [NOTE: D-023 later corrected Dixon AWS elevation to 1078m. The logic remains valid.] The merged climate file contained temperatures already lapse-adjusted from Nuka to Dixon AWS elevation, but FastDETIM was initialized with SNOTEL_ELEV = 1230m, causing the model to apply the lapse rate from the wrong base elevation. Every grid cell was +2.8C too warm.",
   alternatives:"None -- this was a bug.",
   why:"A reference elevation error is invisible in the code because temperatures look reasonable -- they are just shifted. The model compensates by adjusting MF and precip_corr in ways that mask the underlying error. The diagnostic was that even after fixing the SWE double-counting (D-005), the cost remained at ~15 and MF was still at 1.0. Two bugs compounding made diagnosis much harder."},

  {id:"D-007",title:"Nuka-to-Dixon Temperature Transfer Is Invalid",date:"2026-03-06",
   tags:["data"],
   text:"Replace simple lapse rate temperature transfer with statistical downscaling based on empirical Nuka-Dixon relationship. Dixon AWS is 5.10C colder than Nuka during summer overlap (n=256 days). Regression: T_dixon = 0.695 * T_nuka + (-2.650), R2=0.696. [NOTE: D-023 later showed that with corrected elevations (Dixon=1078m ELA, Nuka=375m), the 703m elevation difference at -6.5 to -7.3 C/km fully explains the offset. There is NO katabatic inversion.]",
   alternatives:"Standard lapse rate (oversimplifies), ERA5 reanalysis (coarser resolution).",
   why:"This analysis was correct in identifying the temperature offset but incorrect in attributing it to katabatic cooling. The real lesson (realized only after D-013 and D-023 corrected both station elevations) is that careful analysis on wrong data can produce convincing but wrong conclusions. The regression R2=0.70 and the physical narrative about katabatic cooling were both plausible -- but the 5.1C offset was simply a normal lapse rate over 703m, not an exotic glacier boundary layer effect."},

  {id:"D-008",title:"Elevation-Dependent Melt Factor",date:"2026-03-06",
   tags:["design"],
   text:"Add MF_grad parameter: MF(z) = MF + MF_grad * (z - z_ref). A single MF cannot capture the ABL-to-ACC mass balance gradient. Even with correct temperatures, integrated effects of albedo, wind, humidity, and cloud cover cause melt efficiency to decrease with elevation. MF_grad adds one parameter to capture this. Bounds: [-0.01, 0.0] mm/d/K per m.",
   alternatives:"Single MF for all elevations (too simple), separate MF per elevation band (overfitting with only 3 stakes).",
   why:"The ABL stake at 804m loses 4.5 m w.e./yr while ACC at 1293m gains 0.37 m w.e./yr. Temperature alone (via the lapse rate) explains most of this gradient, but the remaining mismatch requires either unreasonable lapse rates or an elevation-dependent melt efficiency. MF_grad is the minimal parameterization: one number that lets the model produce less melt per degree at higher elevations."},

  {id:"D-009",title:"Model Architecture Overhaul -- v4",date:"2026-03-06",
   tags:["design"],
   text:"Comprehensive model update implementing Phases 1-6 of project plan. Changes: fast_model.py rewritten with statistical temp transfer, MF_grad, daily runoff tracking. config.py updated with monthly transfer coefficients, stake config, routing/dynamics defaults. New modules: glacier_dynamics.py (delta-h), routing.py (linear reservoir), run_projection.py. Parameter set: MF, MF_grad, r_snow, r_ice, internal_lapse, precip_grad, precip_corr, T0.",
   alternatives:"Incremental changes (slower iteration cycle).",
   why:"At this point the model had accumulated enough bug fixes and design changes that a clean rewrite was more reliable than continued patching. The v4 architecture separated concerns cleanly: fast_model.py for computation, model.py for orchestration, glacier_dynamics.py for geometry evolution, routing.py for discharge."},

  {id:"D-010",title:"Winter Katabatic Correction for Temperature Transfer",date:"2026-03-06",
   tags:["design"],
   text:"Apply reduced katabatic correction for Oct-Apr months. CAL-004 diagnosis revealed that the standard lapse transfer for winter months made October and November too warm, causing precipitation to fall as rain instead of snow. The model accumulated only 22% of observed winter balance at ELA/ACC. Winter coefficients changed from alpha=1.0, beta=+2.77 to alpha=0.85, beta=+1.0 for Oct-Apr.",
   alternatives:"No winter correction (too warm), same summer correction for winter (too cold).",
   why:"This was an attempt to fix a real problem (insufficient winter accumulation) with the wrong solution. The real issue was the Nuka elevation error (D-013): with Nuka incorrectly at 1230m, the lapse correction was adding heat instead of removing it. After D-013 corrected Nuka to 375m, the glacier is correctly placed above the station and winter temperatures are naturally colder. This decision was effectively superseded by D-012 and D-013."},

  {id:"D-011",title:"Wind Redistribution of Snow (Winstral Sx)",date:"2026-03-06",
   tags:["design"],
   text:"Add spatially distributed wind redistribution of snowfall using the Winstral et al. (2002) Sx parameter, with prevailing wind from ESE (100 degrees). 22 years of digitized snowlines showed western side of glacier has snowline ~100m lower than eastern side every year. NW-facing slopes: mean snowline 1061m; S-facing: 1175m. Implementation: P_cell *= (1 + k_wind * sx_norm), mass-conserving.",
   alternatives:"No wind redistribution (ignores observed spatial pattern), prescribed deposition map (requires more data).",
   why:"The snowline asymmetry is one of the strongest spatial signals in the observational dataset: 22 years of consistent E-W gradient averaging +60m, with detrended r=+0.59. Despite this strong observational motivation, k_wind converged to ~0 in calibration (CAL-007) because the 3-stake observation network cannot constrain a spatial redistribution parameter. The parameter was removed from calibration (D-015) but the Sx field is retained for future work."},

  {id:"D-012",title:"Revert to Identity Temperature Transfer",date:"2026-03-06",
   tags:["design"],
   text:"Remove statistical katabatic temperature transfer (D-007, D-010). Use raw Nuka SNOTEL temperature at 375m with a calibrated lapse rate. Diagnostic of CAL-004/005/006 revealed that the statistical transfer made on-glacier temperatures too cold for DETIM: ABL summer mean T = 2.4C after transfer (vs ~10C with standard lapse), requiring MF > 19 mm/d/K to match observed melt. Literature MF for ice: 6-12 mm/d/K.",
   alternatives:"Keep statistical transfer with relaxed MF bounds (physically unreasonable), develop hybrid transfer.",
   why:"This is a fundamental insight about how empirical index models work: DETIM was designed to use off-glacier temperature as an INDEX, not a literal physical temperature. The melt factor MF implicitly absorbs the difference between free-air and on-glacier conditions. Hock (1999) calibrated DETIM using off-glacier station data, and the resulting MF values (2-8 mm/d/K) inherently include the katabatic effect. Trying to explicitly correct for katabatic cooling removes information that MF needs to function, requiring unreasonable compensation."},

  {id:"D-013",title:"Nuka SNOTEL Elevation Units Error -- 1230 ft, Not 1230 m",date:"2026-03-09",
   tags:["fix"],
   text:"Correct Nuka SNOTEL reference elevation from 1230 m to 375 m (1230 ft * 0.3048). The NRCS website lists elevation in feet, the standard unit for all US SNOTEL stations. The value was recorded as 1230 m in config.py, introducing an 855 m elevation error that propagated through every calibration run (CAL-001 through CAL-007). All glacier cells were positioned BELOW the reference station instead of ABOVE it. With lapse applied in the wrong direction, ABL was ~3-4C too warm.",
   alternatives:"None -- this was a data entry error.",
   why:"This is the root cause of all calibration failures from CAL-001 through CAL-007, and one of the most instructive errors in the project. With Nuka incorrectly at 1230m, every glacier cell (439-1637m) appeared to be at roughly the same elevation or below the station. The lapse rate, which should cool temperatures as you go up to the glacier, was instead warming them or applying minimal correction. The D-007 'katabatic paradox' (Dixon 5.1C colder despite being 'lower') was never a paradox at all -- Dixon at 1078m IS higher than Nuka at 375m. The lesson: always verify station metadata against the original source (NRCS website), not secondary records."},

  {id:"D-014",title:"Cost Function Restructuring -- Inverse-Variance + Geodetic Hard Constraint",date:"2026-03-09",
   tags:["cal"],
   text:"Replace arbitrary-weight cost function with inverse-variance weighting and a hard geodetic constraint. Literature review of OGGM, PyGEM, and Huss et al. (2009) shows all major glacier models treat geodetic mass balance as the PRIMARY calibration constraint. The v7 cost function gave geodetic weight 0.4 vs combined stake weight 2.4, allowing the optimizer to ignore the 20-year geodetic signal. Also dropped 2000-2020 period (derived from sub-periods, not independent).",
   alternatives:"Equal weighting (ignores measurement precision), geodetic-only (loses spatial information).",
   why:"Inverse-variance weighting is the statistically principled approach: observations with smaller uncertainty carry more weight because they are more informative. The geodetic mass balance (-0.939 +/- 0.122 m w.e./yr) constrains the 20-year glacier-wide average to within ~12%, while individual stake measurements (+/- 0.10-0.15 m w.e.) constrain single-point seasonal balances. The hard penalty (lambda=50) prevents the optimizer from finding mathematically optimal but physically impossible solutions."},

  {id:"D-015",title:"Remove Lapse Rate and k_wind from Calibration",date:"2026-03-09",
   tags:["cal"],
   text:"Fix lapse rate at -5.0 C/km and remove k_wind, reducing free parameters from 9 to 7. Lapse rate rationale: The optimizer consistently exploits lapse rate to compensate for other model deficiencies. Literature values for maritime glaciers converge on -4.5 to -5.5 C/km (Gardner & Sharp 2009: -4.9; Roth et al. 2023 Juneau Icefield: -5.0). k_wind rationale: CAL-007 converged to k_wind ~ 0.",
   alternatives:"Keep lapse rate free with tight bounds (still equifinal), fix at -6.5 (standard atmosphere, too steep for maritime glacier).",
   why:"The equifinality between lapse rate and precipitation correction is the most dangerous parameter trade-off in the model. In CAL-009, the optimizer found lapse_rate = -6.83 C/km with precip_corr = 1.20 -- a combination that fits current observations perfectly but has compensating errors. A steeper lapse rate means more warming at low elevations (more melt) and more cooling at high elevations (more accumulation), which the low precip_corr compensates by under-supplying precipitation everywhere. Under future warming, these errors DIVERGE: the too-steep lapse amplifies warming at the terminus while the too-low precip_corr starves the accumulation zone. Fixing lapse rate at the literature consensus eliminates this time bomb.\n\nThe sensitivity analysis (D-029) quantified the stakes: lapse rate sensitivity is ~10x larger than r_ice/r_snow ratio. Geodetic bias swings 1.9 m w.e./yr across the -4.0 to -6.5 C/km range. The -5.0 choice sits near the minimum geodetic bias, confirming it is well-centered."},

  {id:"D-016",title:"Use Only 2000-2020 Geodetic Mean + Widen precip_corr",date:"2026-03-09",
   tags:["cal"],
   text:"Revert to single 2000-2020 geodetic constraint and widen precip_corr upper bound from 3.0 to 4.0. CAL-008 revealed that the two geodetic sub-periods (2000-2010 and 2010-2020) create a contradictory constraint. Nuka SNOTEL shows cooler summers 2001-2010 (9.07C) than 2011-2020 (10.00C), so the model produces less melt in the first decade. But Hugonnet shows MORE mass loss 2000-2010 (-1.07) than 2010-2020 (-0.81). Statistical test: sub-periods NOT distinguishable (Z=0.88, p>0.30).",
   alternatives:"Keep both sub-periods with relaxed weighting, dynamic precipitation correction.",
   why:"The contradiction between Nuka forcing and Hugonnet sub-periods reveals a fundamental limitation: the off-glacier climate station does not perfectly represent on-glacier conditions decade by decade. The 2000-2020 mean integrates over these discrepancies, providing a robust 20-year constraint. Using it alone with its tighter uncertainty gives the optimizer a cleaner signal. The sub-periods become validation targets."},

  {id:"D-017",title:"Bayesian Ensemble Calibration (DE + MCMC)",date:"2026-03-09",
   tags:["cal"],
   text:"Replace single-optimum calibration with two-phase Bayesian ensemble: differential evolution to find the MAP estimate, then MCMC (emcee) to sample the posterior distribution. 24 walkers, 10,000 steps, burn-in 2000, thinned by autocorrelation time. 6 free parameters: MF, MF_grad, r_snow, precip_grad, precip_corr, T0. Fixed: lapse_rate=-5.0 C/km, r_ice=2.0*r_snow, k_wind=0.",
   alternatives:"Single DE optimum (no uncertainty), grid search (too expensive in 6D), DREAM (more complex).",
   why:"For projections, a single 'best' parameter set is scientifically insufficient. CAL-009 demonstrated the equifinality problem: multiple parameter combinations fit current observations equally well but diverge under future warming. A single optimum gives false precision -- it says 'the glacier will lose 50% of its area by 2100' when the honest answer is '35-65%'.\n\nThe r_ice/r_snow ratio was fixed at 2.0 because CAL-009 converged to near-equality (1.29 vs 1.34), eliminating the albedo feedback. When r_ice ~ r_snow, the transition from snow-covered to bare ice surface produces no change in melt rate -- destroying a physical feedback mechanism critical for projections. Under warming, more ice surface is exposed earlier each summer; if r_ice = r_snow, this exposure has no effect, underestimating melt acceleration. The 2.0 ratio is mid-range of Hock (1999) Table 4.\n\nThe MCMC posterior from CAL-013 produced 1,656 independent samples with acceptance fraction 0.368, confirming good convergence. All 5 DE seeds found the same mode, indicating a unimodal posterior."},

  {id:"D-018",title:"Glacier Dynamics Overhaul -- Correct Delta-h + Ice Thickness",date:"2026-03-10",
   tags:["fix","design"],
   text:"Complete rewrite of glacier_dynamics.py to fix three compounding bugs: (1) Wrong size class -- used small-glacier coefficients with large-glacier exponent for a 40 km2 glacier. (2) Wrong h_r convention -- code used z_norm = (z-z_min)/range but Huss equation expects h_r = (z_max-z)/range, producing maximum thinning at headwall instead of terminus. (3) No ice thickness tracking -- cells losing 4m/yr for 10 years were never removed. Added Farinotti thickness, bedrock DEM, dynamic size-class switching.",
   alternatives:"None -- these were bugs.",
   why:"The three bugs compounded to produce qualitatively wrong retreat patterns: the glacier was thinning most at the headwall (highest elevations) instead of the terminus (lowest elevations), and cells with zero ice remaining were still being treated as glacier. The corrected implementation produces physically realistic retreat: terminus cells deglaciate first, with the retreat front moving upglacier over time."},

  {id:"D-019",title:"CMIP6 Projection Pipeline with Discharge Routing",date:"2026-03-10",
   tags:["proj"],
   text:"Replace placeholder future climate with real CMIP6 projections from NASA NEX-GDDP-CMIP6 (0.25 degree, daily, bias-corrected). 5 GCMs: ACCESS-CM2, EC-Earth3, MPI-ESM1-2-HR, MRI-ESM2-0, NorESM2-MM. SSP scenarios: 1-2.6, 2-4.5, 5-8.5. Bias correction: monthly delta method against Nuka SNOTEL 1991-2020 climatology. Wire discharge routing into projections for peak water analysis.",
   alternatives:"Linear delta method (no interannual variability), single GCM (no climate model uncertainty).",
   why:"The 5-GCM ensemble captures the structural uncertainty in how global warming translates to local conditions at Dixon. The selection follows Rounce et al. (2023), who used a similar approach for all 215,000 glaciers globally."},

  {id:"D-020",title:"Posterior Ensemble Projections (Top 250 Parameter Sets)",date:"2026-03-11",
   tags:["proj"],
   text:"Replace single-parameter projections with ensemble using top 250 MCMC parameter sets (following Geck 2020 on Eklutna Glacier). Each (GCM, param_set) pair runs independently with its own geometry evolution. Total: 250 x 5 GCMs = 1,250 runs per scenario. Aggregated with percentiles (p05, p25, p50, p75, p95).",
   alternatives:"Single MAP parameter set (no parameter uncertainty), full posterior (too expensive).",
   why:"Using the top 250 by log-probability ensures the projection ensemble is weighted toward parameter sets that best fit observations. Parameter uncertainty is relatively small compared to GCM spread but still meaningful for peak water timing."},

  {id:"D-021",title:"Snowline Validation (Independent Spatial Check)",date:"2026-03-11",
   tags:["val"],
   text:"Independent validation against 22 years (1995-2024) of digitized snowline observations that were never used in calibration. For each year, run model from Oct 1 to satellite date, extract modeled snowline as contour where net balance = 0. Metrics: elevation RMSE, bias, correlation, balance at observed snowline. Results with MAP params (19 valid years): bias +6m, RMSE 189m, MAE 122m, r=0.52.",
   alternatives:"Snowline as calibration target (done later in D-028), AAR validation.",
   why:"Snowlines are the most spatially informative validation dataset available: they map the equilibrium line across the entire glacier width, revealing spatial biases that point measurements (stakes) cannot detect. The persistent +100-175m positive bias in recent years (2017-2024) was a key finding that motivated D-028."},

  {id:"D-022",title:"Exclude Snowline Years with Insufficient SNOTEL Data",date:"2026-03-11",
   tags:["data"],
   text:"Automatically exclude snowline validation years where >30% of melt-season (May-Sep) temperature data is missing. WY2000 (37% missing) and WY2005 (86% missing, 132 of 153 days) showed extreme negative snowline bias (-600 to -660m). Root cause: validation code replaced NaN with 0C, eliminating melt and producing snowlines at the glacier terminus.",
   alternatives:"Climatological gap-filling, hardcoded exclusion list.",
   why:"The 30% threshold catches years where missing summer temperature data fundamentally compromises the melt calculation, while retaining years like WY2003 (21% missing, mostly late September) that validate well."},

  {id:"D-023",title:"Correct Dixon AWS Elevation from 804m to 1078m",date:"2026-03-12",
   tags:["fix"],
   text:"The Dixon on-glacier AWS was recorded at 804m (ABL stake elevation) but was actually deployed at the ELA stake site (1078m). Evidence: temperature comparison with Nuka SNOTEL (375m) shows -4.6C offset (2024), exactly matching 1078m at -6.5 C/km lapse rate. At 804m, predicted offset would be only -2.8C. Cross-validated against MFB SNOTEL.",
   alternatives:"None -- this was a metadata error.",
   why:"This is the second elevation metadata error in the project (after D-013), and follows the same pattern: a number was recorded without verifying the original source. The 274m error matters for any analysis using the Dixon AWS as a reference. The corrected elevation reveals that the 'exotic' katabatic effect is only ~1C, consistent with literature values for maritime glaciers."},

  {id:"D-024",title:"Multi-Station Climate Analysis -- Dixon AWS as Ground Truth",date:"2026-03-12",
   tags:["data"],
   text:"Evaluate all nearby SNOTEL stations against Dixon AWS (1078m) as ground truth. Key finding: Middle Fork Bradley is the best single predictor of Dixon temperature (r=0.877, RMSE=4.8C). All transfer slopes are 0.3-0.8 -- the glacier dampens temperature variability. August is the hardest month to predict (peak melt season = maximum glacier-surface decoupling). Nuka has the best precip correlation (r=0.75 on wet days).",
   alternatives:"Use Nuka for everything, use only stations with overlap.",
   why:"Reframing the analysis around Dixon AWS as ground truth was essential: comparing stations to each other tells you about regional coherence, but comparing them to Dixon tells you which station best predicts on-glacier conditions."},

  {id:"D-025",title:"Multi-Station Climate Gap-Filling Pipeline",date:"2026-03-12",
   tags:["data"],
   text:"Replace ffill().fillna(0) gap handling with 5-station cascade. Temperature cascade: Nuka -> MFB -> McNeil -> Anchor -> Kachemak -> Lower Kach -> linear interp (3d max) -> DOY climatology. Precipitation: Nuka -> MFB (monthly ratio) -> DOY climatology. Results: 91.3% Nuka, 6.0% MFB, 1.8% McNeil. WY2005 Jun-Aug mean T: 8.5C (was ~0C). WY2020 total precip: 2307mm (was ~1176mm).",
   alternatives:"ERA5 reanalysis, single-station MFB only, Dixon AWS for forcing.",
   why:"The original ffill().fillna(0) was the single worst data processing choice in the project. Forward-filling temperatures works for 1-2 day gaps, but multi-month gaps in summer (WY2005: 132 days) propagated the last valid spring temperature into August, and fillna(0) set the rest to 0C. This killed all melt in those years, forcing the model to overcompensate with extreme MF values in clean years."},

  {id:"D-026",title:"Recalibrate with Gap-Filled Climate (CAL-011)",date:"2026-03-12",
   tags:["cal"],
   text:"Re-run CAL-010 Bayesian ensemble calibration with multi-station gap-filled climate data from D-025. With gap-filled data, all 20 geodetic water years now contribute to calibration. Previously poisoned years provide real information. CAL-011 killed at DE step 28/200 -- superseded by CAL-012 (D-027).",
   alternatives:"Adjust bounds/priors, free lapse rate.",
   why:"After fixing the climate data (D-025), recalibration was mandatory -- every parameter value from CAL-010 was contaminated by the bad gap handling."},

  {id:"D-027",title:"Multi-Seed Calibration to Address Posterior Multimodality (CAL-012)",date:"2026-03-12",
   tags:["cal"],
   text:"Replace single-seed DE + single MCMC with 5-seed DE [42, 123, 456, 789, 2024] + per-mode MCMC chains. Normalized clustering with 10% Chebyshev threshold identifies distinct modes. Result: all 5 seeds converged to one mode -- posterior is unimodal.",
   alternatives:"Single seed (might miss modes), more seeds (diminishing returns), parallel tempering.",
   why:"The multi-seed approach is a cheap insurance policy against posterior multimodality. Each seed costs ~50 minutes, and if all 5 find the same optimum, you have high confidence the posterior is unimodal. For CAL-012/013, all 5 seeds converged to costs within 0.003 of each other (5.343-5.345), confirming the parameter space is well-identified by the available observations."},

  {id:"D-028",title:"Multi-Objective Calibration with Snowline in MCMC Likelihood",date:"2026-03-18",
   tags:["cal"],
   text:"Add snowline elevation as chi-squared term in MCMC log-likelihood (sigma=75m), apply glacier area evolution as post-hoc behavioral filter. Pipeline: Phase 1 (multi-seed DE) -> Phase 2 (MCMC with snowlines in likelihood) -> Phase 3 (combine posteriors) -> Phase 4 (area filter, top 1000, RMSE <= 1.0 km2). All 1000 samples passed area filter.",
   alternatives:"Post-hoc snowline filter (rejected: no discriminating power), composite scoring, re-enable k_wind.",
   why:"This decision addresses the most important methodological finding of the project: post-hoc snowline filtering has zero discriminating power within the stakes+geodetic posterior.\n\nInitial testing with the top 1000 from CAL-012 showed that ALL parameter sets scored snowline RMSE between 88 and 96m -- a range of only 8m with standard deviation 1.6m. Snowline RMSE was uncorrelated with log-probability (r=0.146). This means the stakes+geodetic calibration produces a posterior that is completely agnostic about snowline fit.\n\nBy putting snowlines IN the likelihood, the MCMC sampler explores parameter space differently: it rewards combinations that simultaneously satisfy stakes, geodetic, AND snowline constraints. The sigma=75m combines observed spatial spread (~50-80m), model resolution (100m), and temporal mismatch.\n\nThe structural snowline limitations are documented and accepted: DETIM produces near-contour-line snowlines (spatial std 6-22m) while observed snowlines show 24-69m spatial spread from wind redistribution and aspect effects. The model also over-amplifies interannual variability (std 129m vs observed 63m). These are inherent DETIM limitations, not parameter-tunable.\n\nThe area filter passed 100% of samples, confirming that the three-constraint likelihood (stakes + geodetic + snowline) produces a posterior that is also behavioral with respect to area, without needing a separate filtering step."},

  {id:"D-029",title:"Validation Suite (Sub-period Geodetic, Stake Predictive Check, Sensitivity)",date:"2026-04-08",
   tags:["val"],
   text:"Three independent validation analyses using v13 posterior. (1) Sub-period geodetic: model reverses the trend -- underestimates 2000-2010 mass loss, overestimates 2010-2020. (2) Stake predictive: overall RMSE 1.20 m w.e., WY2023 ABL/ACC good, ELA biased -1.4 m w.e. both years. (3) Sensitivity: lapse rate dominates (1.9 m w.e./yr swing), r_ice/r_snow ratio has 10x less sensitivity (0.13 m w.e./yr).",
   alternatives:"Cross-validation (too expensive), leave-one-out, bootstrapping.",
   why:"Validation is about honesty, not marketing. The sub-period geodetic result reveals a real limitation of the gap-filled climate data. The ELA stake bias (-1.4 m w.e. in both years) reveals a spatial representativity issue. The sensitivity analysis shows lapse rate dominates the fixed-parameter error budget, motivating D-030 (lapse sensitivity projections)."},

  {id:"D-030",title:"Lapse Rate Sensitivity Projections",date:"2026-04-08",
   tags:["proj"],
   text:"Run projections at three lapse rates (-4.5, -5.0, -5.5 C/km) to bracket structural uncertainty. Same v13 posterior params (250 subsampled), all 5 GCMs, SSP1-2.6/2-4.5/5-8.5. Results show 2100 area ranges from 5.4 km2 (-4.5, SSP5-8.5) to 31.7 km2 (-5.5, SSP1-2.6). Lapse rate choice shifts area by ~9 km2.",
   alternatives:"Recalibrate at each lapse rate, full posterior at each rate, single MAP at each rate.",
   why:"Running projections at the lapse rate endpoints brackets the 'known unknown' without re-opening equifinality. At -4.5, the glacier warms faster with elevation leading to more melt -- accelerated retreat. At -5.5, less warming per meter, more snow retention, slower retreat. The 9 km2 spread in 2100 area across lapse rates is comparable to the spread across SSP scenarios, meaning lapse rate uncertainty is as important as emission scenario uncertainty for Dixon's future."},

  {id:"D-031",title:"ELA Stake Bias -- Wind Redistribution Representativity",date:"2026-04-09",
   tags:["val"],
   text:"Accept the persistent -1.4 m w.e. bias at the ELA stake (1078m) as a measurement representativity issue. The model predicts -1.3 m w.e. as the average across all 814 cells at 1028-1128m. The ELA stake is at ONE location on the southern branch, which receives preferential wind-loaded accumulation. 70% of glacier cells are in sheltered zones.",
   alternatives:"Increase ELA uncertainty and recalibrate, re-enable k_wind, exclude ELA from calibration.",
   why:"This decision encapsulates a core tension in glacier modeling: point measurements are not area averages. The ELA stake sits on the southern branch, a known wind-deposition zone (confirmed by 22 years of snowline asymmetry). It records +0.1 m w.e./yr because it receives extra wind-loaded snow. The model's -1.3 m w.e./yr is the AVERAGE across all 814 cells between 1028-1128m, including both sheltered and exposed zones.\n\nRecalibration would not help: forcing the model to match +0.1 at ELA would require over-accumulating at ALL cells in that band, breaking the geodetic fit and the ABL/ACC stakes. The wind redistribution parameter (k_wind) cannot be constrained by 3 stakes.\n\nThe WY2024 residual at all sites is a separate issue: Nuka SNOTEL recorded similar winter precip to WY2023 (912 vs 864 mm), but observed winter balance was dramatically higher (ABL: 0.85 -> 1.93, +127%), indicating a local accumulation event the off-glacier station missed entirely. This is a forcing limitation, not a model deficiency."}
];

// ── EQUATIONS ────────────────────────────────────────────────────────

DATA.equations = [
  {title:"DETIM Melt Equation (Hock 1999, Method 2)",
   latex:"M = \\begin{cases} (MF + r_{snow/ice} \\cdot I_{pot}) \\cdot T & \\text{if } T > 0 \\\\ 0 & \\text{if } T \\leq 0 \\end{cases}",
   explain:"The core equation of the Distributed Enhanced Temperature Index Model. Melt M (mm/day) at each grid cell equals the sum of a base melt factor MF and a radiation-dependent term (r times potential clear-sky solar radiation I_pot), multiplied by air temperature T (only when above freezing). The radiation factor r differs between snow-covered (r_snow) and ice-exposed (r_ice) surfaces, capturing the albedo feedback: bare ice absorbs roughly twice as much solar radiation as snow.\n\nThis equation occupies the sweet spot between degree-day models (M = MF * T, no spatial information) and full energy balance models (requiring wind, humidity, cloud cover at every cell). By using potential clear-sky radiation -- which depends only on topography, latitude, and day of year -- it captures first-order spatial variability without requiring meteorological data that does not exist for Dixon.\n\nThe temperature T is an INDEX, not the literal on-glacier temperature. The measured katabatic cooling at Dixon (~3C at ABL) is implicitly absorbed by MF. This is by design: Hock (1999) calibrated DETIM using off-glacier station data.",
   variables:[
     {sym:"M",unit:"mm/day",val:"0-30",desc:"Daily melt rate"},
     {sym:"MF",unit:"mm d-1 K-1",val:"7.11",desc:"Melt factor (MAP)"},
     {sym:"r_{snow}",unit:"mm m2 W-1 d-1 K-1",val:"0.00196",desc:"Snow radiation factor"},
     {sym:"r_{ice}",unit:"mm m2 W-1 d-1 K-1",val:"0.00392",desc:"Ice radiation factor"},
     {sym:"I_{pot}",unit:"W/m2",val:"50-350",desc:"Potential clear-sky direct solar radiation"},
     {sym:"T",unit:"C",val:"-10 to 15",desc:"Air temperature (index)"}
   ],
   example:"ABL stake (804m), July 15, clear sky, south-facing slope:\nI_pot = 280 W/m2 (high, south-facing midsummer)\nT = 5.9C (Nuka 8.0C, lapse -5.0 C/km over 429m)\nSurface = ice (SWE depleted)\nMF at 804m = 7.11 + (-0.0041)*(804-375) = 5.35 mm/d/K\nM = (5.35 + 0.00392*280) * 5.9\nM = (5.35 + 1.10) * 5.9 = 38.0 mm/day\n\nACC stake (1293m), July 15, north-facing:\nI_pot = 90 W/m2, T = 3.4C, surface = snow\nMF at 1293m = 7.11 + (-0.0041)*(1293-375) = 3.35\nM = (3.35 + 0.00196*90) * 3.4 = 12.0 mm/day",
   codeRef:"dixon_melt/fast_model.py, line ~100; dixon_melt/melt.py"},

  {title:"Temperature Lapse Rate Distribution",
   latex:"T_{cell} = T_{nuka} + \\lambda \\cdot (z_{cell} - z_{ref})",
   explain:"Distributes temperature from Nuka SNOTEL (375m) to every grid cell using a constant lapse rate lambda = -5.0 C/km. Temperature decreases by 5 degrees for every 1000m of elevation gain.\n\nThis is the simplest possible temperature distribution, and it works because DETIM uses temperature as an index rather than a physical variable. The calibrated melt factor MF absorbs systematic biases. The identity transfer (D-012) means T_nuka is used directly -- no statistical correction.\n\nThe -5.0 C/km value comes from maritime glacier literature: Gardner & Sharp (2009) -4.9 C/km, Roth et al. (2023) -5.0 C/km. The sensitivity analysis (D-029) showed this is the dominant fixed-parameter choice: +/- 0.5 C/km swings geodetic balance by ~0.6 m w.e./yr.",
   variables:[
     {sym:"T_{cell}",unit:"C",val:"-15 to 15",desc:"Temperature at grid cell"},
     {sym:"T_{nuka}",unit:"C",val:"-20 to 20",desc:"Nuka SNOTEL daily mean temperature"},
     {sym:"\\lambda",unit:"C/m",val:"-0.005",desc:"Lapse rate (fixed, D-015)"},
     {sym:"z_{cell}",unit:"m",val:"439-1637",desc:"Grid cell elevation"},
     {sym:"z_{ref}",unit:"m",val:"375",desc:"Nuka SNOTEL elevation"}
   ],
   example:"Summer day, Nuka T = 8.0C:\nABL (804m): T = 8.0 + (-0.005)*(804-375) = 5.85C\nELA (1078m): T = 8.0 + (-0.005)*(1078-375) = 4.49C\nACC (1293m): T = 8.0 + (-0.005)*(1293-375) = 3.41C\nHeadwall (1637m): T = 8.0 + (-0.005)*(1637-375) = 1.69C",
   codeRef:"dixon_melt/fast_model.py, line ~90"},

  {title:"Precipitation Distribution",
   latex:"P_{cell} = P_{nuka} \\cdot c_p \\cdot \\left(1 + p_g \\cdot (z_{cell} - z_{ref})\\right)",
   explain:"Distributes precipitation from Nuka SNOTEL with a bulk correction factor c_p (1.621) and an elevation gradient p_g (0.000694/m, ~7%/100m). The headwall receives ~50% more precipitation than the terminus.\n\nThe correction factor accounts for gauge undercatch (10-30%), orographic enhancement between Nuka's coastal location and the glacier interior, and systematic precipitation differences. The Wolverine Glacier analog is 2.28x and PyGEM caps at 3.0, so 1.621 is conservative.\n\nCombined with the temperature-dependent rain/snow partition, this creates the accumulation pattern: at the terminus in summer, most precipitation falls as rain; at the headwall, almost all is snow year-round.",
   variables:[
     {sym:"P_{cell}",unit:"mm/day",val:"0-50",desc:"Precipitation at grid cell"},
     {sym:"P_{nuka}",unit:"mm/day",val:"0-30",desc:"Nuka SNOTEL daily precipitation"},
     {sym:"c_p",unit:"-",val:"1.621",desc:"Correction factor (MAP)"},
     {sym:"p_g",unit:"1/m",val:"0.000694",desc:"Elevation gradient"}
   ],
   example:"Nuka reports 10mm:\nTerminus (439m): P = 10*1.621*(1+0.000694*(439-375)) = 16.9 mm\nELA (1078m): P = 10*1.621*(1+0.000694*(1078-375)) = 24.1 mm\nHeadwall (1637m): P = 10*1.621*(1+0.000694*(1637-375)) = 30.4 mm",
   codeRef:"dixon_melt/fast_model.py; dixon_melt/precipitation.py"},

  {title:"Rain/Snow Partition",
   latex:"f_{snow} = \\begin{cases} 1 & T \\leq T_0 - 1 \\\\ 0.5(T_0 + 1 - T) & T_0 - 1 < T < T_0 + 1 \\\\ 0 & T \\geq T_0 + 1 \\end{cases}",
   explain:"Partitions precipitation into snow and rain using a linear transition zone around T0 (~0C). Below -1C: all snow. Above +1C: all rain. Linear mix between.\n\nThe near-zero T0 means the transition is centered right at freezing, physically reasonable for a maritime glacier. Under 2C warming at the ELA, nearly all summer precipitation would convert from mixed to pure rain, eliminating summer snowfall events that add ~0.5 m w.e./yr at high elevations.",
   variables:[
     {sym:"f_{snow}",unit:"-",val:"0-1",desc:"Snow fraction of precipitation"},
     {sym:"T",unit:"C",val:"-10 to 15",desc:"Air temperature at cell"},
     {sym:"T_0",unit:"C",val:"~0.0",desc:"Threshold temperature (MAP)"}
   ],
   example:"ELA (1078m), summer T=4.5C: f_snow=0 (all rain)\nACC (1293m), October T=0.5C: f_snow=0.25\nACC (1293m), November T=-2.0C: f_snow=1.0 (all snow)",
   codeRef:"dixon_melt/fast_model.py, _rain_snow_fraction()"},

  {title:"Delta-h Glacier Thinning (Huss et al. 2010)",
   latex:"\\Delta h(h_r) = (h_r + a)^\\gamma + b(h_r + a) + c",
   explain:"Distributes glacier-wide mass change across the elevation profile. h_r ranges from 0 at headwall to 1 at terminus. Maximum thinning at terminus for large glaciers (gamma=6): ~12x more thinning than headwall.\n\nDynamic size-class switching: as Dixon shrinks below 20 km2, it transitions to 'medium' coefficients (gamma=4), spreading thinning more evenly. This feedback accelerates retreat.\n\nThe delta-h method is empirical (not physically based) but standard: OGGM, PyGEM, and GloGEM all use variants for regional projections.",
   variables:[
     {sym:"h_r",unit:"-",val:"0-1",desc:"Normalized elevation (0=headwall, 1=terminus)"},
     {sym:"\\gamma",unit:"-",val:"6/4/2",desc:"Thinning exponent by size class"},
     {sym:"a, b, c",unit:"-",val:"-0.02, 0.12, 0.00",desc:"Large-glacier coefficients"}
   ],
   example:"Large glacier (Dixon, 40 km2):\nTerminus (h_r=1): dh = (1-0.02)^6 + 0.12*(1-0.02) = 1.004\nELA (h_r=0.5): dh = (0.5-0.02)^6 + 0.12*0.48 = 0.070\nTerminus receives 14x more thinning than ELA.\nFor -0.939 m w.e./yr glacier-wide:\n  terminus ~3 m/yr, ELA ~0.2 m/yr",
   codeRef:"dixon_melt/glacier_dynamics.py"},

  {title:"Volume-Area Scaling (Bahr et al. 1997)",
   latex:"V = c_V \\cdot A^{\\gamma_V}",
   explain:"Relates glacier volume (km3) to area (km2). For Dixon at 40.1 km2: V = 0.034 * 40.1^1.36 = 3.75 km3, giving mean thickness ~94m. Used for initialization when Farinotti consensus thickness is not available, and as a consistency check.",
   variables:[
     {sym:"V",unit:"km3",val:"~3.75",desc:"Glacier volume"},
     {sym:"A",unit:"km2",val:"40.1",desc:"Glacier area"},
     {sym:"c_V",unit:"-",val:"0.034",desc:"Scaling coefficient"},
     {sym:"\\gamma_V",unit:"-",val:"1.36",desc:"Scaling exponent"}
   ],
   example:"Current: V = 0.034 * 40.1^1.36 = 3.75 km3 (94m mean)\nSSP2-4.5 2100 (19.6 km2): V = 0.034 * 19.6^1.36 = 1.50 km3 (77m mean)",
   codeRef:"dixon_melt/glacier_dynamics.py; dixon_melt/config.py"},

  {title:"MCMC Log-Likelihood (CAL-013)",
   latex:"\\ln \\mathcal{L} = -\\frac{1}{2} \\sum_{i}^{stakes} \\left(\\frac{b_i - \\hat{b}_i}{\\sigma_i}\\right)^2 - \\frac{1}{2}\\left(\\frac{\\bar{B}_{geo} - \\hat{B}_{geo}}{\\sigma_{geo}}\\right)^2 - \\frac{1}{2}\\sum_{j}^{snowlines}\\left(\\frac{z_j - \\hat{z}_j}{\\sigma_{sl}}\\right)^2",
   explain:"Three-component log-likelihood combining stakes, geodetic, and snowline observations. Each term is weighted by inverse variance. The hard geodetic penalty (lambda=50) prevents solutions that exceed reported uncertainty.\n\nThis three-component likelihood was the key innovation of CAL-013 (D-028). Previous calibrations used only stakes and geodetic, producing posteriors agnostic about snowline fit.",
   variables:[
     {sym:"b_i",unit:"m w.e.",val:"-5 to +3",desc:"Observed stake balance"},
     {sym:"\\sigma_i",unit:"m w.e.",val:"0.10-0.15",desc:"Stake uncertainty"},
     {sym:"\\bar{B}_{geo}",unit:"m w.e./yr",val:"-0.939",desc:"Geodetic balance"},
     {sym:"\\sigma_{geo}",unit:"m w.e./yr",val:"0.122",desc:"Geodetic uncertainty"},
     {sym:"z_j / \\sigma_{sl}",unit:"m",val:"984-1238 / 75",desc:"Snowline elevation / uncertainty"}
   ],
   example:"MAP params, WY2023:\nABL annual: chi2 = (-0.38/0.12)^2 = 10.0\nGeodetic: chi2 = (0.122/0.122)^2 = 1.0\nSnowline 2023: chi2 = (30/75)^2 = 0.16\nTotal ln(L) = -0.5*(10.0+1.0+0.16) = -5.58",
   codeRef:"run_calibration_v13.py; dixon_melt/calibration.py"},

  {title:"Linear Reservoir Discharge",
   latex:"Q_i(t) = k_i \\cdot S_i(t), \\quad S_i(t+1) = S_i(t) + f_i \\cdot R(t) - Q_i(t)",
   explain:"Three parallel linear reservoirs: fast (k=0.3/day, 60%), slow (k=0.05/day, 30%), groundwater (k=0.01/day, 10%). Total discharge Q = sum of all three, converted from mm/day to m3/s. Used in projections for peak water timing.",
   variables:[
     {sym:"Q_i",unit:"mm/day or m3/s",val:"0-12",desc:"Discharge from reservoir i"},
     {sym:"S_i",unit:"mm",val:"0-100",desc:"Storage in reservoir i"},
     {sym:"k_i",unit:"day-1",val:"0.3, 0.05, 0.01",desc:"Recession coefficients"},
     {sym:"f_i",unit:"-",val:"0.6, 0.3, 0.1",desc:"Partitioning fractions"}
   ],
   example:"Peak day, R=25 mm over 40 km2:\nFast: Q = 0.3*(10+15) = 7.5 mm/day\nSlow: Q = 0.05*(50+7.5) = 2.9 mm/day\nGW: Q = 0.01*(30+2.5) = 0.3 mm/day\nTotal = 10.7 mm/day * 40e6/86400 = 4.95 m3/s",
   codeRef:"dixon_melt/routing.py"},

  {title:"Gap-Fill Temperature Transfer",
   latex:"T_{nuka} = \\alpha_m \\cdot T_{station} + \\beta_m",
   explain:"Monthly regression predicting Nuka-equivalent temperature from other stations. Separate slope/intercept for each month, computed from overlapping valid days. The cascade fills gaps in priority order: MFB (best RMSE), McNeil, Anchor, Kachemak, Lower Kachemak.\n\nFor precipitation, monthly ratios (P_nuka / P_mfb) are used because precip transfer is noisier.",
   variables:[
     {sym:"\\alpha_m",unit:"-",val:"0.6-1.0",desc:"Monthly slope"},
     {sym:"\\beta_m",unit:"C",val:"-2 to +4",desc:"Monthly intercept"},
     {sym:"r_m",unit:"-",val:"1.4-2.4",desc:"Precip ratio (Nuka/MFB)"}
   ],
   example:"January gap, MFB = -8C:\nT_nuka = 0.8687*(-8) + (-0.25) = -7.20C\nJuly gap, MFB = 14C:\nT_nuka = 0.955*14 + 1.20 = 14.57C",
   codeRef:"dixon_melt/climate.py; config.py TEMP_TRANSFER_TO_NUKA"}
];

// ── VIEW RENDERING ──────────────────────────────────────────────────

function clearChildren(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function makeTable(headers, rows, opts) {
  opts = opts || {};
  var table = el('table');
  var thead = el('thead');
  var tr = el('tr');
  headers.forEach(function(h) { tr.appendChild(el('th', {textContent: h})); });
  thead.appendChild(tr);
  table.appendChild(thead);
  var tbody = el('tbody');
  rows.forEach(function(row) {
    var r = el('tr');
    row.forEach(function(cell, i) {
      var td = el('td', {textContent: String(cell)});
      if (opts.mono && opts.mono.indexOf(i) >= 0) td.style.fontFamily = "'Fira Code', monospace";
      r.appendChild(td);
    });
    tbody.appendChild(r);
  });
  table.appendChild(tbody);
  return table;
}

// ── Architecture View ───────────────────────────────────────────────

function renderArchitecture() {
  var v = document.getElementById('view-architecture');
  clearChildren(v);
  v.appendChild(el('h1', {textContent: 'Model Architecture'}));

  var diagramText = [
    '                        DIXON GLACIER DETIM -- DATA FLOW',
    '                        ================================',
    '',
    '  INPUT DATA                    PROCESSING                    CALIBRATION',
    '  ----------                    ----------                    -----------',
    '',
    '  Nuka SNOTEL (375m)  ------>  [climate.py]  ------+',
    '  Middle Fork Bradley          Gap-fill cascade     |',
    '  McNeil Canyon                5-station transfer    |',
    '  Anchor River Divide                                |',
    '                                                     v',
    '  IfSAR DEM (5m)     ------>  [terrain.py]  ------> [fast_model.py]',
    '  Glacier outline (RGI7)       Slope, aspect         DETIM kernel',
    '                               Horizon angles        (Numba JIT)',
    '                               Wind exposure (Sx)         |',
    '                                      |                    |',
    '  Solar geometry      ------>  [solar.py]  ---------->    |',
    '  Latitude 59.66N              I_pot lookup (365d)        |',
    '                                                          |',
    '  [config.py]  ----------------------------------------->|',
    '  All constants, params                                   |',
    '                                                          |',
    '                                                          v',
    '  Stake obs (27 rows) ------>  [calibration.py]  <---- model output',
    '  Geodetic MB (Hugonnet)       Objective function',
    '  Snowline obs (22 yr)         Inverse-variance',
    '                               + snowline chi2',
    '                                      |',
    '                                      v',
    '                               [run_calibration_v13.py]',
    '                               DE (5 seeds) + MCMC',
    '                               1,656 posterior samples',
    '                                      |',
    '  PROJECTION                          v                   OUTPUT',
    '  ----------                   [behavioral_filter.py]     ------',
    '                               Area evolution check',
    '  CMIP6 (5 GCMs)    ------>           |',
    '  SSP1-2.6 / 2-4.5 / 5-8.5           v',
    '                             [climate_projections.py]',
    '  [glacier_dynamics.py] <--- Bias correction',
    '  Delta-h thinning           Monthly delta method',
    '  Ice thickness track              |',
    '  Size-class switching             v',
    '           |               [run_projection.py]',
    '           +-------------> 250 params x 5 GCMs',
    '                           = 1,250 runs/scenario',
    '                                   |',
    '  [routing.py]  <----- daily melt  |',
    '  Linear reservoirs                v',
    '  Fast/slow/GW            Peak water timing',
    '                          Area/volume trajectories',
    '                          Discharge projections',
    '',
    '  VALIDATION',
    '  ----------',
    '  [snowline_validation.py]   22 years digitized snowlines',
    '  [behavioral_filter.py]     6 digitized outlines (2000-2025)',
    '  [run_validation.py]        Sub-period geodetic, stake check, sensitivity'
  ].join('\n');

  var pre = el('div', {className: 'ascii-box'});
  var moduleNames = DATA.modules.map(function(m) { return m.name; });
  var parts = diagramText.split(/(\[[\w_.]+\])/g);
  parts.forEach(function(part) {
    var match = part.match(/^\[(\w+\.py)\]$/);
    if (match && moduleNames.indexOf(match[1]) >= 0) {
      var span = el('span', {className: 'mod-link', textContent: match[1]});
      span.addEventListener('click', function() { openModulePanel(match[1]); });
      pre.appendChild(span);
    } else {
      pre.appendChild(document.createTextNode(part));
    }
  });
  v.appendChild(pre);

  // Module inventory table
  v.appendChild(el('h2', {textContent: 'Module Inventory'}));
  var rows = DATA.modules.map(function(m) {
    return [m.name, m.category, m.lines, m.deps.join(', ') || 'none', m.decisions.join(', ')];
  });
  var table = makeTable(['Module', 'Category', 'Lines', 'Dependencies', 'Decisions'], rows);
  var trs = table.querySelectorAll('tbody tr');
  trs.forEach(function(row, i) {
    var firstCell = row.querySelector('td');
    firstCell.style.color = '#6c8cff';
    firstCell.style.cursor = 'pointer';
    firstCell.addEventListener('click', function() {
      openModulePanel(DATA.modules[i].name);
    });
  });
  v.appendChild(el('div', {className: 'card'}, [table]));

  // Calibration summary
  v.appendChild(el('h2', {textContent: 'Current Calibration (CAL-013)'}));
  var cs = DATA.calSummary;
  v.appendChild(el('div', {className: 'card'}, [
    makeTable(['Property', 'Value'], [
      ['Version', cs.version], ['Method', cs.method], ['Decision', cs.decision],
      ['DE Seeds', cs.de_seeds.join(', ')], ['Modes Found', cs.n_modes],
      ['Best DE Cost', cs.de_best_cost.toFixed(3)], ['MCMC Samples', cs.n_samples],
      ['Acceptance', (cs.acceptance * 100).toFixed(1) + '%'],
      ['Wall Time', cs.wall_time_h.toFixed(1) + ' hours']
    ])
  ]));

  // MAP parameters
  v.appendChild(el('h2', {textContent: 'MAP Parameters (Best Fit)'}));
  var paramRows = Object.keys(DATA.bestParams).map(function(k) {
    var r = DATA.calSummary.posteriorRanges[k];
    return [k, DATA.bestParams[k].toFixed ? DATA.bestParams[k].toFixed(6) : DATA.bestParams[k],
            r ? '[' + r[0] + ', ' + r[1] + ']' : 'fixed'];
  });
  v.appendChild(el('div', {className: 'card'}, [
    makeTable(['Parameter', 'MAP Value', '90% CI'], paramRows)
  ]));
}

// ── Module Side Panel ───────────────────────────────────────────────

function openModulePanel(moduleName) {
  var mod = DATA.modules.find(function(m) { return m.name === moduleName; });
  if (!mod) return;

  document.getElementById('panel-title').textContent = mod.name;
  document.getElementById('panel-path').textContent = mod.path + ' (' + mod.lines + ' lines)';

  var body = document.getElementById('panel-body');
  clearChildren(body);

  mod.description.split('\n\n').forEach(function(para) {
    body.appendChild(el('p', {textContent: para}));
  });

  if (mod.equations && mod.equations.length > 0 && mod.equations[0] !== 'Same as fast_model.py' && mod.equations[0] !== 'All constants: see parameter table') {
    var eqSection = el('div', {className: 'panel-section'});
    eqSection.appendChild(el('div', {className: 'panel-section-title', textContent: 'Key Equations'}));
    mod.equations.forEach(function(eq) {
      var block = el('div', {className: 'eq-block'});
      block.textContent = '\\(' + eq + '\\)';
      eqSection.appendChild(block);
    });
    body.appendChild(eqSection);
  }

  if (mod.params && mod.params.length > 0) {
    var paramSection = el('div', {className: 'panel-section'});
    paramSection.appendChild(el('div', {className: 'panel-section-title', textContent: 'Parameters & Constants'}));
    paramSection.appendChild(makeTable(['Name', 'Value', 'Description'],
      mod.params.map(function(p) { return [p.name, p.val, p.desc]; })));
    body.appendChild(paramSection);
  }

  if (mod.decisions && mod.decisions.length > 0) {
    var decSection = el('div', {className: 'panel-section'});
    decSection.appendChild(el('div', {className: 'panel-section-title', textContent: 'Related Decisions'}));
    mod.decisions.forEach(function(dId) {
      var dec = DATA.decisions.find(function(d) { return d.id === dId; });
      var link = el('span', {className: 'decision-link', textContent: dId + ': ' + (dec ? dec.title : '')});
      link.addEventListener('click', function() {
        closePanel();
        switchView('decisions');
        setTimeout(function() { expandDecision(dId); }, 100);
      });
      decSection.appendChild(link);
    });
    body.appendChild(decSection);
  }

  document.getElementById('side-panel').classList.add('open');
  document.body.classList.add('panel-open');
  if (typeof MathJax !== 'undefined' && MathJax.typesetPromise) {
    MathJax.typesetPromise([body]);
  }
}

function closePanel() {
  document.getElementById('side-panel').classList.remove('open');
  document.body.classList.remove('panel-open');
}

document.getElementById('panel-close').addEventListener('click', closePanel);

// ── Data View ───────────────────────────────────────────────────────

var dataSubTabs = ['Stakes','Geodetic','Snowlines','Area','Sensitivity','Lapse Projections','Charts'];

function renderData() {
  var v = document.getElementById('view-data');
  clearChildren(v);
  v.appendChild(el('h1', {textContent: 'Observation Data & Results'}));

  var tabContainer = el('div', {className: 'sub-tabs'});
  dataSubTabs.forEach(function(name, i) {
    var tab = el('div', {className: 'sub-tab' + (i === 0 ? ' active' : ''), textContent: name});
    tab.addEventListener('click', function() {
      tabContainer.querySelectorAll('.sub-tab').forEach(function(t) { t.classList.remove('active'); });
      tab.classList.add('active');
      v.querySelectorAll('.data-panel').forEach(function(p) { p.classList.remove('active'); });
      document.getElementById('data-panel-' + i).classList.add('active');
      if (i === 6) setTimeout(renderCharts, 50);
    });
    tabContainer.appendChild(tab);
  });
  v.appendChild(tabContainer);

  // Stakes
  var p0 = el('div', {className: 'data-panel active', id: 'data-panel-0'});
  p0.appendChild(el('h2', {textContent: 'Stake Mass Balance Observations (25 rows)'}));
  p0.appendChild(el('p', {textContent: '3 sites (ABL 804m, ELA 1078m, ACC 1293m), WY2023-2025. Annual, summer, and winter periods.', style:{color:'#a0a4b8',marginBottom:'12px'}}));
  p0.appendChild(makeTable(['Site','Period','Year','Start','End','MB (m w.e.)','Unc','Elev'],
    DATA.stakes.map(function(s){return[s.site,s.period,s.year,s.start,s.end,s.mb.toFixed(2),s.unc.toFixed(2),s.elev];}),{mono:[5,6]}));
  v.appendChild(p0);

  // Geodetic
  var p1 = el('div', {className: 'data-panel', id: 'data-panel-1'});
  p1.appendChild(el('h2', {textContent: 'Geodetic Mass Balance (Hugonnet et al. 2021)'}));
  p1.appendChild(el('p', {textContent: 'RGI60-01.18059. 2000-2020 mean used for calibration; sub-periods are validation.', style:{color:'#a0a4b8',marginBottom:'12px'}}));
  p1.appendChild(makeTable(['Period','Area (km2)','dh/dt','err','dm/dt/da','err'],
    DATA.geodetic.map(function(g){return[g.period,(g.area_m2/1e6).toFixed(2),g.dhdt.toFixed(3),g.err.toFixed(3),g.dmdtda.toFixed(3),g.err_dm.toFixed(3)];}),{mono:[2,3,4,5]}));
  v.appendChild(p1);

  // Snowlines
  var p2 = el('div', {className: 'data-panel', id: 'data-panel-2'});
  p2.appendChild(el('h2', {textContent: 'Digitized Snowline Observations (22 years)'}));
  p2.appendChild(makeTable(['Year','Date','Source','Mean (m)','Median','Std','Min','Max','N'],
    DATA.snowlines.map(function(s){return[s.year,s.date,s.source,s.mean.toFixed(1),s.median.toFixed(1),s.std.toFixed(1),s.min.toFixed(1),s.max.toFixed(1),s.n];}),{mono:[3,4,5,6,7]}));
  v.appendChild(p2);

  // Area
  var p3 = el('div', {className: 'data-panel', id: 'data-panel-3'});
  p3.appendChild(el('h2', {textContent: 'Glacier Area Evolution (6 Outlines)'}));
  p3.appendChild(el('p', {textContent: 'Manual digitization, 5-year intervals. Total retreat: 1.77 km2 (4.4%).', style:{color:'#a0a4b8',marginBottom:'12px'}}));
  p3.appendChild(makeTable(['Year','Area (km2)','Loss (km2)','Source'],
    DATA.areas.map(function(a){return[a.year,a.area.toFixed(2),(40.11-a.area).toFixed(2),a.source];}),{mono:[1,2]}));
  v.appendChild(p3);

  // Sensitivity
  var p4 = el('div', {className: 'data-panel', id: 'data-panel-4'});
  p4.appendChild(el('h2', {textContent: 'Fixed Parameter Sensitivity (D-029)'}));
  p4.appendChild(el('p', {textContent: 'Lapse rate sensitivity is ~10x larger than r_ice/r_snow ratio.', style:{color:'#a0a4b8',marginBottom:'12px'}}));
  p4.appendChild(makeTable(['Parameter','Value','Geod Mod','Bias','Stake RMSE'],
    DATA.sensitivity.map(function(s){return[s.param,s.value.toFixed(2),s.geod_mod.toFixed(3),s.bias.toFixed(3),s.stake_rmse.toFixed(3)];}),{mono:[1,2,3,4]}));
  v.appendChild(p4);

  // Lapse projections
  var p5 = el('div', {className: 'data-panel', id: 'data-panel-5'});
  p5.appendChild(el('h2', {textContent: 'Lapse Rate Sensitivity Projections (D-030)'}));
  p5.appendChild(el('p', {textContent: '2100 area ranges from 5.4 km2 (-4.5, SSP5-8.5) to 31.7 km2 (-5.5, SSP1-2.6).', style:{color:'#a0a4b8',marginBottom:'12px'}}));
  p5.appendChild(makeTable(['Lapse','Scenario','Area p50','p05','p95','Vol (km3)','Peak Yr','Peak Q'],
    DATA.lapseProjections.map(function(l){return[l.lapse.toFixed(1),l.scenario.toUpperCase(),l.area_p50.toFixed(1),l.area_p05.toFixed(1),l.area_p95.toFixed(1),l.vol_p50.toFixed(2),l.peak_year,l.peak_q.toFixed(2)];}),{mono:[0,2,3,4,5,6,7]}));
  v.appendChild(p5);

  // Charts
  var p6 = el('div', {className: 'data-panel', id: 'data-panel-6'});
  p6.appendChild(el('h2', {textContent: 'Interactive Charts'}));
  p6.appendChild(el('div', {id: 'chart-stakes', style: {height:'400px',marginBottom:'24px'}}));
  p6.appendChild(el('div', {id: 'chart-snowlines', style: {height:'400px',marginBottom:'24px'}}));
  p6.appendChild(el('div', {id: 'chart-area', style: {height:'350px',marginBottom:'24px'}}));
  p6.appendChild(el('div', {id: 'chart-sensitivity', style: {height:'350px',marginBottom:'24px'}}));
  v.appendChild(p6);
}

function renderCharts() {
  var L = {
    paper_bgcolor:'#0f1117', plot_bgcolor:'#161822',
    font:{color:'#e8e8e8',family:'Inter, sans-serif',size:12},
    margin:{l:60,r:30,t:40,b:50},
    xaxis:{gridcolor:'#2a2d42',zerolinecolor:'#2a2d42'},
    yaxis:{gridcolor:'#2a2d42',zerolinecolor:'#2a2d42'},
    legend:{bgcolor:'rgba(0,0,0,0)'}
  };

  if (document.getElementById('chart-stakes')) {
    var sites=['ABL','ELA','ACC'], colors=['#ef4444','#6c8cff','#22c55e'];
    Plotly.newPlot('chart-stakes', sites.map(function(site,si){
      var d=DATA.stakes.filter(function(s){return s.site===site&&s.period==='annual';});
      return{x:d.map(function(s){return s.year;}),y:d.map(function(s){return s.mb;}),
        error_y:{type:'data',array:d.map(function(s){return s.unc;}),visible:true,color:colors[si]},
        name:site+' ('+d[0].elev+'m)',type:'scatter',mode:'markers+lines',
        marker:{color:colors[si],size:8},line:{color:colors[si]}};
    }), Object.assign({},L,{title:{text:'Annual Stake Mass Balance',font:{color:'#5eead4'}},
      yaxis:Object.assign({},L.yaxis,{title:'m w.e.'})}), {responsive:true});
  }

  if (document.getElementById('chart-snowlines')) {
    Plotly.newPlot('chart-snowlines', [
      {x:DATA.snowlines.map(function(s){return s.year;}),y:DATA.snowlines.map(function(s){return s.mean;}),
       error_y:{type:'data',array:DATA.snowlines.map(function(s){return s.std;}),visible:true,color:'#6c8cff44'},
       name:'Mean',type:'scatter',mode:'markers+lines',marker:{color:'#6c8cff',size:6},line:{color:'#6c8cff'}},
      {x:DATA.snowlines.map(function(s){return s.year;}),y:DATA.snowlines.map(function(s){return s.median;}),
       name:'Median',type:'scatter',mode:'markers',marker:{color:'#5eead4',size:5,symbol:'diamond'}}
    ], Object.assign({},L,{title:{text:'Snowline Elevation (22 years)',font:{color:'#5eead4'}},
      yaxis:Object.assign({},L.yaxis,{title:'Elevation (m)'})}), {responsive:true});
  }

  if (document.getElementById('chart-area')) {
    Plotly.newPlot('chart-area', [{
      x:DATA.areas.map(function(a){return a.year;}),y:DATA.areas.map(function(a){return a.area;}),
      type:'scatter',mode:'markers+lines',marker:{color:'#f59e0b',size:10},line:{color:'#f59e0b'},name:'Digitized'
    }], Object.assign({},L,{title:{text:'Glacier Area Evolution',font:{color:'#5eead4'}},
      yaxis:Object.assign({},L.yaxis,{title:'Area (km2)',range:[37,41]})}), {responsive:true});
  }

  if (document.getElementById('chart-sensitivity')) {
    var ls=DATA.sensitivity.filter(function(s){return s.param==='lapse_rate';});
    Plotly.newPlot('chart-sensitivity', [
      {x:ls.map(function(s){return s.value;}),y:ls.map(function(s){return s.bias;}),
       name:'Geodetic bias',type:'scatter',mode:'markers+lines',marker:{color:'#6c8cff',size:8},line:{color:'#6c8cff'}},
      {x:ls.map(function(s){return s.value;}),y:ls.map(function(s){return s.stake_rmse;}),
       name:'Stake RMSE',type:'scatter',mode:'markers+lines',marker:{color:'#ef4444',size:8},line:{color:'#ef4444'},yaxis:'y2'}
    ], Object.assign({},L,{title:{text:'Lapse Rate Sensitivity',font:{color:'#5eead4'}},
      xaxis:Object.assign({},L.xaxis,{title:'Lapse Rate (C/km)'}),
      yaxis:Object.assign({},L.yaxis,{title:'Geodetic Bias',titlefont:{color:'#6c8cff'}}),
      yaxis2:{title:'Stake RMSE',titlefont:{color:'#ef4444'},overlaying:'y',side:'right',gridcolor:'#2a2d42'}}),
      {responsive:true});
  }
}

// ── Decisions View ──────────────────────────────────────────────────

function renderDecisions() {
  var v = document.getElementById('view-decisions');
  clearChildren(v);
  v.appendChild(el('h1', {textContent: 'Decision Log (D-001 through D-031)'}));
  v.appendChild(el('p', {textContent: 'Every modeling decision with full rationale, alternatives, and deep explanation. Click to expand.', style:{color:'#a0a4b8',marginBottom:'20px'}}));

  var allTags=['all','fix','design','data','cal','val','proj'];
  var tagLabels={all:'All',fix:'Bug Fixes',design:'Design',data:'Data',cal:'Calibration',val:'Validation',proj:'Projection'};
  var tagBar = el('div', {className: 'sub-tabs', style:{marginBottom:'20px'}});
  allTags.forEach(function(t, i) {
    var btn = el('div', {className: 'sub-tab' + (i===0?' active':''), textContent: tagLabels[t]});
    btn.addEventListener('click', function() {
      tagBar.querySelectorAll('.sub-tab').forEach(function(b){b.classList.remove('active');});
      btn.classList.add('active');
      filterDecisions(t);
    });
    tagBar.appendChild(btn);
  });
  v.appendChild(tagBar);

  var listContainer = el('div', {id: 'decision-list'});
  v.appendChild(listContainer);

  DATA.decisions.forEach(function(dec) {
    var card = el('div', {className: 'decision-card', id: 'dec-' + dec.id});
    card.setAttribute('data-tags', dec.tags.join(','));

    var head = el('div', {className: 'decision-head'});
    head.appendChild(el('span', {className: 'decision-id', textContent: dec.id}));
    head.appendChild(el('span', {className: 'decision-title', textContent: dec.title}));
    dec.tags.forEach(function(t) {
      head.appendChild(el('span', {className: 'tag tag-' + t, textContent: t}));
    });
    head.appendChild(el('span', {className: 'decision-date', textContent: dec.date}));
    head.appendChild(el('span', {className: 'decision-chevron', textContent: '\u25B6'}));
    head.addEventListener('click', function() { card.classList.toggle('expanded'); });
    card.appendChild(head);

    var body = el('div', {className: 'decision-body'});
    dec.text.split('\n').forEach(function(para) {
      if (para.trim()) body.appendChild(el('p', {textContent: para.trim()}));
    });

    if (dec.alternatives) {
      var altBox = el('div', {style:{background:'#1e2030',borderRadius:'6px',padding:'12px 16px',margin:'12px 0'}});
      altBox.appendChild(el('div', {textContent: 'Alternatives Considered', style:{fontSize:'12px',fontWeight:'600',color:'#f59e0b',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:'6px'}}));
      altBox.appendChild(el('p', {textContent: dec.alternatives, style:{color:'#a0a4b8',margin:'0'}}));
      body.appendChild(altBox);
    }

    if (dec.why) {
      var whyBox = el('div', {className: 'why-box'});
      whyBox.appendChild(el('div', {className: 'why-box-title', textContent: 'Deep Explanation -- Why This Matters'}));
      dec.why.split('\n\n').forEach(function(para) {
        if (para.trim()) whyBox.appendChild(el('p', {textContent: para.trim(), style:{margin:'0 0 8px 0'}}));
      });
      body.appendChild(whyBox);
    }

    card.appendChild(body);
    listContainer.appendChild(card);
  });
}

function filterDecisions(tag) {
  document.querySelectorAll('.decision-card').forEach(function(card) {
    card.style.display = (tag === 'all' || card.getAttribute('data-tags').indexOf(tag) >= 0) ? '' : 'none';
  });
}

function expandDecision(id) {
  var card = document.getElementById('dec-' + id);
  if (card) {
    card.classList.add('expanded');
    card.scrollIntoView({behavior: 'smooth', block: 'start'});
  }
}

// ── Equations View ──────────────────────────────────────────────────

function renderEquations() {
  var v = document.getElementById('view-equations');
  clearChildren(v);
  v.appendChild(el('h1', {textContent: 'Model Equations'}));
  v.appendChild(el('p', {textContent: 'LaTeX-rendered equations with explanations, variable tables, and worked examples using real Dixon numbers.', style:{color:'#a0a4b8',marginBottom:'20px'}}));

  DATA.equations.forEach(function(eq) {
    var card = el('div', {className: 'eq-card'});
    card.appendChild(el('div', {className: 'eq-card-title', textContent: eq.title}));

    var eqDiv = el('div', {className: 'eq-main'});
    eqDiv.textContent = '$$' + eq.latex + '$$';
    card.appendChild(eqDiv);

    eq.explain.split('\n\n').forEach(function(para) {
      if (para.trim()) card.appendChild(el('p', {className: 'eq-explain', textContent: para.trim()}));
    });

    if (eq.variables && eq.variables.length > 0) {
      card.appendChild(el('h3', {textContent: 'Variables', style:{color:'#6c8cff',marginTop:'16px'}}));
      var vt = makeTable(['Symbol','Unit','Value','Description'],
        eq.variables.map(function(va){return['\\('+va.sym+'\\)',va.unit,va.val,va.desc];}));
      vt.className = 'var-table';
      card.appendChild(vt);
    }

    if (eq.example) {
      card.appendChild(el('h3', {textContent: 'Worked Example', style:{color:'#6c8cff',marginTop:'16px'}}));
      card.appendChild(el('div', {className: 'worked-example', textContent: eq.example}));
    }

    if (eq.codeRef) {
      card.appendChild(el('p', {style:{fontSize:'12px',color:'#6e7291',marginTop:'12px',fontFamily:"'Fira Code', monospace"},
        textContent: 'Source: ' + eq.codeRef}));
    }

    v.appendChild(card);
  });

  if (typeof MathJax !== 'undefined' && MathJax.typesetPromise) {
    MathJax.typesetPromise([v]);
  }
}

// ── Search View ─────────────────────────────────────────────────────

function renderSearch() {
  var v = document.getElementById('view-search');
  clearChildren(v);
  v.appendChild(el('h1', {textContent: 'Search'}));

  var input = el('input', {type:'text', id:'search-input', placeholder:'Search decisions, modules, equations, data...'});
  v.appendChild(input);
  var results = el('div', {id: 'search-results'});
  v.appendChild(results);

  input.addEventListener('input', function() {
    var q = input.value.toLowerCase().trim();
    clearChildren(results);
    if (q.length < 2) return;
    var hits = [];

    DATA.decisions.forEach(function(d) {
      if ((d.id+' '+d.title+' '+d.text+' '+(d.why||'')+' '+(d.alternatives||'')).toLowerCase().indexOf(q) >= 0)
        hits.push({type:'Decision',title:d.id+': '+d.title,excerpt:d.text.substring(0,150)+'...',
          action:function(){switchView('decisions');setTimeout(function(){expandDecision(d.id);},100);}});
    });
    DATA.modules.forEach(function(m) {
      if ((m.name+' '+m.description+' '+m.category).toLowerCase().indexOf(q) >= 0)
        hits.push({type:'Module',title:m.name,excerpt:m.description.substring(0,150)+'...',
          action:function(){switchView('architecture');setTimeout(function(){openModulePanel(m.name);},100);}});
    });
    DATA.equations.forEach(function(eq) {
      if ((eq.title+' '+eq.explain+' '+eq.example).toLowerCase().indexOf(q) >= 0)
        hits.push({type:'Equation',title:eq.title,excerpt:eq.explain.substring(0,150)+'...',
          action:function(){switchView('equations');}});
    });

    if (hits.length === 0) {
      results.appendChild(el('p', {textContent:'No results found.',style:{color:'#6e7291',padding:'20px'}}));
      return;
    }

    hits.slice(0, 30).forEach(function(hit) {
      var card = el('div', {className: 'search-hit'});
      card.appendChild(el('div', {className: 'search-hit-type', textContent: hit.type}));
      card.appendChild(el('div', {className: 'search-hit-title', textContent: hit.title}));
      card.appendChild(el('div', {className: 'search-hit-excerpt', textContent: hit.excerpt}));
      card.addEventListener('click', hit.action);
      results.appendChild(card);
    });
    results.appendChild(el('p', {textContent:hits.length+' result'+(hits.length!==1?'s':'')+' found',style:{color:'#6e7291',padding:'12px',fontSize:'12px'}}));
  });
}

// ── Navigation ──────────────────────────────────────────────────────

var views = ['architecture','data','decisions','equations','search'];
var rendered = {};

function switchView(name) {
  views.forEach(function(vn) {
    document.getElementById('view-'+vn).classList.remove('active');
  });
  document.getElementById('view-'+name).classList.add('active');
  document.querySelectorAll('nav .tab').forEach(function(tab) {
    tab.classList.toggle('active', tab.getAttribute('data-view') === name);
  });
  if (!rendered[name]) {
    rendered[name] = true;
    if (name === 'architecture') renderArchitecture();
    else if (name === 'data') renderData();
    else if (name === 'decisions') renderDecisions();
    else if (name === 'equations') renderEquations();
    else if (name === 'search') renderSearch();
  }
  if (name === 'data') setTimeout(renderCharts, 50);
  closePanel();
}

document.querySelectorAll('nav .tab').forEach(function(tab) {
  tab.addEventListener('click', function() { switchView(tab.getAttribute('data-view')); });
});

// Initialize
rendered.architecture = true;
renderArchitecture();
