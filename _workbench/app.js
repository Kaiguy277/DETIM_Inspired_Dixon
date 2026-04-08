// Dixon Glacier DETIM — Model Workbench App
// All rendering uses safe DOM methods (createElement, textContent, appendChild)

// ─── HELPER: safe element builder ───
function el(tag, attrs, children) {
  const e = document.createElement(tag);
  if (attrs) Object.entries(attrs).forEach(([k,v]) => {
    if (k === 'text') e.textContent = v;
    else if (k === 'cls') e.className = v;
    else if (k === 'click') e.addEventListener('click', v);
    else if (k === 'css') e.style.cssText = v;
    else e.setAttribute(k, v);
  });
  if (children) {
    if (typeof children === 'string') e.textContent = children;
    else if (Array.isArray(children)) children.forEach(c => { if (c) e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
  }
  return e;
}
function txt(s) { return document.createTextNode(s); }

// Math rendering helper — creates a span with TeX that MathJax will process
function texSpan(latex) {
  const s = el('span'); s.textContent = '$$' + latex + '$$'; return s;
}

// ─── EMBEDDED DATA ───

// Global color map for stake sites (used in data view + charts)
const sColors={ABL:'#ef4444',ELA:'#f59e0b',ACC:'#22c55e'};

const ANNUAL_CLIMATE = [{"year":1999,"t":0.60,"p":2070},{"year":2000,"t":2.04,"p":2520},{"year":2001,"t":0.26,"p":2243},{"year":2002,"t":2.55,"p":3439},{"year":2003,"t":2.99,"p":2344},{"year":2004,"t":2.89,"p":2423},{"year":2005,"t":2.01,"p":2301},{"year":2006,"t":1.18,"p":2182},{"year":2007,"t":1.36,"p":2210},{"year":2008,"t":0.34,"p":1887},{"year":2009,"t":1.70,"p":1816},{"year":2010,"t":1.59,"p":1867},{"year":2011,"t":1.06,"p":2324},{"year":2012,"t":0.12,"p":2347},{"year":2013,"t":2.27,"p":2352},{"year":2014,"t":3.57,"p":2908},{"year":2015,"t":3.45,"p":2609},{"year":2016,"t":3.70,"p":2784},{"year":2017,"t":1.78,"p":2459},{"year":2018,"t":3.45,"p":2741},{"year":2019,"t":5.05,"p":2697},{"year":2020,"t":2.92,"p":1999},{"year":2021,"t":2.05,"p":1514},{"year":2022,"t":3.24,"p":2009},{"year":2023,"t":1.99,"p":1869},{"year":2024,"t":2.18,"p":2225},{"year":2025,"t":4.46,"p":1608}];

const MONTHLY_CLIM = [{m:1,t:-4.64,p:6.66},{m:2,t:-3.60,p:5.19},{m:3,t:-3.82,p:3.68},{m:4,t:-0.10,p:4.25},{m:5,t:3.96,p:3.50},{m:6,t:8.09,p:3.44},{m:7,t:10.81,p:4.18},{m:8,t:10.70,p:5.96},{m:9,t:7.42,p:10.31},{m:10,t:2.67,p:11.48},{m:11,t:-2.02,p:8.67},{m:12,t:-3.49,p:8.64}];

const STAKE_DATA = [
  {s:"ABL",ty:"annual",yr:2023,mb:-4.50,u:0.12,z:804},{s:"ABL",ty:"summer",yr:2023,mb:-5.35,u:0.12,z:804},{s:"ABL",ty:"winter",yr:2023,mb:0.85,u:0.10,z:804},
  {s:"ABL",ty:"annual",yr:2024,mb:-2.63,u:0.12,z:804},{s:"ABL",ty:"summer",yr:2024,mb:-4.56,u:0.12,z:804},{s:"ABL",ty:"winter",yr:2024,mb:1.93,u:0.10,z:804},{s:"ABL",ty:"winter",yr:2025,mb:1.60,u:0.10,z:804},
  {s:"ACC",ty:"annual",yr:2023,mb:0.37,u:0.12,z:1293},{s:"ACC",ty:"summer",yr:2023,mb:-2.25,u:0.12,z:1293},{s:"ACC",ty:"winter",yr:2023,mb:2.45,u:0.10,z:1293},
  {s:"ACC",ty:"annual",yr:2024,mb:1.46,u:0.12,z:1293},{s:"ACC",ty:"summer",yr:2024,mb:-1.55,u:0.12,z:1293},{s:"ACC",ty:"winter",yr:2024,mb:3.01,u:0.10,z:1293},{s:"ACC",ty:"winter",yr:2025,mb:3.53,u:0.15,z:1293},{s:"ACC",ty:"annual",yr:2025,mb:1.88,u:0.15,z:1293},{s:"ACC",ty:"summer",yr:2025,mb:-1.66,u:0.15,z:1293},
  {s:"ELA",ty:"annual",yr:2023,mb:0.10,u:0.12,z:1078},{s:"ELA",ty:"summer",yr:2023,mb:-2.26,u:0.12,z:1078},{s:"ELA",ty:"winter",yr:2023,mb:2.36,u:0.10,z:1078},
  {s:"ELA",ty:"annual",yr:2024,mb:0.10,u:0.12,z:1078},{s:"ELA",ty:"summer",yr:2024,mb:-2.50,u:0.12,z:1078},{s:"ELA",ty:"winter",yr:2024,mb:2.60,u:0.10,z:1078},{s:"ELA",ty:"winter",yr:2025,mb:3.04,u:0.10,z:1078},{s:"ELA",ty:"annual",yr:2025,mb:1.08,u:0.12,z:1078},{s:"ELA",ty:"summer",yr:2025,mb:-1.96,u:0.12,z:1078}
];

const GEODETIC = [{per:"2000-2010",dh:-1.261,edh:0.246,mb:-1.072,emb:0.225},{per:"2010-2020",dh:-0.948,edh:0.226,mb:-0.806,emb:0.202},{per:"2000-2020",dh:-1.105,edh:0.115,mb:-0.939,emb:0.122}];

const SNOWLINES = [{yr:1995,mn:1027,md:1031,mi:926,mx:1156,sd:55,n:780,src:"landsat-5"},{yr:1999,mn:1107,md:1087,mi:1041,mx:1297,sd:58,n:975,src:"landsat-7"},{yr:2000,mn:1036,md:1022,mi:961,mx:1201,sd:56,n:578,src:"landsat-7"},{yr:2003,mn:984,md:985,mi:930,mx:1029,sd:24,n:666,src:"landsat-7"},{yr:2004,mn:1204,md:1197,mi:1131,mx:1341,sd:51,n:752,src:"landsat-7"},{yr:2005,mn:1107,md:1097,mi:1047,mx:1184,sd:38,n:755,src:"landsat-7"},{yr:2006,mn:1110,md:1108,mi:1030,mx:1203,sd:42,n:1002,src:"landsat-5"},{yr:2007,mn:1129,md:1127,mi:1037,mx:1327,sd:67,n:988,src:"landsat-5"},{yr:2009,mn:1232,md:1225,mi:1191,mx:1283,sd:23,n:524,src:"landsat-7"},{yr:2010,mn:1087,md:1084,mi:956,mx:1224,sd:61,n:1139,src:"landsat-7"},{yr:2011,mn:1065,md:1053,mi:1014,mx:1159,sd:34,n:476,src:"landsat-7"},{yr:2012,mn:1080,md:1071,mi:1018,mx:1166,sd:41,n:566,src:"landsat-7"},{yr:2013,mn:1158,md:1158,mi:1046,mx:1312,sd:57,n:2225,src:"landsat-8"},{yr:2014,mn:1238,md:1251,mi:1159,mx:1292,sd:39,n:674,src:"landsat-8"},{yr:2015,mn:1055,md:1057,mi:961,mx:1133,sd:49,n:915,src:"landsat-8"},{yr:2016,mn:1074,md:1057,mi:969,mx:1193,sd:56,n:799,src:"landsat-8"},{yr:2017,mn:1161,md:1162,mi:1044,mx:1307,sd:59,n:1744,src:"sentinel-2"},{yr:2018,mn:1170,md:1172,mi:1071,mx:1243,sd:45,n:1456,src:"sentinel-2"},{yr:2019,mn:1160,md:1152,mi:1054,mx:1356,sd:62,n:2420,src:"sentinel-2"},{yr:2020,mn:1126,md:1125,mi:1067,mx:1221,sd:34,n:1045,src:"sentinel-2"},{yr:2021,mn:1088,md:1077,mi:1018,mx:1190,sd:40,n:853,src:"sentinel-2"},{yr:2023,mn:1125,md:1111,mi:1065,mx:1265,sd:49,n:939,src:"sentinel-2"},{yr:2024,mn:1166,md:1178,mi:1008,mx:1338,sd:70,n:1712,src:"sentinel-2"}];

const OUTLINE_AREAS = [{yr:2000,a:40.11},{yr:2005,a:40.11},{yr:2010,a:39.83},{yr:2015,a:39.26},{yr:2020,a:38.59},{yr:2025,a:38.34}];

const POST = [{"MF":7.561,"MG":-0.00465,"RS":0.001634,"PG":0.000537,"PC":1.765,"T0":0.025},{"MF":7.377,"MG":-0.00406,"RS":0.001089,"PG":0.000644,"PC":1.710,"T0":0.016},{"MF":6.850,"MG":-0.00371,"RS":0.001733,"PG":0.000721,"PC":1.600,"T0":0.002},{"MF":7.111,"MG":-0.00381,"RS":0.001502,"PG":0.001018,"PC":1.448,"T0":0.022},{"MF":6.954,"MG":-0.00390,"RS":0.001794,"PG":0.000453,"PC":1.838,"T0":0.001},{"MF":7.099,"MG":-0.00409,"RS":0.001833,"PG":0.000679,"PC":1.644,"T0":0.007},{"MF":7.274,"MG":-0.00357,"RS":0.000572,"PG":0.001143,"PC":1.387,"T0":0.012},{"MF":6.981,"MG":-0.00396,"RS":0.001933,"PG":0.000573,"PC":1.725,"T0":0.001},{"MF":7.310,"MG":-0.00429,"RS":0.001506,"PG":0.000643,"PC":1.663,"T0":0.007},{"MF":7.555,"MG":-0.00422,"RS":0.000705,"PG":0.000797,"PC":1.569,"T0":0.022},{"MF":7.036,"MG":-0.00410,"RS":0.001979,"PG":0.000735,"PC":1.591,"T0":0.004},{"MF":7.121,"MG":-0.00410,"RS":0.001549,"PG":0.000915,"PC":1.446,"T0":0.002},{"MF":7.352,"MG":-0.00404,"RS":0.000641,"PG":0.000913,"PC":1.451,"T0":0.011},{"MF":7.489,"MG":-0.00452,"RS":0.001437,"PG":0.000616,"PC":1.680,"T0":0.010},{"MF":7.464,"MG":-0.00451,"RS":0.001462,"PG":0.000447,"PC":1.841,"T0":0.004},{"MF":7.199,"MG":-0.00423,"RS":0.001960,"PG":0.000846,"PC":1.545,"T0":0.023},{"MF":7.370,"MG":-0.00450,"RS":0.001791,"PG":0.000609,"PC":1.682,"T0":0.007},{"MF":7.436,"MG":-0.00446,"RS":0.001456,"PG":0.000351,"PC":1.945,"T0":0.012},{"MF":7.606,"MG":-0.00441,"RS":0.000744,"PG":0.000785,"PC":1.552,"T0":0.017},{"MF":7.141,"MG":-0.00419,"RS":0.001710,"PG":0.000684,"PC":1.620,"T0":0.007},{"MF":7.442,"MG":-0.00445,"RS":0.001388,"PG":0.000214,"PC":2.107,"T0":0.006},{"MF":7.388,"MG":-0.00411,"RS":0.001010,"PG":0.000922,"PC":1.468,"T0":0.018},{"MF":7.068,"MG":-0.00410,"RS":0.001706,"PG":0.000555,"PC":1.718,"T0":0.008},{"MF":7.427,"MG":-0.00444,"RS":0.001425,"PG":0.000214,"PC":2.113,"T0":0.003},{"MF":7.387,"MG":-0.00434,"RS":0.001148,"PG":0.000672,"PC":1.616,"T0":0.006},{"MF":7.024,"MG":-0.00400,"RS":0.001693,"PG":0.000791,"PC":1.534,"T0":0.021},{"MF":7.353,"MG":-0.00438,"RS":0.001621,"PG":0.000241,"PC":2.090,"T0":0.002},{"MF":7.203,"MG":-0.00425,"RS":0.001762,"PG":0.000386,"PC":1.907,"T0":0.005},{"MF":7.383,"MG":-0.00393,"RS":0.000699,"PG":0.000852,"PC":1.523,"T0":0.039},{"MF":7.414,"MG":-0.00452,"RS":0.001718,"PG":0.000264,"PC":2.051,"T0":0.009}];

// ─── MODULE DATA ───
const MODULES = [
  {name:"config.py",role:"Configuration",lines:191,desc:"Site constants, station metadata, default parameters, physical constants, delta-h coefficients, routing defaults",details:"Defines all site-specific constants for Dixon Glacier. Key values: SNOTEL_ELEV=375m (D-013), DIXON_AWS_ELEV=1078m (D-023), PSI_A=0.75, DEFAULT_PARAMS dict.",eqs:["EQ06"],params:["SNOTEL_ELEV","DIXON_AWS_ELEV","PSI_A","SOLAR_CONSTANT","DELTAH_PARAMS","VA_C","VA_GAMMA","DEFAULT_ROUTING"],decisions:["D-002","D-013","D-015","D-023"],calledBy:["melt.py","temperature.py","solar.py","glacier_dynamics.py","routing.py"]},
  {name:"melt.py",role:"Core melt computation",lines:71,desc:"DETIM Method 2: M = (MF + r * I_pot) * T. Numba JIT.",details:"Implements the core DETIM equation (Hock 1999 Method 2). Takes distributed temperature, potential radiation, surface type to compute melt at every cell.",eqs:["EQ01"],params:["MF","r_snow","r_ice"],decisions:["D-001"],calledBy:["fast_model.py","model.py"]},
  {name:"temperature.py",role:"Temperature distribution",lines:47,desc:"Lapse-rate extrapolation from station to grid cells.",details:"T_cell = T_station + lapse * (z_cell - z_station). Lapse fixed at -5.0 C/km (D-015).",eqs:["EQ02"],params:["lapse_rate"],decisions:["D-006","D-012","D-013","D-015"],calledBy:["fast_model.py","model.py"]},
  {name:"precipitation.py",role:"Precipitation distribution",lines:68,desc:"Elevation gradient, correction, rain/snow partition.",details:"Distributes station precipitation with Cp correction + elevation gradient, partitions rain/snow via linear T0 transition.",eqs:["EQ03","EQ04"],params:["precip_corr","precip_grad","T0"],decisions:["D-011","D-013","D-016"],calledBy:["fast_model.py","model.py"]},
  {name:"solar.py",role:"Solar radiation",lines:188,desc:"Oke (1987) solar geometry, topographic correction, daily integration.",details:"Potential clear-sky direct radiation at every cell for every DOY. 365-day lookup table at 3-hour intervals. Includes declination, hour angle, earth-sun distance, atmospheric transmissivity, slope/aspect correction.",eqs:["EQ06"],params:["PSI_A","SOLAR_CONSTANT"],decisions:["D-001"],calledBy:["model.py","fast_model.py"]},
  {name:"terrain.py",role:"DEM processing",lines:100,desc:"Load/reproject DEM, slope/aspect, Winstral Sx.",details:"Loads IfSAR GeoTIFF, reprojects UTM 5N, resamples to target resolution, computes slope/aspect, optional Winstral Sx wind exposure.",eqs:[],params:[],decisions:["D-011"],calledBy:["model.py","fast_model.py"]},
  {name:"snowpack.py",role:"SWE tracking",lines:99,desc:"Snow accumulation/ablation, surface type (snow/firn/ice).",details:"Tracks SWE per cell. Snowfall adds, melt subtracts snow first then ice. Surface type drives radiation factor selection.",eqs:["EQ11"],params:[],decisions:["D-005"],calledBy:["fast_model.py","model.py"]},
  {name:"massbalance.py",role:"Balance integration",lines:63,desc:"Glacier-wide and point balance extraction.",details:"Integrates cumulative melt and accumulation into glacier-wide specific balance (m w.e.) and point balances at stake elevations.",eqs:[],params:[],decisions:["D-003"],calledBy:["calibration.py","fast_model.py"]},
  {name:"fast_model.py",role:"JIT simulation kernel",lines:370,desc:"Monolithic Numba kernel + FastDETIM class wrapper.",details:"Single @njit(parallel=True) function: temperature transfer, lapse, precipitation, rain/snow, elevation-dependent MF, DETIM melt, snowpack, runoff. ~240ms/WY at 100m grid.",eqs:["EQ01","EQ02","EQ03","EQ04","EQ05","EQ11"],params:["MF","MF_grad","r_snow","r_ice","internal_lapse","precip_grad","precip_corr","T0","k_wind"],decisions:["D-004","D-008","D-009","D-012"],calledBy:["run_calibration_v13.py","run_projection.py"]},
  {name:"calibration.py",role:"Calibration helpers",lines:100,desc:"Cost/likelihood functions, DE/MCMC setup.",details:"Combines stake residuals (inverse-variance), geodetic penalty, snowline chi-squared into objective for DE/MCMC.",eqs:["EQ10"],params:[],decisions:["D-014","D-017","D-028"],calledBy:["run_calibration_v13.py"]},
  {name:"climate.py",role:"Climate I/O + gap-fill",lines:150,desc:"Load SNOTEL, multi-station gap-fill cascade (D-025).",details:"5-station cascade: Nuka -> MFB -> McNeil -> Anchor -> Kachemak -> Lower Kachemak -> interp -> climatology. 91.3% Nuka, zero NaN output.",eqs:[],params:[],decisions:["D-024","D-025"],calledBy:["run_calibration_v13.py","run_projection.py"]},
  {name:"snowline_validation.py",role:"Snowline comparison",lines:200,desc:"Rasterize observed snowlines, compare modeled contour.",details:"22 years of digitized snowlines. RMSE, bias, MAE, correlation. Modeled = net balance=0 contour.",eqs:[],params:[],decisions:["D-021","D-022","D-028"],calledBy:["run_snowline_validation.py"]},
  {name:"behavioral_filter.py",role:"Post-hoc filtering",lines:150,desc:"Screen posterior vs snowline + area RMSE.",details:"Filters MCMC posterior against snowline RMSE and area evolution thresholds.",eqs:[],params:[],decisions:["D-028"],calledBy:["run_behavioral_filter.py"]},
  {name:"glacier_dynamics.py",role:"Geometry evolution",lines:452,desc:"Delta-h (Huss 2010), Farinotti thickness, bedrock.",details:"Loads Farinotti (2019) ice thickness, computes bedrock, applies Huss delta-h parameterization with dynamic size-class switching. Cells deglaciate when ice < 1m.",eqs:["EQ07","EQ08"],params:["DELTAH_PARAMS","VA_C","VA_GAMMA"],decisions:["D-018"],calledBy:["run_projection.py","animate_glacier_retreat.py"]},
  {name:"climate_projections.py",role:"CMIP6 processing",lines:200,desc:"Load/bias-correct NEX-GDDP-CMIP6 daily data.",details:"Monthly delta bias correction vs Nuka 1991-2020 climatology (additive T, multiplicative P).",eqs:[],params:[],decisions:["D-019"],calledBy:["run_projection.py"]},
  {name:"routing.py",role:"Discharge routing",lines:113,desc:"Three parallel linear reservoirs: fast+slow+groundwater.",details:"Routes melt+rain through fast (k=0.3, 60%), slow (k=0.05, 30%), groundwater (k=0.01, 10%). Output in m3/s.",eqs:["EQ09"],params:["k_fast","k_slow","k_gw","f_fast","f_slow"],decisions:["D-019"],calledBy:["run_projection.py"]}
];

// ─── EQUATION EXPLANATIONS (multi-paragraph plain English) ───
const EQ_EXPLAIN = {
'EQ01': "This is the heart of the entire model -- the single equation that converts weather into melt. Every day, at every point on the glacier, the model asks: \"How warm is it here, and how much sunlight is hitting this exact slope?\" The answer determines how much ice or snow melts.\n\nThe equation has two parts multiplied by temperature. The first part, MF (the melt factor, calibrated at 7.30 mm per degree per day), captures all the \"invisible\" energy sources that melt ice: warm air flowing over the surface, longwave radiation from clouds and the atmosphere, and turbulent heat exchange. These are hard to measure individually, so DETIM lumps them into one empirical number.\n\nThe second part, r times I_pot, adds the effect of direct sunlight. A south-facing slope in full sun gets hammered with radiation; a north-facing slope in a cirque shadow gets almost none. The radiation factor r differs for snow (1.41e-3, more reflective) versus bare ice (2.82e-3, darker and absorbs more). This is a simplified way to handle albedo without measuring it.\n\nThe key insight: this isn't an energy balance -- it's an index model. The temperature isn't being used to compute actual energy fluxes. It's an empirical proxy that happens to correlate well with melt. That's why the model works with off-glacier station temperatures (D-012): the MF absorbs the systematic difference between station temperature and actual surface energy.",
'EQ02': "This equation is conceptually simple but was the source of the project's most painful bugs. It answers: \"If I know the temperature at the weather station, what's the temperature at any point on the glacier?\"\n\nThe answer uses the environmental lapse rate: air temperature drops about 5 degrees for every 1000 meters of elevation gain. The Nuka SNOTEL station sits at 375m; the glacier spans from 439m (terminus) to 1637m (headwall). So on a summer day when Nuka reads 10C, the terminus (only 64m higher) sees about 9.7C -- still warm enough for vigorous melting. But the headwall (1262m higher) sees only 3.7C -- enough for some melt on sunny days, but much less, and precipitation more likely falls as snow.\n\nThe lapse rate is fixed at -5.0 C/km based on two independent literature sources for Alaskan glaciers: Gardner & Sharp (2009) measured -4.9, and Roth et al. (2023) found -5.0. Earlier calibration attempts let the optimizer tune the lapse rate freely, but it exploited this parameter to compensate for other errors (D-015) -- for example, a too-steep lapse rate combined with a too-low precipitation correction could produce the right glacier-wide balance for the wrong reasons.\n\nGetting the reference elevation right was critical. The first 7 calibration attempts failed because the Nuka station was recorded as 1230m instead of 375m (D-013 -- NRCS reports in feet, not meters!). This placed the glacier BELOW the station, reversing the lapse rate direction and making every cell 3-4C too warm.",
'EQ03': "Precipitation is the supply side of the glacier's mass balance: how much new snow accumulates each winter determines whether the glacier grows or shrinks. But measuring precipitation on a remote glacier is notoriously difficult, so this equation bridges the gap between a weather station 20km away and the glacier surface.\n\nThree adjustments are applied. First, the raw station measurement is multiplied by a correction factor Cp (calibrated at 1.61). This seems like a lot -- 61% more precipitation than measured -- but it accounts for two real effects: (a) wind blows snow particles past the collection funnel at the SNOTEL gauge (undercatch can be 20-50% for snow), and (b) the glacier sits in a wetter microclimate than the station, receiving more orographic precipitation from moist air masses off the Gulf of Alaska.\n\nSecond, an elevation gradient increases precipitation at higher elevations. At 0.07% per meter, this means the ELA (703m above the station) gets about 49% more precipitation than the station. The accumulation zone near the headwall gets even more. This captures orographic enhancement: as moist air is forced up over the mountains, it cools and drops moisture.\n\nThe effective precipitation correction at the ELA combines both effects: 1.61 x 1.49 = 2.40 times the station measurement. This is consistent with the Wolverine Glacier analog (2.28x), giving confidence the calibrated value is physically reasonable.",
'EQ04': "This equation makes a critical decision for every precipitation event at every grid cell: does it fall as snow (which accumulates and can persist for years) or rain (which runs off immediately)? The difference has enormous consequences for glacier mass balance.\n\nThe partitioning uses a simple linear transition around a threshold temperature T0. Below T0 minus 1 degree, everything is snow. Above T0 plus 1 degree, everything is rain. In between, there's a gradual mix. This 2-degree transition window reflects reality: precipitation phase depends on local humidity, droplet size, and temperature profile through the atmospheric column, not just surface temperature.\n\nThe calibrated T0 of 0.011C is remarkably close to 0 -- essentially, the freezing point. This makes physical sense for a maritime glacier on the Kenai Peninsula, where moist Gulf of Alaska air masses dominate. In continental climates, T0 might be 1-2C because drier air allows snowflakes to survive slightly above freezing.\n\nThe stakes are high at mid-elevations: near the ELA (1078m), summer temperatures hover around 4-5C, so all precipitation is rain. But in September and October, as temperatures drop through the 0-1C range, the fraction that falls as snow increases rapidly. A warm autumn that delays this transition by even a few weeks can mean hundreds of millimeters less snowfall at the ELA -- enough to shift the annual balance from positive to negative.",
'EQ05': "A single melt factor cannot simultaneously match the observed melt rates at the ablation zone (804m), the equilibrium line (1078m), and the accumulation zone (1293m). The ablation zone melts much faster per degree of warming than the accumulation zone, even after accounting for the temperature difference.\n\nThis elevation gradient captures several physical effects that DETIM doesn't model explicitly: (1) albedo decreases at lower elevations because snow melts away earlier, exposing darker ice; (2) wind speeds and turbulent heat exchange tend to be higher at exposed lower elevations; (3) longwave radiation from surrounding valley walls is greater at lower elevations; (4) humidity and cloud patterns differ across the 800m elevation range.\n\nThe calibrated gradient of -0.0042 mm/d/K per meter means that the melt factor at the accumulation zone (1293m, 918m above reference) is only 3.44 mm/d/K -- less than half the base MF of 7.30. At the ablation zone (804m, 429m above reference), it's 5.50 mm/d/K. This captures the real-world observation that low-elevation bare ice melts dramatically faster than high-elevation snowfields, even at the same temperature.\n\nA floor of 0.1 mm/d/K prevents unphysical negative values at very high elevations.",
'EQ06': "This equation computes how much direct sunlight could theoretically reach each point on the glacier under clear skies. It's the I_pot in the core melt equation -- the term that captures topographic effects on melt.\n\nThe calculation chains together several physical components. First, the solar constant (1368 W/m2) -- the energy flux at the top of the atmosphere. Then the earth-sun distance factor, which varies 3.3% through the year (closest in January, farthest in July). Then atmospheric absorption: sunlight must pass through the atmosphere, and the path length depends on both the sun angle (longer path at low angles) and elevation (less atmosphere above high-elevation cells). The atmospheric transmissivity of 0.75 means 25% of direct-beam radiation is absorbed or scattered on a single vertical pass.\n\nFinally, the topographic correction: each cell's slope and aspect determine how directly it faces the sun. A 30-degree south-facing slope at noon receives sunlight almost perpendicular -- maximizing the energy per unit area. A steep north-facing slope may be completely self-shaded for months during winter at latitude 59.66N.\n\nAt Dixon, the radiation contrast is dramatic. In June, south-facing slopes near the terminus can receive a daily mean of over 300 W/m2, while north-facing cirque walls get less than 100 W/m2. This creates visible melt patterns: south-facing glacier surfaces become heavily crevassed and sun-cupped, while adjacent north-facing areas retain snow. The solar lookup table (365 days, 3-hour sub-daily resolution) is precomputed at startup to avoid recalculating expensive trigonometry every timestep.",
'EQ07': "When a glacier loses mass, it doesn't thin uniformly like an ice cube in a glass. Real glaciers thin most at the terminus (lowest elevations) and least at the headwall (highest elevations). This empirical pattern, documented by Huss et al. (2010) from observations of Swiss glaciers, is encoded in this equation.\n\nThe variable h_r is normalized elevation: 0 at the headwall, 1 at the terminus. The equation produces a thinning \"weight\" at each elevation -- how much of the total annual mass loss is applied there. For Dixon (~40 km2, classified as \"large\" with gamma=6), the thinning is extremely concentrated at the terminus: the terminus weight is over 1000 times larger than the headwall weight.\n\nPhysically, this concentration makes sense. The terminus is at the lowest, warmest elevation, exposed to the most melt. It also receives the least new snow. And as the terminus thins, it reaches bedrock overdeepening areas where warm subglacial water pools, accelerating basal melt.\n\nAs Dixon shrinks below 20 km2 (projected around 2070-2080 under SSP5-8.5), it automatically switches to the \"medium\" size class (gamma=4, more distributed thinning). Below 5 km2, it becomes \"small\" (gamma=2). This dynamic switching captures the observation that small glaciers thin more uniformly because they lack the strong elevation contrast of large valley glaciers.\n\nWhen cumulative thinning at any cell exceeds its ice thickness (from Farinotti 2019), that cell deglaciates -- the surface drops to bedrock, the cell is removed from the glacier mask, and the glacier has permanently lost that area.",
'EQ08': "This is a simple empirical power law relating glacier area to ice volume, used primarily as a sanity check rather than a core model component. It answers: \"Given that Dixon is 40 km2, roughly how much ice should it contain?\"\n\nThe relationship V = 0.034 * A^1.36 comes from Bahr et al. (1997), who derived it from the physical scaling properties of glacier flow. The exponent 1.36 means that larger glaciers hold proportionally more ice per unit area -- they're thicker, because ice flow hasn't had time to spread the mass as thin.\n\nFor Dixon at 40.1 km2: V = 0.034 x 40.1^1.36 = 5.0 km3. The Farinotti et al. (2019) consensus estimate (computed from 5 independent ice thickness models using radar data, ice flow physics, and surface observations) gives 6.87 km3 -- a ratio of 1.37. This is within the normal range of scatter for the V-A relationship and suggests the Farinotti estimate is reasonable.\n\nThe model uses this as a diagnostic: if the modeled volume after years of geometry evolution diverges more than 3x from the V-A prediction, a warning is raised indicating something may be physically unreasonable.",
'EQ09': "Meltwater doesn't teleport from the glacier surface to the outlet stream. It travels through a complex network of supraglacial streams, moulins (vertical shafts through the ice), englacial conduits, subglacial channels, and finally through glacial sediments and bedrock fractures. This routing model simplifies all of that into three parallel \"buckets.\"\n\nThe fast reservoir (60% of runoff, draining with a 3-day timescale) represents water that flows quickly over or through the glacier: supraglacial streams on the ice surface, and large englacial/subglacial channels. On a hot sunny day, this component produces a sharp discharge peak the next day or two.\n\nThe slow reservoir (30%, 20-day timescale) represents water that takes longer paths through the subglacial drainage system -- seeping through the distributed drainage network of linked cavities beneath the ice. This produces a broad, sustained contribution to discharge that lags the melt event by weeks.\n\nThe groundwater reservoir (10%, 100-day timescale) represents water that enters the sediment and bedrock beneath the glacier. This provides baseflow even in winter, when surface melt is zero but slowly draining groundwater still feeds the outlet stream.\n\nThe parameters are NOT calibrated because Dixon has no discharge measurements. The values (k_fast=0.3, k_slow=0.05, k_gw=0.01 per day) are typical for temperate glaciers from Hock & Jansson (2005). The main purpose is peak water analysis: as the glacier shrinks under climate warming, there's initially MORE meltwater (tapping the ice reservoir), reaching a peak before declining as the glacier becomes too small to sustain high melt volumes.",
'EQ10': "This is the objective function that guides the calibration -- it tells the MCMC sampler how well any proposed set of parameters fits ALL the available observations simultaneously. Getting this right determines whether the calibrated model is physically meaningful or just curve-fitting.\n\nThe likelihood has three terms, each addressing a different type of observation. The stake term compares 25 individual mass balance measurements at three elevations against the model's predictions, weighted by the inverse of each measurement's uncertainty squared. Stakes with smaller error bars (better measurements) get more influence. This term constrains the elevation distribution of melt and accumulation.\n\nThe snowline term compares 19 years of satellite-derived snowline elevations against modeled snowline positions. With sigma=75m (accounting for spatial spread within each year, model grid resolution, and the mismatch between observation date and model date), this term constrains the spatial pattern of the snow-ice transition. It was added in D-028 after discovering that post-hoc snowline filtering had zero discriminating power.\n\nThe geodetic term is a hard penalty: if the 20-year average modeled mass balance deviates from the Hugonnet satellite-derived value (-0.939 m w.e./yr) by more than its reported uncertainty (0.122), a steep penalty (lambda=50) is applied. This prevents the optimizer from matching the short-term stake record while violating the long-term mass loss trajectory.\n\nThe MCMC sampler (emcee, 24 walkers, 10,000 steps) explores the 6-dimensional parameter space, spending more time in regions where this likelihood is high. The resulting posterior (1,656 independent samples) represents the range of parameter combinations consistent with all three data types simultaneously.",
'EQ11': "This equation tracks the snowpack at every grid cell -- the running tally of how much snow is on the ground, updated every day. It's bookkeeping, but it has critical consequences for the melt equation because the surface type (snow vs. ice) determines which radiation factor is used.\n\nEach day, two things happen. First, any snowfall (determined by the precipitation and rain/snow equations) is added to the cell's snow water equivalent (SWE). Second, melt energy (from the DETIM equation) is applied. The melt removes snow first -- if there's 500mm of SWE and 30mm of melt, the SWE drops to 470mm and the surface stays classified as \"snow\" (using the lower radiation factor r_snow). But if the melt exceeds the remaining SWE, the snow is gone and the excess energy melts the underlying ice or firn.\n\nThis creates a critical positive feedback: once snow melts away exposing darker ice, the surface switches from r_snow (1.41e-3) to r_ice (2.82e-3) -- doubling the radiation-driven melt contribution. This \"albedo feedback\" can accelerate melt dramatically at mid-elevations near the ELA, where the snowpack is marginal. A warm spell in June that strips the last snow from the ELA zone triggers weeks of enhanced ice melt for the rest of the summer.\n\nThe firn zone (above the median glacier elevation) uses the snow radiation factor even when SWE=0, reflecting the physical reality that old compacted firn is brighter than bare glacier ice. This three-way surface type classification (snow/firn/ice) is a simplified albedo scheme that avoids needing actual albedo measurements."
};

// ─── EQUATIONS ───
const EQUATIONS = [
  {id:"EQ01",name:"DETIM Method 2 Melt",latex:"M = (\\text{MF} + r \\cdot I_{\\text{pot}}) \\cdot T \\quad (T>0)",pe:"Daily melt = temperature x (melt factor + radiation factor x solar radiation). Hock 1999 Method 2.",code:"melt.py:66-68\nM = (MF + r * I) * T * dt_days",vars:[["M","Melt","mm/d","0-50"],["MF","Melt factor","mm/d/K","7.30 (cal)"],["r","Rad. factor","mm m2/W/d/K","1.41e-3"],["I_pot","Solar radiation","W/m2","0-500"],["T","Temperature","C","-30 to +20"]],ex:"ABL July: (7.30+0.00141x280)x5.9 = 45.4 mm/d",cite:"Hock (1999) J. Glaciol. 45(149)",conf:"high",decs:["D-001","D-004"]},
  {id:"EQ02",name:"Temperature Distribution",latex:"T_{cell} = T_{ref} + \\lambda(z_{cell}-z_{ref})",pe:"Lapse-rate extrapolation. -5.0 C/km fixed from literature.",code:"fast_model.py:144-145\nT_cell = T_ref + internal_lapse * dz",vars:[["T_cell","Cell temp","C","computed"],["lambda","Lapse","C/m","-0.005 fixed"],["z","Elevation","m","439-1637"]],ex:"ELA 1078m, Nuka 8.0C: T = 8.0-0.005x703 = 4.5C",cite:"Gardner & Sharp (2009)",conf:"high",decs:["D-012","D-013","D-015"]},
  {id:"EQ03",name:"Precipitation Distribution",latex:"P_{cell} = P_{stn} \\cdot C_p \\cdot (1+\\gamma_p \\Delta z)",pe:"Station precip corrected for undercatch + elevation gradient.",code:"fast_model.py:151\nP_cell = P * precip_corr * (1+precip_grad*dz)",vars:[["P_cell","Cell precip","mm/d","0-60"],["C_p","Correction","","1.61 (cal)"],["gamma_p","Gradient","1/m","0.0007 (cal)"]],ex:"Nuka 10mm, ELA dz=703m: 10x1.61x1.49 = 24 mm/d",cite:"Standard orographic model",conf:"high",decs:["D-013","D-016"]},
  {id:"EQ04",name:"Rain/Snow Partitioning",latex:"f_{snow} = \\begin{cases}1&T<T_0{-}1\\\\0.5(T_0{+}1{-}T)&\\text{between}\\\\0&T>T_0{+}1\\end{cases}",pe:"Linear transition over 2C window around T0. Calibrated T0 near 0C.",code:"fast_model.py:28-35\nif T<=T0-1: return 1.0 ...",vars:[["f_snow","Snow fraction","[0,1]","0-1"],["T0","Threshold","C","0.011 (cal)"]],ex:"T=0.5, T0=0.011: f = 0.5(1.011-0.5) = 0.26",cite:"Hock (2005), Rounce et al. (2020)",conf:"high",decs:["D-009"]},
  {id:"EQ05",name:"Elevation-Dependent MF",latex:"MF_{cell} = MF + MF_{grad}(z_{cell}-z_{ref})",pe:"Melt factor decreases with elevation (drier air, higher albedo). Floor at 0.1.",code:"fast_model.py:175-177\nMF_cell = MF + MF_grad * dz",vars:[["MF_grad","Gradient","mm/d/K/m","-0.0042 (cal)"]],ex:"ACC 1293m: 7.30+(-0.0042)(918) = 3.44. ABL 804m: 5.50",cite:"Hock (1999)",conf:"high",decs:["D-008"]},
  {id:"EQ06",name:"Potential Clear-Sky Radiation",latex:"I_{pot}=I_0(r_m/r)^2\\psi_a^{P/P_0\\sec Z}\\cos\\Theta/\\cos Z",pe:"Direct sunlight on slope accounting for solar geometry, atmosphere, and terrain.",code:"solar.py:78-116\nI_horiz = SOLAR_CONSTANT*r2*(PSI_A**exp)*cz",vars:[["I_0","Solar constant","W/m2","1368"],["psi_a","Transmissivity","","0.75"],["Z","Zenith","rad","0-pi/2"]],ex:"June 21 noon, ELA: ~860 W/m2 horiz, ~280 W/m2 daily mean",cite:"Oke (1987), Hock (1999)",conf:"high",decs:["D-001"]},
  {id:"EQ07",name:"Delta-h Geometry",latex:"\\Delta h=(h_r+a)^\\gamma+b(h_r+a)+c",pe:"Thinning pattern: maximum at terminus (h_r=1), minimum at headwall (h_r=0). Size-class dependent.",code:"glacier_dynamics.py:193-198\nval = x**gamma + b*x + c",vars:[["h_r","Norm. elevation","[0,1]","0=head,1=term"],["gamma,a,b,c","Coefficients","","size-dependent"]],ex:"Large class, terminus: (0.98)^6+0.12(0.98) = 1.00. Headwall: 0.",cite:"Huss et al. (2010) HESS",conf:"high",decs:["D-018"]},
  {id:"EQ08",name:"Volume-Area Scaling",latex:"V=0.034 A^{1.36}",pe:"Power-law glacier volume from area. Consistency check vs Farinotti.",code:"glacier_dynamics.py:96\nvolume_km3 = VA_C * area**VA_GAMMA",vars:[["V","Volume","km3","0-10"],["A","Area","km2","0-40"]],ex:"40.1 km2: V = 0.034x40.1^1.36 = 5.0 km3 (Farinotti: 6.87)",cite:"Bahr et al. (1997)",conf:"high",decs:["D-018"]},
  {id:"EQ09",name:"Linear Reservoir Routing",latex:"Q_i=k_iS_i,\\; S_i(t{+}1)=S_i+f_iR-Q_i",pe:"3 parallel reservoirs: fast (60%, k=0.3/d), slow (30%, k=0.05/d), groundwater (10%, k=0.01/d).",code:"routing.py:57-80\nS_fast += f_fast*input; out = k_fast*S_fast",vars:[["k_i","Recession","1/d","0.3/0.05/0.01"],["f_i","Fraction","","0.6/0.3/0.1"]],ex:"40.1e6 m2, 15mm runoff: fast out = 0.3x861k = 258k m3/d = 3.0 m3/s",cite:"Hock & Jansson (2005)",conf:"high",decs:["D-019"]},
  {id:"EQ10",name:"MCMC Log-Likelihood",latex:"\\ln L=-\\tfrac{1}{2}\\sum(m_i{-}o_i)^2/\\sigma_i^2-\\tfrac{1}{2}\\sum(s_j^{mod}{-}s_j^{obs})^2/\\sigma_{sl}^2-\\lambda\\max(0,|B^{mod}{-}B^{geo}|{-}\\sigma_{geo})",pe:"Stakes (inv-variance) + snowlines (sigma=75m) + geodetic hard penalty (lambda=50).",code:"run_calibration_v13.py:~200-280",vars:[["sigma_sl","Snowline unc.","m","75"],["lambda","Geo penalty","","50"]],ex:"Stakes chi2=178, snowline chi2=27, geo ok: ln L = -103",cite:"Rounce et al. (2020), emcee",conf:"medium",decs:["D-014","D-017","D-028"]},
  {id:"EQ11",name:"Snowpack Tracking",latex:"SWE(t{+}1)=SWE(t)+P_{snow}-\\min(SWE,M)",pe:"Snow added, melt subtracted (snow first, then ice). Surface type drives radiation factor.",code:"snowpack.py:51-73\nswe += snowfall; melt_snow = min(swe, melt)",vars:[["SWE","Snow water eq.","mm","0-3000"]],ex:"SWE=500, snow=5, melt=30: SWE=475mm, surface=snow",cite:"Hock (1999)",conf:"high",decs:["D-005"]}
];

// ─── DECISIONS (28) ───
const DECISIONS = [
  {id:"D-001",t:"Model Selection -- DETIM Method 2",d:"Pre-2026-03-06",s:"Hock (1999) Method 2: M = (MF + r*I_pot)*T. Balances realism vs data.",alt:"Degree-day (too simple), DEBAM (needs more data).",cit:[{t:"Hock (1999) J. Glaciol. 45(149)",r:"primary"}],p:["MF","r_snow","r_ice"],dep:[],fwd:["D-004","D-008","D-009"],imp:"Defines entire framework.",fl:["single_source"]},
  {id:"D-002",t:"Climate Source -- Nuka SNOTEL + Dixon AWS",d:"Prior",s:"Nuka (375m, 20km) + Dixon AWS (1078m ELA, summer 2024-25).",alt:"Reanalysis (biased in terrain).",cit:[{t:"NRCS SNOTEL",r:"primary"}],p:[],dep:[],fwd:["D-013","D-023","D-025"],imp:"All climate inputs.",fl:[]},
  {id:"D-003",t:"Calibration Targets -- Stakes + Geodetic",d:"Prior",s:"Stake MB at 3 elevations (2023-25) + Hugonnet geodetic 2000-2020.",alt:"Single target (equifinality).",cit:[{t:"Hugonnet et al. (2021) Nature",r:"primary"},{t:"Field measurements",r:"primary"}],p:[],dep:[],fwd:["D-014","D-016","D-017","D-028"],imp:"Two independent constraints.",fl:[]},
  {id:"D-004",t:"Numba JIT Compilation",d:"Prior",s:"@njit(parallel=True) kernel. ~300ms/eval enables 240k MCMC evals in 8-10hrs.",alt:"NumPy (3-5x slower).",cit:[],p:[],dep:["D-001"],fwd:[],imp:"Enables Bayesian calibration.",fl:["judgment"]},
  {id:"D-005",t:"Fix SWE Double-Counting",d:"2026-03-06",s:"v1 double-counted winter snowpack. Fix: SWE=0 at Oct 1.",alt:"Bug fix.",cit:[],p:["MF"],dep:[],fwd:[],imp:"Params 8 to 7.",fl:[]},
  {id:"D-006",t:"Fix Temperature Reference Elevation",d:"2026-03-06",s:"Wrong station elevation made all cells +2.8C too warm.",alt:"Bug fix.",cit:[],p:[],dep:[],fwd:["D-023"],imp:"Fundamental T geometry error.",fl:[]},
  {id:"D-007",t:"Statistical Temperature Transfer (Superseded)",d:"2026-03-06",s:"Monthly regressions Nuka->Dixon. D-023 showed offset = elevation, not katabatic.",alt:"Simple lapse (adopted D-012).",cit:[{t:"Summer overlap 256 days",r:"primary"}],p:[],dep:["D-002"],fwd:["D-010","D-012"],imp:"Superseded.",fl:["superseded"]},
  {id:"D-008",t:"Elevation-Dependent Melt Factor",d:"2026-03-06",s:"MF(z) = MF + MF_grad*(z-z_ref). Single MF can't fit 3 elevations.",alt:"Single MF (poor), band MFs (overfit).",cit:[{t:"Hock (1999)",r:"supporting"}],p:["MF_grad"],dep:["D-001"],fwd:[],imp:"+1 param, matches 3 stakes.",fl:[]},
  {id:"D-009",t:"Architecture Overhaul v4",d:"2026-03-06",s:"Temp transfer, MF_grad, routing, delta-h, projections. 8 free params.",alt:"Incremental changes.",cit:[],p:["MF","MF_grad","r_snow","r_ice","precip_grad","precip_corr","T0"],dep:["D-001","D-007","D-008"],fwd:["D-018","D-019"],imp:"Enables projections.",fl:["judgment"]},
  {id:"D-010",t:"Winter Katabatic Correction",d:"2026-03-06",s:"Tested CAL-005, did NOT improve. Root cause: spatial precip.",alt:"Standard lapse (adopted).",cit:[{t:"Katabatic theory",r:"context"}],p:[],dep:["D-007"],fwd:["D-011","D-012"],imp:"Rejected.",fl:["rejected"]},
  {id:"D-011",t:"Wind Redistribution (Winstral Sx)",d:"2026-03-06",s:"Tested CAL-006, k_wind->0. Deferred.",alt:"Uniform precip (current).",cit:[{t:"Winstral et al. (2002) WRR",r:"primary"}],p:["k_wind"],dep:["D-010"],fwd:["D-015"],imp:"k_wind=0.",fl:["deferred"]},
  {id:"D-012",t:"Identity Temperature Transfer",d:"2026-03-06",s:"Raw Nuka + calibrated lapse. DETIM absorbs micro-climate through MF.",alt:"Statistical transfer (rejected).",cit:[{t:"Hock (1999) index temps",r:"primary"}],p:["lapse_rate","MF"],dep:["D-007","D-010"],fwd:["D-013"],imp:"Key DETIM insight.",fl:[]},
  {id:"D-013",t:"Nuka Elevation: 1230 ft NOT 1230 m",d:"2026-03-09",s:"NRCS reports feet. Correct to 375m. ROOT CAUSE of CAL-001 thru CAL-007.",alt:"Critical fix.",cit:[{t:"NRCS site 1037: 1230 ft",r:"primary"}],p:["MF","precip_corr"],dep:["D-002","D-012"],fwd:["D-014","D-015","D-016"],imp:"Resolved 7 failed calibrations.",fl:["critical"]},
  {id:"D-014",t:"Inverse-Variance + Geodetic Penalty",d:"2026-03-09",s:"1/sigma2 weighting. Lambda=50 geodetic hard penalty.",alt:"Equal weights.",cit:[{t:"Zekollari (2023) OGGM",r:"supporting"},{t:"Rounce (2020) PyGEM",r:"supporting"}],p:[],dep:["D-003","D-013"],fwd:["D-016"],imp:"Proper statistical weighting.",fl:[]},
  {id:"D-015",t:"Fix Lapse, Remove k_wind",d:"2026-03-09",s:"Lapse=-5.0C/km (literature), k_wind=0. Params 9 to 7.",alt:"Calibrate lapse (exploitable).",cit:[{t:"Gardner & Sharp (2009) -4.9",r:"primary"},{t:"Roth et al. (2023) -5.0",r:"supporting"}],p:["lapse_rate","k_wind"],dep:["D-011","D-013"],fwd:["D-017"],imp:"Reduces equifinality.",fl:[]},
  {id:"D-016",t:"Single Geodetic + Wider precip_corr",d:"2026-03-09",s:"Sub-periods not distinguishable (p>0.30). precip_corr [1.2, 4.0].",alt:"Both sub-periods (contradictory).",cit:[{t:"Hugonnet uncertainties",r:"primary"}],p:["precip_corr"],dep:["D-003","D-013","D-014"],fwd:["D-017"],imp:"Removes contradiction.",fl:[]},
  {id:"D-017",t:"Bayesian Ensemble (DE + MCMC)",d:"2026-03-09",s:"DE for MAP, emcee (24 walkers, 10k steps). 6 free, 2 fixed params.",alt:"Single best-fit (equifinality).",cit:[{t:"Rounce (2020) PyGEM",r:"primary"},{t:"Foreman-Mackey (2013) emcee",r:"primary"}],p:["MF","MF_grad","r_snow","precip_grad","precip_corr","T0"],dep:["D-015","D-016"],fwd:["D-027","D-028"],imp:"Uncertainty quantification.",fl:[]},
  {id:"D-018",t:"Delta-h + Ice Thickness Overhaul",d:"2026-03-10",s:"Fixed 3 bugs, added Farinotti (2019) + dynamic size switching.",alt:"Bug fixes.",cit:[{t:"Huss et al. (2010) HESS",r:"primary"},{t:"Farinotti et al. (2019) Nature Geosci.",r:"primary"},{t:"Bahr et al. (1997)",r:"supporting"}],p:[],dep:["D-009"],fwd:["D-019","D-020"],imp:"Enables retreat projections.",fl:[]},
  {id:"D-019",t:"CMIP6 Projection Pipeline",d:"2026-03-10",s:"NEX-GDDP-CMIP6, 5 GCMs, 3 SSPs, 3-reservoir routing.",alt:"Linear delta (unrealistic).",cit:[{t:"NEX-GDDP-CMIP6 AWS S3",r:"primary"},{t:"Hock & Jansson (2005)",r:"supporting"}],p:[],dep:["D-009","D-018"],fwd:["D-020"],imp:"21st-century projections.",fl:[]},
  {id:"D-020",t:"Posterior Ensemble Projections",d:"2026-03-11",s:"250 params x 5 GCMs = 1,250 runs/SSP. Peak water SSP245 ~WY2043, SSP585 ~WY2058.",alt:"Single best-fit.",cit:[{t:"Geck (2020) Eklutna",r:"supporting"}],p:[],dep:["D-017","D-018","D-019"],fwd:[],imp:"Peak water with uncertainty.",fl:[]},
  {id:"D-021",t:"Snowline Validation (22-Year)",d:"2026-03-11",s:"Independent validation. MAP: RMSE 189m, r=0.52. Post-2017 bias +100-175m.",alt:"No spatial validation.",cit:[{t:"Digitized Landsat/Sentinel",r:"primary"}],p:[],dep:["D-003"],fwd:["D-022","D-028"],imp:"Found structural DETIM limitation.",fl:[]},
  {id:"D-022",t:"Exclude >30% Missing SNOTEL Years",d:"2026-03-11",s:"WY2000/2005 gaps filled with 0C. Exclude if >30% missing May-Sep.",alt:"Climatological fill (D-025).",cit:[],p:[],dep:["D-021"],fwd:["D-025"],imp:"n=21 to 19 valid years.",fl:[]},
  {id:"D-023",t:"Dixon AWS: 1078m ELA, NOT 804m ABL",d:"2026-03-12",s:"T offset matches 1078m lapse exactly. Same error class as D-013.",alt:"Error correction.",cit:[{t:"MFB cross-validation",r:"primary"}],p:[],dep:["D-002"],fwd:["D-024","D-025"],imp:"Essential for T merge.",fl:["critical"]},
  {id:"D-024",t:"Multi-Station Analysis",d:"2026-03-12",s:"7 stations vs Dixon AWS. MFB best T predictor (r=0.877).",alt:"Nuka only (gaps).",cit:[{t:"Dixon AWS overlap",r:"primary"}],p:[],dep:["D-002","D-023"],fwd:["D-025"],imp:"Station hierarchy.",fl:[]},
  {id:"D-025",t:"Multi-Station Gap-Fill Pipeline",d:"2026-03-12",s:"5-station cascade replacing ffill(0). 91.3% Nuka, zero NaN.",alt:"ffill+zero (catastrophic).",cit:[{t:"Transfer RMSE 1-3C",r:"primary"}],p:[],dep:["D-023","D-024"],fwd:["D-026"],imp:"Fixed data quality.",fl:["critical"]},
  {id:"D-026",t:"Recalibrate with Gap-Filled (Superseded)",d:"2026-03-12",s:"KILLED at DE step 28. Superseded by CAL-012.",alt:"Keep old climate.",cit:[],p:[],dep:["D-025","D-017"],fwd:["D-027"],imp:"Superseded.",fl:["superseded"]},
  {id:"D-027",t:"Multi-Seed Multimodality Test",d:"2026-03-12",s:"5-seed DE: UNIMODAL. All within 0.003 cost.",alt:"Single seed.",cit:[{t:"Rounce (2020)",r:"primary"}],p:[],dep:["D-017","D-026"],fwd:["D-028"],imp:"Confirmed unimodal.",fl:[]},
  {id:"D-028",t:"Snowline in MCMC Likelihood",d:"2026-03-18",s:"Snowline (22yr, sigma=75m) in likelihood + area filter. All 1000 passed. Cost 7.17->5.34. CAL-013.",alt:"Post-hoc filter (zero power).",cit:[{t:"D-021 results",r:"primary"},{t:"Rounce (2020)",r:"supporting"}],p:["MF","MF_grad","r_snow","precip_grad","precip_corr","T0"],dep:["D-017","D-021","D-027"],fwd:[],imp:"DEFINITIVE calibration.",fl:[]}
];

const CAL_RUNS = [
  {id:"CAL-001",v:1,c:"15.016",st:"FAILED",n:"5/8 at bounds. SWE double-count (D-005)."},
  {id:"CAL-002",v:2,c:"ABORT",st:"FAILED",n:"Same. Temp ref elev (D-006)."},
  {id:"CAL-003",v:3,c:"17.508",st:"IMPROVED",n:"precip_corr off bounds. 4/7 at bounds."},
  {id:"CAL-004",v:4,c:"17.823",st:"PROGRESS",n:"MF=4.1, geodetic close. Winter snow deficit."},
  {id:"CAL-005",v:"4b",c:"16.43",st:"KILLED",n:"Katabatic (D-010). Worse."},
  {id:"CAL-006",v:6,c:"16.54",st:"KILLED",n:"Wind (D-011). k_wind->0."},
  {id:"CAL-007",v:7,c:"17.035",st:"BAD",n:"Converged but geodetic catastrophic. ROOT: D-013."},
  {id:"CAL-008",v:8,c:"577",st:"PROGRESS",n:"Elev fix. r_snow collapsed."},
  {id:"CAL-009",v:9,c:"7.681",st:"BEST",n:"MF=7.6, equifinality -> ensemble needed."},
  {id:"CAL-010",v:10,c:"7.703",st:"SUCCESS",n:"First Bayesian. 2,760 samples. MF=7.11."},
  {id:"CAL-011",v:11,c:"7.23",st:"KILLED",n:"Gap-filled. Superseded."},
  {id:"CAL-012",v:12,c:"7.170",st:"DEFINITIVE",n:"5-seed UNIMODAL. 2,736 samples."},
  {id:"CAL-013",v:13,c:"5.343",st:"DEFINITIVE",n:"Multi-obj +snowline. 1,656 samples. 100% pass."}
];

// ─── SEARCH INDEX ───
const SX = [];
EQUATIONS.forEach(e => SX.push({ty:"Equation",id:e.id,nm:e.name,tx:e.name+" "+e.pe,vw:"equations",anc:"eq-"+e.id}));
DECISIONS.forEach(d => SX.push({ty:"Decision",id:d.id,nm:d.id+": "+d.t,tx:d.id+" "+d.t+" "+d.s,vw:"decisions",anc:"dec-"+d.id}));
MODULES.forEach(m => SX.push({ty:"Module",id:m.name,nm:m.name,tx:m.name+" "+m.role+" "+m.desc,vw:"architecture",anc:null}));

// ─── PANEL ───
const mainEl = document.getElementById('main-content');
const panel = document.getElementById('detail-panel');
const pc = document.getElementById('detail-content');
function openPanel(node) {
  pc.replaceChildren();
  pc.appendChild(node);
  panel.classList.add('open');
  mainEl.classList.add('panel-open');
  document.body.classList.add('panel-open');
  // Scroll panel to top on each open
  panel.scrollTop = 0;
  if(window.MathJax&&MathJax.typesetPromise)MathJax.typesetPromise([pc]);
}
function closePanel() {
  panel.classList.remove('open');
  mainEl.classList.remove('panel-open');
  document.body.classList.remove('panel-open');
}
document.getElementById('close-detail').textContent = '\u00d7';
document.getElementById('close-detail').addEventListener('click', closePanel);

// ─── NAV ───
document.querySelectorAll('nav .tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('nav .tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.view).classList.add('active');
  });
});

