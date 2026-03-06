"""
Temperature distribution across the glacier grid via lapse rate.
"""
import numpy as np
from numba import njit, prange


@njit(parallel=True)
def distribute_temperature(T_station, station_elev, elevation, lapse_rate, nodata):
    """Extrapolate station temperature to every grid cell using a constant lapse rate.

    Parameters
    ----------
    T_station : float
        Temperature at the climate station (°C)
    station_elev : float
        Elevation of climate station (m)
    elevation : 2D array
        Grid elevations (m)
    lapse_rate : float
        Temperature lapse rate (°C/m), typically negative (e.g., -0.0065)
    nodata : float
        Nodata value in elevation grid

    Returns
    -------
    T_grid : 2D array (°C)
    """
    nrows, ncols = elevation.shape
    T_grid = np.empty((nrows, ncols), dtype=np.float64)

    for i in prange(nrows):
        for j in range(ncols):
            if elevation[i, j] == nodata:
                T_grid[i, j] = nodata
            else:
                dz = elevation[i, j] - station_elev
                T_grid[i, j] = T_station + lapse_rate * dz

    return T_grid


def positive_temperature(T_grid, nodata):
    """Return temperature clipped to >= 0 (for degree-day melt). NoData stays."""
    T_pos = np.where(T_grid == nodata, nodata, np.maximum(T_grid, 0.0))
    return T_pos
