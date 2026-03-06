"""
Snow water equivalent tracking and surface type determination.

Surface types:
    0 = off-glacier / nodata
    1 = snow
    2 = firn
    3 = ice
"""
import numpy as np
from numba import njit, prange


@njit(parallel=True)
def update_snowpack(swe, snowfall, melt, glacier_mask, firn_mask, nodata_elev, elevation):
    """Update snow water equivalent and determine surface type.

    Parameters
    ----------
    swe : 2D array
        Current snow water equivalent (mm w.e.). Modified in-place.
    snowfall : 2D array
        Snowfall this time step (mm w.e.)
    melt : 2D array
        Melt this time step (mm w.e.)
    glacier_mask : 2D bool array
        True where glacier exists
    firn_mask : 2D bool array
        True where firn zone (above approximate ELA)
    nodata_elev : float
    elevation : 2D array

    Returns
    -------
    surface_type : 2D int array
    ice_melt : 2D array (mm w.e.) - melt that came from ice (after snow depleted)
    snow_melt : 2D array (mm w.e.) - melt that came from snow
    """
    nrows, ncols = swe.shape
    surface_type = np.zeros((nrows, ncols), dtype=np.int32)
    ice_melt = np.zeros((nrows, ncols), dtype=np.float64)
    snow_melt = np.zeros((nrows, ncols), dtype=np.float64)

    for i in prange(nrows):
        for j in range(ncols):
            if elevation[i, j] == nodata_elev or not glacier_mask[i, j]:
                surface_type[i, j] = 0
                continue

            # Add snowfall
            swe[i, j] += snowfall[i, j]

            # Apply melt
            melt_remaining = melt[i, j]

            # First melt snow
            if swe[i, j] > 0 and melt_remaining > 0:
                snow_melted = min(swe[i, j], melt_remaining)
                swe[i, j] -= snow_melted
                melt_remaining -= snow_melted
                snow_melt[i, j] = snow_melted

            # Remaining melt goes to ice/firn
            if melt_remaining > 0:
                ice_melt[i, j] = melt_remaining

            # Determine surface type
            if swe[i, j] > 0:
                surface_type[i, j] = 1  # snow
            elif firn_mask[i, j]:
                surface_type[i, j] = 2  # firn
            else:
                surface_type[i, j] = 3  # ice

    return surface_type, ice_melt, snow_melt


def initialize_swe(elevation, glacier_mask, winter_precip_total, precip_grad,
                    station_elev, T0_elev=None):
    """Create initial SWE grid based on an elevation-dependent gradient.

    Simple approach: assume all winter precip above T0_elev fell as snow,
    scaled by the precip gradient.
    """
    swe = np.zeros_like(elevation)

    if T0_elev is None:
        T0_elev = station_elev

    for i in range(elevation.shape[0]):
        for j in range(elevation.shape[1]):
            if not glacier_mask[i, j]:
                continue
            dz = elevation[i, j] - station_elev
            scaling = 1.0 + precip_grad * dz
            swe[i, j] = max(winter_precip_total * scaling, 0.0)

    return swe