function navTo(view, anchorId) {
  document.querySelector('[data-view="'+view+'"]').click();
  if(anchorId) setTimeout(()=>{const e=document.getElementById(anchorId);if(e)e.scrollIntoView({behavior:'smooth',block:'center'});},150);
}

// ═══════════ MODULE PANEL (comprehensive) ═══════════

// Extended plain-English module descriptions for the side panel
const MODULE_EXPLAIN = {
'config.py': 'This is the single source of truth for all site-specific constants in the Dixon Glacier model. It defines where the glacier is (59.66N, 150.88W), how high the weather stations are (Nuka SNOTEL at 375m -- corrected from 1230m in D-013 after discovering NRCS reports in feet not meters; Dixon AWS at 1078m at the ELA -- corrected from 804m in D-023), and the default starting values for all model parameters.\n\nPhysical constants here include the solar constant (1368 W/m2), ice density (900 kg/m3), and atmospheric transmissivity (0.75). The delta-h glacier retreat coefficients from Huss et al. (2010) are defined for three size classes -- Dixon starts as "large" (>20 km2) with gamma=6, meaning thinning is very concentrated at the terminus.\n\nThe routing parameters (k_fast=0.3, k_slow=0.05, k_gw=0.01 per day) control how fast meltwater reaches the outlet. The multi-station gap-fill transfer coefficients (monthly slope/intercept for 5 backup SNOTEL stations) are also stored here.',
'melt.py': 'This is the core physics of the model -- the equation that converts temperature and solar radiation into melt. It implements Hock (1999) Method 2, the defining equation of DETIM:\n\nM = (MF + r * I_pot) * T\n\nIn plain English: on any day where air temperature T is above freezing, each glacier cell melts by an amount proportional to temperature. The proportionality constant has two parts: (1) MF, the "melt factor," which captures all the non-radiative energy sources (sensible heat, longwave radiation, turbulent fluxes) as a single empirical number; and (2) r * I_pot, which adds extra melt for direct sunlight hitting the slope. South-facing cells with the sun hitting them head-on melt more; shaded north-facing cells melt less.\n\nThe surface type matters: snow (r_snow = 1.41e-3) reflects more sunlight than bare ice (r_ice = 2 * r_snow = 2.82e-3), so ice melts faster per unit of radiation. This is a simplified way to capture albedo differences without measuring albedo directly.\n\nAll computation is JIT-compiled with Numba for speed -- this function is called for every grid cell (4,011 cells at 100m) for every day of the simulation.',
'temperature.py': 'A deceptively simple but critically important module. It takes the single temperature reading from Nuka SNOTEL (at 375m elevation, 20km from the glacier) and extrapolates it to every single cell on the glacier using a constant lapse rate:\n\nT_cell = T_station + lapse_rate * (z_cell - z_station)\n\nThe lapse rate is fixed at -5.0 C per 1000m, meaning for every 1000m you go up, temperature drops 5 degrees. This value comes from Gardner & Sharp (2009) who found -4.9 C/km, and Roth et al. (2023) who found -5.0 C/km for Alaskan glaciers.\n\nThis means the glacier terminus (439m, just 64m above the station) is only ~0.3C cooler than Nuka, while the headwall (1637m, 1262m above) is 6.3C cooler. On a summer day when Nuka reads 10C, the terminus sees 9.7C but the headwall only 3.7C -- which is why the headwall accumulates snow while the terminus melts vigorously.\n\nGetting this module right was the hardest part of the project. The first 7 calibration attempts failed because of elevation errors in this chain (D-006, D-013).',
'precipitation.py': 'Distributes precipitation from the Nuka SNOTEL station across the glacier with two adjustments, then decides if each cell gets rain or snow.\n\nFirst, the measured precipitation is multiplied by a correction factor (precip_corr = 1.61, calibrated). This accounts for: (a) wind-induced undercatch at the SNOTEL gauge (wind blows snow particles past the collector), and (b) the fact that the glacier is in a different precipitation regime 20km away and 700m higher.\n\nSecond, an elevation gradient increases precipitation at higher elevations (precip_grad = 0.0007 per meter). This captures orographic enhancement: as moist air rises over the mountains, it cools and drops more moisture. At the ELA (1078m), precipitation is about 49% higher than at the station.\n\nFinally, rain vs snow is determined by temperature with a 2-degree linear transition around T0 (calibrated near 0C). Below T0-1, it is all snow. Above T0+1, all rain. In between, a linear mix. This matters enormously for mass balance: rain runs off immediately, but snow accumulates and can survive into the next melt season.',
'solar.py': 'Computes the potential clear-sky direct solar radiation reaching every point on the glacier, for every day of the year. This is the I_pot in the core melt equation.\n\nThe calculation follows Oke (1987) solar geometry with corrections for: (1) solar declination (how high the sun gets, varying from 7 degrees at winter solstice to 54 degrees at summer solstice at latitude 59.66N); (2) earth-sun distance (3.3% variation through the year); (3) atmospheric absorption (more at low sun angles because light passes through more atmosphere, and less at high elevations because there is less atmosphere above); (4) topographic effects -- the slope angle and aspect of each cell determine how directly it faces the sun, and steep north-facing slopes may be completely shaded.\n\nThe result is precomputed as a lookup table: 365 days x full grid, with 3-hour sub-daily integration (8 timesteps per day). This means the expensive trigonometry is done once at startup, and during the simulation the model just looks up the radiation value for each day.\n\nAt Dixon, south-facing slopes near the terminus can receive >300 W/m2 daily mean in June, while steep north-facing slopes in cirques may get <100 W/m2.',
'terrain.py': 'Handles all the geospatial data processing. Loads the IfSAR 2010 digital elevation model (5m native resolution, survey-grade quality), reprojects it from geographic coordinates to UTM Zone 5N (the projection used for all spatial calculations), and resamples it to the model grid resolution (50m for analysis, 100m for calibration speed).\n\nFrom the DEM it derives slope and aspect at each cell using numpy gradient (central differences). These feed directly into the solar radiation calculation -- a 30-degree south-facing slope gets much more direct radiation than a flat surface at high latitudes.\n\nOptionally computes the Winstral Sx parameter for wind redistribution of snow: for each cell, it looks upwind (ESE, 100 degrees, based on Gulf of Alaska storm analysis) and measures how sheltered or exposed the cell is relative to the surrounding terrain. Sheltered leeward areas accumulate more wind-deposited snow. However, calibration could not constrain this parameter (D-011, D-015), so k_wind is currently fixed at 0.',
'snowpack.py': 'Tracks the snow water equivalent (SWE) at every grid cell and determines the surface type, which controls which radiation factor the melt equation uses.\n\nEach day: (1) any snowfall from the precipitation module is added to the cell\'s SWE; (2) melt energy from the melt module is applied -- first melting snow (reducing SWE), and if all snow is gone, the remaining energy melts ice or firn beneath.\n\nThe surface type assignment: if SWE > 0, the surface is "snow" (r_snow used, higher albedo). If SWE = 0 and the cell is above the median glacier elevation, it is "firn" (old compacted snow, also uses r_snow). If SWE = 0 and below the firn line, it is bare "ice" (uses r_ice = 2 * r_snow, darker surface absorbs more radiation, melts faster).\n\nThis creates a positive feedback: once snow melts away exposing darker ice, that ice melts faster, creating a "melt acceleration" through the summer. This is especially important at mid-elevations near the ELA where the transition from snow-covered to ice-exposed determines the annual mass balance.',
'fast_model.py': 'The computational engine of the entire project. This is a monolithic Numba-compiled function that combines ALL the physics from the other modules (temperature, precipitation, melt, snowpack) into a single JIT-compiled kernel that runs at near-C speed.\n\nFor each day in the simulation:\n1. Temperature transfer: apply monthly regression coefficients to convert Nuka SNOTEL temperature to on-glacier reference (currently identity transfer -- raw Nuka with calibrated lapse)\n2. Temperature distribution: lapse from reference to every cell\n3. Precipitation distribution: correction, elevation gradient, wind factor\n4. Rain/snow partitioning: linear transition around T0\n5. Snowfall accumulation: add to each cell\'s SWE\n6. Melt computation: elevation-dependent MF, radiation factor by surface type, DETIM Method 2\n7. Snowpack update: remove melted snow, update surface type\n8. Runoff tracking: melt + rain = daily runoff for each cell\n\nAt 100m resolution (289 x 117 grid, 4,011 glacier cells), one water year (365 days) runs in ~240ms. This speed is essential: the MCMC sampler calls this function 240,000 times during calibration (24 walkers x 10,000 steps), so even at 240ms/call, the full calibration takes 8-10 hours.\n\nThe FastDETIM class wraps this kernel with a Python-friendly interface, handles initial SWE setup, and extracts stake-elevation mass balances for comparison with observations.',
'massbalance.py': 'Integrates the spatially distributed melt and accumulation grids into the summary metrics needed for calibration and analysis.\n\nGlacier-wide specific balance: averages the net balance (accumulation - melt) across all glacier cells and converts from mm to m w.e. This is compared against the Hugonnet geodetic mass balance (-0.939 m w.e./yr for 2000-2020).\n\nPoint balance extraction: for each stake site (ABL at 804m, ELA at 1078m, ACC at 1293m), averages the net balance of all cells within an elevation tolerance (50m band). These are compared against the 25 field stake measurements.\n\nAlso provides data loading utilities for the stake observation CSV and Hugonnet geodetic CSV.',
'calibration.py': 'Provides the objective/likelihood functions that tell the optimizer and MCMC sampler how well a parameter set fits the observations.\n\nThe cost function combines three data types:\n(1) Stake residuals: 25 measurements at 3 elevations, each weighted by 1/sigma^2 (inverse variance). Stakes with lower measurement uncertainty get more weight. Typical sigma = 0.10-0.15 m w.e. for measured, 0.30 for estimated.\n(2) Geodetic: the 20-year mean modeled balance must match Hugonnet (-0.939 +/- 0.122 m w.e./yr). If the residual exceeds the reported uncertainty, a hard penalty (lambda=50) is applied. This prevents the optimizer from matching short-term stakes while violating the long-term mass loss.\n(3) Snowline: 19 valid years of satellite-derived snowline elevations, with sigma=75m uncertainty accounting for spatial spread, model grid resolution, and temporal mismatch.\n\nFor the MCMC sampler, this becomes a log-likelihood with Gaussian priors on MF and T0. The DE optimizer minimizes the negative log-likelihood.',
'climate.py': 'Handles all climate data I/O and the critical multi-station gap-filling pipeline (D-025).\n\nThe raw Nuka SNOTEL record has significant gaps: WY2001 had 282 days missing temperature, WY2005 had 157 days, WY2020 had a 192-day precipitation gap (1,019mm of precipitation lost!). The original approach -- forward-fill then fillna(0) -- set summer temperatures to 0C in gap years, killing all melt and producing absurd calibration results.\n\nThe gap-fill cascade uses 5 nearby SNOTEL stations as backup sources, each with monthly regression transfer coefficients computed from overlapping valid days:\n1. Middle Fork Bradley (701m, 16km, r=0.877 vs Dixon) -- best predictor\n2. McNeil Canyon (411m, 24km) -- covers WY2001 gaps\n3. Anchor River Divide (503m, 34km) -- longest record\n4. Kachemak Creek (503m, 14km) -- discontinued 2019\n5. Lower Kachemak (597m, 13km) -- since 2015 only\n\nFor each missing day, the cascade tries Nuka first, then MFB, then McNeil, etc. Precipitation uses ratio scaling. Remaining 1-3 day gaps use linear interpolation, and any still missing get DOY climatology.\n\nResult: 91.3% original Nuka, 6.0% MFB, 1.8% McNeil, zero NaN. WY2005 summer temperature corrected from 0C to 8.5C.',
'snowline_validation.py': 'Implements the independent spatial validation against 22 years (1999-2024) of satellite-derived snowline observations -- data that was never used in calibration.\n\nFor each year: (1) loads the digitized snowline shapefile (UTM 5N coordinates); (2) rasterizes it onto the model grid; (3) runs the model to the snowline observation date; (4) extracts the modeled snow/ice boundary (the elevation contour where net balance = 0); (5) compares the mean elevation, spatial pattern, and mass balance at the observed snowline positions.\n\nWith the CAL-013 parameters: RMSE = 90m, mean bias = +32m (model places snowline slightly too high), correlation = 0.73. The structural limitation is that DETIM produces spatially smooth snowlines (std 6-22m across the glacier width) while real snowlines are much more variable (std 24-69m) due to wind redistribution and aspect effects that the model cannot capture. The model also over-amplifies interannual variability (modeled std 129m vs observed 63m) and shows systematic +88 to +178m bias in recent years (2019-2024).',
'behavioral_filter.py': 'Post-hoc quality control for the MCMC posterior. Takes candidate parameter sets and screens them against additional validation criteria that were too expensive to include in the MCMC likelihood directly.\n\nThe filter runs each candidate through: (1) a 22-year snowline simulation and scores the RMSE against observed snowline elevations; (2) a multi-year area evolution simulation using the delta-h parameterization, checking the modeled glacier area at 6 checkpoints (2000, 2005, 2010, 2015, 2020, 2025) against manually digitized outlines.\n\nFor CAL-013, the area RMSE threshold was set at 1.0 km2. All 1,000 posterior samples passed (100%), meaning the snowline-informed posterior was already consistent with observed area retreat (40.11 to 38.34 km2). This validates that the multi-objective calibration produces physically consistent parameter sets.',
'glacier_dynamics.py': 'Handles how the glacier changes shape over time as it gains or loses mass. This is essential for projections: as the climate warms, the glacier thins and shrinks, which changes its elevation distribution and therefore its mass balance.\n\nThe core is the Huss et al. (2010) delta-h parameterization: when the glacier loses mass in a given year, the thinning is not uniform. Instead, it follows an empirical pattern where the terminus thins the most and the headwall thins the least. For Dixon (~40 km2, "large" class): the shape exponent gamma=6 concentrates thinning very strongly at the terminus.\n\nIce thickness comes from the Farinotti et al. (2019) consensus estimate -- a global dataset combining 5 different ice thickness models. For Dixon: mean thickness 173m, total volume 6.87 km3. When cumulative thinning at any cell exceeds its ice thickness, that cell deglaciates: the surface elevation drops to bedrock, the cell is removed from the glacier mask, and the glacier shrinks.\n\nAs the glacier loses area and drops below 20 km2, it automatically switches to the "medium" size class with different thinning patterns (gamma=4, more distributed thinning). Below 5 km2, "small" class (gamma=2, even more distributed).\n\nAlso includes Bahr et al. (1997) volume-area scaling (V = 0.034 * A^1.36) as a consistency check: if modeled volume diverges more than 3x from the V-A prediction, a warning is raised.',
'climate_projections.py': 'Prepares future climate forcing from CMIP6 global climate models for the projection simulations (2026-2100).\n\nData source: NASA NEX-GDDP-CMIP6, a bias-corrected, downscaled dataset at 0.25 degree resolution (~25 km), daily timestep, available on AWS S3 (no authentication needed). The model extracts the single pixel nearest to Dixon Glacier (59.62N, 150.88W).\n\n5 GCMs selected for good high-latitude performance and inter-model spread: ACCESS-CM2 (Australia), EC-Earth3 (Europe), MPI-ESM1-2-HR (Germany), MRI-ESM2-0 (Japan), NorESM2-MM (Norway).\n\n2 scenarios downloaded: SSP2-4.5 (moderate mitigation, ~2.7C global warming by 2100) and SSP5-8.5 (fossil-fuel intensive, ~4.4C warming).\n\nBias correction: monthly delta method against Nuka SNOTEL 1991-2020 climatology. Additive for temperature (GCM monthly mean adjusted to match historical), multiplicative for precipitation (ratio scaling). This preserves the GCM\'s interannual variability and trend while centering on the local observed climate.',
'routing.py': 'Converts the spatially distributed daily meltwater and rainfall into a time series of discharge at the glacier outlet.\n\nUses three parallel linear reservoirs representing different flow pathways through the glacier:\n- Fast reservoir (60% of runoff, k=0.3/day, residence time ~3 days): supraglacial streams and moulins. Water that flows over the glacier surface or through crevasses reaches the outlet quickly.\n- Slow reservoir (30%, k=0.05/day, ~20 days): subglacial channels. Water that reaches the glacier bed drains more slowly through the subglacial drainage system.\n- Groundwater (10%, k=0.01/day, ~100 days): water that enters the groundwater system beneath and around the glacier, providing baseflow even in winter.\n\nEach reservoir fills with its fraction of daily runoff and drains at a rate proportional to its current storage (Q = k * S). The sum of all three reservoirs gives total discharge.\n\nParameters are fixed (not calibrated) because there are no discharge observations at Dixon to constrain them. The values are typical for temperate glaciers from Hock & Jansson (2005). The main purpose is peak water analysis: the 11-year running mean of ensemble-mean discharge identifies when glacier discharge peaks before declining as the ice reservoir depletes.'
};

