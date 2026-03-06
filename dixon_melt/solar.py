"""
Solar geometry and potential clear-sky direct radiation.

Implements Oke (1987) solar geometry and the topographic correction
from Hock (1999) as described in the DEBAM/DETIM model manual.
All angles in radians internally, degrees at the interface.
"""
import numpy as np
from numba import njit, prange
from . import config


@njit
def declination(doy):
    """Solar declination (radians) from day of year."""
    return -23.4 * np.cos(np.radians(360.0 * (doy + 10) / 365.0)) * np.pi / 180.0


@njit
def hour_angle(solar_hour):
    """Hour angle (radians). solar_hour is local apparent solar time."""
    return (12.0 - solar_hour) * 15.0 * np.pi / 180.0


@njit
def earth_sun_distance_factor(doy):
    """Squared ratio (r_m/r)^2 of mean to actual earth-sun distance."""
    theta = 2.0 * np.pi * doy / 365.0
    return (1.000110 + 0.034221 * np.cos(theta) + 0.001280 * np.sin(theta)
            + 0.000719 * np.cos(2 * theta) + 0.000077 * np.sin(2 * theta))


@njit
def cos_zenith(lat_rad, decl, h):
    """Cosine of solar zenith angle."""
    return (np.sin(lat_rad) * np.sin(decl)
            + np.cos(lat_rad) * np.cos(decl) * np.cos(h))


@njit
def solar_azimuth(lat_rad, decl, h, cos_z, sin_z):
    """Solar azimuth angle (radians from north, clockwise)."""
    if sin_z == 0:
        return 0.0
    cos_az = (np.sin(decl) * np.cos(lat_rad)
              - np.cos(decl) * np.sin(lat_rad) * np.cos(h)) / sin_z
    cos_az = max(-1.0, min(1.0, cos_az))
    az = np.arccos(cos_az)
    # Afternoon: azimuth > 180 (hour angle < 0 means afternoon)
    if h < 0:
        az = 2.0 * np.pi - az
    return az


@njit
def cos_incidence(slope_rad, aspect_rad, zenith_rad, azimuth_rad):
    """Cosine of angle of incidence on a tilted surface.

    aspect_rad: slope azimuth (radians from north, clockwise).
    """
    cos_z = np.cos(zenith_rad)
    sin_z = np.sin(zenith_rad)
    return (np.cos(slope_rad) * cos_z
            + np.sin(slope_rad) * sin_z * np.cos(azimuth_rad - aspect_rad))


@njit
def pressure_from_elevation(elev):
    """Atmospheric pressure (Pa) from elevation (m)."""
    return config.STANDARD_PRESSURE * np.exp(-0.0001184 * elev)


@njit
def potential_direct_radiation_horizontal(doy, solar_hour, lat_deg, elev):
    """Potential clear-sky direct solar radiation on a horizontal surface (W/m²).

    Implements I = I₀ * (r_m/r)² * ψ_a^(P/P₀/cos Z) * cos Z
    """
    lat_rad = lat_deg * np.pi / 180.0
    decl = declination(doy)
    h = hour_angle(solar_hour)
    cz = cos_zenith(lat_rad, decl, h)

    if cz <= 0:
        return 0.0

    r2 = earth_sun_distance_factor(doy)
    p = pressure_from_elevation(elev)
    p_ratio = p / config.STANDARD_PRESSURE

    # Transmissivity exponent: P/P₀ / cos(Z)
    exponent = p_ratio / cz
    I_horiz = config.SOLAR_CONSTANT * r2 * (config.PSI_A ** exponent) * cz

    return max(I_horiz, 0.0)


@njit
def topographic_correction(slope_rad, aspect_rad, zenith_rad, azimuth_rad):
    """Topographic correction factor cos(Θ)/cos(Z).

    Returns the ratio that converts horizontal radiation to slope radiation.
    Capped at 5 (zenith > 78°) per the manual. Returns 0 if shaded.
    """
    cos_z = np.cos(zenith_rad)
    if cos_z <= 0:
        return 0.0

    cos_theta = cos_incidence(slope_rad, aspect_rad, zenith_rad, azimuth_rad)

    if cos_theta <= 0:
        return 0.0  # self-shading

    ratio = cos_theta / cos_z
    return min(ratio, 5.0)


@njit(parallel=True)
def compute_ipot_grid(doy, solar_hour, lat_deg, elevation, slope, aspect):
    """Compute potential clear-sky direct radiation for entire grid.

    Parameters
    ----------
    doy : int
    solar_hour : float
    lat_deg : float
    elevation : 2D array (m)
    slope : 2D array (radians)
    aspect : 2D array (radians, from north clockwise)

    Returns
    -------
    ipot : 2D array (W/m²) - potential direct radiation on the slope
    """
    nrows, ncols = elevation.shape
    ipot = np.zeros((nrows, ncols), dtype=np.float64)

    lat_rad = lat_deg * np.pi / 180.0
    decl = declination(doy)
    h = hour_angle(solar_hour)
    cz = cos_zenith(lat_rad, decl, h)

    if cz <= 0:
        return ipot

    sin_z = np.sqrt(1.0 - cz * cz)
    zenith_rad = np.arccos(max(-1.0, min(1.0, cz)))
    azimuth_rad = solar_azimuth(lat_rad, decl, h, cz, sin_z)
    r2 = earth_sun_distance_factor(doy)

    for i in prange(nrows):
        for j in range(ncols):
            elev = elevation[i, j]
            if elev == config.NODATA:
                ipot[i, j] = 0.0
                continue

            p = pressure_from_elevation(elev)
            p_ratio = p / config.STANDARD_PRESSURE
            exponent = p_ratio / cz
            I_horiz = config.SOLAR_CONSTANT * r2 * (config.PSI_A ** exponent) * cz

            # Topographic correction
            corr = topographic_correction(
                slope[i, j], aspect[i, j], zenith_rad, azimuth_rad
            )
            ipot[i, j] = I_horiz * corr

    return ipot


def compute_daily_ipot(doy, lat_deg, elevation, slope, aspect, dt_hours=1.0):
    """Compute daily-integrated potential direct radiation (W/m² * hours → MJ/m²/day).

    Averages over all hours of the day. Returns mean W/m² over 24h (equivalent to
    the daily total energy / 24).
    """
    n_steps = int(24.0 / dt_hours)
    nrows, ncols = elevation.shape
    ipot_sum = np.zeros((nrows, ncols), dtype=np.float64)

    for step in range(n_steps):
        solar_hour = dt_hours * (step + 0.5)
        ipot = compute_ipot_grid(doy, solar_hour, lat_deg, elevation, slope, aspect)
        ipot_sum += ipot

    return ipot_sum / n_steps
