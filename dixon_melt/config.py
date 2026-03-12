"""
Dixon Glacier site-specific configuration and physical constants.
"""
import numpy as np

# ── Dixon Glacier location ──────────────────────────────────────────
LATITUDE = 59.66        # degrees N
LONGITUDE = -150.88     # degrees W (negative for west)
UTM_ZONE = 5            # UTM Zone 5N
UTM_EPSG = 32605        # EPSG:32605

# ── Elevation reference ─────────────────────────────────────────────
ELEV_MIN = 439.0        # m, approximate glacier terminus
ELEV_MAX = 1637.0       # m, approximate glacier headwall
GLACIER_AREA_KM2 = 40.1

# ── Climate station (Nuka SNOTEL, site 1037) ────────────────────────
SNOTEL_ELEV = 375.0     # m (1230 ft; D-013: NRCS reports in feet, not meters)
SNOTEL_LAT = 59.698     # from NRCS metadata
SNOTEL_LON = -150.712   # from NRCS metadata

# ── Dixon on-glacier AWS ────────────────────────────────────────────
DIXON_AWS_ELEV = 1078.0  # m, at ELA stake site (D-023: was incorrectly 804m/ABL)

# ── Temperature transfer (D-012) ─────────────────────────────────
# Identity transfer: use raw Nuka SNOTEL temperature at 1230m.
# The calibrated lapse rate handles elevation adjustment to each cell.
#
# Rationale (D-012): The statistical katabatic transfer (D-007, D-010)
# made on-glacier temperatures too cold for DETIM to generate observed
# summer melt. ABL summer mean was 2.4C, requiring MF > 19 mm/d/K.
# DETIM is designed for off-glacier index temperatures with MF absorbing
# the katabatic effect implicitly (Hock 1999). With identity transfer,
# standard lapse gives ABL summer ~10C → MF ~3.5 (literature range).
#
# The measured katabatic effect (-5.1C at ABL, R2=0.70) is real and should
# be discussed in the thesis as validation, not used for forcing.
TRANSFER_ALPHA = np.ones(12, dtype=np.float64)   # identity: T_ref = T_nuka
TRANSFER_BETA = np.zeros(12, dtype=np.float64)    # no offset

# ── Multi-station gap-filling (D-025) ──────────────────────────────
# Fill stations for Nuka SNOTEL temperature and precipitation gaps.
# Transfer coefficients computed by compute_transfer_coefficients.py.
SNOTEL_STATIONS = {
    'nuka': {
        'name': 'Nuka Glacier', 'site': 1037, 'elev_m': 375,
        'path': 'data/climate/nuka_snotel_full.csv',
    },
    'mfb': {
        'name': 'Middle Fork Bradley', 'site': 1064, 'elev_m': 701,
        'path': 'data/climate/snotel_stations/middle_fork_bradley_1064.csv',
    },
    'mcneil': {
        'name': 'McNeil Canyon', 'site': 1003, 'elev_m': 411,
        'path': 'data/climate/snotel_stations/mcneil_canyon_1003.csv',
    },
    'anchor': {
        'name': 'Anchor River Divide', 'site': 1062, 'elev_m': 503,
        'path': 'data/climate/snotel_stations/anchor_river_divide_1062.csv',
    },
    'kachemak': {
        'name': 'Kachemak Creek', 'site': 1063, 'elev_m': 503,
        'path': 'data/climate/snotel_stations/kachemak_creek_1063.csv',
    },
    'lower_kach': {
        'name': 'Lower Kachemak Ck', 'site': 1265, 'elev_m': 597,
        'path': 'data/climate/snotel_stations/lower_kachemak_1265.csv',
    },
}

# Cascade order for gap-filling (best predictor first)
TEMP_FILL_ORDER = ['mfb', 'mcneil', 'anchor', 'kachemak', 'lower_kach']
PRECIP_FILL_ORDER = ['mfb']

# Monthly reverse regression: T_nuka = slope * T_other + intercept
# Computed from overlapping valid days (compute_transfer_coefficients.py)
# Index: [Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec]
TEMP_TRANSFER_TO_NUKA = {
    'mfb': {
        'slopes': np.array([0.8687, 0.8431, 0.8167, 0.7163, 0.7189, 0.8206,
                            0.9550, 0.7823, 0.6566, 0.7137, 0.8023, 0.8181]),
        'intercepts': np.array([-0.25, -0.06, -0.16, +0.07, +0.99, +1.69,
                                +1.20, +3.41, +4.03, +1.94, +0.78, -0.04]),
    },
    'mcneil': {
        'slopes': np.array([0.8370, 0.8028, 0.8472, 0.7826, 0.8317, 1.0242,
                            1.0178, 0.8290, 0.7217, 0.8086, 0.8070, 0.7654]),
        'intercepts': np.array([+0.02, -0.37, -0.62, -0.82, -0.82, -1.46,
                                -0.75, +1.80, +2.38, +1.13, +0.70, +0.18]),
    },
    'anchor': {
        'slopes': np.array([0.9010, 0.8414, 0.8275, 0.7528, 0.7203, 0.7722,
                            0.7478, 0.6671, 0.7055, 0.8049, 0.8706, 0.8699]),
        'intercepts': np.array([+0.82, +0.37, -0.26, -0.50, -0.03, +1.04,
                                +2.43, +3.59, +2.76, +1.79, +1.49, +1.24]),
    },
    'kachemak': {
        'slopes': np.array([0.8668, 0.8864, 0.9162, 0.5534, 0.7615, 0.9400,
                            0.9267, -0.0272, 0.3751, 0.8294, 0.7760, 0.7404]),
        'intercepts': np.array([-0.81, -0.91, -0.86, -0.52, -0.07, -0.08,
                                +0.49, +10.77, +4.83, +0.79, -0.37, -1.17]),
    },
    'lower_kach': {
        'slopes': np.array([0.8956, 0.8617, 0.8723, 0.7768, 0.8534, 0.8788,
                            0.8412, 0.8050, 0.8620, 0.8822, 0.9298, 0.9122]),
        'intercepts': np.array([-0.55, -0.57, -0.25, +0.19, +0.54, +1.45,
                                +2.32, +2.72, +1.83, +1.39, +0.60, -0.07]),
    },
}

