/* ===================================================================
   Dixon Glacier DETIM -- Interactive Model Workbench (Enhanced)
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

// ── Lightbox ────────────────────────────────────────────────────────
function openLightbox(src, caption) {
  var lb = document.getElementById('lightbox');
  document.getElementById('lightbox-img').src = src;
  document.getElementById('lightbox-caption').textContent = caption || '';
  lb.classList.add('visible');
}

function makeFigThumb(figKey, label) {
  if (typeof FIGURES === 'undefined' || !FIGURES[figKey]) return el('div');
  var thumb = el('div', {className: 'fig-thumb'});
  var img = el('img', {src: FIGURES[figKey], alt: label});
  thumb.appendChild(img);
  thumb.appendChild(el('div', {className: 'fig-label', textContent: label}));
  thumb.addEventListener('click', function() { openLightbox(FIGURES[figKey], label); });
  return thumb;
}

function makeFigGrid(figures) {
  var grid = el('div', {className: 'fig-grid'});
  figures.forEach(function(f) { grid.appendChild(makeFigThumb(f[0], f[1])); });
  return grid;
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

// ── CLIMATE DATA ────────────────────────────────────────────────────
DATA.climate = {
  annual: [{"wy":1999,"T_ann":0.93,"T_sum":8.63,"P_ann":2032},{"wy":2000,"T_ann":1.4,"T_sum":8.0,"P_ann":1989},{"wy":2001,"T_ann":1.13,"T_sum":6.13,"P_ann":2903},{"wy":2002,"T_ann":1.2,"T_sum":8.5,"P_ann":1971},{"wy":2003,"T_ann":3.75,"T_sum":9.77,"P_ann":3523},{"wy":2004,"T_ann":2.54,"T_sum":10.52,"P_ann":2360},{"wy":2005,"T_ann":2.4,"T_sum":8.38,"P_ann":2421},{"wy":2006,"T_ann":1.45,"T_sum":8.65,"P_ann":2083},{"wy":2007,"T_ann":1.01,"T_sum":9.43,"P_ann":2131},{"wy":2008,"T_ann":0.83,"T_sum":7.61,"P_ann":2469},{"wy":2009,"T_ann":1.09,"T_sum":9.28,"P_ann":1557},{"wy":2010,"T_ann":1.93,"T_sum":8.18,"P_ann":1872},{"wy":2011,"T_ann":1.29,"T_sum":8.41,"P_ann":2187},{"wy":2012,"T_ann":0.16,"T_sum":7.74,"P_ann":2728},{"wy":2013,"T_ann":1.64,"T_sum":9.99,"P_ann":2019},{"wy":2014,"T_ann":3.11,"T_sum":9.87,"P_ann":2720},{"wy":2015,"T_ann":3.67,"T_sum":9.9,"P_ann":2604},{"wy":2016,"T_ann":3.94,"T_sum":10.43,"P_ann":3104},{"wy":2017,"T_ann":1.66,"T_sum":9.17,"P_ann":2309},{"wy":2018,"T_ann":2.85,"T_sum":10.83,"P_ann":2233},{"wy":2019,"T_ann":5.02,"T_sum":12.7,"P_ann":2756},{"wy":2020,"T_ann":3.47,"T_sum":10.97,"P_ann":2307},{"wy":2021,"T_ann":2.77,"T_sum":9.71,"P_ann":1918},{"wy":2022,"T_ann":2.73,"T_sum":10.31,"P_ann":2131},{"wy":2023,"T_ann":2.05,"T_sum":8.99,"P_ann":1803},{"wy":2024,"T_ann":1.79,"T_sum":8.89,"P_ann":1735},{"wy":2025,"T_ann":3.46,"T_sum":9.54,"P_ann":2606}],
  monthly: [{"month":1,"T":-4.64,"P":6.66},{"month":2,"T":-3.6,"P":5.19},{"month":3,"T":-3.82,"P":3.68},{"month":4,"T":-0.1,"P":4.25},{"month":5,"T":3.96,"P":3.5},{"month":6,"T":8.09,"P":3.44},{"month":7,"T":10.81,"P":4.18},{"month":8,"T":10.7,"P":5.96},{"month":9,"T":7.42,"P":10.31},{"month":10,"T":2.67,"P":11.48},{"month":11,"T":-2.02,"P":8.67},{"month":12,"T":-3.49,"P":8.64}]
};

// ── POSTERIOR DISTRIBUTIONS (top 250) ───────────────────────────────
DATA.posterior = {"MF":[7.057,7.051,7.143,7.204,7.113,7.112,7.114,7.313,7.215,7.014,7.177,7.027,7.028,7.065,7.218,7.068,7.352,7.319,7.304,7.345,7.214,7.140,7.148,7.167,7.156,7.334,7.295,7.294,7.287,7.286,7.075,7.215,7.149,7.205,7.150,6.979,7.123,7.247,7.151,7.184,7.009,7.155,7.288,7.209,7.250,6.999,7.203,7.170,7.247,7.227,7.222,7.200,7.226,7.195,7.196,7.194,7.225,7.169,7.217,7.276,7.320,7.202,7.281,7.126,7.134,7.281,7.210,7.285,7.154,7.342,7.308,7.278,7.106,7.277,7.153,7.022,7.279,7.319,7.153,7.250,7.280,7.194,7.246,7.245,7.223,7.011,7.246,7.178,7.101,7.330,7.142,7.164,7.318,7.330,7.227,7.165,7.193,7.264,7.189,7.243,7.143,7.231,6.988,7.162,7.185,7.163,7.266,7.199,7.168,7.252,7.199,7.138,7.283,7.249,7.259,7.035,7.213,7.298,7.371,7.133,6.997,7.025,7.025,7.301,7.134,7.218,7.145,7.176,7.081,7.092,7.206,7.265,7.246,7.203,7.014,7.228,7.253,7.214,7.147,7.134,7.109,7.199,7.296,7.163,7.100,7.258,7.185,7.184,7.231,7.384,7.162,7.099,7.247,7.091,7.091,7.090,7.094,7.309,7.209,7.225,7.298,7.295,7.027,7.047,7.087,7.128,7.293,7.121,7.229,7.100,7.183,7.230,7.281,7.168,7.139,7.374,7.186,7.117,7.265,7.084,7.298,7.174,7.354,7.275,7.184,7.179,7.100,7.056,7.221,7.059,7.139,7.116,7.155,7.177,7.061,7.045,7.334,7.300,7.149,7.215,7.087,6.969,7.269,7.057,7.036,7.068,7.202,7.275,7.346,7.202,7.203,7.050,6.948,6.948,7.243,7.058,7.188,7.191,7.226,7.269,7.026,7.196,7.000,7.107,7.163,7.057,7.333,7.297,7.299,7.232,7.167,7.249,7.204,7.242,7.027,7.215,7.199,7.252,7.301,7.197,7.118,7.300,7.133,7.201,7.200,7.181,7.137,7.199,7.054,7.208],"MF_grad":[-0.00409,-0.00409,-0.00417,-0.00429,-0.00412,-0.00412,-0.00412,-0.00423,-0.00431,-0.00405,-0.00420,-0.00406,-0.00407,-0.00414,-0.00428,-0.00411,-0.00434,-0.00437,-0.00428,-0.00429,-0.00418,-0.00416,-0.00415,-0.00421,-0.00414,-0.00433,-0.00428,-0.00427,-0.00426,-0.00426,-0.00412,-0.00422,-0.00405,-0.00425,-0.00416,-0.00396,-0.00413,-0.00420,-0.00413,-0.00420,-0.00403,-0.00409,-0.00422,-0.00425,-0.00433,-0.00398,-0.00421,-0.00421,-0.00419,-0.00420,-0.00431,-0.00421,-0.00430,-0.00418,-0.00418,-0.00418,-0.00419,-0.00419,-0.00416,-0.00421,-0.00429,-0.00424,-0.00424,-0.00403,-0.00414,-0.00424,-0.00413,-0.00436,-0.00417,-0.00431,-0.00427,-0.00422,-0.00413,-0.00423,-0.00423,-0.00404,-0.00424,-0.00424,-0.00422,-0.00420,-0.00424,-0.00414,-0.00419,-0.00419,-0.00410,-0.00404,-0.00415,-0.00420,-0.00410,-0.00433,-0.00416,-0.00415,-0.00423,-0.00433,-0.00435,-0.00409,-0.00413,-0.00423,-0.00413,-0.00433,-0.00420,-0.00437,-0.00394,-0.00414,-0.00417,-0.00414,-0.00417,-0.00419,-0.00417,-0.00420,-0.00419,-0.00411,-0.00424,-0.00426,-0.00427,-0.00396,-0.00436,-0.00427,-0.00433,-0.00412,-0.00399,-0.00400,-0.00400,-0.00424,-0.00412,-0.00431,-0.00413,-0.00416,-0.00410,-0.00405,-0.00431,-0.00424,-0.00431,-0.00413,-0.00406,-0.00416,-0.00416,-0.00430,-0.00413,-0.00410,-0.00410,-0.00412,-0.00425,-0.00420,-0.00411,-0.00431,-0.00412,-0.00409,-0.00421,-0.00432,-0.00411,-0.00407,-0.00423,-0.00410,-0.00410,-0.00410,-0.00410,-0.00428,-0.00413,-0.00411,-0.00428,-0.00427,-0.00400,-0.00401,-0.00409,-0.00403,-0.00418,-0.00405,-0.00423,-0.00410,-0.00411,-0.00417,-0.00418,-0.00415,-0.00418,-0.00431,-0.00413,-0.00414,-0.00424,-0.00405,-0.00426,-0.00422,-0.00426,-0.00421,-0.00406,-0.00411,-0.00404,-0.00407,-0.00418,-0.00407,-0.00402,-0.00414,-0.00418,-0.00415,-0.00413,-0.00401,-0.00426,-0.00419,-0.00414,-0.00432,-0.00409,-0.00388,-0.00420,-0.00400,-0.00407,-0.00413,-0.00410,-0.00421,-0.00426,-0.00411,-0.00411,-0.00401,-0.00387,-0.00387,-0.00420,-0.00403,-0.00417,-0.00415,-0.00413,-0.00420,-0.00400,-0.00410,-0.00395,-0.00403,-0.00423,-0.00397,-0.00415,-0.00428,-0.00428,-0.00416,-0.00419,-0.00425,-0.00414,-0.00412,-0.00400,-0.00403,-0.00417,-0.00418,-0.00431,-0.00419,-0.00413,-0.00425,-0.00413,-0.00411,-0.00418,-0.00411,-0.00413,-0.00411,-0.00397,-0.00411],"r_snow":[0.00196,0.00198,0.00186,0.00187,0.00181,0.00181,0.00180,0.00144,0.00197,0.00199,0.00173,0.00196,0.00196,0.00199,0.00181,0.00194,0.00152,0.00166,0.00157,0.00147,0.00171,0.00186,0.00178,0.00176,0.00180,0.00156,0.00163,0.00161,0.00162,0.00162,0.00193,0.00167,0.00162,0.00172,0.00183,0.00196,0.00196,0.00164,0.00187,0.00175,0.00198,0.00178,0.00156,0.00174,0.00187,0.00195,0.00169,0.00176,0.00168,0.00171,0.00192,0.00170,0.00190,0.00184,0.00184,0.00184,0.00161,0.00178,0.00156,0.00158,0.00154,0.00174,0.00159,0.00163,0.00184,0.00159,0.00163,0.00170,0.00197,0.00151,0.00155,0.00155,0.00193,0.00156,0.00198,0.00198,0.00157,0.00145,0.00197,0.00163,0.00163,0.00177,0.00164,0.00163,0.00146,0.00200,0.00152,0.00189,0.00188,0.00160,0.00190,0.00183,0.00144,0.00160,0.00194,0.00172,0.00157,0.00157,0.00176,0.00186,0.00192,0.00192,0.00193,0.00185,0.00179,0.00184,0.00146,0.00184,0.00188,0.00155,0.00184,0.00185,0.00162,0.00171,0.00165,0.00177,0.00198,0.00160,0.00148,0.00178,0.00196,0.00199,0.00199,0.00146,0.00175,0.00193,0.00173,0.00180,0.00180,0.00179,0.00195,0.00168,0.00181,0.00166,0.00199,0.00168,0.00151,0.00193,0.00184,0.00185,0.00181,0.00166,0.00151,0.00187,0.00191,0.00178,0.00166,0.00163,0.00174,0.00145,0.00172,0.00178,0.00169,0.00189,0.00189,0.00190,0.00189,0.00159,0.00149,0.00151,0.00166,0.00167,0.00197,0.00192,0.00191,0.00168,0.00135,0.00170,0.00170,0.00187,0.00166,0.00167,0.00156,0.00173,0.00190,0.00147,0.00175,0.00189,0.00158,0.00187,0.00152,0.00191,0.00146,0.00158,0.00164,0.00153,0.00181,0.00196,0.00176,0.00195,0.00154,0.00194,0.00188,0.00170,0.00190,0.00190,0.00150,0.00147,0.00192,0.00192,0.00188,0.00182,0.00161,0.00184,0.00196,0.00188,0.00168,0.00163,0.00146,0.00170,0.00155,0.00186,0.00186,0.00187,0.00172,0.00181,0.00162,0.00178,0.00152,0.00160,0.00188,0.00171,0.00192,0.00183,0.00200,0.00177,0.00120,0.00168,0.00168,0.00164,0.00187,0.00169,0.00153,0.00145,0.00187,0.00137,0.00175,0.00161,0.00172,0.00173,0.00195,0.00157,0.00186,0.00156,0.00167,0.00162,0.00186,0.00156,0.00171,0.00153],"precip_corr":[1.578,1.582,1.576,1.637,1.492,1.498,1.498,1.656,1.622,1.492,1.547,1.497,1.497,1.550,1.638,1.569,1.601,1.630,1.568,1.584,1.545,1.575,1.535,1.574,1.524,1.609,1.576,1.573,1.559,1.558,1.570,1.572,1.471,1.599,1.575,1.595,1.554,1.567,1.553,1.568,1.509,1.630,1.569,1.599,1.666,1.600,1.577,1.578,1.563,1.561,1.621,1.578,1.623,1.589,1.587,1.588,1.562,1.583,1.636,1.574,1.619,1.589,1.592,1.587,1.581,1.591,1.545,1.669,1.594,1.635,1.617,1.581,1.574,1.583,1.579,1.539,1.595,1.659,1.580,1.559,1.590,1.565,1.559,1.562,1.586,1.541,1.570,1.602,1.559,1.657,1.599,1.580,1.657,1.658,1.689,1.525,1.550,1.575,1.570,1.677,1.614,1.721,1.592,1.584,1.592,1.583,1.576,1.589,1.598,1.580,1.589,1.571,1.618,1.640,1.634,1.602,1.716,1.637,1.639,1.563,1.534,1.531,1.531,1.605,1.564,1.686,1.568,1.579,1.572,1.534,1.685,1.624,1.667,1.554,1.544,1.574,1.574,1.685,1.579,1.566,1.559,1.558,1.623,1.625,1.573,1.673,1.582,1.533,1.623,1.645,1.583,1.524,1.640,1.593,1.593,1.593,1.594,1.661,1.576,1.565,1.640,1.640,1.526,1.530,1.581,1.532,1.562,1.614,1.640,1.598,1.583,1.602,1.605,1.561,1.594,1.645,1.569,1.607,1.585,1.578,1.590,1.618,1.622,1.579,1.541,1.574,1.569,1.595,1.573,1.595,1.515,1.578,1.595,1.614,1.590,1.540,1.598,1.612,1.575,1.716,1.602,1.478,1.589,1.539,1.557,1.590,1.589,1.595,1.601,1.589,1.592,1.540,1.483,1.483,1.642,1.603,1.612,1.613,1.602,1.589,1.540,1.588,1.538,1.559,1.676,1.525,1.566,1.637,1.639,1.616,1.603,1.678,1.581,1.583,1.541,1.509,1.612,1.589,1.694,1.590,1.589,1.654,1.577,1.547,1.640,1.599,1.579,1.545,1.594,1.549],"precip_grad":[0.000752,0.000747,0.000760,0.000671,0.000883,0.000873,0.000872,0.000660,0.000711,0.000877,0.000795,0.000870,0.000870,0.000787,0.000672,0.000761,0.000732,0.000687,0.000781,0.000757,0.000816,0.000762,0.000820,0.000751,0.000846,0.000725,0.000772,0.000775,0.000797,0.000798,0.000760,0.000765,0.000928,0.000719,0.000763,0.000735,0.000808,0.000785,0.000812,0.000770,0.000856,0.000708,0.000785,0.000725,0.000647,0.000730,0.000756,0.000746,0.000802,0.000796,0.000710,0.000755,0.000709,0.000764,0.000766,0.000765,0.000780,0.000751,0.000676,0.000783,0.000712,0.000736,0.000753,0.000750,0.000755,0.000753,0.000819,0.000633,0.000764,0.000686,0.000717,0.000762,0.000767,0.000757,0.000769,0.000811,0.000741,0.000657,0.000767,0.000798,0.000757,0.000802,0.000798,0.000794,0.000751,0.000806,0.000776,0.000740,0.000797,0.000661,0.000742,0.000775,0.000662,0.000660,0.000617,0.000854,0.000795,0.000767,0.000797,0.000636,0.000713,0.000571,0.000748,0.000771,0.000755,0.000771,0.000767,0.000765,0.000748,0.000756,0.000765,0.000786,0.000722,0.000678,0.000686,0.000728,0.000579,0.000686,0.000685,0.000783,0.000820,0.000842,0.000842,0.000727,0.000776,0.000625,0.000770,0.000770,0.000756,0.000822,0.000625,0.000714,0.000646,0.000807,0.000803,0.000788,0.000771,0.000626,0.000774,0.000793,0.000786,0.000803,0.000701,0.000702,0.000772,0.000641,0.000762,0.000841,0.000716,0.000686,0.000761,0.000839,0.000684,0.000739,0.000739,0.000740,0.000738,0.000658,0.000758,0.000787,0.000694,0.000694,0.000848,0.000841,0.000761,0.000838,0.000782,0.000712,0.000680,0.000734,0.000762,0.000746,0.000745,0.000790,0.000742,0.000685,0.000796,0.000723,0.000754,0.000768,0.000750,0.000718,0.000720,0.000782,0.000838,0.000757,0.000784,0.000739,0.000795,0.000738,0.000856,0.000775,0.000749,0.000712,0.000729,0.000824,0.000753,0.000729,0.000792,0.000584,0.000728,0.000913,0.000770,0.000826,0.000788,0.000730,0.000773,0.000763,0.000749,0.000774,0.000745,0.000822,0.000905,0.000905,0.000695,0.000719,0.000707,0.000736,0.000733,0.000770,0.000813,0.000776,0.000827,0.000813,0.000644,0.000850,0.000788,0.000704,0.000700,0.000727,0.000739,0.000634,0.000750,0.000763,0.000812,0.000873,0.000729,0.000768,0.000625,0.000751,0.000765,0.000671,0.000775,0.000817,0.000676,0.000734,0.000773,0.000820,0.000735,0.000814],"T0":[0.004,0.004,0.004,0.000,0.002,0.002,0.002,0.001,0.001,0.004,0.004,0.004,0.004,0.006,0.001,0.002,0.001,0.002,0.002,0.004,0.001,0.004,0.005,0.003,0.002,0.001,0.002,0.002,0.001,0.001,0.002,0.004,0.001,0.002,0.004,0.000,0.002,0.003,0.002,0.005,0.005,0.001,0.003,0.004,0.005,0.005,0.003,0.003,0.004,0.001,0.002,0.003,0.002,0.001,0.000,0.001,0.003,0.007,0.002,0.004,0.003,0.003,0.003,0.002,0.003,0.003,0.002,0.001,0.000,0.000,0.004,0.008,0.004,0.008,0.002,0.009,0.007,0.001,0.002,0.004,0.004,0.001,0.004,0.004,0.003,0.009,0.001,0.005,0.001,0.002,0.012,0.005,0.001,0.002,0.000,0.002,0.005,0.004,0.001,0.000,0.010,0.002,0.003,0.005,0.009,0.005,0.005,0.000,0.005,0.006,0.000,0.004,0.002,0.001,0.007,0.000,0.003,0.004,0.003,0.008,0.008,0.000,0.000,0.006,0.001,0.001,0.002,0.009,0.002,0.004,0.000,0.004,0.000,0.004,0.003,0.003,0.002,0.001,0.004,0.004,0.002,0.004,0.004,0.012,0.012,0.000,0.007,0.002,0.002,0.002,0.007,0.005,0.003,0.003,0.003,0.003,0.003,0.005,0.002,0.004,0.002,0.002,0.001,0.003,0.004,0.003,0.003,0.005,0.003,0.003,0.007,0.009,0.004,0.005,0.011,0.004,0.002,0.009,0.004,0.011,0.004,0.010,0.004,0.003,0.005,0.000,0.010,0.002,0.003,0.003,0.003,0.002,0.008,0.006,0.001,0.002,0.004,0.006,0.001,0.003,0.004,0.001,0.001,0.005,0.005,0.001,0.003,0.001,0.005,0.004,0.006,0.003,0.000,0.000,0.003,0.001,0.006,0.006,0.004,0.001,0.007,0.003,0.003,0.003,0.011,0.006,0.004,0.003,0.003,0.001,0.009,0.000,0.003,0.000,0.008,0.001,0.003,0.003,0.004,0.005,0.002,0.001,0.001,0.000,0.006,0.006,0.002,0.000,0.001,0.000]};

// ── PROJECTION ENVELOPES ────────────────────────────────────────────
DATA.projections = {"ssp126":{"year":[2005,2010,2015,2020,2025,2030,2035,2040,2045,2050,2055,2060,2065,2070,2075,2080,2085,2090,2095,2100],"p05":[40.11,40.06,39.74,39.2,38.14,37.17,36.16,35.96,35.31,34.4,33.44,32.06,30.82,29.11,27.32,25.92,25.25,23.17,21.88,21.76],"p25":[40.11,40.06,39.75,39.2,38.14,37.8,37.05,36.53,35.62,34.8,33.53,32.89,32.1,30.8,30.16,28.54,27.73,25.95,24.67,24.15],"p50":[40.11,40.06,39.75,39.2,38.15,38.01,37.4,36.78,35.74,35.03,33.72,33.32,32.59,31.76,31.18,29.65,28.74,27.36,25.93,25.0],"p75":[40.11,40.06,39.75,39.21,38.16,38.02,37.48,36.82,35.81,35.09,34.26,33.91,33.27,32.62,31.87,30.79,29.99,29.13,27.88,27.0],"p95":[40.11,40.06,39.76,39.21,38.17,38.03,37.55,36.92,35.93,35.13,35.11,35.11,35.02,34.0,33.72,33.71,33.18,32.92,32.64,32.64]},"ssp245":{"year":[2005,2010,2015,2020,2025,2030,2035,2040,2045,2050,2055,2060,2065,2070,2075,2080,2085,2090,2095,2100],"p05":[40.11,40.06,39.74,39.2,38.14,37.44,36.74,35.83,35.38,34.25,32.81,31.33,29.37,27.72,25.45,22.61,21.0,19.54,18.16,17.04],"p25":[40.11,40.06,39.75,39.2,38.14,37.55,36.85,36.14,35.68,34.3,32.99,31.53,30.29,29.2,27.05,25.23,23.4,21.84,19.96,18.92],"p50":[40.11,40.06,39.75,39.2,38.15,37.79,37.03,36.51,35.74,34.43,33.53,32.54,31.05,29.31,27.88,25.87,23.92,22.27,21.11,19.6],"p75":[40.11,40.06,39.75,39.21,38.16,38.05,37.44,36.97,36.54,35.71,34.97,33.63,32.46,30.57,28.16,26.08,24.52,22.62,21.66,19.87],"p95":[40.11,40.06,39.76,39.21,38.17,38.06,37.68,37.06,36.75,35.74,35.24,33.71,33.16,32.53,31.82,30.96,29.25,28.19,26.77,25.53]},"ssp585":{"year":[2005,2010,2015,2020,2025,2030,2035,2040,2045,2050,2055,2060,2065,2070,2075,2080,2085,2090,2095,2100],"p05":[40.11,40.06,39.74,39.2,38.14,37.59,37.08,36.16,35.14,33.77,32.03,30.79,28.14,25.09,21.62,19.12,17.01,14.31,12.21,8.79],"p25":[40.11,40.06,39.75,39.2,38.14,37.63,37.12,36.38,35.57,33.97,32.56,30.83,28.7,25.39,22.07,19.19,17.14,14.8,12.4,9.6],"p50":[40.11,40.06,39.75,39.2,38.15,37.75,37.3,36.59,35.71,34.05,32.97,31.52,28.82,25.47,22.31,20.17,18.09,15.39,12.99,10.49],"p75":[40.11,40.06,39.75,39.21,38.16,37.92,37.41,36.81,36.0,35.04,33.54,31.61,29.55,26.8,23.49,21.36,19.6,18.42,16.24,13.7],"p95":[40.11,40.06,39.76,39.21,38.17,37.96,37.49,37.26,36.77,36.12,36.0,35.14,33.8,33.15,32.26,30.82,28.19,26.08,24.13,22.57]}};

// ── CALIBRATION TIMELINE ────────────────────────────────────────────
DATA.calTimeline = [
  {id:"CAL-001",date:"2026-03-05",status:"FAILED",change:"Initial calibration",issue:"5/8 params at bounds. SWE double-counting (D-005)",cost:15.016,params:8},
  {id:"CAL-002",date:"2026-03-06",status:"FAILED",change:"Fix SWE init (D-005)",issue:"Aborted. MF=1.0, precip_corr=6.0 at bounds. Wrong ref elevation (D-006)",cost:15.87,params:7},
  {id:"CAL-003",date:"2026-03-06",status:"FAILED",change:"Fix ref elev 1230m->804m (D-006)",issue:"4/7 params at bounds. lapse_rate=-3.5 at bound",cost:17.508,params:7},
  {id:"CAL-004",date:"2026-03-06",status:"FAILED",change:"Statistical temp transfer + MF_grad (D-007,D-008)",issue:"MF=19.3 -- unreasonable. Transfer too cold for DETIM",cost:8.49,params:8},
  {id:"CAL-005",date:"2026-03-06",status:"FAILED",change:"Wider MF bounds [1,25]",issue:"MF=22.6. Statistical transfer incompatible with DETIM",cost:7.24,params:8},
  {id:"CAL-006",date:"2026-03-06",status:"FAILED",change:"Winter katabatic correction (D-010)",issue:"MF=21.3. Winter improved, summer T still too cold",cost:6.98,params:8},
  {id:"CAL-007",date:"2026-03-06",status:"PROGRESS",change:"Identity transfer, raw Nuka (D-012)",issue:"k_wind~0, lapse=-6.83 equifinal. First reasonable params",cost:5.66,params:8},
  {id:"CAL-008",date:"2026-03-09",status:"PROGRESS",change:"Nuka 375m + inv-variance (D-013,D-014)",issue:"Sub-period geodetic contradiction. precip_corr at bound",cost:6.12,params:8},
  {id:"CAL-009",date:"2026-03-09",status:"PROGRESS",change:"Single geodetic + wider precip_corr (D-016)",issue:"lapse=-6.83 equifinal with precip_corr=1.20",cost:5.34,params:8},
  {id:"CAL-010",date:"2026-03-09",status:"SUCCESS",change:"DE+MCMC, fix lapse/r_ice/k_wind (D-015,D-017)",issue:"First Bayesian ensemble. MF=7.3, precip_corr=1.67",cost:5.35,params:6},
  {id:"CAL-011",date:"2026-03-12",status:"FAILED",change:"Gap-filled climate (D-025,D-026)",issue:"Killed at DE step 28 -- superseded by multi-seed",cost:null,params:6},
  {id:"CAL-012",date:"2026-03-12",status:"SUCCESS",change:"Multi-seed DE, 5 seeds (D-027)",issue:"Unimodal confirmed. Snowline filter has zero power",cost:5.343,params:6},
  {id:"CAL-013",date:"2026-03-18",status:"SUCCESS",change:"Snowline in MCMC likelihood (D-028)",issue:"Final: 1656 samples, acceptance 0.368. 100% pass area filter",cost:5.343,params:6}
];

// ── MODULES ─────────────────────────────────────────────────────────

DATA.modules = [
  {name:"config.py",path:"dixon_melt/config.py",lines:193,category:"Core",
   deps:[],decisions:["D-013","D-015","D-017","D-023"],
   description:"Site-specific configuration and physical constants for Dixon Glacier. Contains all elevation references, station metadata, temperature transfer coefficients, gap-filling parameters, default model parameters, physical constants, delta-h coefficients, and routing defaults.\n\nThis file is the single source of truth for every number in the model that is not a calibrated parameter. Every correction to elevation data (D-013: Nuka from 1230m to 375m; D-023: Dixon AWS from 804m to 1078m) propagated through config.py first.\n\nIf any constant here were wrong, the entire model would be silently miscalibrated. The Nuka elevation error (D-013) is the clearest example: 855m of wrong elevation caused every calibration from CAL-001 through CAL-007 to fail.",
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
   description:"The Numba-compiled simulation kernel -- the computational heart of the model. This single @njit(parallel=True) function runs the full DETIM physics for an arbitrary time period on the entire glacier grid, returning cumulative melt, accumulation, daily runoff, stake balances, glacier-wide balance, and end-of-run SWE.\n\nThe function takes raw Nuka SNOTEL temperature at 375m and applies identity transfer (alpha=1, beta=0 for all months, per D-012) followed by the calibrated lapse rate to reach each grid cell.\n\nPerformance matters because calibration requires ~250,000 evaluations. Numba JIT compilation plus parallel=True across grid cells reduces per-evaluation time from several seconds to ~300ms.",
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
   description:"The objective function builder for differential evolution calibration. Defines the cost function that tells the optimizer how well a given parameter set reproduces observations. Uses inverse-variance weighting (D-014) with a hard geodetic penalty.\n\nFor CAL-013 (D-028), snowline elevations were added as a chi-squared term in the MCMC log-likelihood with sigma=75m.",
   equations:["\\mathcal{L} = -\\frac{1}{2} \\sum_i \\left(\\frac{y_i - \\hat{y}_i}{\\sigma_i}\\right)^2"],
   params:[
     {name:"sigma_stakes",val:"0.10-0.15 m w.e.",desc:"Stake measurement uncertainty"},
     {name:"sigma_geodetic",val:"0.122 m w.e./yr",desc:"Hugonnet 2000-2020 uncertainty"},
     {name:"sigma_snowline",val:"75 m",desc:"Combined snowline uncertainty"},
     {name:"lambda_penalty",val:"50",desc:"Hard geodetic penalty multiplier"}
   ]},

  {name:"climate.py",path:"dixon_melt/climate.py",lines:606,category:"Data",
   deps:["config.py"],decisions:["D-002","D-025"],
   description:"Climate data ingestion, quality control, and multi-station gap-filling. The largest module (606 lines). Loads Nuka SNOTEL daily data, converts from imperial to metric, and fills gaps using a cascade of 5 nearby SNOTEL stations.\n\nThe gap-filling cascade (D-025) replaced the original ffill().fillna(0) approach that had been silently poisoning calibration. Each fill station has monthly regression coefficients stored in config.py. Coverage: 91.3% Nuka, 6.0% MFB, 1.8% McNeil.",
   equations:["T_{nuka} = \\alpha_m \\cdot T_{station} + \\beta_m","P_{nuka} = r_m \\cdot P_{mfb}"],
   params:[
     {name:"Fill cascade",val:"Nuka -> MFB -> McNeil -> Anchor -> Kach -> LKC",desc:"Priority order"},
     {name:"Coverage",val:"91.3% / 6.0% / 1.8% / 0.4% / 0.3%",desc:"Fraction per station"}
   ]},

  {name:"solar.py",path:"dixon_melt/solar.py",lines:195,category:"Physics",
   deps:["config.py"],decisions:[],
   description:"Potential clear-sky direct solar radiation computation. Generates a (365, nrows, ncols) lookup table of daily I_pot values for every grid cell. Accounts for: solar declination, hour angle, slope, aspect, self-shading, and horizon shading from surrounding terrain.",
   equations:["I_{pot} = I_0 \\cdot \\psi_a^{(P/P_0 \\cdot \\cos\\theta_z)} \\cdot \\cos\\theta_i"],
   params:[
     {name:"I_0",val:"1368 W/m2",desc:"Solar constant"},
     {name:"psi_a",val:"0.75",desc:"Clear-sky atmospheric transmissivity"}
   ]},

  {name:"terrain.py",path:"dixon_melt/terrain.py",lines:240,category:"Data",
   deps:["config.py"],decisions:["D-011"],
   description:"DEM processing, slope/aspect computation, horizon angle calculation, and wind exposure (Winstral Sx) computation. Loads the 5m IfSAR DEM, resamples to model resolution, and prepares all static terrain arrays.",
   equations:["Sx = \\max_{d=1}^{D} \\arctan\\left(\\frac{z_{upwind}(d) - z_0}{d}\\right)"],
   params:[
     {name:"WIND_AZIMUTH",val:"100 deg",desc:"Prevailing wind direction (ESE)"},
     {name:"WIND_SEARCH_DIST",val:"300 m",desc:"Maximum upwind search distance"}
   ]},

  {name:"glacier_dynamics.py",path:"dixon_melt/glacier_dynamics.py",lines:285,category:"Physics",
   deps:["config.py"],decisions:["D-018"],
   description:"Delta-h parameterization of glacier geometry change (Huss et al. 2010). Distributes glacier-wide volume change across elevation bands using empirical thinning profiles. Tracks ice thickness using Farinotti (2019) consensus estimate. Cells with zero remaining ice are removed from the glacier mask.",
   equations:["\\Delta h(z) = \\frac{\\Delta V}{A} \\cdot f_s \\cdot \\left(\\frac{z_{max} - z}{z_{max} - z_{min}}\\right)^\\gamma"],
   params:[
     {name:"VA_C",val:"0.0340",desc:"Volume-area coefficient"},
     {name:"VA_GAMMA",val:"1.36",desc:"Volume-area exponent (Bahr et al.)"}
   ]},

  {name:"climate_projections.py",path:"dixon_melt/climate_projections.py",lines:180,category:"Projection",
   deps:["config.py","climate.py"],decisions:["D-019"],
   description:"CMIP6 bias correction and projection climate generation. Downloads NEX-GDDP-CMIP6 data from AWS S3, applies monthly delta method against Nuka SNOTEL 1991-2020 climatology. Supports 5 GCMs and 3 SSP scenarios.",
   equations:["T_{proj}(m) = T_{nuka}(m) + \\overline{T_{gcm,fut}(m)} - \\overline{T_{gcm,hist}(m)}"],
   params:[
     {name:"Reference period",val:"1991-2020",desc:"Climatology baseline"},
     {name:"GCMs",val:"5",desc:"ACCESS-CM2, EC-Earth3, MPI-ESM1-2-HR, MRI-ESM2-0, NorESM2-MM"}
   ]},

  {name:"routing.py",path:"dixon_melt/routing.py",lines:130,category:"Physics",
   deps:["config.py"],decisions:["D-019"],
   description:"Parallel linear reservoir discharge model. Three reservoirs (fast, slow, groundwater) partition daily melt and route it through exponential recession. Converts mm/day over glacier area to m3/s discharge.",
   equations:["Q_i(t) = k_i \\cdot S_i(t)"],
   params:[
     {name:"k_fast",val:"0.3 /day",desc:"Fast reservoir recession (60% partition)"},
     {name:"k_slow",val:"0.05 /day",desc:"Slow reservoir recession (30% partition)"},
     {name:"k_gw",val:"0.01 /day",desc:"Groundwater recession (10% partition)"}
   ]},

  {name:"snowline_validation.py",path:"dixon_melt/snowline_validation.py",lines:210,category:"Validation",
   deps:["fast_model.py","config.py"],decisions:["D-021","D-022","D-028"],
   description:"Independent snowline validation against 22 years of digitized satellite snowlines. Runs model from Oct 1 to satellite date, extracts modeled snowline as zero-balance contour. Compares elevation statistics across glacier width.",
   equations:[],
   params:[
     {name:"Missing data threshold",val:"30%",desc:"Max melt-season gaps before exclusion (D-022)"},
     {name:"Snowline RMSE",val:"~90 m",desc:"Structural limitation of DETIM"}
   ]},

  {name:"behavioral_filter.py",path:"dixon_melt/behavioral_filter.py",lines:150,category:"Validation",
   deps:["fast_model.py","glacier_dynamics.py"],decisions:["D-028"],
   description:"Post-hoc behavioral filter using 6 digitized glacier outlines (2000-2025). Runs each parameter set through full historical period with glacier dynamics, checks that modeled area evolution has RMSE <= 1.0 km2 against observed areas. All 1000 filtered params from CAL-013 passed.",
   equations:[],
   params:[
     {name:"Area RMSE threshold",val:"1.0 km2",desc:"Maximum allowed area mismatch"},
     {name:"Outlines",val:"6 (2000-2025, 5yr)",desc:"Manual digitization reference"}
   ]}
];

// ── DECISIONS ───────────────────────────────────────────────────────

DATA.decisions = [
  {id:"D-001",title:"Model Selection -- DETIM Method 2 (Hock 1999)",date:"Pre-2026-03-06",
   tags:["design"],
   text:"Use Distributed Enhanced Temperature Index Model, Method 2: M = (MF + r_snow/ice * I_pot) * T, where T > 0. Balances physical realism (radiation + temperature) against data availability. Dixon Glacier lacks the full energy balance data needed for DEBAM. Method 2 adds spatially distributed potential clear-sky radiation to a basic degree-day model, capturing topographic shading and aspect effects.",
   alternatives:"Classical degree-day (Method 1): Too simple for a 40 km2 glacier with significant topographic variability (439-1637m). Full energy balance (DEBAM): Requires wind, humidity, albedo, cloud cover at grid scale -- not available.",
   why:"DETIM Method 2 occupies the sweet spot for Dixon: it captures the first-order spatial physics (topographic shading, aspect-dependent radiation) that matter on a 40 km2 glacier spanning 1200m of elevation, without requiring the meteorological inputs that simply do not exist for this remote site. The key insight from Hock (1999) is that potential clear-sky radiation, which can be computed from topography alone, correlates strongly enough with actual energy inputs that adding it to a temperature index substantially improves spatial melt patterns. For Dixon, south-facing terminus slopes receive 3-4x more radiation than north-facing headwall slopes -- a difference that a basic degree-day model would completely miss.",
   relatedDecisions:["D-004","D-012"],params:["MF","r_snow","r_ice","I_pot"]},

  {id:"D-002",title:"Climate Data Source -- Nuka SNOTEL + On-Glacier AWS",date:"Pre-2026-03-06",
   tags:["data"],
   text:"Primary forcing from Nuka SNOTEL (site 1037, 375m, ~20 km from Dixon), supplemented by on-glacier AWS at ELA site (1078m; D-023 corrected from 804m) for 2024-2025 summers. Nuka SNOTEL is the nearest long-record station with daily T and P going back to 1990.",
   alternatives:"ERA5 reanalysis (coarser, different biases), other SNOTEL stations (tested in D-024, Nuka best for precip).",
   why:"Nuka is the only station within 20km that has both temperature and precipitation records spanning the full geodetic calibration period (2000-2020). While Middle Fork Bradley proved to be a better temperature predictor for Dixon (D-024), it lacks the precipitation correlation. Using Nuka as primary forcing with multi-station gap-filling (D-025) gives the best combination of record length, proximity, and data completeness.",
   relatedDecisions:["D-013","D-024","D-025"],params:["lapse_rate","precip_corr"]},

  {id:"D-003",title:"Calibration Targets -- Stakes + Geodetic",date:"Pre-2026-03-06",
   tags:["cal"],
   text:"Multi-objective calibration against: (1) Stake mass balance at 3 elevations (ABL 804m, ELA 1078m, ACC 1293m), 2023-2025, and (2) Geodetic mass balance from Hugonnet et al. (2021), 2000-2020. Stakes provide point-scale seasonal resolution. Geodetic provides glacier-wide decadal constraint.",
   alternatives:"Stakes only (insufficient temporal constraint), geodetic only (no spatial constraint), degree-day factor literature values (not site-specific).",
   why:"The complementarity is the key: stakes tell you the model gets the elevation gradient right (ABL should melt ~5x more than ACC), while geodetic tells you the glacier-wide total is correct over 20 years. Neither alone is sufficient -- a model could match all three stakes perfectly while getting the glacier-wide balance wrong by distributing melt incorrectly across the 36,000 grid cells between stake sites.",
   relatedDecisions:["D-014","D-028"],params:["MF","precip_corr"]},

  {id:"D-004",title:"Numba JIT Compilation for Calibration Speed",date:"Pre-2026-03-06",
   tags:["design"],
   text:"Implement core simulation loop as a single Numba @njit(parallel=True) function (FastDETIM) for calibration, separate from the Pandas-based orchestrator (DETIMModel) used for analysis. Differential evolution requires ~10,000+ objective evaluations. Each evaluation runs 365-day simulations on a 578x233 grid. JIT compilation reduces per-evaluation time from seconds to ~300 ms.",
   alternatives:"Pure Python (too slow for calibration), Cython (less portable), Fortran (less maintainable), coarser grid (loses spatial resolution).",
   why:"The full DE+MCMC calibration (CAL-013) required ~250,000 model evaluations. At 300ms each, that is ~20 hours -- already a weekend-long computation. At the original Python speed of ~3 seconds per evaluation, it would have taken 200+ hours.",
   relatedDecisions:["D-009"],params:[]},

  {id:"D-005",title:"Fix SWE Double-Counting in Calibration v2",date:"2026-03-06",
   tags:["fix"],
   text:"Three fixes: (1) Annual runs: Set initial SWE = 0. (2) Summer runs: Use observed winter balance at ELA as initial SWE. (3) Remove snow_redist parameter (redundant with precip_corr). v1 calibration initialized annual runs with observed winter SWE AND accumulated snow from daily precipitation -- double-counting winter snowpack. 5 of 8 parameters hit bounds.",
   alternatives:"None -- this was a bug, not a design choice.",
   why:"When you double-count winter accumulation, the model sees roughly 2x the correct snow input. The only way the optimizer can compensate is to suppress melt (MF to minimum) and suppress additional accumulation (precip parameters to extremes). The diagnostic clue was that 5 of 8 parameters hit their bounds -- a strong signal that the model physics are fighting the data.",
   relatedDecisions:["D-006"],params:["MF","precip_corr","T0"]},

  {id:"D-006",title:"Fix Temperature Reference Elevation Mismatch",date:"2026-03-06",
   tags:["fix"],
   text:"Change model station_elev from 1230m (SNOTEL) to 804m (Dixon AWS) to match the merged climate data's actual reference elevation. [NOTE: D-023 later corrected Dixon AWS to 1078m.] Every grid cell was +2.8C too warm.",
   alternatives:"None -- this was a bug.",
   why:"A reference elevation error is invisible in the code because temperatures look reasonable -- they are just shifted. The model compensates by adjusting MF and precip_corr in ways that mask the underlying error.",
   relatedDecisions:["D-013","D-023"],params:["lapse_rate"]},

  {id:"D-007",title:"Nuka-to-Dixon Temperature Transfer Is Invalid",date:"2026-03-06",
   tags:["data"],
   text:"Replace simple lapse rate with statistical downscaling. Dixon AWS is 5.10C colder than Nuka during summer. Regression: T_dixon = 0.695 * T_nuka + (-2.650). [NOTE: D-023 showed the 703m elevation difference fully explains the offset -- NO katabatic inversion.]",
   alternatives:"Standard lapse rate (oversimplifies), ERA5 reanalysis (coarser resolution).",
   why:"This analysis was correct in identifying the temperature offset but incorrect in attributing it to katabatic cooling. The real lesson (realized after D-013 and D-023) is that careful analysis on wrong data can produce convincing but wrong conclusions.",
   relatedDecisions:["D-012","D-013","D-023"],params:["lapse_rate"]},

  {id:"D-008",title:"Elevation-Dependent Melt Factor",date:"2026-03-06",
   tags:["design"],
   text:"Add MF_grad parameter: MF(z) = MF + MF_grad * (z - z_ref). A single MF cannot capture the ABL-to-ACC mass balance gradient. MF_grad adds one parameter to capture elevation-dependent melt efficiency. Bounds: [-0.01, 0.0] mm/d/K per m.",
   alternatives:"Single MF for all elevations (too simple), separate MF per elevation band (overfitting with only 3 stakes).",
   why:"The ABL stake at 804m loses 4.5 m w.e./yr while ACC at 1293m gains 0.37 m w.e./yr. Temperature alone via the lapse rate explains most of this gradient, but the remaining mismatch requires an elevation-dependent melt efficiency. MF_grad is the minimal parameterization.",
   relatedDecisions:["D-001"],params:["MF","MF_grad"]},

  {id:"D-009",title:"Model Architecture Overhaul -- v4",date:"2026-03-06",
   tags:["design"],
   text:"Comprehensive model update: fast_model.py rewritten, config.py updated, new modules (glacier_dynamics.py, routing.py, run_projection.py). Parameter set: MF, MF_grad, r_snow, r_ice, internal_lapse, precip_grad, precip_corr, T0.",
   alternatives:"Incremental changes (slower iteration cycle).",
   why:"At this point the model had accumulated enough bug fixes and design changes that a clean rewrite was more reliable than continued patching.",
   relatedDecisions:["D-004"],params:[]},

  {id:"D-010",title:"Winter Katabatic Correction for Temperature Transfer",date:"2026-03-06",
   tags:["design"],
   text:"Apply reduced katabatic correction for Oct-Apr months. CAL-004 revealed winter temperatures too warm, causing rain instead of snow. Model accumulated only 22% of observed winter balance.",
   alternatives:"No winter correction (too warm), same summer correction for winter (too cold).",
   why:"This was an attempt to fix a real problem (insufficient winter accumulation) with the wrong solution. The real issue was the Nuka elevation error (D-013). After D-013 corrected Nuka to 375m, winter temperatures are naturally colder. Superseded by D-012 and D-013.",
   relatedDecisions:["D-012","D-013"],params:["T0"]},

  {id:"D-011",title:"Wind Redistribution of Snow (Winstral Sx)",date:"2026-03-06",
   tags:["design"],
   text:"Add spatially distributed wind redistribution using Winstral Sx. 22 years of snowlines showed western side ~100m lower. Implementation: P_cell *= (1 + k_wind * sx_norm), mass-conserving.",
   alternatives:"No wind redistribution (ignores observed spatial pattern), prescribed deposition map.",
   why:"The snowline asymmetry is one of the strongest spatial signals: 22 years of consistent E-W gradient averaging +60m. Despite this, k_wind converged to ~0 in calibration (CAL-007) because 3 stakes cannot constrain a spatial parameter. Removed from calibration (D-015) but Sx field retained.",
   relatedDecisions:["D-015","D-031"],params:["k_wind"]},

  {id:"D-012",title:"Revert to Identity Temperature Transfer",date:"2026-03-06",
   tags:["design"],
   text:"Remove statistical katabatic transfer. Use raw Nuka SNOTEL temperature at 375m with a calibrated lapse rate. Statistical transfer made ABL summer T = 2.4C, requiring MF > 19 mm/d/K. Literature MF for ice: 6-12.",
   alternatives:"Keep statistical transfer with relaxed MF bounds (physically unreasonable).",
   why:"This is a fundamental insight: DETIM was designed to use off-glacier temperature as an INDEX, not a literal physical temperature. The melt factor MF implicitly absorbs the katabatic cooling. Hock (1999) calibrated DETIM using off-glacier station data, and the resulting MF values inherently include the katabatic effect. Trying to explicitly correct removes information MF needs.",
   relatedDecisions:["D-007","D-013"],params:["MF","lapse_rate"]},

  {id:"D-013",title:"Nuka SNOTEL Elevation Units Error -- 1230 ft, Not 1230 m",date:"2026-03-09",
   tags:["fix"],
   text:"Correct Nuka SNOTEL reference elevation from 1230 m to 375 m (1230 ft * 0.3048). The NRCS website lists elevation in feet. This 855m error propagated through every calibration from CAL-001 through CAL-007. All glacier cells were positioned BELOW the reference station instead of ABOVE it.",
   alternatives:"None -- this was a data entry error.",
   why:"This is the root cause of all calibration failures from CAL-001 through CAL-007, and one of the most instructive errors in the project. With Nuka incorrectly at 1230m, every glacier cell (439-1637m) appeared to be at roughly the same elevation or below the station. The lapse rate, which should cool temperatures going up to the glacier, was instead warming them. The D-007 'katabatic paradox' (Dixon 5.1C colder despite being 'lower') was never a paradox -- Dixon at 1078m IS higher than Nuka at 375m.\n\nThe lesson: always verify station metadata against the original source (NRCS website), not secondary records. An 855m elevation error is invisible in the code because temperatures still look 'reasonable' -- but every derivative quantity (lapse correction, rain/snow partitioning, melt rate) is wrong.\n\nThe corrected geometry changes everything: ABL at 804m is 429m ABOVE Nuka at 375m, so the lapse correction now cools by 2.1C instead of warming by 2.8C. A 4.9C swing in the model's temperature field.",
   relatedDecisions:["D-006","D-007","D-012","D-023"],params:["lapse_rate","MF","precip_corr"]},

  {id:"D-014",title:"Cost Function Restructuring -- Inverse-Variance + Geodetic Hard Constraint",date:"2026-03-09",
   tags:["cal"],
   text:"Replace arbitrary-weight cost function with inverse-variance weighting and a hard geodetic constraint. Literature review shows all major glacier models treat geodetic mass balance as the PRIMARY calibration constraint.",
   alternatives:"Equal weighting (ignores measurement precision), geodetic-only (loses spatial information).",
   why:"Inverse-variance weighting is the statistically principled approach: observations with smaller uncertainty carry more weight. The geodetic mass balance (-0.939 +/- 0.122 m w.e./yr) constrains the 20-year glacier-wide average to within ~12%. The hard penalty (lambda=50) prevents physically impossible solutions.",
   relatedDecisions:["D-003","D-016"],params:[]},

  {id:"D-015",title:"Remove Lapse Rate and k_wind from Calibration",date:"2026-03-09",
   tags:["cal"],
   text:"Fix lapse rate at -5.0 C/km and remove k_wind, reducing free parameters from 9 to 7. The optimizer consistently exploits lapse rate to compensate for other deficiencies. Literature: -4.5 to -5.5 C/km for maritime glaciers.",
   alternatives:"Keep lapse rate free with tight bounds (still equifinal), fix at -6.5 (too steep for maritime glacier).",
   why:"The equifinality between lapse rate and precipitation correction is the most dangerous parameter trade-off. In CAL-009, the optimizer found lapse_rate = -6.83 C/km with precip_corr = 1.20 -- fits current observations but has compensating errors. A steeper lapse means more warming at low elevations (more melt) and more cooling at high elevations (more accumulation), which the low precip_corr compensates. Under future warming, these errors DIVERGE.\n\nThe sensitivity analysis (D-029) quantified the stakes: lapse rate sensitivity is ~10x larger than r_ice/r_snow ratio. Geodetic bias swings 1.9 m w.e./yr across the -4.0 to -6.5 C/km range. The -5.0 choice sits near the minimum geodetic bias.",
   relatedDecisions:["D-017","D-029","D-030"],params:["lapse_rate","k_wind"]},

  {id:"D-016",title:"Use Only 2000-2020 Geodetic Mean + Widen precip_corr",date:"2026-03-09",
   tags:["cal"],
   text:"Revert to single 2000-2020 geodetic constraint. CAL-008 revealed sub-periods create contradictory constraint: Nuka shows cooler summers 2001-2010 but Hugonnet shows MORE mass loss. Statistical test: sub-periods NOT distinguishable (Z=0.88, p>0.30).",
   alternatives:"Keep both sub-periods with relaxed weighting, dynamic precipitation correction.",
   why:"The contradiction reveals a limitation: the off-glacier station does not perfectly represent on-glacier conditions decade by decade. The 2000-2020 mean integrates over discrepancies, providing a robust constraint.",
   relatedDecisions:["D-014"],params:["precip_corr"]},

  {id:"D-017",title:"Bayesian Ensemble Calibration (DE + MCMC)",date:"2026-03-09",
   tags:["cal"],
   text:"Replace single-optimum with two-phase Bayesian ensemble: differential evolution for MAP, then MCMC (emcee) for posterior sampling. 24 walkers, 10,000 steps, burn-in 2000. 6 free parameters: MF, MF_grad, r_snow, precip_grad, precip_corr, T0. Fixed: lapse=-5.0, r_ice=2.0*r_snow, k_wind=0.",
   alternatives:"Single DE optimum (no uncertainty), grid search (too expensive in 6D), DREAM (more complex).",
   why:"For projections, a single 'best' parameter set is scientifically insufficient. CAL-009 demonstrated equifinality: multiple combinations fit current observations equally well but diverge under warming. A single optimum gives false precision.\n\nThe r_ice/r_snow ratio was fixed at 2.0 because CAL-009 converged to near-equality (1.29 vs 1.34), eliminating the albedo feedback. When r_ice ~ r_snow, the transition from snow-covered to bare ice produces no melt rate change -- destroying a physical feedback critical for projections.\n\nThe MCMC posterior from CAL-013 produced 1,656 independent samples with acceptance 0.368, confirming good convergence. All 5 DE seeds found the same mode -- unimodal posterior.",
   relatedDecisions:["D-015","D-027","D-028"],params:["MF","MF_grad","r_snow","precip_grad","precip_corr","T0"]},

  {id:"D-018",title:"Glacier Dynamics Overhaul -- Correct Delta-h + Ice Thickness",date:"2026-03-10",
   tags:["fix","design"],
   text:"Complete rewrite of glacier_dynamics.py to fix three compounding bugs: (1) Wrong size class for a 40 km2 glacier. (2) Wrong h_r convention -- maximum thinning at headwall instead of terminus. (3) No ice thickness tracking -- cells with zero ice never removed.",
   alternatives:"None -- these were bugs.",
   why:"The three bugs compounded to produce qualitatively wrong retreat: the glacier was thinning most at the headwall instead of the terminus, and cells with zero ice were still treated as glacier. The corrected implementation produces physically realistic terminus-first retreat.",
   relatedDecisions:["D-019"],params:[]},

  {id:"D-019",title:"CMIP6 Projection Pipeline with Discharge Routing",date:"2026-03-10",
   tags:["proj"],
   text:"Real CMIP6 projections from NASA NEX-GDDP-CMIP6 (0.25 degree, daily, bias-corrected). 5 GCMs, 3 SSPs. Bias correction: monthly delta method against 1991-2020 climatology. Discharge routing for peak water analysis.",
   alternatives:"Linear delta method (no interannual variability), single GCM (no climate uncertainty).",
   why:"The 5-GCM ensemble captures structural uncertainty in how warming translates to local conditions. The selection follows Rounce et al. (2023).",
   relatedDecisions:["D-020"],params:[]},

  {id:"D-020",title:"Posterior Ensemble Projections (Top 250 Parameter Sets)",date:"2026-03-11",
   tags:["proj"],
   text:"Ensemble using top 250 MCMC parameter sets (following Geck 2020). Each (GCM, param_set) pair runs independently. Total: 250 x 5 = 1,250 runs per scenario. Aggregated with percentiles (p05, p25, p50, p75, p95).",
   alternatives:"Single MAP parameter set (no parameter uncertainty), full posterior (too expensive).",
   why:"Using top 250 by log-probability ensures the projection ensemble is weighted toward parameter sets that best fit observations. Parameter uncertainty is relatively small compared to GCM spread but still meaningful for peak water timing.",
   relatedDecisions:["D-017"],params:[]},

  {id:"D-021",title:"Snowline Validation (Independent Spatial Check)",date:"2026-03-11",
   tags:["val"],
   text:"Independent validation against 22 years of digitized snowlines never used in calibration. For each year, run model to satellite date, extract modeled snowline. Results: bias +6m, RMSE 189m, MAE 122m, r=0.52. Persistent +100-175m bias in recent years (2017-2024).",
   alternatives:"Snowline as calibration target (done later in D-028), AAR validation.",
   why:"Snowlines are the most spatially informative validation dataset: they map the equilibrium line across the entire glacier width. The persistent positive bias in recent years motivated D-028.",
   relatedDecisions:["D-028"],params:[]},

  {id:"D-022",title:"Exclude Snowline Years with Insufficient SNOTEL Data",date:"2026-03-11",
   tags:["data"],
   text:"Exclude years where >30% of melt-season temperature data is missing. WY2000 (37%) and WY2005 (86%, 132 of 153 days) showed extreme negative snowline bias (-600 to -660m). Root cause: validation code replaced NaN with 0C, eliminating all melt.",
   alternatives:"Climatological gap-filling, hardcoded exclusion list.",
   why:"The 30% threshold catches years where missing summer temperature data fundamentally compromises the melt calculation, while retaining years like WY2003 (21% missing, mostly late September) that validate well.",
   relatedDecisions:["D-025"],params:[]},

  {id:"D-023",title:"Correct Dixon AWS Elevation from 804m to 1078m",date:"2026-03-12",
   tags:["fix"],
   text:"The Dixon AWS was recorded at 804m (ABL stake) but was actually at the ELA site (1078m). Evidence: temperature comparison with Nuka (375m) shows -4.6C offset, matching 1078m at -6.5 C/km. At 804m, offset would be only -2.8C.",
   alternatives:"None -- this was a metadata error.",
   why:"This is the second elevation metadata error (after D-013). The 274m error matters for any analysis using Dixon AWS as a reference. The corrected elevation reveals the 'exotic' katabatic effect is only ~1C, consistent with literature for maritime glaciers.\n\nThe pattern is the same as D-013: a number was recorded without verifying the original source. Two independent elevation errors, both caught by comparing model predictions against physical expectations, both producing cascading effects throughout the analysis.",
   relatedDecisions:["D-006","D-013"],params:["lapse_rate"]},

  {id:"D-024",title:"Multi-Station Climate Analysis -- Dixon AWS as Ground Truth",date:"2026-03-12",
   tags:["data"],
   text:"Evaluate all nearby SNOTEL stations against Dixon AWS (1078m). Key finding: Middle Fork Bradley is the best single T predictor (r=0.877, RMSE=4.8C). All transfer slopes 0.3-0.8. August hardest to predict (peak glacier-surface decoupling). Nuka best for precip (r=0.75).",
   alternatives:"Use Nuka for everything, use only stations with overlap.",
   why:"Reframing the analysis around Dixon AWS as ground truth was essential: comparing stations to each other tells you about regional coherence, but comparing them to Dixon tells you which best predicts on-glacier conditions.",
   relatedDecisions:["D-002","D-025"],params:[]},

  {id:"D-025",title:"Multi-Station Climate Gap-Filling Pipeline",date:"2026-03-12",
   tags:["data"],
   text:"Replace ffill().fillna(0) with 5-station cascade. Temperature: Nuka -> MFB -> McNeil -> Anchor -> Kach -> LKC -> interp -> climatology. Results: 91.3% Nuka, 6.0% MFB, 1.8% McNeil. WY2005 Jun-Aug mean T: 8.5C (was ~0C). WY2020 total precip: 2307mm (was ~1176mm).",
   alternatives:"ERA5 reanalysis, single-station MFB only, Dixon AWS for forcing.",
   why:"The original ffill().fillna(0) was the single worst data processing choice in the project. Forward-filling works for 1-2 day gaps, but multi-month gaps in summer (WY2005: 132 days) propagated the last valid spring temperature into August, and fillna(0) set the rest to 0C. This killed all melt in those years, forcing the model to overcompensate with extreme MF values.\n\nThe cascade approach uses each station's monthly regression against Nuka, filling in priority order of temperature prediction skill. The result is a zero-NaN dataset that preserves real interannual variability even during gap periods.",
   relatedDecisions:["D-022","D-024","D-026"],params:["precip_corr"]},

  {id:"D-026",title:"Recalibrate with Gap-Filled Climate (CAL-011)",date:"2026-03-12",
   tags:["cal"],
   text:"Re-run calibration with gap-filled climate data from D-025. CAL-011 killed at DE step 28/200 -- superseded by multi-seed approach (D-027).",
   alternatives:"Adjust bounds/priors, free lapse rate.",
   why:"After fixing the climate data (D-025), recalibration was mandatory -- every parameter value from CAL-010 was contaminated by the bad gap handling.",
   relatedDecisions:["D-025","D-027"],params:[]},

  {id:"D-027",title:"Multi-Seed Calibration for Posterior Multimodality (CAL-012)",date:"2026-03-12",
   tags:["cal"],
   text:"Replace single-seed DE with 5 seeds [42, 123, 456, 789, 2024] + per-mode MCMC. Clustering with 10% Chebyshev threshold. Result: all 5 seeds converged to one mode -- unimodal posterior confirmed.",
   alternatives:"Single seed (might miss modes), more seeds (diminishing returns), parallel tempering.",
   why:"The multi-seed approach is cheap insurance against multimodality. Each seed costs ~50 minutes. For CAL-012/013, all 5 seeds converged to costs within 0.003 (5.343-5.345), confirming the posterior is well-identified.",
   relatedDecisions:["D-017","D-028"],params:[]},

  {id:"D-028",title:"Multi-Objective Calibration with Snowline in MCMC Likelihood",date:"2026-03-18",
   tags:["cal"],
   text:"Add snowline elevation as chi-squared term in MCMC log-likelihood (sigma=75m). Pipeline: multi-seed DE -> MCMC with snowlines -> combine posteriors -> area filter (top 1000, RMSE <= 1.0 km2). All 1000 passed.",
   alternatives:"Post-hoc snowline filter (rejected: no discriminating power), composite scoring, re-enable k_wind.",
   why:"This addresses the most important methodological finding: post-hoc snowline filtering has zero discriminating power within the stakes+geodetic posterior.\n\nInitial testing showed ALL 1000 parameter sets scored snowline RMSE between 88 and 96m -- a range of only 8m with std 1.6m. Snowline RMSE was uncorrelated with log-probability (r=0.146). The stakes+geodetic calibration produces a posterior completely agnostic about snowline fit.\n\nBy putting snowlines IN the likelihood, the MCMC sampler explores parameter space differently: it rewards combinations that simultaneously satisfy all three constraints. The sigma=75m combines spatial spread (~50-80m), model resolution (100m), and temporal mismatch.\n\nThe structural snowline limitations are documented and accepted: DETIM produces near-contour-line snowlines (spatial std 6-22m vs observed 24-69m) and over-amplifies interannual variability (std 129m vs observed 63m). These are inherent DETIM limitations, not parameter-tunable.\n\nThe area filter passed 100% of samples, confirming that the three-constraint likelihood produces a posterior that is also behavioral with respect to area.",
   relatedDecisions:["D-021","D-027","D-031"],params:["MF","precip_corr","r_snow"]},

  {id:"D-029",title:"Validation Suite (Sub-period Geodetic, Stake Check, Sensitivity)",date:"2026-04-08",
   tags:["val"],
   text:"Three independent validation analyses: (1) Sub-period geodetic: model reverses the trend. (2) Stake predictive: RMSE 1.20 m w.e., ELA biased -1.4 m w.e. (3) Sensitivity: lapse rate dominates (1.9 m w.e./yr swing), r_ice/r_snow ratio has 10x less sensitivity.",
   alternatives:"Cross-validation (too expensive), leave-one-out, bootstrapping.",
   why:"Validation is about honesty, not marketing. The sub-period geodetic result reveals a limitation of gap-filled climate data. The ELA stake bias reveals spatial representativity issues (D-031). The sensitivity analysis motivates D-030.",
   relatedDecisions:["D-015","D-030","D-031"],params:["lapse_rate"]},

  {id:"D-030",title:"Lapse Rate Sensitivity Projections",date:"2026-04-08",
   tags:["proj"],
   text:"Projections at three lapse rates (-4.5, -5.0, -5.5 C/km) to bracket structural uncertainty. Same v13 posterior, all 5 GCMs, 3 SSPs. 2100 area ranges from 5.4 km2 (-4.5, SSP5-8.5) to 31.7 km2 (-5.5, SSP1-2.6). Lapse rate choice shifts area by ~9 km2.",
   alternatives:"Recalibrate at each lapse rate, full posterior at each rate.",
   why:"Running at the lapse rate endpoints brackets the 'known unknown' without re-opening equifinality. The 9 km2 spread across lapse rates is comparable to the spread across SSP scenarios, meaning lapse rate uncertainty is as important as emission scenario uncertainty for Dixon's future.",
   relatedDecisions:["D-015","D-029"],params:["lapse_rate"]},

  {id:"D-031",title:"ELA Stake Bias -- Wind Redistribution Representativity",date:"2026-04-09",
   tags:["val"],
   text:"Accept the persistent -1.4 m w.e. bias at ELA stake (1078m). Model predicts -1.3 m w.e. as the average across 814 cells at that elevation band. The ELA stake sits in a wind-loaded zone on the southern branch; 70% of glacier cells are sheltered.",
   alternatives:"Increase ELA uncertainty and recalibrate, re-enable k_wind, exclude ELA from calibration.",
   why:"This encapsulates a core tension in glacier modeling: point measurements are not area averages. The ELA stake records +0.1 m w.e./yr because it receives extra wind-loaded snow. The model's -1.3 m w.e./yr is the AVERAGE across all cells in that band, including both sheltered and exposed zones.\n\nRecalibration would not help: forcing the model to match +0.1 at ELA would require over-accumulating at ALL cells, breaking geodetic and ABL/ACC fits. The wind redistribution parameter (k_wind) cannot be constrained by 3 stakes.\n\nWY2024 shows a separate issue: Nuka recorded similar winter precip to WY2023, but observed winter balance was dramatically higher (ABL: 0.85 -> 1.93, +127%), indicating a local accumulation event the off-glacier station missed entirely.",
   relatedDecisions:["D-011","D-028","D-029"],params:["k_wind"]}
];

// ── EQUATIONS ────────────────────────────────────────────────────────

DATA.equations = [
  {title:"DETIM Melt Equation (Hock 1999, Method 2)",
   latex:"M = \\begin{cases} (MF + r_{snow/ice} \\cdot I_{pot}) \\cdot T & \\text{if } T > 0 \\\\ 0 & \\text{if } T \\leq 0 \\end{cases}",
   explain:"The core equation. Melt M (mm/day) at each grid cell equals the sum of a base melt factor MF and a radiation-dependent term (r times potential clear-sky solar radiation I_pot), multiplied by air temperature T. The radiation factor r differs between snow (r_snow) and ice (r_ice), capturing the albedo feedback.\n\nThe temperature T is an INDEX, not the literal on-glacier temperature. The measured katabatic cooling at Dixon (~3C at ABL) is implicitly absorbed by MF.",
   variables:[
     {sym:"M",unit:"mm/day",val:"0-30",desc:"Daily melt rate"},
     {sym:"MF",unit:"mm d-1 K-1",val:"7.11",desc:"Melt factor (MAP)"},
     {sym:"r_{snow}",unit:"mm m2 W-1 d-1 K-1",val:"0.00196",desc:"Snow radiation factor"},
     {sym:"r_{ice}",unit:"mm m2 W-1 d-1 K-1",val:"0.00392",desc:"Ice radiation factor"},
     {sym:"I_{pot}",unit:"W/m2",val:"50-350",desc:"Potential clear-sky direct solar radiation"},
     {sym:"T",unit:"C",val:"-10 to 15",desc:"Air temperature (index)"}
   ],
   example:"ABL on a July day (T_nuka = 12C, I_pot = 280 W/m2):\nT_ABL = 12 + (-5.0)*(804-375)/1000 = 12 - 2.15 = 9.85C\nSurface = ice (bare in July)\nMF_eff = 7.11 + (-0.00411)*(804-375) = 7.11 - 1.76 = 5.35\nM = (5.35 + 0.00392*280) * 9.85\nM = (5.35 + 1.10) * 9.85 = 63.5 mm/day\n\nACC on the same day:\nT_ACC = 12 + (-5.0)*(1293-375)/1000 = 12 - 4.59 = 7.41C\nSurface = snow\nMF_eff = 7.11 + (-0.00411)*(1293-375) = 7.11 - 3.77 = 3.34\nM = (3.34 + 0.00196*280) * 7.41 = (3.34 + 0.55) * 7.41 = 28.8 mm/day",
   codeRef:"dixon_melt/fast_model.py",
   tryIt:{params:["T_nuka","I_pot","elev","surface"],defaults:[12,280,804,"ice"]}},

  {title:"Elevation-Dependent Melt Factor",
   latex:"MF_{eff}(z) = MF + MF_{grad} \\cdot (z - z_{ref})",
   explain:"The effective melt factor decreases with elevation. MF_grad is negative, so higher cells melt less per degree. This captures integrated effects of lower albedo, less longwave absorption, and cooler microclimate at higher elevations.\n\nWith MAP values: MF_eff at ABL (804m) = 7.11 + (-0.00411)*(804-375) = 5.35 mm/d/K. At ACC (1293m) = 7.11 + (-0.00411)*(1293-375) = 3.34 mm/d/K. The 38% reduction from ABL to ACC means ACC needs 1.6x more degree-days to melt the same amount.",
   variables:[
     {sym:"MF",unit:"mm d-1 K-1",val:"7.11",desc:"Base melt factor at reference elevation"},
     {sym:"MF_{grad}",unit:"mm d-1 K-1 m-1",val:"-0.00411",desc:"Melt factor elevation gradient"},
     {sym:"z_{ref}",unit:"m",val:"375",desc:"Nuka SNOTEL reference elevation"}
   ],
   example:"At ABL (804m): MF_eff = 7.11 + (-0.00411)*(804-375) = 7.11 - 1.76 = 5.35\nAt ELA (1078m): MF_eff = 7.11 + (-0.00411)*(1078-375) = 7.11 - 2.89 = 4.22\nAt ACC (1293m): MF_eff = 7.11 + (-0.00411)*(1293-375) = 7.11 - 3.77 = 3.34",
   codeRef:"dixon_melt/fast_model.py"},

  {title:"Temperature Distribution",
   latex:"T_{cell} = T_{nuka} + \\lambda \\cdot (z_{cell} - z_{ref})",
   explain:"Temperature at each grid cell is derived from Nuka SNOTEL using a fixed lapse rate. With lambda = -5.0 C/km and z_ref = 375m (Nuka), every 100m of elevation cools the temperature by 0.5C. The terminus at 439m is only 64m above Nuka, while the headwall at 1637m is 1262m above -- a 6.3C temperature range across the glacier.",
   variables:[
     {sym:"T_{nuka}",unit:"C",val:"-20 to 20",desc:"Nuka SNOTEL daily temperature"},
     {sym:"\\lambda",unit:"C/km",val:"-5.0",desc:"Fixed lapse rate (D-015)"},
     {sym:"z_{cell}",unit:"m",val:"439-1637",desc:"Grid cell elevation"},
     {sym:"z_{ref}",unit:"m",val:"375",desc:"Reference station elevation"}
   ],
   example:"Summer day, T_nuka = 10.0C:\nTerminus (439m): 10.0 + (-5.0)*(439-375)/1000 = 10.0 - 0.32 = 9.68C (melting)\nMidglacier (1000m): 10.0 + (-5.0)*(1000-375)/1000 = 10.0 - 3.13 = 6.87C (melting)\nHeadwall (1637m): 10.0 + (-5.0)*(1637-375)/1000 = 10.0 - 6.31 = 3.69C (melting)\n\nWinter day, T_nuka = -2.0C:\nTerminus (439m): -2.0 - 0.32 = -2.32C (no melt)\nHeadwall (1637m): -2.0 - 6.31 = -8.31C (no melt)",
   codeRef:"dixon_melt/fast_model.py"},

  {title:"Precipitation Distribution",
   latex:"P_{cell} = P_{nuka} \\cdot c_p \\cdot (1 + p_g \\cdot (z_{cell} - z_{ref}))",
   explain:"Precipitation increases with elevation (orographic enhancement) and is scaled by a bulk correction factor. The elevation gradient p_g adds ~7% per 100m. The correction factor c_p compensates for SNOTEL undercatch and spatial difference between Nuka and Dixon.\n\nRain/snow partitioning uses T0 with a 2-degree linear transition: 100% snow below T0-1, 100% rain above T0+1.",
   variables:[
     {sym:"P_{nuka}",unit:"mm/day",val:"0-60",desc:"Nuka SNOTEL daily precipitation"},
     {sym:"c_p",unit:"-",val:"1.621",desc:"Bulk precipitation correction"},
     {sym:"p_g",unit:"1/m",val:"0.000694",desc:"Precipitation elevation gradient"}
   ],
   example:"Storm day: P_nuka = 20mm, T_nuka = 2C\nAt ABL (804m): P = 20*1.621*(1+0.000694*(804-375)) = 32.42*(1+0.298) = 42.1mm\n  T_ABL = 2 + (-5)*(429/1000) = -0.15C -> ~52% snow (T0~0, transition zone)\nAt ACC (1293m): P = 20*1.621*(1+0.000694*(1293-375)) = 32.42*(1+0.637) = 53.1mm\n  T_ACC = 2 + (-5)*(918/1000) = -2.59C -> 100% snow",
   codeRef:"dixon_melt/fast_model.py"},

  {title:"Log-Likelihood (MCMC)",
   latex:"\\ln \\mathcal{L} = -\\frac{1}{2} \\sum_i \\left(\\frac{y_i - \\hat{y}_i}{\\sigma_i}\\right)^2 - \\lambda \\cdot \\max(0, |\\bar{B}_{geo} - \\hat{B}_{geo}| - \\sigma_{geo})",
   explain:"The MCMC likelihood combines three data streams: stake mass balance observations (inverse-variance weighted), geodetic mass balance with hard penalty, and snowline elevations (added in D-028). The penalty term activates only when the geodetic residual exceeds its reported uncertainty.\n\nFor CAL-013: 25 stake observations (2023-2025), 1 geodetic constraint (2000-2020), and ~20 snowline elevation comparisons.",
   variables:[
     {sym:"y_i / \\hat{y}_i",unit:"m w.e.",val:"varies",desc:"Observed / modeled mass balance"},
     {sym:"\\sigma_i",unit:"m w.e.",val:"0.10-0.15",desc:"Stake observation uncertainty"},
     {sym:"\\bar{B}_{geo}",unit:"m w.e./yr",val:"-0.939",desc:"Geodetic balance"},
     {sym:"\\sigma_{geo}",unit:"m w.e./yr",val:"0.122",desc:"Geodetic uncertainty"},
     {sym:"z_j / \\sigma_{sl}",unit:"m",val:"984-1238 / 75",desc:"Snowline elevation / uncertainty"}
   ],
   example:"MAP params, WY2023:\nABL annual: chi2 = (-0.38/0.12)^2 = 10.0\nGeodetic: chi2 = (0.122/0.122)^2 = 1.0\nSnowline 2023: chi2 = (30/75)^2 = 0.16\nTotal ln(L) = -0.5*(10.0+1.0+0.16) = -5.58",
   codeRef:"run_calibration_v13.py; dixon_melt/calibration.py"},

  {title:"Volume-Area Scaling",
   latex:"V = c \\cdot A^{\\gamma}, \\quad c = 0.0340, \\quad \\gamma = 1.36",
   explain:"Relates glacier volume (km3) to area (km2). Used for ice thickness initialization and to convert projected area loss to volume loss. From Bahr et al. (1997), calibrated globally.\n\nFor Dixon at 40.1 km2: V = 0.034 * 40.1^1.36 = 4.62 km3. This gives a mean ice thickness of V/A = 115m.",
   variables:[
     {sym:"V",unit:"km3",val:"4.62",desc:"Glacier volume"},
     {sym:"A",unit:"km2",val:"40.1",desc:"Glacier area"},
     {sym:"c",unit:"km3-2gamma",val:"0.0340",desc:"VA coefficient"},
     {sym:"\\gamma",unit:"-",val:"1.36",desc:"VA exponent"}
   ],
   example:"Current (2025): A=38.34 -> V = 0.034*38.34^1.36 = 4.30 km3\nSSP2-4.5 at 2100: A=19.6 -> V = 0.034*19.6^1.36 = 1.75 km3\nSSP5-8.5 at 2100: A=10.5 -> V = 0.034*10.5^1.36 = 0.72 km3\nVolume loss SSP2-4.5: 4.30-1.75 = 2.55 km3 = 2.55 Gt water",
   codeRef:"dixon_melt/glacier_dynamics.py"},

  {title:"Linear Reservoir Discharge",
   latex:"Q_i(t) = k_i \\cdot S_i(t), \\quad S_i(t+1) = S_i(t) + f_i \\cdot R(t) - Q_i(t)",
   explain:"Three parallel linear reservoirs partition daily melt and route it through exponential recession. Fast reservoir (k=0.3/day, 60%) captures direct runoff. Slow reservoir (k=0.05/day, 30%) represents firn and subglacial drainage. Groundwater (k=0.01/day, 10%) smooths the baseflow.",
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
   explain:"Monthly regression predicting Nuka-equivalent temperature from other stations. Separate slope/intercept for each month, computed from overlapping valid days. The cascade fills gaps in priority order: MFB, McNeil, Anchor, Kachemak, Lower Kachemak.",
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
  rows.forEach(function(row, ri) {
    var r = el('tr');
    row.forEach(function(cell, i) {
      var td = el('td', {textContent: String(cell)});
      if (opts.mono && opts.mono.indexOf(i) >= 0) td.style.fontFamily = "'Fira Code', monospace";
      if (opts.onClick && opts.onClick[i]) {
        td.style.color = '#6c8cff';
        td.style.cursor = 'pointer';
        td.addEventListener('click', function() { opts.onClick[i](ri); });
      }
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

  // Thesis figures: glacier map + outline retreat
  if (typeof FIGURES !== 'undefined') {
    v.appendChild(el('h2', {textContent: 'Study Site'}));
    v.appendChild(makeFigGrid([
      ['fig_09', 'Fig 9: Glacier Map -- Dixon Glacier, Kenai Peninsula'],
      ['fig_10', 'Fig 10: Outline Retreat (2000-2025)']
    ]));
  }

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
    '  Stake obs (25 rows) ------>  [calibration.py]  <---- model output',
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
    '  [behavioral_filter.py]     6 digitized outlines (2000-2025)'
  ].join('\n');

  v.appendChild(el('h2', {textContent: 'Data Flow Diagram'}));
  v.appendChild(el('p', {textContent: 'Click any [module.py] link to open its detail panel.', style:{color:'#a0a4b8',marginBottom:'12px'}}));

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
  v.appendChild(el('h2', {textContent: 'Module Inventory (' + DATA.modules.length + ' modules)'}));
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

  if (mod.equations && mod.equations.length > 0 && mod.equations[0] !== 'All constants: see parameter table') {
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

var dataSubTabs = ['Climate','Stakes','Geodetic','Snowlines','Area','Calibration','Projections','Sensitivity','Charts'];

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
      if (i === 8) setTimeout(renderAllCharts, 50);
    });
    tabContainer.appendChild(tab);
  });
  v.appendChild(tabContainer);

  // 0: Climate
  var p0 = el('div', {className: 'data-panel active', id: 'data-panel-0'});
  p0.appendChild(el('h2', {textContent: 'Climate Forcing (Nuka SNOTEL, Gap-Filled)'}));
  p0.appendChild(el('p', {textContent: 'Water years 1999-2025. Annual mean T, summer (Jun-Sep) mean T, total precipitation. Source: dixon_gap_filled_climate.csv', style:{color:'#a0a4b8',marginBottom:'12px'}}));
  if (typeof FIGURES !== 'undefined') {
    p0.appendChild(makeFigGrid([
      ['fig_11', 'Fig 11: Climate Forcing'],
      ['fig_12', 'Fig 12: Model Response']
    ]));
  }
  p0.appendChild(el('div', {id: 'chart-temp-annual', style: {height:'350px',marginBottom:'24px'}}));
  p0.appendChild(el('div', {id: 'chart-precip-annual', style: {height:'350px',marginBottom:'24px'}}));
  p0.appendChild(el('div', {id: 'chart-climatology', style: {height:'400px',marginBottom:'24px'}}));
  p0.appendChild(makeTable(['Water Year','Ann Mean T (C)','Summer T (C)','Total P (mm)'],
    DATA.climate.annual.map(function(c){return[c.wy,c.T_ann.toFixed(2),c.T_sum.toFixed(2),c.P_ann.toFixed(0)];}),{mono:[1,2,3]}));
  v.appendChild(p0);

  // 1: Stakes
  var p1 = el('div', {className: 'data-panel', id: 'data-panel-1'});
  p1.appendChild(el('h2', {textContent: 'Stake Mass Balance Observations (25 rows)'}));
  p1.appendChild(el('p', {textContent: '3 sites (ABL 804m, ELA 1078m, ACC 1293m), WY2023-2025.', style:{color:'#a0a4b8',marginBottom:'12px'}}));
  if (typeof FIGURES !== 'undefined') {
    p1.appendChild(makeFigGrid([['fig_02', 'Fig 2: Stake Fit (Obs vs Modeled)']]));
  }
  p1.appendChild(el('div', {id: 'chart-stakes', style: {height:'400px',marginBottom:'24px'}}));
  p1.appendChild(makeTable(['Site','Period','Year','Start','End','MB (m w.e.)','Unc','Elev'],
    DATA.stakes.map(function(s){return[s.site,s.period,s.year,s.start,s.end,s.mb.toFixed(2),s.unc.toFixed(2),s.elev];}),{mono:[5,6]}));
  v.appendChild(p1);

  // 2: Geodetic
  var p2 = el('div', {className: 'data-panel', id: 'data-panel-2'});
  p2.appendChild(el('h2', {textContent: 'Geodetic Mass Balance (Hugonnet et al. 2021)'}));
  if (typeof FIGURES !== 'undefined') {
    p2.appendChild(makeFigGrid([['fig_03', 'Fig 3: Geodetic Validation']]));
  }
  p2.appendChild(makeTable(['Period','Area (km2)','dh/dt','err','dm/dt/da','err'],
    DATA.geodetic.map(function(g){return[g.period,(g.area_m2/1e6).toFixed(2),g.dhdt.toFixed(3),g.err.toFixed(3),g.dmdtda.toFixed(3),g.err_dm.toFixed(3)];}),{mono:[2,3,4,5]}));
  v.appendChild(p2);

  // 3: Snowlines
  var p3 = el('div', {className: 'data-panel', id: 'data-panel-3'});
  p3.appendChild(el('h2', {textContent: 'Digitized Snowline Observations (22 years)'}));
  if (typeof FIGURES !== 'undefined') {
    p3.appendChild(makeFigGrid([['fig_13', 'Fig 13: Snowline Validation (Obs vs Modeled)']]));
  }
  p3.appendChild(el('div', {id: 'chart-snowlines', style: {height:'400px',marginBottom:'24px'}}));
  p3.appendChild(makeTable(['Year','Date','Source','Mean (m)','Median','Std','Min','Max','N'],
    DATA.snowlines.map(function(s){return[s.year,s.date,s.source,s.mean.toFixed(1),s.median.toFixed(1),s.std.toFixed(1),s.min.toFixed(1),s.max.toFixed(1),s.n];}),{mono:[3,4,5,6,7]}));
  v.appendChild(p3);

  // 4: Area
  var p4 = el('div', {className: 'data-panel', id: 'data-panel-4'});
  p4.appendChild(el('h2', {textContent: 'Glacier Area Evolution (6 Outlines)'}));
  p4.appendChild(el('p', {textContent: 'Manual digitization, 5-year intervals. Total retreat: 1.77 km2 (4.4%).', style:{color:'#a0a4b8',marginBottom:'12px'}}));
  p4.appendChild(el('div', {id: 'chart-area', style: {height:'350px',marginBottom:'24px'}}));
  p4.appendChild(makeTable(['Year','Area (km2)','Loss (km2)','Source'],
    DATA.areas.map(function(a){return[a.year,a.area.toFixed(2),(40.11-a.area).toFixed(2),a.source];}),{mono:[1,2]}));
  v.appendChild(p4);

  // 5: Calibration (posterior)
  var p5 = el('div', {className: 'data-panel', id: 'data-panel-5'});
  p5.appendChild(el('h2', {textContent: 'Posterior Parameter Distributions (CAL-013)'}));
  p5.appendChild(el('p', {textContent: 'Top 250 parameter sets from v13 MCMC posterior. Histograms show marginal distributions.', style:{color:'#a0a4b8',marginBottom:'12px'}}));
  if (typeof FIGURES !== 'undefined') {
    p5.appendChild(makeFigGrid([['fig_01', 'Fig 1: Full Parameter Posterior (Corner Plot)']]));
  }
  var posteriorParams = ['MF','MF_grad','r_snow','precip_corr','precip_grad','T0'];
  posteriorParams.forEach(function(param) {
    p5.appendChild(el('div', {id: 'chart-post-' + param, style: {height:'250px',marginBottom:'12px'}}));
  });
  v.appendChild(p5);

  // 6: Projections
  var p6 = el('div', {className: 'data-panel', id: 'data-panel-6'});
  p6.appendChild(el('h2', {textContent: 'Projection Envelopes (2005-2100)'}));
  p6.appendChild(el('p', {textContent: '250 params x 5 GCMs = 1,250 runs per scenario. Shaded bands: 5th-95th percentile. SSP1-2.6 (green), SSP2-4.5 (amber), SSP5-8.5 (red).', style:{color:'#a0a4b8',marginBottom:'12px'}}));
  if (typeof FIGURES !== 'undefined') {
    p6.appendChild(makeFigGrid([
      ['fig_07', 'Fig 7: Projection Ensemble (3 SSPs)'],
      ['fig_08', 'Fig 8: Lapse Sensitivity Bracket'],
      ['fig_05', 'Fig 5: Historical Mass Balance'],
      ['fig_06', 'Fig 6: Mass Balance Trends']
    ]));
  }
  p6.appendChild(el('div', {id: 'chart-projections', style: {height:'450px',marginBottom:'24px'}}));
  p6.appendChild(el('div', {id: 'chart-lapse-proj', style: {height:'400px',marginBottom:'24px'}}));
  v.appendChild(p6);

  // 7: Sensitivity
  var p7 = el('div', {className: 'data-panel', id: 'data-panel-7'});
  p7.appendChild(el('h2', {textContent: 'Fixed Parameter Sensitivity (D-029)'}));
  p7.appendChild(el('p', {textContent: 'Lapse rate sensitivity is ~10x larger than r_ice/r_snow ratio.', style:{color:'#a0a4b8',marginBottom:'12px'}}));
  p7.appendChild(el('div', {id: 'chart-sensitivity', style: {height:'350px',marginBottom:'24px'}}));
  p7.appendChild(makeTable(['Parameter','Value','Geod Mod','Bias','Stake RMSE'],
    DATA.sensitivity.map(function(s){return[s.param,s.value.toFixed(2),s.geod_mod.toFixed(3),s.bias.toFixed(3),s.stake_rmse.toFixed(3)];}),{mono:[1,2,3,4]}));
  v.appendChild(p7);

  // 8: Charts (renders on tab click)
  var p8 = el('div', {className: 'data-panel', id: 'data-panel-8'});
  p8.appendChild(el('h2', {textContent: 'All Interactive Charts'}));
  p8.appendChild(el('p', {textContent: 'All Plotly charts rendered together. Use zoom/pan/hover for details.', style:{color:'#a0a4b8',marginBottom:'12px'}}));
  p8.appendChild(el('div', {id: 'chart-all-temp', style: {height:'350px',marginBottom:'24px'}}));
  p8.appendChild(el('div', {id: 'chart-all-precip', style: {height:'350px',marginBottom:'24px'}}));
  p8.appendChild(el('div', {id: 'chart-all-climatology', style: {height:'400px',marginBottom:'24px'}}));
  p8.appendChild(el('div', {id: 'chart-all-stakes', style: {height:'400px',marginBottom:'24px'}}));
  p8.appendChild(el('div', {id: 'chart-all-snowlines', style: {height:'400px',marginBottom:'24px'}}));
  p8.appendChild(el('div', {id: 'chart-all-area', style: {height:'350px',marginBottom:'24px'}}));
  p8.appendChild(el('div', {id: 'chart-all-projections', style: {height:'450px',marginBottom:'24px'}}));
  p8.appendChild(el('div', {id: 'chart-all-sensitivity', style: {height:'350px',marginBottom:'24px'}}));
  p8.appendChild(el('div', {id: 'chart-all-lapse', style: {height:'400px',marginBottom:'24px'}}));
  v.appendChild(p8);

  // Auto-render charts for the currently visible sub-tab (Climate)
  setTimeout(function() { renderClimateCharts(); }, 50);
}

var PLOTLY_LAYOUT = {
  paper_bgcolor:'#0f1117', plot_bgcolor:'#161822',
  font:{color:'#e8e8e8',family:'Inter, sans-serif',size:12},
  margin:{l:60,r:30,t:40,b:50},
  xaxis:{gridcolor:'#2a2d42',zerolinecolor:'#2a2d42'},
  yaxis:{gridcolor:'#2a2d42',zerolinecolor:'#2a2d42'},
  legend:{bgcolor:'rgba(0,0,0,0)'}
};

function pLayout(overrides) {
  var base = JSON.parse(JSON.stringify(PLOTLY_LAYOUT));
  for (var k in overrides) {
    if (typeof overrides[k] === 'object' && !Array.isArray(overrides[k]) && base[k]) {
      for (var k2 in overrides[k]) base[k][k2] = overrides[k][k2];
    } else {
      base[k] = overrides[k];
    }
  }
  return base;
}

function renderClimateCharts() {
  var c = DATA.climate;
  var wys = c.annual.map(function(a){return a.wy;});

  // Annual temperature
  if (document.getElementById('chart-temp-annual') && !document.getElementById('chart-temp-annual').hasChildNodes()) {
    Plotly.newPlot('chart-temp-annual', [
      {x:wys,y:c.annual.map(function(a){return a.T_ann;}),name:'Annual Mean',type:'scatter',mode:'markers+lines',marker:{color:'#6c8cff',size:6},line:{color:'#6c8cff'}},
      {x:wys,y:c.annual.map(function(a){return a.T_sum;}),name:'Summer Mean (JJAS)',type:'scatter',mode:'markers+lines',marker:{color:'#ef4444',size:6},line:{color:'#ef4444'}}
    ], pLayout({title:{text:'Nuka SNOTEL Temperature (375m)',font:{color:'#5eead4'}},yaxis:{title:'Temperature (C)'}}), {responsive:true});
  }

  // Annual precipitation
  if (document.getElementById('chart-precip-annual') && !document.getElementById('chart-precip-annual').hasChildNodes()) {
    Plotly.newPlot('chart-precip-annual', [{
      x:wys,y:c.annual.map(function(a){return a.P_ann;}),type:'bar',
      marker:{color:c.annual.map(function(a){return a.P_ann > 2500 ? '#22c55e' : a.P_ann < 2000 ? '#ef4444' : '#6c8cff';})}
    }], pLayout({title:{text:'Annual Total Precipitation',font:{color:'#5eead4'}},yaxis:{title:'Precipitation (mm)'},showlegend:false}), {responsive:true});
  }

  // Monthly climatology
  if (document.getElementById('chart-climatology') && !document.getElementById('chart-climatology').hasChildNodes()) {
    var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    Plotly.newPlot('chart-climatology', [
      {x:months,y:c.monthly.map(function(m){return m.T;}),name:'Temperature',type:'scatter',mode:'markers+lines',marker:{color:'#ef4444',size:8},line:{color:'#ef4444'}},
      {x:months,y:c.monthly.map(function(m){return m.P;}),name:'Precipitation',type:'bar',marker:{color:'#6c8cff88'},yaxis:'y2'}
    ], pLayout({title:{text:'Monthly Climatology (1990-2025)',font:{color:'#5eead4'}},yaxis:{title:'Temperature (C)',titlefont:{color:'#ef4444'}},yaxis2:{title:'Precipitation (mm/day)',titlefont:{color:'#6c8cff'},overlaying:'y',side:'right',gridcolor:'#2a2d4200'}}), {responsive:true});
  }
}

function renderStakeCharts() {
  if (document.getElementById('chart-stakes') && !document.getElementById('chart-stakes').hasChildNodes()) {
    var sites=['ABL','ELA','ACC'], colors=['#ef4444','#6c8cff','#22c55e'];
    Plotly.newPlot('chart-stakes', sites.map(function(site,si){
      var d=DATA.stakes.filter(function(s){return s.site===site&&s.period==='annual';});
      return{x:d.map(function(s){return s.year;}),y:d.map(function(s){return s.mb;}),
        error_y:{type:'data',array:d.map(function(s){return s.unc;}),visible:true,color:colors[si]},
        name:site+' ('+d[0].elev+'m)',type:'scatter',mode:'markers+lines',
        marker:{color:colors[si],size:8},line:{color:colors[si]}};
    }), pLayout({title:{text:'Annual Stake Mass Balance',font:{color:'#5eead4'}},yaxis:{title:'m w.e.'}}), {responsive:true});
  }
}

function renderSnowlineCharts() {
  if (document.getElementById('chart-snowlines') && !document.getElementById('chart-snowlines').hasChildNodes()) {
    Plotly.newPlot('chart-snowlines', [
      {x:DATA.snowlines.map(function(s){return s.year;}),y:DATA.snowlines.map(function(s){return s.mean;}),
       error_y:{type:'data',array:DATA.snowlines.map(function(s){return s.std;}),visible:true,color:'#6c8cff44'},
       name:'Mean',type:'scatter',mode:'markers+lines',marker:{color:'#6c8cff',size:6},line:{color:'#6c8cff'}},
      {x:DATA.snowlines.map(function(s){return s.year;}),y:DATA.snowlines.map(function(s){return s.median;}),
       name:'Median',type:'scatter',mode:'markers',marker:{color:'#5eead4',size:5,symbol:'diamond'}}
    ], pLayout({title:{text:'Snowline Elevation (22 years)',font:{color:'#5eead4'}},yaxis:{title:'Elevation (m)'}}), {responsive:true});
  }
}

function renderAreaCharts() {
  if (document.getElementById('chart-area') && !document.getElementById('chart-area').hasChildNodes()) {
    Plotly.newPlot('chart-area', [{
      x:DATA.areas.map(function(a){return a.year;}),y:DATA.areas.map(function(a){return a.area;}),
      type:'scatter',mode:'markers+lines',marker:{color:'#f59e0b',size:10},line:{color:'#f59e0b'},name:'Digitized'
    }], pLayout({title:{text:'Glacier Area Evolution',font:{color:'#5eead4'}},yaxis:{title:'Area (km2)',range:[37,41]}}), {responsive:true});
  }
}

function renderPosteriorCharts() {
  var params = ['MF','MF_grad','r_snow','precip_corr','precip_grad','T0'];
  var labels = {MF:'MF (mm/d/K)',MF_grad:'MF_grad (mm/d/K/m)',r_snow:'r_snow (mm m2/W/d/K)',precip_corr:'precip_corr',precip_grad:'precip_grad (1/m)',T0:'T0 (C)'};
  var colors = {'MF':'#6c8cff','MF_grad':'#5eead4','r_snow':'#f59e0b','precip_corr':'#ef4444','precip_grad':'#22c55e','T0':'#a855f7'};

  params.forEach(function(param) {
    var divId = 'chart-post-' + param;
    var div = document.getElementById(divId);
    if (div && !div.hasChildNodes() && DATA.posterior[param]) {
      Plotly.newPlot(divId, [{
        x: DATA.posterior[param], type: 'histogram', nbinsx: 30,
        marker: {color: colors[param] + '88', line: {color: colors[param], width: 1}}
      }], pLayout({
        title: {text: labels[param] || param, font: {color: '#5eead4', size: 14}},
        xaxis: {title: labels[param] || param},
        yaxis: {title: 'Count'},
        margin: {t: 35, b: 45}
      }), {responsive: true});
    }
  });
}

function renderProjectionCharts() {
  if (document.getElementById('chart-projections') && !document.getElementById('chart-projections').hasChildNodes()) {
    var traces = [];
    var ssps = [
      {key:'ssp126',name:'SSP1-2.6',color:'#22c55e'},
      {key:'ssp245',name:'SSP2-4.5',color:'#f59e0b'},
      {key:'ssp585',name:'SSP5-8.5',color:'#ef4444'}
    ];
    ssps.forEach(function(ssp) {
      var d = DATA.projections[ssp.key];
      // Fill band p05-p95
      traces.push({x:d.year.concat(d.year.slice().reverse()),
        y:d.p95.concat(d.p05.slice().reverse()),
        fill:'toself',fillcolor:ssp.color+'15',line:{color:'transparent'},
        showlegend:false,name:ssp.name+' 5-95%',hoverinfo:'skip'});
      // Fill band p25-p75
      traces.push({x:d.year.concat(d.year.slice().reverse()),
        y:d.p75.concat(d.p25.slice().reverse()),
        fill:'toself',fillcolor:ssp.color+'30',line:{color:'transparent'},
        showlegend:false,name:ssp.name+' 25-75%',hoverinfo:'skip'});
      // Median line
      traces.push({x:d.year,y:d.p50,name:ssp.name+' median',type:'scatter',mode:'lines',
        line:{color:ssp.color,width:2.5}});
    });
    // Observed area
    traces.push({x:DATA.areas.map(function(a){return a.year;}),y:DATA.areas.map(function(a){return a.area;}),
      name:'Observed',type:'scatter',mode:'markers',marker:{color:'#ffffff',size:8,symbol:'diamond'}});

    Plotly.newPlot('chart-projections', traces, pLayout({
      title:{text:'Glacier Area Projections (250 params x 5 GCMs)',font:{color:'#5eead4'}},
      yaxis:{title:'Area (km2)',range:[0,42]},
      xaxis:{title:'Year'}
    }), {responsive:true});
  }
}

function renderLapseProjectionChart() {
  if (document.getElementById('chart-lapse-proj') && !document.getElementById('chart-lapse-proj').hasChildNodes()) {
    var ssps = ['ssp126','ssp245','ssp585'];
    var sspColors = {ssp126:'#22c55e',ssp245:'#f59e0b',ssp585:'#ef4444'};
    var sspNames = {ssp126:'SSP1-2.6',ssp245:'SSP2-4.5',ssp585:'SSP5-8.5'};
    var lapses = [-4.5,-5.0,-5.5];

    var traces = [];
    ssps.forEach(function(ssp) {
      var rows = DATA.lapseProjections.filter(function(r){return r.scenario===ssp;});
      traces.push({
        x: rows.map(function(r){return r.lapse;}),
        y: rows.map(function(r){return r.area_p50;}),
        error_y: {type:'data',
          array: rows.map(function(r){return r.area_p95 - r.area_p50;}),
          arrayminus: rows.map(function(r){return r.area_p50 - r.area_p05;}),
          visible:true, color:sspColors[ssp]},
        name: sspNames[ssp], type:'scatter', mode:'markers+lines',
        marker:{color:sspColors[ssp],size:10}, line:{color:sspColors[ssp],width:2}
      });
    });

    Plotly.newPlot('chart-lapse-proj', traces, pLayout({
      title:{text:'2100 Area vs Lapse Rate (Sensitivity Bracket)',font:{color:'#5eead4'}},
      xaxis:{title:'Lapse Rate (C/km)',dtick:0.5},
      yaxis:{title:'Area at 2100 (km2)',range:[0,40]}
    }), {responsive:true});
  }
}

function renderSensitivityChart() {
  if (document.getElementById('chart-sensitivity') && !document.getElementById('chart-sensitivity').hasChildNodes()) {
    var ls=DATA.sensitivity.filter(function(s){return s.param==='lapse_rate';});
    Plotly.newPlot('chart-sensitivity', [
      {x:ls.map(function(s){return s.value;}),y:ls.map(function(s){return s.bias;}),
       name:'Geodetic bias',type:'scatter',mode:'markers+lines',marker:{color:'#6c8cff',size:8},line:{color:'#6c8cff'}},
      {x:ls.map(function(s){return s.value;}),y:ls.map(function(s){return s.stake_rmse;}),
       name:'Stake RMSE',type:'scatter',mode:'markers+lines',marker:{color:'#ef4444',size:8},line:{color:'#ef4444'},yaxis:'y2'}
    ], pLayout({title:{text:'Lapse Rate Sensitivity',font:{color:'#5eead4'}},
      xaxis:{title:'Lapse Rate (C/km)'},
      yaxis:{title:'Geodetic Bias',titlefont:{color:'#6c8cff'}},
      yaxis2:{title:'Stake RMSE',titlefont:{color:'#ef4444'},overlaying:'y',side:'right',gridcolor:'#2a2d4200'}}),
      {responsive:true});
  }
}

function renderAllCharts() {
  // Render duplicates of all charts in the "All Charts" tab
  var c = DATA.climate;
  var wys = c.annual.map(function(a){return a.wy;});
  var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

  if (document.getElementById('chart-all-temp') && !document.getElementById('chart-all-temp').hasChildNodes()) {
    Plotly.newPlot('chart-all-temp', [
      {x:wys,y:c.annual.map(function(a){return a.T_ann;}),name:'Annual',type:'scatter',mode:'markers+lines',marker:{color:'#6c8cff',size:6},line:{color:'#6c8cff'}},
      {x:wys,y:c.annual.map(function(a){return a.T_sum;}),name:'Summer',type:'scatter',mode:'markers+lines',marker:{color:'#ef4444',size:6},line:{color:'#ef4444'}}
    ], pLayout({title:{text:'Temperature Time Series',font:{color:'#5eead4'}},yaxis:{title:'C'}}), {responsive:true});
  }

  if (document.getElementById('chart-all-precip') && !document.getElementById('chart-all-precip').hasChildNodes()) {
    Plotly.newPlot('chart-all-precip', [{x:wys,y:c.annual.map(function(a){return a.P_ann;}),type:'bar',marker:{color:'#6c8cff'}}],
      pLayout({title:{text:'Annual Precipitation',font:{color:'#5eead4'}},yaxis:{title:'mm'},showlegend:false}), {responsive:true});
  }

  if (document.getElementById('chart-all-climatology') && !document.getElementById('chart-all-climatology').hasChildNodes()) {
    Plotly.newPlot('chart-all-climatology', [
      {x:months,y:c.monthly.map(function(m){return m.T;}),name:'T',type:'scatter',mode:'markers+lines',marker:{color:'#ef4444',size:8},line:{color:'#ef4444'}},
      {x:months,y:c.monthly.map(function(m){return m.P;}),name:'P',type:'bar',marker:{color:'#6c8cff88'},yaxis:'y2'}
    ], pLayout({title:{text:'Monthly Climatology',font:{color:'#5eead4'}},yaxis:{title:'C'},yaxis2:{title:'mm/day',overlaying:'y',side:'right',gridcolor:'#2a2d4200'}}), {responsive:true});
  }

  // Stakes
  if (document.getElementById('chart-all-stakes') && !document.getElementById('chart-all-stakes').hasChildNodes()) {
    var sites=['ABL','ELA','ACC'], colors=['#ef4444','#6c8cff','#22c55e'];
    Plotly.newPlot('chart-all-stakes', sites.map(function(site,si){
      var d=DATA.stakes.filter(function(s){return s.site===site&&s.period==='annual';});
      return{x:d.map(function(s){return s.year;}),y:d.map(function(s){return s.mb;}),
        error_y:{type:'data',array:d.map(function(s){return s.unc;}),visible:true,color:colors[si]},
        name:site,type:'scatter',mode:'markers+lines',marker:{color:colors[si],size:8},line:{color:colors[si]}};
    }), pLayout({title:{text:'Stake Mass Balance',font:{color:'#5eead4'}},yaxis:{title:'m w.e.'}}), {responsive:true});
  }

  // Snowlines
  if (document.getElementById('chart-all-snowlines') && !document.getElementById('chart-all-snowlines').hasChildNodes()) {
    Plotly.newPlot('chart-all-snowlines', [{
      x:DATA.snowlines.map(function(s){return s.year;}),y:DATA.snowlines.map(function(s){return s.mean;}),
      error_y:{type:'data',array:DATA.snowlines.map(function(s){return s.std;}),visible:true,color:'#6c8cff44'},
      name:'Mean',type:'scatter',mode:'markers+lines',marker:{color:'#6c8cff',size:6},line:{color:'#6c8cff'}}
    ], pLayout({title:{text:'Snowline Elevation',font:{color:'#5eead4'}},yaxis:{title:'m'}}), {responsive:true});
  }

  // Area
  if (document.getElementById('chart-all-area') && !document.getElementById('chart-all-area').hasChildNodes()) {
    Plotly.newPlot('chart-all-area', [{x:DATA.areas.map(function(a){return a.year;}),y:DATA.areas.map(function(a){return a.area;}),
      type:'scatter',mode:'markers+lines',marker:{color:'#f59e0b',size:10},line:{color:'#f59e0b'}}],
      pLayout({title:{text:'Glacier Area',font:{color:'#5eead4'}},yaxis:{title:'km2',range:[37,41]}}), {responsive:true});
  }

  // Projections (copy from renderProjectionCharts logic)
  if (document.getElementById('chart-all-projections') && !document.getElementById('chart-all-projections').hasChildNodes()) {
    var traces = [];
    [{key:'ssp126',name:'SSP1-2.6',color:'#22c55e'},{key:'ssp245',name:'SSP2-4.5',color:'#f59e0b'},{key:'ssp585',name:'SSP5-8.5',color:'#ef4444'}].forEach(function(ssp) {
      var d = DATA.projections[ssp.key];
      traces.push({x:d.year.concat(d.year.slice().reverse()),y:d.p95.concat(d.p05.slice().reverse()),fill:'toself',fillcolor:ssp.color+'15',line:{color:'transparent'},showlegend:false,hoverinfo:'skip'});
      traces.push({x:d.year,y:d.p50,name:ssp.name,type:'scatter',mode:'lines',line:{color:ssp.color,width:2.5}});
    });
    Plotly.newPlot('chart-all-projections', traces, pLayout({title:{text:'Projections',font:{color:'#5eead4'}},yaxis:{title:'km2',range:[0,42]}}), {responsive:true});
  }

  // Sensitivity
  if (document.getElementById('chart-all-sensitivity') && !document.getElementById('chart-all-sensitivity').hasChildNodes()) {
    var ls=DATA.sensitivity.filter(function(s){return s.param==='lapse_rate';});
    Plotly.newPlot('chart-all-sensitivity', [
      {x:ls.map(function(s){return s.value;}),y:ls.map(function(s){return s.bias;}),name:'Bias',type:'scatter',mode:'markers+lines',marker:{color:'#6c8cff',size:8},line:{color:'#6c8cff'}},
      {x:ls.map(function(s){return s.value;}),y:ls.map(function(s){return s.stake_rmse;}),name:'RMSE',type:'scatter',mode:'markers+lines',marker:{color:'#ef4444',size:8},line:{color:'#ef4444'},yaxis:'y2'}
    ], pLayout({title:{text:'Lapse Sensitivity',font:{color:'#5eead4'}},xaxis:{title:'C/km'},yaxis:{title:'Bias'},yaxis2:{title:'RMSE',overlaying:'y',side:'right',gridcolor:'#2a2d4200'}}), {responsive:true});
  }

  // Lapse projection
  if (document.getElementById('chart-all-lapse') && !document.getElementById('chart-all-lapse').hasChildNodes()) {
    var traces2 = [];
    [{key:'ssp126',name:'SSP1-2.6',color:'#22c55e'},{key:'ssp245',name:'SSP2-4.5',color:'#f59e0b'},{key:'ssp585',name:'SSP5-8.5',color:'#ef4444'}].forEach(function(ssp) {
      var rows = DATA.lapseProjections.filter(function(r){return r.scenario===ssp.key;});
      traces2.push({x:rows.map(function(r){return r.lapse;}),y:rows.map(function(r){return r.area_p50;}),
        name:ssp.name,type:'scatter',mode:'markers+lines',marker:{color:ssp.color,size:10},line:{color:ssp.color}});
    });
    Plotly.newPlot('chart-all-lapse', traces2, pLayout({title:{text:'2100 Area vs Lapse',font:{color:'#5eead4'}},xaxis:{title:'C/km'},yaxis:{title:'km2'}}), {responsive:true});
  }
}

// ── Decisions View ──────────────────────────────────────────────────

function renderDecisions() {
  var v = document.getElementById('view-decisions');
  clearChildren(v);
  v.appendChild(el('h1', {textContent: 'Decision Log (D-001 through D-031)'}));
  v.appendChild(el('p', {textContent: 'Every modeling decision with full rationale, alternatives, and physical explanation. Click to expand.', style:{color:'#a0a4b8',marginBottom:'20px'}}));

  // Calibration evolution timeline
  v.appendChild(el('h2', {textContent: 'Calibration Evolution Timeline (CAL-001 to CAL-013)'}));
  v.appendChild(el('p', {textContent: '13 calibration runs over 2 weeks. Red = failed, amber = progress (usable but flawed), green = success.', style:{color:'#a0a4b8',marginBottom:'12px'}}));

  var timeline = el('div', {className: 'cal-timeline'});
  DATA.calTimeline.forEach(function(cal) {
    var card = el('div', {className: 'cal-card'});
    var dotClass = cal.status === 'FAILED' ? 'failed' : cal.status === 'PROGRESS' ? 'progress' : 'success';
    card.appendChild(el('div', {className: 'cal-dot ' + dotClass}));

    var header = el('div', {className: 'cal-card-header'});
    header.appendChild(el('span', {className: 'cal-card-id', textContent: cal.id}));
    header.appendChild(el('span', {className: 'cal-card-status ' + dotClass, textContent: cal.status}));
    header.appendChild(el('span', {className: 'cal-card-date', textContent: cal.date}));
    card.appendChild(header);

    card.appendChild(el('div', {className: 'cal-card-change', textContent: cal.change}));
    card.appendChild(el('div', {className: 'cal-card-issue', textContent: cal.issue}));
    if (cal.cost !== null) {
      card.appendChild(el('div', {className: 'cal-card-cost', textContent: 'Cost: ' + cal.cost.toFixed(3) + ' | Params: ' + cal.params}));
    }
    timeline.appendChild(card);
  });
  v.appendChild(timeline);

  // Decision filter tags
  v.appendChild(el('h2', {textContent: 'Decision Cards', style:{marginTop:'36px'}}));
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

    // Main text
    dec.text.split('\n').forEach(function(para) {
      if (para.trim()) body.appendChild(el('p', {textContent: para.trim()}));
    });

    // Alternatives
    if (dec.alternatives) {
      var altBox = el('div', {style:{background:'#1e2030',borderRadius:'6px',padding:'12px 16px',margin:'12px 0'}});
      altBox.appendChild(el('div', {textContent: 'Alternatives Considered', style:{fontSize:'12px',fontWeight:'600',color:'#f59e0b',textTransform:'uppercase',letterSpacing:'0.5px',marginBottom:'6px'}}));
      altBox.appendChild(el('p', {textContent: dec.alternatives, style:{color:'#a0a4b8',margin:'0'}}));
      body.appendChild(altBox);
    }

    // Why this matters
    if (dec.why) {
      var whyBox = el('div', {className: 'why-box'});
      whyBox.appendChild(el('div', {className: 'why-box-title', textContent: 'Deep Explanation -- Why This Matters'}));
      dec.why.split('\n\n').forEach(function(para) {
        if (para.trim()) whyBox.appendChild(el('p', {textContent: para.trim(), style:{margin:'0 0 8px 0'}}));
      });
      body.appendChild(whyBox);
    }

    // Parameters affected (clickable)
    if (dec.params && dec.params.length > 0) {
      var paramBox = el('div', {style:{marginTop:'12px'}});
      paramBox.appendChild(el('span', {textContent: 'Parameters affected: ', style:{fontSize:'12px',color:'#6e7291'}}));
      dec.params.forEach(function(p) {
        var link = el('span', {className: 'decision-link', textContent: p});
        link.addEventListener('click', function(e) {
          e.stopPropagation();
          switchView('equations');
        });
        paramBox.appendChild(link);
      });
      body.appendChild(paramBox);
    }

    // Related decisions (clickable)
    if (dec.relatedDecisions && dec.relatedDecisions.length > 0) {
      var relBox = el('div', {style:{marginTop:'8px'}});
      relBox.appendChild(el('span', {textContent: 'Related: ', style:{fontSize:'12px',color:'#6e7291'}}));
      dec.relatedDecisions.forEach(function(dId) {
        var rdec = DATA.decisions.find(function(d) { return d.id === dId; });
        var link = el('span', {className: 'decision-link', textContent: dId + (rdec ? ': ' + rdec.title.substring(0,40) + '...' : '')});
        link.addEventListener('click', function(e) {
          e.stopPropagation();
          expandDecision(dId);
        });
        relBox.appendChild(link);
      });
      body.appendChild(relBox);
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
  v.appendChild(el('p', {textContent: 'LaTeX-rendered equations with explanations, variable tables, worked examples, and interactive calculators using real Dixon values.', style:{color:'#a0a4b8',marginBottom:'20px'}}));

  DATA.equations.forEach(function(eq, eqi) {
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

    // Interactive "Try it" calculator for the DETIM melt equation
    if (eqi === 0) {
      card.appendChild(buildMeltCalculator());
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

function buildMeltCalculator() {
  var tryIt = el('div', {className: 'try-it'});
  tryIt.appendChild(el('div', {className: 'try-it-title', textContent: 'Try It: DETIM Melt Calculator'}));

  var state = {T_nuka: 12, I_pot: 280, elev: 804, surface: 'ice'};
  var resultDiv = el('div', {className: 'try-it-result'});

  function updateResult() {
    var dz = state.elev - 375;
    var T_cell = state.T_nuka + (-5.0) * dz / 1000;
    var MF_eff = 7.11 + (-0.00411) * dz;
    if (MF_eff < 0.1) MF_eff = 0.1;
    var r = state.surface === 'ice' ? 0.00392 : 0.00196;
    var M = T_cell > 0 ? (MF_eff + r * state.I_pot) * T_cell : 0;

    resultDiv.textContent =
      'Step 1: T_cell = ' + state.T_nuka.toFixed(1) + ' + (-5.0)*(' + state.elev + '-375)/1000 = ' + T_cell.toFixed(2) + ' C\n' +
      'Step 2: MF_eff = 7.11 + (-0.00411)*(' + state.elev + '-375) = ' + MF_eff.toFixed(2) + ' mm/d/K\n' +
      'Step 3: r_' + state.surface + ' = ' + r.toFixed(5) + '\n' +
      'Step 4: M = (' + MF_eff.toFixed(2) + ' + ' + r.toFixed(5) + '*' + state.I_pot + ') * ' + T_cell.toFixed(2) + '\n' +
      '       = (' + MF_eff.toFixed(2) + ' + ' + (r * state.I_pot).toFixed(3) + ') * ' + T_cell.toFixed(2) + '\n' +
      '       = ' + M.toFixed(1) + ' mm/day' + (T_cell <= 0 ? ' (no melt: T <= 0)' : '') + '\n' +
      '       = ' + (M / 1000).toFixed(4) + ' m w.e./day';
  }

  function makeSlider(label, min, max, step, key, unit) {
    var row = el('div', {className: 'try-it-row'});
    row.appendChild(el('label', {textContent: label}));
    var valDisplay = el('span', {className: 'val-display', textContent: state[key] + unit});
    var input = el('input', {type: 'range', min: String(min), max: String(max), step: String(step), value: String(state[key])});
    input.addEventListener('input', function() {
      state[key] = parseFloat(input.value);
      valDisplay.textContent = state[key] + unit;
      updateResult();
    });
    row.appendChild(input);
    row.appendChild(valDisplay);
    return row;
  }

  tryIt.appendChild(makeSlider('T_nuka (C)', -10, 20, 0.5, 'T_nuka', ' C'));
  tryIt.appendChild(makeSlider('I_pot (W/m2)', 0, 400, 10, 'I_pot', ' W/m2'));
  tryIt.appendChild(makeSlider('Elevation (m)', 439, 1637, 10, 'elev', ' m'));

  // Surface toggle
  var surfRow = el('div', {className: 'try-it-row'});
  surfRow.appendChild(el('label', {textContent: 'Surface'}));
  ['snow', 'ice'].forEach(function(s) {
    var btn = el('div', {className: 'sub-tab' + (s === state.surface ? ' active' : ''), textContent: s,
      style:{padding:'4px 12px',fontSize:'12px',cursor:'pointer'}});
    btn.addEventListener('click', function() {
      state.surface = s;
      surfRow.querySelectorAll('.sub-tab').forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
      updateResult();
    });
    surfRow.appendChild(btn);
  });
  tryIt.appendChild(surfRow);

  tryIt.appendChild(resultDiv);
  updateResult();
  return tryIt;
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

    // Search calibration timeline
    DATA.calTimeline.forEach(function(cal) {
      if ((cal.id+' '+cal.change+' '+cal.issue).toLowerCase().indexOf(q) >= 0)
        hits.push({type:'Calibration',title:cal.id+': '+cal.change,excerpt:cal.issue,
          action:function(){switchView('decisions');}});
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
  // Render charts when switching to data view
  if (name === 'data') {
    setTimeout(function() {
      renderClimateCharts();
      renderStakeCharts();
      renderSnowlineCharts();
      renderAreaCharts();
      renderPosteriorCharts();
      renderProjectionCharts();
      renderLapseProjectionChart();
      renderSensitivityChart();
    }, 100);
  }
  closePanel();
}

document.querySelectorAll('nav .tab').forEach(function(tab) {
  tab.addEventListener('click', function() { switchView(tab.getAttribute('data-view')); });
});

// Keyboard shortcut: Escape closes panel and lightbox
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    closePanel();
    document.getElementById('lightbox').classList.remove('visible');
  }
});

// Initialize
rendered.architecture = true;
renderArchitecture();