function openModulePanel(name) {
  const m = MODULES.find(x=>x.name===name); if(!m) return;
  const frag = document.createDocumentFragment();
  frag.appendChild(el('h2',{css:'color:var(--accent2)'},m.name));
  frag.appendChild(el('p',{css:'color:var(--accent);font-size:12px;margin-bottom:4px'},m.role+' \u00b7 '+m.lines+' lines'));
  frag.appendChild(el('p',{css:'font-size:11px;color:var(--text3);margin-bottom:12px'},'dixon_melt/'+m.name));

  // Comprehensive explanation
  const explain = MODULE_EXPLAIN[m.name] || m.details;
  explain.split('\n\n').forEach(para => {
    frag.appendChild(el('p',{css:'margin-bottom:10px;line-height:1.7'},para));
  });

  if(m.eqs.length){
    frag.appendChild(el('h3',{css:'color:var(--accent);margin:20px 0 8px;border-top:1px solid var(--border);padding-top:16px'},'Equations in this module'));
    m.eqs.forEach(eqId=>{
      const eq=EQUATIONS.find(e=>e.id===eqId);if(!eq)return;
      const box=el('div',{css:'padding:10px;background:var(--bg3);border-radius:6px;margin:6px 0;cursor:pointer;border-left:3px solid var(--accent)',click:()=>navTo('equations','eq-'+eqId)});
      box.appendChild(el('span',{cls:'badge badge-param'},eqId));
      box.appendChild(txt(' '+eq.name));
      const math=el('div',{css:'margin-top:6px;text-align:center'}); math.textContent='$$'+eq.latex+'$$'; box.appendChild(math);
      // Show first paragraph of explanation
      const eqExplain = EQ_EXPLAIN[eqId] || eq.pe;
      const firstPara = eqExplain.split('\n\n')[0];
      box.appendChild(el('p',{css:'font-size:12px;color:var(--text2);margin:6px 0 0;line-height:1.6'},firstPara));
      if(eqExplain.includes('\n\n')) box.appendChild(el('p',{css:'font-size:11px;color:var(--accent);margin:4px 0 0'},'Click to read full explanation \u2192'));
      frag.appendChild(box);
    });
  }
  if(m.params.length){
    frag.appendChild(el('h3',{css:'color:var(--accent);margin:20px 0 8px;border-top:1px solid var(--border);padding-top:16px'},'Parameters & Constants'));
    const ptable=el('table',{css:'font-size:12px'});
    const pth=el('thead');const ptr=el('tr');
    ['Name','Role'].forEach(h=>ptr.appendChild(el('th',{css:'padding:4px 8px;font-size:11px'},h)));
    pth.appendChild(ptr);ptable.appendChild(pth);
    const ptb=el('tbody');
    const paramDescriptions = {
      'SNOTEL_ELEV':'Station elevation: 375m (1230 ft, D-013)',
      'DIXON_AWS_ELEV':'On-glacier AWS: 1078m at ELA (D-023)',
      'PSI_A':'Atmospheric transmissivity: 0.75 (clear-sky)',
      'SOLAR_CONSTANT':'Top-of-atmosphere irradiance: 1368 W/m2',
      'DELTAH_PARAMS':'Huss (2010) thinning coefficients by size class',
      'VA_C':'Volume-area scaling coefficient: 0.034',
      'VA_GAMMA':'Volume-area scaling exponent: 1.36',
      'DEFAULT_ROUTING':'Reservoir coefficients: k_fast=0.3, k_slow=0.05, k_gw=0.01',
      'MF':'Melt factor: 7.30 mm/d/K (calibrated)',
      'MF_grad':'Melt factor gradient: -0.0042 mm/d/K/m',
      'r_snow':'Radiation factor snow: 1.41e-3 (calibrated)',
      'r_ice':'Radiation factor ice: 2 x r_snow = 2.82e-3',
      'lapse_rate':'Temperature lapse: -5.0 C/km (fixed)',
      'precip_corr':'Precipitation correction: 1.61 (calibrated)',
      'precip_grad':'Precipitation gradient: 0.0007 /m',
      'T0':'Rain/snow threshold: 0.011 C (calibrated)',
      'k_wind':'Wind redistribution strength: 0 (fixed, D-015)',
      'internal_lapse':'On-glacier lapse rate (same as lapse_rate)',
      'ICE_DENSITY':'Ice density: 900 kg/m3',
      'WATER_DENSITY':'Water density: 1000 kg/m3',
      'k_fast':'Fast reservoir: 0.3/day (~3 day residence)',
      'k_slow':'Slow reservoir: 0.05/day (~20 day residence)',
      'k_gw':'Groundwater: 0.01/day (~100 day residence)',
      'f_fast':'Fraction to fast: 60%',
      'f_slow':'Fraction to slow: 30%',
      'TEMP_TRANSFER_TO_NUKA':'Monthly regression coefficients for gap-fill',
      'PRECIP_RATIO_NUKA_OVER_MFB':'Monthly precip ratios Nuka/MFB'
    };
    m.params.forEach(p=>{
      const tr=el('tr');
      tr.appendChild(el('td',{css:'padding:4px 8px;color:var(--accent);font-family:"Fira Code",monospace;font-feature-settings:"calt" 0;font-size:11px'},p));
      tr.appendChild(el('td',{css:'padding:4px 8px;font-size:12px'},paramDescriptions[p]||p));
      ptb.appendChild(tr);
    });
    ptable.appendChild(ptb);frag.appendChild(ptable);
  }
  if(m.decisions.length){
    frag.appendChild(el('h3',{css:'color:var(--accent);margin:20px 0 8px;border-top:1px solid var(--border);padding-top:16px'},'Design Decisions'));
    m.decisions.forEach(did=>{
      const dec=DECISIONS.find(x=>x.id===did);
      const row=el('div',{css:'padding:8px;cursor:pointer;border-bottom:1px solid var(--border);border-radius:4px',click:()=>openDecPanel(did)});
      row.appendChild(el('span',{cls:'badge badge-decision'},did));
      if(dec) {
        row.appendChild(txt(' '+dec.t));
        row.appendChild(el('p',{css:'font-size:11px;color:var(--text3);margin:4px 0 0;padding-left:8px'},dec.s));
      }
      frag.appendChild(row);
    });
  }
  // Call graph
  frag.appendChild(el('h3',{css:'color:var(--accent);margin:20px 0 8px;border-top:1px solid var(--border);padding-top:16px'},'Dependencies'));
  if(m.calledBy.length){
    frag.appendChild(el('p',{css:'font-size:12px;color:var(--text3);margin-bottom:4px'},'Used by:'));
    const w=el('div',{css:'display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px'});
    m.calledBy.forEach(c=>w.appendChild(el('span',{cls:'dp-tag',click:()=>openModulePanel(c)},c)));
    frag.appendChild(w);
  } else {
    frag.appendChild(el('p',{css:'font-size:12px;color:var(--text3)'},'No direct dependents in the model package.'));
  }
  openPanel(frag);
}

