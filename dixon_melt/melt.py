"""
DETIM core: Distributed Enhanced Temperature Index melt computation.

Method 2 from Hock (1999):
    M = (MF + r_snow/ice * I_pot) * T    if T > 0
    M = 0                                 if T <= 0

Where I_pot is potential clear-sky direct solar radiation on the slope.
"""
import numpy as np
from numba import njit, prange


@njit(parallel=True)
def compute_melt(
    T_grid, ipot, surface_type, MF, r_snow, r_ice, nodata, dt_days=1.0
):
    """Compute melt for every grid cell for one time step.

    Parameters
    ----------
    T_grid : 2D array
        Distributed air temperature (°C)
    ipot : 2D array
        Potential clear-sky direct radiation on the slope (W/m²),
        averaged over the time step
    surface_type : 2D int array
        0 = off-glacier/nodata, 1 = snow, 2 = firn, 3 = ice
    MF : float
        Melt factor (mm d⁻¹ K⁻¹)
    r_snow : float
        Radiation factor for snow (mm m² W⁻¹ d⁻¹ K⁻¹)
    r_ice : float
        Radiation factor for ice (mm m² W⁻¹ d⁻¹ K⁻¹)
    nodata : float
    dt_days : float
        Length of time step in days (1.0 for daily, 1/24 for hourly)

    Returns
    -------
    melt : 2D array (mm w.e. / timestep)
    """
    nrows, ncols = T_grid.shape
    melt = np.zeros((nrows, ncols), dtype=np.float64)

    for i in prange(nrows):
        for j in range(ncols):
            if T_grid[i, j] == nodata or surface_type[i, j] == 0:
                continue

            T = T_grid[i, j]
            if T <= 0.0:
                continue

            I = ipot[i, j]
            stype = surface_type[i, j]

            # Select radiation factor based on surface type
            if stype == 1:       # snow
                r = r_snow
            elif stype == 2:     # firn (use snow factor)
                r = r_snow
            else:                # ice
                r = r_ice

            # DETIM Method 2: M = (MF + r * I_pot) * T * dt
            M = (MF + r * I) * T * dt_days
            melt[i, j] = max(M, 0.0)

    return melt
