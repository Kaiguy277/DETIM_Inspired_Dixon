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
DIXON_AWS_ELEV = 804.0  # m, near ABL stake

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

# ── Ice dynamics (delta-h parameterization) ─────────────────────────
# Huss et al. (2010) empirical coefficients for normalized elevation change
# Pattern: most thinning at terminus, least at headwall
DELTAH_A = -0.30   # terminus exponent
DELTAH_B =  0.60   # mid-glacier
DELTAH_C =  0.09   # headwall

# ── Routing (linear reservoir) ──────────────────────────────────────
DEFAULT_ROUTING = dict(
    k_fast=0.3,       # fast reservoir coefficient (d-1)
    k_slow=0.05,      # slow reservoir coefficient (d-1)
    k_gw=0.01,        # groundwater reservoir coefficient (d-1)
    f_fast=0.6,       # fraction to fast reservoir
    f_slow=0.3,       # fraction to slow reservoir
    # f_gw = 1 - f_fast - f_slow
)