// ═══════════ DECISION PANEL (comprehensive) ═══════════
function openDecPanel(id) {
  const d=DECISIONS.find(x=>x.id===id);if(!d)return;
  const frag=document.createDocumentFragment();
  frag.appendChild(el('h2',{css:'color:var(--accent2)'},d.id+': '+d.t));
  frag.appendChild(el('p',{css:'font-size:12px;color:var(--text3);margin-bottom:12px'},d.d));

  // Flags
  const flagRow=el('div',{css:'display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap'});
  if(d.fl.includes('critical'))flagRow.appendChild(el('span',{cls:'badge badge-low'},'CRITICAL FIX'));
  if(d.fl.includes('superseded'))flagRow.appendChild(el('span',{cls:'badge badge-med'},'SUPERSEDED'));
  if(d.fl.includes('rejected'))flagRow.appendChild(el('span',{cls:'badge badge-med'},'REJECTED'));
  if(d.fl.includes('deferred'))flagRow.appendChild(el('span',{cls:'badge badge-med'},'DEFERRED'));
  if(d.fl.includes('single_source'))flagRow.appendChild(el('span',{cls:'badge badge-med'},'SINGLE SOURCE'));
  if(d.fl.includes('judgment'))flagRow.appendChild(el('span',{cls:'badge badge-med'},'JUDGMENT CALL'));
  if(flagRow.children.length) frag.appendChild(flagRow);

  // Summary - in a highlighted box
  const sumBox=el('div',{css:'background:var(--bg3);border-radius:6px;padding:12px;margin-bottom:16px;border-left:3px solid var(--accent2)'});
  sumBox.appendChild(el('p',{css:'margin:0;line-height:1.7'},d.s));
  frag.appendChild(sumBox);

  // Evidence
  frag.appendChild(el('h3',{css:'color:var(--accent);margin:16px 0 8px;border-top:1px solid var(--border);padding-top:16px'},'Evidence Base ('+d.cit.length+' source'+(d.cit.length!==1?'s':'')+')'));
  if(!d.cit.length) {
    frag.appendChild(el('p',{css:'color:var(--text3);font-style:italic'},'No external citations. This was either a bug fix or an author judgment call based on calibration results.'));
  }
  d.cit.forEach(c=>{
    const row=el('div',{css:'padding:8px;margin:4px 0;background:var(--bg);border-radius:4px;display:flex;align-items:flex-start;gap:8px'});
    row.appendChild(el('span',{cls:'badge badge-'+c.r,css:'flex-shrink:0'},c.r));
    row.appendChild(el('span',{css:'font-size:13px'},c.t));
    frag.appendChild(row);
  });

  // Alternatives
  frag.appendChild(el('h3',{css:'color:var(--accent);margin:16px 0 8px;border-top:1px solid var(--border);padding-top:16px'},'Alternatives Considered'));
  frag.appendChild(el('p',{css:'font-size:13px;line-height:1.7'},d.alt));

  // Parameters
  if(d.p.length){
    frag.appendChild(el('h3',{css:'color:var(--accent);margin:16px 0 8px;border-top:1px solid var(--border);padding-top:16px'},'Parameters Affected'));
    const w=el('div',{css:'display:flex;flex-wrap:wrap;gap:6px'});
    d.p.forEach(p=>w.appendChild(el('span',{cls:'badge badge-param',css:'font-size:12px;padding:4px 10px'},p)));
    frag.appendChild(w);
  }

  // Dependency chain
  if(d.dep.length || d.fwd.length) {
    frag.appendChild(el('h3',{css:'color:var(--accent);margin:16px 0 8px;border-top:1px solid var(--border);padding-top:16px'},'Decision Chain'));
    if(d.dep.length){
      frag.appendChild(el('p',{css:'font-size:12px;color:var(--text3);margin-bottom:4px'},'This decision builds on:'));
      d.dep.forEach(did=>{
        const dec=DECISIONS.find(x=>x.id===did);
        const row=el('div',{css:'padding:8px;cursor:pointer;border-left:3px solid var(--accent2);margin:4px 0 4px 8px;padding-left:12px;border-radius:0 4px 4px 0',click:()=>openDecPanel(did)});
        row.appendChild(el('span',{cls:'badge badge-decision'},did));
        if(dec) {
          row.appendChild(txt(' '+dec.t));
          row.appendChild(el('p',{css:'font-size:11px;color:var(--text3);margin:2px 0 0'},dec.s.substring(0,120)+(dec.s.length>120?'...':'')));
        }
        frag.appendChild(row);
      });
    }
    if(d.fwd.length){
      frag.appendChild(el('p',{css:'font-size:12px;color:var(--text3);margin:8px 0 4px'},'Required by:'));
      d.fwd.forEach(did=>{
        const dec=DECISIONS.find(x=>x.id===did);
        const row=el('div',{css:'padding:8px;cursor:pointer;border-left:3px solid var(--accent);margin:4px 0 4px 8px;padding-left:12px;border-radius:0 4px 4px 0',click:()=>openDecPanel(did)});
        row.appendChild(el('span',{cls:'badge badge-decision'},did));
        if(dec) row.appendChild(txt(' '+dec.t));
        frag.appendChild(row);
      });
    }
  }

  // Related modules
  const relMods = MODULES.filter(m=>m.decisions.includes(d.id));
  if(relMods.length) {
    frag.appendChild(el('h3',{css:'color:var(--accent);margin:16px 0 8px;border-top:1px solid var(--border);padding-top:16px'},'Source Code Affected'));
    relMods.forEach(m=>{
      frag.appendChild(el('div',{css:'padding:6px 0;cursor:pointer',click:()=>openModulePanel(m.name)},[
        el('span',{css:'color:var(--accent);font-family:"Fira Code",monospace;font-feature-settings:"calt" 0;font-size:12px'},m.name),
        txt(' \u2014 '+m.role)
      ]));
    });
  }

  // Impact
  frag.appendChild(el('h3',{css:'color:var(--accent);margin:16px 0 8px;border-top:1px solid var(--border);padding-top:16px'},'Impact'));
  frag.appendChild(el('p',{css:'font-style:italic;line-height:1.7'},d.imp));
  openPanel(frag);
}