# Monthly precipitation ratio: P_nuka = ratio * P_mfb
# Computed from wet-day pairs (both > 0.5mm) on overlapping days
PRECIP_RATIO_NUKA_OVER_MFB = np.array([
    1.636, 1.652, 1.701, 1.574, 2.196, 2.395,
    1.855, 2.030, 1.525, 1.457, 1.394, 1.611,
])

# Historical water year range for gap-filled output
HISTORICAL_WY_START = 1999
HISTORICAL_WY_END = 2025

# ── Wind redistribution (D-011) ───────────────────────────────────
# Prevailing wind during precipitation: ESE (~100 deg), from Gulf of
# Alaska storm analysis + snowline asymmetry (west side 100m lower).
# Sx parameter (Winstral et al. 2002) computed along upwind direction.
WIND_AZIMUTH = 100.0       # degrees CW from N, direction wind comes FROM
WIND_SEARCH_DIST = 300.0   # meters, max upwind search distance for Sx

# ── Stake locations ─────────────────────────────────────────────────
STAKE_NAMES = ['ABL', 'ELA', 'ACC']
STAKE_ELEVS = np.array([804.0, 1078.0, 1293.0])
STAKE_TOL = 50.0  # m, elevation tolerance for extracting stake values

# ── Default model parameters (calibration will tune these) ──────────
DEFAULT_PARAMS = dict(
    MF=4.0,              # melt factor, mm d-1 K-1
    MF_grad=-0.002,      # melt factor gradient, mm d-1 K-1 per m elevation
    r_snow=0.3e-3,       # radiation factor for snow, mm m2 W-1 d-1 K-1
    r_ice=0.6e-3,        # radiation factor for ice
    internal_lapse=-5.0e-3,  # lapse rate C/m, fixed D-015 (Gardner & Sharp 2009)
    precip_grad=0.0005,  # fractional increase per meter elevation
    precip_corr=2.0,     # gauge undercatch + spatial transfer (D-013: bounded 1.2-3.0)
    T0=1.5,              # rain/snow threshold temperature, C
)

# ── Physical constants ──────────────────────────────────────────────
SOLAR_CONSTANT = 1368.0     # W/m2
STANDARD_PRESSURE = 101325  # Pa
LATENT_HEAT_FUSION = 334000 # J/kg
WATER_DENSITY = 1000.0      # kg/m3
ICE_DENSITY = 900.0         # kg/m3

# ── Atmospheric transmissivity ──────────────────────────────────────
PSI_A = 0.75  # clear-sky atmospheric transmissivity (typical 0.6-0.9)

# ── Grid processing ─────────────────────────────────────────────────
TARGET_RESOLUTION = 50.0  # m, resample DEM to this for model runs
NODATA = -9999.0

# ── RGI Identifiers ───────────────────────────────────────────────
RGI6_ID = 'RGI60-01.18059'
RGI7_ID = 'RGI2000-v7.0-G-01-07538'

# ── Ice dynamics (delta-h parameterization) ─────────────────────────
# Huss et al. (2010) HESS 14, 815-829, Figure 3b / Table equivalent.
# Equation: delta_h = (h_r + a)^gamma + b*(h_r + a) + c
# where h_r = (z_max - z) / (z_max - z_min), so h_r=0 at headwall, 1 at terminus.
# Pattern: most thinning at terminus, least at headwall.
# Coefficients by glacier size class:
DELTAH_PARAMS = {
    'large':  {'gamma': 6, 'a': -0.02, 'b': 0.12, 'c': 0.00},  # A > 20 km2
    'medium': {'gamma': 4, 'a': -0.05, 'b': 0.19, 'c': 0.01},  # 5 < A < 20 km2
    'small':  {'gamma': 2, 'a': -0.30, 'b': 0.60, 'c': 0.09},  # A < 5 km2
}
DELTAH_AREA_THRESHOLDS = (5.0, 20.0)  # km2, boundaries between size classes

# ── Volume-area scaling (Bahr et al. 1997; Chen & Ohmura 1990) ─────
# V [km3] = VA_C * A[km2]^VA_GAMMA  (mountain/valley glaciers)
VA_C = 0.0340
VA_GAMMA = 1.36

# ── Routing (linear reservoir) ──────────────────────────────────────
DEFAULT_ROUTING = dict(
    k_fast=0.3,       # fast reservoir coefficient (d-1)
    k_slow=0.05,      # slow reservoir coefficient (d-1)
    k_gw=0.01,        # groundwater reservoir coefficient (d-1)
    f_fast=0.6,       # fraction to fast reservoir
    f_slow=0.3,       # fraction to slow reservoir
    # f_gw = 1 - f_fast - f_slow
)
