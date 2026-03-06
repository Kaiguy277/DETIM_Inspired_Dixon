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

# ── Default model parameters (calibration will tune these) ──────────
DEFAULT_PARAMS = dict(
    # Melt parameters (Method 2: enhanced temperature index)
    MF=4.0,              # melt factor, mm d⁻¹ K⁻¹
    r_snow=0.3e-3,       # radiation factor for snow, mm m² W⁻¹ d⁻¹ K⁻¹
    r_ice=0.6e-3,        # radiation factor for ice, mm m² W⁻¹ d⁻¹ K⁻¹

    # Temperature
    lapse_rate=-6.5e-3,  # °C/m (negative: colder with elevation)

    # Precipitation
    precip_grad=0.0005,  # fractional increase per meter elevation
    precip_corr=1.2,     # gauge undercatch correction factor
    T0=1.5,              # rain/snow threshold temperature, °C

    # Initial snow water equivalent scaling
    snow_redist=1.0,     # snow redistribution factor
)

# ── Physical constants ──────────────────────────────────────────────
SOLAR_CONSTANT = 1368.0     # W/m², I₀
STANDARD_PRESSURE = 101325  # Pa, P₀
LATENT_HEAT_FUSION = 334000 # J/kg, Lf
WATER_DENSITY = 1000.0      # kg/m³
ICE_DENSITY = 900.0         # kg/m³

# ── Atmospheric transmissivity ──────────────────────────────────────
PSI_A = 0.75  # clear-sky atmospheric transmissivity (typical 0.6-0.9)

# ── Grid processing ─────────────────────────────────────────────────
TARGET_RESOLUTION = 50.0  # m, resample DEM to this for model runs
NODATA = -9999.0