// ═══════════ BUILD ARCHITECTURE VIEW ═══════════
(function(){
const view = document.getElementById('architecture');

// Stats row
const g1=el('div',{cls:'grid-3',css:'margin-bottom:24px'});
[[17,'Source Files'],[11,'Core Equations'],[28,'Design Decisions']].forEach(([n,l])=>{
  const c=el('div',{cls:'card stat'});c.appendChild(el('div',{cls:'num'},String(n)));c.appendChild(el('div',{cls:'label'},l));g1.appendChild(c);
});
view.appendChild(g1);
const g2=el('div',{cls:'grid-3',css:'margin-bottom:24px'});
[[13,'Calibration Runs'],[6,'Calibrated Params'],['40.1 km\u00b2','Glacier Area (2000)']].forEach(([n,l])=>{
  const c=el('div',{cls:'card stat'});c.appendChild(el('div',{cls:'num'},String(n)));c.appendChild(el('div',{cls:'label'},l));g2.appendChild(c);
});
view.appendChild(g2);

// ASCII diagram
const dCard=el('div',{cls:'card'});
dCard.appendChild(el('h3',{},'Data Flow Diagram \u2014 click highlighted modules'));
const dCont=el('div',{cls:'arch-container'});

// Each line is an array of [text, type] pairs. type: 't'=text, 'm'=module, 'd'=decision
const lines = [
["             DIXON GLACIER DETIM v13 -- COMPLETE DATA FLOW DIAGRAM\n"],
["             =====================================================\n"],
["\n"],
[" INPUT DATA FILES                                                                      \n"],
[" ~~~~~~~~~~~~~~~~                                                                      \n"],
[" nuka_snotel_full.csv (375m, 35yr)    IfSAR DTM 5m (2010)       stake_observations.csv \n"],
[" snotel_stations/ (5 backup)          glacier_outline_rgi7       hugonnet.csv (geodetic)\n"],
[" dixon_gap_filled_climate.csv         ice_thickness (Farinotti)  snowline shapefiles    \n"],
[" CMIP6 NEX-GDDP (10 CSVs)            glacier_outlines/digitized manual_snowline_elev   \n"],
["       |                                     |                          |               \n"],
["       v                                     v                          |               \n"],
["  +------------------+    +------------------+   +--------------+       |               \n"],
["  | ","climate.py","m","        |    | ","terrain.py","m","        |   | ","solar.py","m","      |       |               \n"],
["  |                  |    |                  |   |              |       |               \n"],
["  | 5-station gap-   |    | Load DEM 5m      |   | Solar geom   |       |               \n"],
["  | fill cascade     |    | Reproject UTM 5N |   | (Oke 1987)   |       |               \n"],
["  | (","D-025","d",")           |    | Resample 100m   |   | Topo correct |       |               \n"],
["  | Monthly transfer |    | Slope / Aspect   |   | Self-shading |       |               \n"],
["  | coeff (5 stn)    |    | Glacier mask     |   | 365 DOY LUT  |       |               \n"],
["  | Nuka 91.3%       |    | Winstral Sx      |   | 3-hr integr  |       |               \n"],
["  | MFB 6%, McN 1.8% |    | (","D-011","d",")          |   | PSI_a = 0.75 |       |               \n"],
["  +--------+---------+    +--------+---------+   +------+-------+       |               \n"],
["           |                       |                    |               |               \n"],
["           +-- T(t), P(t) daily ---+--- grid, mask -----+               |               \n"],
["                                   |                                    |               \n"],
["                                   v                                    |               \n"],
["  +-----------------------------------------------------------------------+             \n"],
["  |                       ","fast_model.py","m"," (FastDETIM)                       |             \n"],
["  |                                                                       |             \n"],
["  |  @njit(parallel=True) -- ~240ms per water year at 100m grid           |             \n"],
["  |  4,011 glacier cells x 365 days = 1.46 million cell-day evaluations   |             \n"],
["  |                                                                       |             \n"],
["  |  For each day t = 1..365:                                             |             \n"],
["  |    1. T_ref = T_nuka(t)                (identity transfer, ","D-012","d",")    |             \n"],
["  |    2. T_cell = T_ref + lapse*(z-z_ref) (","temperature.py","m",", -5 C/km)     |             \n"],
["  |    3. P_cell = P*Cp*(1+grad*dz)        (","precipitation.py","m",")             |             \n"],
["  |    4. f_snow = partition(T, T0)         (rain/snow, 2C window)        |             \n"],
["  |    5. SWE += snowfall                  (","snowpack.py","m",", accumulation)     |             \n"],
["  |    6. MF_cell = MF + MF_grad*(z-z_ref) (elevation-dependent, ","D-008","d",")   |             \n"],
["  |    7. M = (MF_cell + r*Ipot) * T       (","melt.py","m",", DETIM Method 2)     |             \n"],
["  |    8. SWE -= min(SWE, M)               (snowpack update)             |             \n"],
["  |    9. surface_type = snow/firn/ice     (determines r_snow or r_ice)  |             \n"],
["  |   10. runoff = melt + rain             (daily sum for routing)       |             \n"],
["  |                                                                       |             \n"],
["  |  Output: cum_melt[grid], cum_accum[grid], daily_runoff[t],           |             \n"],
["  |          stake_balances[3], glacier_wide_balance                      |             \n"],
["  +-----------------------------------------------------------------------+             \n"],
["                                   |                                    |               \n"],
["           +-----------+-----------+-----------+                        |               \n"],
["           |           |           |           |                        |               \n"],
["           v           v           v           v                        v               \n"],
["  +------------+ +----------+ +---------+ +---------------+  +-------------------+      \n"],
["  |","massbalance","m","  | |","routing.py","m","| |","snowline_","m","  | |","glacier_dynamics","m","| |","calibration.py","m","     |      \n"],
["  |",".py","m","         | |          | |","validation","m","| |",".py","m","            | |                   |      \n"],
["  | Glacier-   | |3 linear  | |         | | Delta-h       | | Phase 1: DE         |      \n"],
["  | wide MB    | |reservoirs| | 22-year | | (Huss 2010)   | |  5 seeds x 200 iter |      \n"],
["  | & stake    | | fast 60% | | indep.  | | Farinotti ice | |  cost: 7.17 -> 5.34 |      \n"],
["  | extraction | | slow 30% | | RMSE    | | thickness     | | Phase 2: MCMC       |      \n"],
["  | (","D-003","d",")     | | gw   10% | | 90m     | | Bedrock DEM   | |  24 walk x 10k step|      \n"],
["  |            | | Q (m3/s) | | (","D-021","d",")  | | Deglaciation  | |  1,656 samples      |      \n"],
["  +------------+ +----------+ +---------+ | (","D-018","d",")        | | Phase 4: Area filter|      \n"],
["                                          +-------+-------+ |  1,000 survivors    |      \n"],
["                                                  |         | (","D-028","d",")             |      \n"],
["                                                  |         +-------------------+      \n"],
["                                                  v                  |               \n"],
["                                  +-------------------------------+  |               \n"],
["                                  |   run_projection.py           |<-+               \n"],
["                                  |                               |                  \n"],
["                                  |  1,000 params x 5 GCMs       |                  \n"],
["                                  |  = 5,000 runs per SSP        |                  \n"],
["                                  |  (or 250 ranked, ","D-020","d",")       |                  \n"],
["                                  |                               |                  \n"],
["                                  |  ","climate_projections.py","m","       |                  \n"],
["                                  |  Bias-correct CMIP6 (","D-019","d",")   |                  \n"],
["                                  |                               |                  \n"],
["                                  |  Annual loop WY2026-WY2100:   |                  \n"],
["                                  |    FastDETIM -> annual MB     |                  \n"],
["                                  |    delta-h -> geometry update |                  \n"],
["                                  |    ","routing.py","m"," -> discharge    |                  \n"],
["                                  |                               |                  \n"],
["                                  |  Output: area, volume, MB,    |                  \n"],
["                                  |  discharge, peak water        |                  \n"],
["                                  |  SSP245: peak ~WY2043         |                  \n"],
["                                  |  SSP585: peak ~WY2058         |                  \n"],
["                                  +-------------------------------+                  \n"]
];

lines.forEach(parts => {
  const row = el('div',{cls:'arch-row'});
  for(let i=0;i<parts.length;i++){
    const p = parts[i];
    // check if next element is a type marker
    if(i+1<parts.length && (parts[i+1]==='m'||parts[i+1]==='d')){
      const type = parts[i+1];
      const span = el('span',{cls:'arch-click'});
      span.textContent = p;
      if(type==='m'){
        // find matching module
        const mod = MODULES.find(m=>m.name===p || m.name.startsWith(p));
        if(mod) span.addEventListener('click',()=>openModulePanel(mod.name));
        span.style.color = 'var(--accent)';
      } else {
        span.style.color = 'var(--accent2)';
        span.addEventListener('click',()=>{navTo('decisions','dec-'+p);openDecPanel(p);});
      }
      row.appendChild(span);
      i++; // skip type marker
    } else {
      row.appendChild(el('span',{css:'color:var(--text2)'},p));
    }
  }
  dCont.appendChild(row);
});
dCard.appendChild(dCont);
view.appendChild(dCard);

// Module table
const mCard=el('div',{cls:'card'});
mCard.appendChild(el('h3',{},'Module Inventory'));
const mt=el('table');
const mth=el('thead');const mtr=el('tr');
['Module','Role','Eqs','Lines'].forEach(h=>mtr.appendChild(el('th',{},h)));
mth.appendChild(mtr);mt.appendChild(mth);
const mtb=el('tbody');
MODULES.forEach(m=>{
  const tr=el('tr',{css:'cursor:pointer',click:()=>openModulePanel(m.name)});
  tr.appendChild(el('td',{css:'color:var(--accent);font-family:"Fira Code",monospace;font-feature-settings:"calt" 0'},m.name));
  tr.appendChild(el('td',{},m.desc));
  tr.appendChild(el('td',{css:'text-align:center'},m.eqs.length?String(m.eqs.length):'-'));
  tr.appendChild(el('td',{css:'text-align:center'},String(m.lines)));
  mtb.appendChild(tr);
});
mt.appendChild(mtb);mCard.appendChild(mt);view.appendChild(mCard);
})();

