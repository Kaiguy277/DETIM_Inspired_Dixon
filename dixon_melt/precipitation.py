"""
Precipitation distribution: elevation gradient, rain/snow partitioning.
"""
import numpy as np
from numba import njit, prange


@njit(parallel=True)
def distribute_precipitation(
    precip_station, T_grid, elevation, station_elev,
    precip_grad, precip_corr, T0, nodata
):
    """Distribute precipitation across the grid and partition into rain/snow.

    Parameters
    ----------
    precip_station : float
        Measured precipitation at climate station (mm/timestep)
    T_grid : 2D array
        Distributed temperature (°C)
    elevation : 2D array
        Grid elevations (m)
    station_elev : float
        Climate station elevation (m)
    precip_grad : float
        Fractional increase per meter elevation (e.g. 0.0005 = 0.05%/m)
    precip_corr : float
        Gauge undercatch correction factor
    T0 : float
        Rain/snow threshold temperature (°C)
    nodata : float

    Returns
    -------
    snowfall : 2D array (mm w.e. / timestep)
    rainfall : 2D array (mm w.e. / timestep)
    """
    nrows, ncols = T_grid.shape
    snowfall = np.zeros((nrows, ncols), dtype=np.float64)
    rainfall = np.zeros((nrows, ncols), dtype=np.float64)

    corrected = precip_station * precip_corr

    for i in prange(nrows):
        for j in range(ncols):
            if elevation[i, j] == nodata:
                continue

            dz = elevation[i, j] - station_elev
            # Elevation scaling
            P = corrected * (1.0 + precip_grad * dz)
            P = max(P, 0.0)

            T = T_grid[i, j]

            # Rain/snow partitioning with 2°C linear transition around T0
            if T <= T0 - 1.0:
                snow_frac = 1.0
            elif T >= T0 + 1.0:
                snow_frac = 0.0
            else:
                snow_frac = 0.5 * (T0 + 1.0 - T)

            snowfall[i, j] = P * snow_frac
            rainfall[i, j] = P * (1.0 - snow_frac)

    return snowfall, rainfall
