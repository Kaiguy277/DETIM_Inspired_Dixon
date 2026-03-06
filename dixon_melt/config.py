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
SNOTEL_ELEV = 1230.0    # m, Nuka SNOTEL actual elevation
SNOTEL_LAT = 59.698     # from NRCS metadata
SNOTEL_LON = -150.712   # from NRCS metadata

# ── Dixon on-glacier AWS ────────────────────────────────────────────
DIXON_AWS_ELEV = 804.0  # m, near ABL stake

# ── Nuka → Dixon temperature transfer (D-007) ──────────────────────
# Statistical downscaling from off-glacier SNOTEL to on-glacier surface.
# T_glacier_ref = TRANSFER_ALPHA[month] * T_nuka + TRANSFER_BETA[month]
# Derived from 256-day overlap (2024-2025 summers). Months without data
# (Oct-Apr) use standard lapse rate equivalent (+2.77°C offset at 804m).
# See research_log/nuka_dixon_temperature_analysis.md
TRANSFER_ALPHA = np.array([
    1.0,    1.0,    1.0,    1.0,     # Jan-Apr: standard lapse
    0.667,  0.534,  0.574,  0.391,   # May-Aug: katabatic-corrected
    1.211,                            # Sep: transition
    1.0,    1.0,    1.0,             # Oct-Dec: standard lapse
])
TRANSFER_BETA = np.array([
    2.77,   2.77,   2.77,   2.77,    # Jan-Apr
   -2.77,  -1.27,  -1.29,   0.56,   # May-Aug
   -7.06,                            # Sep
    2.77,   2.77,   2.77,            # Oct-Dec
])

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
    internal_lapse=-5.5e-3,  # on-glacier lapse rate, C/m
    precip_grad=0.0005,  # fractional increase per meter elevation
    precip_corr=2.5,     # gauge undercatch + spatial transfer correction
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