// ═══════════ BUILD DATA VIEW ═══════════
(function(){
const view=document.getElementById('data');
view.appendChild(el('h2',{css:'margin-bottom:16px'},'Data Browser'));

const filterRow=el('div',{cls:'filter-row'});
['all','climate','stakes','snowline','calibration','projection'].forEach(f=>{
  const btn=el('div',{cls:'filter-btn'+(f==='all'?' active':''),'data-filter':f,click:function(){
    filterRow.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
    this.classList.add('active');
    view.querySelectorAll('.data-section').forEach(s=>s.style.display=(f==='all'||s.dataset.filter===f)?'block':'none');
  }},f==='all'?'All':f.charAt(0).toUpperCase()+f.slice(1));
  filterRow.appendChild(btn);
});
view.appendChild(filterRow);

function addSection(filter,title){
  const sec=el('div',{cls:'data-section','data-filter':filter});
  sec.appendChild(el('h3',{css:'color:var(--accent2);margin-bottom:12px;font-size:18px'},title));
  view.appendChild(sec);return sec;
}

// CLIMATE
const cs=addSection('climate','Climate Forcing');
const cc=el('div',{cls:'card'});cc.appendChild(el('h3',{},'Annual Temperature & Precipitation (1999-2025)'));
cc.appendChild(el('div',{cls:'plotly-chart-tall',id:'chart-annual'}));
cc.appendChild(el('p',{css:'font-size:12px'},'Source: data/climate/dixon_gap_filled_climate.csv (9,863 days, zero NaN). Gap-fill: 91.3% Nuka, 6.0% MFB, 1.8% McNeil.'));
cs.appendChild(cc);
const mc=el('div',{cls:'card'});mc.appendChild(el('h3',{},'Monthly Climatology'));mc.appendChild(el('div',{cls:'plotly-chart',id:'chart-monthly'}));cs.appendChild(mc);

// STAKES
const ss=addSection('stakes','Stake & Geodetic Mass Balance');
const sc=el('div',{cls:'card'});sc.appendChild(el('h3',{},'Stake Observations (25 measurements, 3 sites, WY2023-2025)'));
sc.appendChild(el('div',{cls:'plotly-chart-tall',id:'chart-stakes'}));
const stScroll=el('div',{cls:'table-scroll'});
const stTable=el('table');
const stH=el('thead');const stHr=el('tr');
['Site','Type','Year','MB (m w.e.)','Unc.','Elev (m)'].forEach(h=>stHr.appendChild(el('th',{},h)));
stH.appendChild(stHr);stTable.appendChild(stH);
const stB=el('tbody');
STAKE_DATA.forEach(s=>{
  const tr=el('tr');
  tr.appendChild(el('td',{css:'color:'+sColors[s.s]},s.s));
  tr.appendChild(el('td',{},s.ty));tr.appendChild(el('td',{},String(s.yr)));
  tr.appendChild(el('td',{css:'font-weight:600'},s.mb.toFixed(2)));
  tr.appendChild(el('td',{},'\u00b1'+s.u.toFixed(2)));tr.appendChild(el('td',{},String(s.z)));
  stB.appendChild(tr);
});
stTable.appendChild(stB);stScroll.appendChild(stTable);sc.appendChild(stScroll);ss.appendChild(sc);

const gc=el('div',{cls:'card'});gc.appendChild(el('h3',{},'Geodetic Mass Balance (Hugonnet et al. 2021)'));
const gt=el('table');const gth=el('thead');const gtr=el('tr');
['Period','dh/dt (m/yr)','\u00b1','MB (m w.e./yr)','\u00b1'].forEach(h=>gtr.appendChild(el('th',{},h)));
gth.appendChild(gtr);gt.appendChild(gth);
const gtb=el('tbody');
GEODETIC.forEach(g=>{const tr=el('tr');[g.per,g.dh.toFixed(3),g.edh.toFixed(3),g.mb.toFixed(3),g.emb.toFixed(3)].forEach(v=>tr.appendChild(el('td',{},v)));gtb.appendChild(tr);});
gt.appendChild(gtb);gc.appendChild(gt);ss.appendChild(gc);

// SNOWLINES
const sls=addSection('snowline','Snowlines & Glacier Outlines');
const slc=el('div',{cls:'card'});slc.appendChild(el('h3',{},'Snowline Elevations (22 Years, 1995-2024)'));
slc.appendChild(el('div',{cls:'plotly-chart-tall',id:'chart-snowlines'}));
const slScroll=el('div',{cls:'table-scroll'});
const slT=el('table');const slTh=el('thead');const slTr=el('tr');
['Year','Mean (m)','Median','Min','Max','Std','Samples','Source'].forEach(h=>slTr.appendChild(el('th',{},h)));
slTh.appendChild(slTr);slT.appendChild(slTh);
const slTb=el('tbody');
SNOWLINES.forEach(s=>{const tr=el('tr');[s.yr,s.mn,s.md,s.mi,s.mx,s.sd,s.n,s.src].forEach(v=>tr.appendChild(el('td',{},String(v))));slTb.appendChild(tr);});
slT.appendChild(slTb);slScroll.appendChild(slT);slc.appendChild(slScroll);sls.appendChild(slc);

const oc=el('div',{cls:'card'});oc.appendChild(el('h3',{},'Glacier Area Evolution (Digitized Outlines)'));
oc.appendChild(el('div',{cls:'plotly-chart',id:'chart-area'}));sls.appendChild(oc);

// CALIBRATION
const cas=addSection('calibration','Calibration Posterior');
const cac=el('div',{cls:'card'});cac.appendChild(el('h3',{},'CAL-013 Posterior Distributions (1,656 samples)'));
const pg=el('div',{cls:'grid-2'});
pg.appendChild(el('div',{cls:'plotly-chart',id:'chart-post-mf'}));
pg.appendChild(el('div',{cls:'plotly-chart',id:'chart-post-pc'}));
cac.appendChild(pg);
const pg2=el('div',{cls:'grid-2'});
pg2.appendChild(el('div',{cls:'plotly-chart',id:'chart-post-rs'}));
pg2.appendChild(el('div',{cls:'plotly-chart',id:'chart-post-mg'}));
cac.appendChild(pg2);
cac.appendChild(el('div',{cls:'plotly-chart-tall',id:'chart-post-scatter'}));
cas.appendChild(cac);

// PROJECTION
const ps=addSection('projection','Projection Outputs');
const pc2=el('div',{cls:'card'});
pc2.appendChild(el('h3',{},'Ensemble Projections'));
pc2.appendChild(el('p',{},'SSP2-4.5: PROJ-009 (250 params x 5 GCMs = 1,250 runs). Peak water ~WY2043 (8.17 m3/s, 45% area).'));
pc2.appendChild(el('p',{},'SSP5-8.5: PROJ-011 (250 params x 5 GCMs = 1,250 runs). Peak water ~WY2058 (8.54 m3/s, 21% area).'));
pc2.appendChild(el('p',{css:'font-size:12px;color:var(--text3)'},'Projection CSVs have per-year ensemble percentiles (p05/p25/p50/p75/p95) for area, volume, mass balance, discharge.'));
ps.appendChild(pc2);
})();

// ═══════════ BUILD DECISIONS VIEW ═══════════
(function(){
const view=document.getElementById('decisions');
view.appendChild(el('h2',{css:'margin-bottom:16px'},'Decision Log (28 Decisions)'));
view.appendChild(el('p',{css:'color:var(--text2);margin-bottom:16px'},'Click any decision ID badge to open details in the side panel.'));
DECISIONS.forEach(d=>{
  const card=el('div',{cls:'card',id:'dec-'+d.id});
  const hdr=el('div',{css:'display:flex;align-items:center;gap:12px;margin-bottom:8px'});
  hdr.appendChild(el('span',{cls:'badge badge-decision',css:'cursor:pointer',click:()=>openDecPanel(d.id)},d.id));
  const title=el('h3',{css:'margin:0;flex:1'},d.t);hdr.appendChild(title);
  hdr.appendChild(el('span',{css:'font-size:11px;color:var(--text3)'},d.d));
  card.appendChild(hdr);
  const flags=el('div',{css:'display:flex;gap:6px;margin-bottom:8px'});
  if(d.fl.includes('critical'))flags.appendChild(el('span',{cls:'badge badge-low'},'CRITICAL'));
  if(d.fl.includes('superseded'))flags.appendChild(el('span',{cls:'badge badge-med'},'SUPERSEDED'));
  if(d.fl.includes('rejected'))flags.appendChild(el('span',{cls:'badge badge-med'},'REJECTED'));
  if(d.fl.includes('deferred'))flags.appendChild(el('span',{cls:'badge badge-med'},'DEFERRED'));
  if(d.fl.includes('single_source'))flags.appendChild(el('span',{cls:'badge badge-med'},'SINGLE SOURCE'));
  if(d.fl.includes('judgment'))flags.appendChild(el('span',{cls:'badge badge-med'},'JUDGMENT'));
  card.appendChild(flags);
  card.appendChild(el('p',{},d.s));
  if(d.dep.length||d.fwd.length){
    const depDiv=el('div',{css:'font-size:12px;margin:4px 0'});depDiv.appendChild(txt('Deps: '));
    d.dep.forEach((dep,i)=>{depDiv.appendChild(el('a',{click:()=>navTo('decisions','dec-'+dep)},dep));if(i<d.dep.length-1)depDiv.appendChild(txt(', '));});
    if(d.dep.length&&d.fwd.length)depDiv.appendChild(txt(' \u2192 '));
    d.fwd.forEach((dep,i)=>{depDiv.appendChild(el('a',{click:()=>navTo('decisions','dec-'+dep)},dep));if(i<d.fwd.length-1)depDiv.appendChild(txt(', '));});
    card.appendChild(depDiv);
  }
  if(d.p.length){const pw=el('div',{css:'margin:4px 0'});d.p.forEach(p=>pw.appendChild(el('span',{cls:'badge badge-param',css:'margin:2px'},p)));card.appendChild(pw);}
  view.appendChild(card);
});

// Cal runs table
const cc=el('div',{cls:'card',css:'margin-top:24px'});cc.appendChild(el('h3',{},'Calibration Run History'));
const ct=el('table');const cth=el('thead');const ctr=el('tr');
['Run','V','Cost','Status','Notes'].forEach(h=>ctr.appendChild(el('th',{},h)));cth.appendChild(ctr);ct.appendChild(cth);
const ctb=el('tbody');
const stC={FAILED:'var(--red)',IMPROVED:'var(--accent3)',PROGRESS:'var(--accent3)',KILLED:'var(--text3)',BAD:'var(--red)',BEST:'var(--green)',SUCCESS:'var(--green)',DEFINITIVE:'var(--accent2)'};
CAL_RUNS.forEach(c=>{const tr=el('tr');tr.appendChild(el('td',{},c.id));tr.appendChild(el('td',{},'v'+c.v));tr.appendChild(el('td',{},c.c));tr.appendChild(el('td',{css:'color:'+(stC[c.st]||'var(--text2)')+';font-weight:600'},c.st));tr.appendChild(el('td',{},c.n));ctb.appendChild(tr);});
ct.appendChild(ctb);cc.appendChild(ct);view.appendChild(cc);
})();

// ═══════════ BUILD EQUATIONS VIEW ═══════════
(function(){
const view=document.getElementById('equations');
view.appendChild(el('h2',{css:'margin-bottom:16px'},'Equation Reference'));

// Param table
const pc=el('div',{cls:'card',css:'margin-bottom:24px'});pc.appendChild(el('h3',{},'Calibrated Parameters (CAL-013)'));
const pt=el('table');const pth=el('thead');const ptr=el('tr');
['Param','Symbol','Units','Bounds','Median','95% CI','Prior'].forEach(h=>ptr.appendChild(el('th',{},h)));
pth.appendChild(ptr);pt.appendChild(pth);
const ptb=el('tbody');
[['Melt factor','MF','mm/d/K','[1, 12]','7.30','[7.06, 7.58]','N(5,3)'],
 ['MF gradient','MF_grad','mm/d/K/m','[-0.01, 0]','-0.0042','[-0.0044, -0.0039]','Uniform'],
 ['Rad. factor','r_snow','mm m2/W/d/K','[0.02, 2]e-3','1.41e-3','[0.73, 1.82]e-3','Uniform'],
 ['Precip grad','precip_grad','1/m','[2e-4, 6e-3]','0.0007','[6e-4, 9e-4]','Uniform'],
 ['Precip corr','precip_corr','','[1.2, 4.0]','1.61','[1.48, 1.74]','Uniform'],
 ['Rain/snow T','T0','C','[0.5, 3.0]','0.011','[0.003, 0.029]','N(1.5,0.5)']
].forEach(r=>{const tr=el('tr');r.forEach(v=>tr.appendChild(el('td',{},v)));ptb.appendChild(tr);});
pt.appendChild(ptb);pc.appendChild(pt);
pc.appendChild(el('p',{css:'margin-top:8px;font-size:12px'},'Fixed: lapse = -5.0 C/km (Gardner & Sharp 2009); r_ice = 2 x r_snow (Hock 1999 Table 4)'));
view.appendChild(pc);

EQUATIONS.forEach(eq=>{
  const card=el('div',{cls:'card',id:'eq-'+eq.id});
  const hdr=el('div',{css:'display:flex;align-items:center;gap:12px;margin-bottom:12px'});
  hdr.appendChild(el('span',{cls:'badge badge-param'},eq.id));
  hdr.appendChild(el('h3',{css:'margin:0;flex:1'},eq.name));
  hdr.appendChild(el('span',{cls:'badge badge-'+(eq.conf==='high'?'high':'med')},eq.conf));
  card.appendChild(hdr);
  const eqBox=el('div',{cls:'eq-box'});eqBox.textContent='$$'+eq.latex+'$$';card.appendChild(eqBox);
  // Comprehensive plain-English explanation
  const explain = EQ_EXPLAIN[eq.id] || eq.pe;
  explain.split('\n\n').forEach(para => {
    card.appendChild(el('p',{css:'margin-bottom:10px;line-height:1.7'},para));
  });
  // Vars
  card.appendChild(el('h4',{},'Variables'));
  const vt=el('table');const vth=el('thead');const vtr=el('tr');
  ['Symbol','Name','Units','Range/Value'].forEach(h=>vtr.appendChild(el('th',{},h)));
  vth.appendChild(vtr);vt.appendChild(vth);
  const vtb=el('tbody');
  eq.vars.forEach(v=>{const tr=el('tr');v.forEach(x=>tr.appendChild(el('td',{},x)));vtb.appendChild(tr);});
  vt.appendChild(vtb);card.appendChild(vt);
  // Worked example
  const we=el('div',{cls:'worked-example'});we.appendChild(el('div',{cls:'wlabel'},'Worked Example'));we.appendChild(el('p',{css:'font-size:13px;color:var(--text2);margin:0'},eq.ex));card.appendChild(we);
  // Code
  const det=el('details');det.appendChild(el('summary',{},'Source Code'));
  const pre=el('pre',{cls:'code-block'},eq.code);det.appendChild(pre);card.appendChild(det);
  // Cite
  card.appendChild(el('p',{css:'font-size:12px;color:var(--text3);margin-top:8px'},'Ref: '+eq.cite));
  // Decisions
  if(eq.decs.length){const dd=el('div',{css:'font-size:12px;margin-top:4px'});dd.appendChild(txt('Related: '));eq.decs.forEach((d,i)=>{dd.appendChild(el('a',{click:()=>openDecPanel(d)},d));if(i<eq.decs.length-1)dd.appendChild(txt(', '));});card.appendChild(dd);}
  view.appendChild(card);
});
})();

// ═══════════ BUILD SEARCH VIEW ═══════════
(function(){
const view=document.getElementById('search');
view.appendChild(el('h2',{css:'margin-bottom:16px'},'Explorer'));
const inp=el('input',{type:'text',id:'search-input',placeholder:'Search equations, parameters, decisions, modules...'});
view.appendChild(inp);
const res=el('div',{id:'search-results'});view.appendChild(res);
inp.addEventListener('input',()=>{
  const q=inp.value.toLowerCase().trim();res.replaceChildren();
  if(q.length<2)return;
  const hits=SX.filter(i=>i.tx.toLowerCase().includes(q)).slice(0,25);
  if(!hits.length){res.appendChild(el('p',{css:'color:var(--text3);padding:12px'},'No results.'));return;}
  const cols={Equation:'var(--accent)',Decision:'var(--accent2)',Module:'var(--green)',Parameter:'#c084fc'};
  hits.forEach(hit=>{
    const div=el('div',{cls:'search-hit',click:()=>{
      navTo(hit.vw,hit.anc);
      if(hit.ty==='Module')setTimeout(()=>openModulePanel(hit.id),100);
      if(hit.ty==='Decision')setTimeout(()=>openDecPanel(hit.id),100);
    }});
    div.appendChild(el('div',{cls:'hit-type',css:'color:'+(cols[hit.ty]||'var(--text2)')},hit.ty));
    div.appendChild(el('div',{css:'font-weight:500;margin-top:2px'},hit.nm));
    const idx=hit.tx.toLowerCase().indexOf(q);
    const snip=hit.tx.substring(Math.max(0,idx-40),Math.min(hit.tx.length,idx+q.length+60));
    div.appendChild(el('div',{css:'font-size:12px;color:var(--text3);margin-top:2px'},'...'+snip+'...'));
    res.appendChild(div);
  });
});
})();

// ═══════════ PLOTLY CHARTS ═══════════
setTimeout(()=>{
const L={paper_bgcolor:'#0f1117',plot_bgcolor:'#0f1117',font:{color:'#a0a4b8',family:'Inter'},margin:{l:50,r:20,t:30,b:40},xaxis:{gridcolor:'#2a2d42',zerolinecolor:'#2a2d42'},yaxis:{gridcolor:'#2a2d42',zerolinecolor:'#2a2d42'}};
const C={displayModeBar:true,displaylogo:false,responsive:true};

// Annual climate
Plotly.newPlot('chart-annual',[
  {x:ANNUAL_CLIMATE.map(d=>d.year),y:ANNUAL_CLIMATE.map(d=>d.t),type:'scatter',mode:'lines+markers',name:'Mean Temp (C)',marker:{color:'#ef4444',size:6},line:{color:'#ef4444'}},
  {x:ANNUAL_CLIMATE.map(d=>d.year),y:ANNUAL_CLIMATE.map(d=>d.p),type:'bar',name:'Total Precip (mm)',marker:{color:'#3b82f644'},yaxis:'y2'}
],{...L,yaxis:{...L.yaxis,title:'Temperature (C)'},yaxis2:{title:'Precipitation (mm)',overlaying:'y',side:'right',gridcolor:'transparent'},legend:{x:0.02,y:0.98,bgcolor:'transparent'}},C);

// Monthly
const months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
Plotly.newPlot('chart-monthly',[
  {x:months,y:MONTHLY_CLIM.map(d=>d.t),type:'bar',name:'Temp (C)',marker:{color:'#ef4444aa'}},
  {x:months,y:MONTHLY_CLIM.map(d=>d.p),type:'bar',name:'Precip (mm/d)',marker:{color:'#3b82f6aa'},yaxis:'y2'}
],{...L,barmode:'group',yaxis:{...L.yaxis,title:'Temp (C)'},yaxis2:{title:'Precip (mm/d)',overlaying:'y',side:'right',gridcolor:'transparent'},legend:{x:0.02,y:0.98,bgcolor:'transparent'}},C);

// Stakes
const traces=[];
['annual','summer','winter'].forEach(ty=>{
  ['ABL','ELA','ACC'].forEach(site=>{
    const d=STAKE_DATA.filter(s=>s.s===site&&s.ty===ty);if(!d.length)return;
    const off={ABL:-0.15,ELA:0,ACC:0.15}[site];
    traces.push({x:d.map(s=>s.yr+off),y:d.map(s=>s.mb),error_y:{type:'data',array:d.map(s=>s.u),visible:true,color:sColors[site]+'88'},type:'scatter',mode:'markers',name:site+' '+ty,marker:{color:sColors[site],size:ty==='annual'?10:6,symbol:ty==='annual'?'circle':ty==='summer'?'triangle-down':'triangle-up'}});
  });
});
Plotly.newPlot('chart-stakes',traces,{...L,yaxis:{...L.yaxis,title:'Mass Balance (m w.e.)'},xaxis:{...L.xaxis,title:'Year'},shapes:[{type:'line',x0:2022.5,x1:2025.5,y0:0,y1:0,line:{color:'#6e7291',dash:'dash',width:1}}],legend:{bgcolor:'transparent'}},C);

// Snowlines
Plotly.newPlot('chart-snowlines',[
  {x:SNOWLINES.map(s=>s.yr),y:SNOWLINES.map(s=>s.mn),error_y:{type:'data',array:SNOWLINES.map(s=>s.sd),visible:true,color:'#6c8cff44'},type:'scatter',mode:'lines+markers',name:'Mean',marker:{color:'#6c8cff',size:7},line:{color:'#6c8cff'}},
  {x:SNOWLINES.map(s=>s.yr),y:SNOWLINES.map(s=>s.mi),type:'scatter',mode:'lines',name:'Min',line:{color:'#6c8cff33',dash:'dot'}},
  {x:SNOWLINES.map(s=>s.yr),y:SNOWLINES.map(s=>s.mx),type:'scatter',mode:'lines',name:'Max',line:{color:'#6c8cff33',dash:'dot'},fill:'tonexty',fillcolor:'#6c8cff0d'}
],{...L,yaxis:{...L.yaxis,title:'Elevation (m)'},xaxis:{...L.xaxis,title:'Year'},legend:{bgcolor:'transparent'}},C);

// Area
Plotly.newPlot('chart-area',[
  {x:OUTLINE_AREAS.map(d=>d.yr),y:OUTLINE_AREAS.map(d=>d.a),type:'scatter',mode:'lines+markers',name:'Area',marker:{color:'#5eead4',size:10},line:{color:'#5eead4',width:2},fill:'tozeroy',fillcolor:'#5eead40d'}
],{...L,yaxis:{...L.yaxis,title:'Area (km\u00b2)',range:[37,41]},xaxis:{...L.xaxis,title:'Year'}},C);

// Posterior histograms
function postHist(id,key,label,color){
  Plotly.newPlot(id,[{x:POST.map(d=>d[key]),type:'histogram',nbinsx:20,marker:{color:color+'88',line:{color:color,width:1}}}],{...L,xaxis:{...L.xaxis,title:label},yaxis:{...L.yaxis,title:'Count'},title:{text:label,font:{size:13,color:'#a0a4b8'}}},C);
}
postHist('chart-post-mf','MF','MF (mm/d/K)','#6c8cff');
postHist('chart-post-pc','PC','precip_corr','#5eead4');
postHist('chart-post-rs','RS','r_snow','#f59e0b');
postHist('chart-post-mg','MG','MF_grad','#ef4444');

// MF vs precip_corr scatter
Plotly.newPlot('chart-post-scatter',[{x:POST.map(d=>d.MF),y:POST.map(d=>d.PC),mode:'markers',type:'scatter',marker:{color:POST.map(d=>d.RS),colorscale:'Viridis',size:6,showscale:true,colorbar:{title:'r_snow',titlefont:{size:11}}}}],{...L,xaxis:{...L.xaxis,title:'MF'},yaxis:{...L.yaxis,title:'precip_corr'},title:{text:'MF vs precip_corr (color = r_snow)',font:{size:13,color:'#a0a4b8'}}},C);

},400);

// MathJax
setTimeout(()=>{if(window.MathJax&&MathJax.typesetPromise)MathJax.typesetPromise();},500);
