"""
Glacier geometry evolution using the delta-h parameterization.

Implements Huss et al. (2010): empirical redistribution of mass change
across the glacier hypsometry. Thinning is greatest at the terminus and
decreases toward the headwall.

Reference: Huss, M., Jouvet, G., Farinotti, D., & Bauder, A. (2010).
Future high-mountain hydrology: a new parameterization of glacier retreat.
Hydrology and Earth System Sciences, 14(5), 815-829.
"""
import numpy as np
from numba import njit


@njit
def compute_deltah_curve(elevation, glacier_mask, nodata=-9999.0):
    """Compute the normalized delta-h curve for current glacier geometry.

    Returns normalized elevations (0=terminus, 1=headwall) and the
    empirical thinning pattern.
    """
    # Find glacier elevation range
    z_min = 1e10
    z_max = -1e10
    for i in range(elevation.shape[0]):
        for j in range(elevation.shape[1]):
            if glacier_mask[i, j] and elevation[i, j] != nodata:
                if elevation[i, j] < z_min:
                    z_min = elevation[i, j]
                if elevation[i, j] > z_max:
                    z_max = elevation[i, j]

    z_range = z_max - z_min
    if z_range < 1.0:
        z_range = 1.0

    return z_min, z_max, z_range


@njit
def deltah_pattern(z_norm):
    """Empirical delta-h thinning pattern (Huss et al. 2010, curve type 3).

    Parameters
    ----------
    z_norm : float, normalized elevation (0=terminus, 1=headwall)

    Returns
    -------
    float : relative thinning (larger magnitude = more thinning)
    """
    # Polynomial fit for mountain glacier type
    # dh_norm = (z_norm + a)^6 + b*(z_norm + a) + c
    a = -0.30
    b = 0.60
    c = 0.09
    x = z_norm + a
    return x**6 + b * x + c


@njit
def apply_deltah(elevation, glacier_mask, annual_mb_mwe, nodata=-9999.0):
    """Apply delta-h redistribution of mass change to the DEM.

    Parameters
    ----------
    elevation : 2D array, current DEM (m)
    glacier_mask : 2D bool array
    annual_mb_mwe : float, glacier-wide specific mass balance (m w.e.)
        Negative = mass loss → surface lowering

    Returns
    -------
    new_elevation : 2D array, updated DEM
    new_mask : 2D bool array, updated glacier mask (cells removed if too thin)
    area_change_km2 : float, area lost (negative) or gained
    """
    nrows, ncols = elevation.shape
    new_elev = elevation.copy()
    new_mask = glacier_mask.copy()

    if abs(annual_mb_mwe) < 0.001:
        return new_elev, new_mask, 0.0

    z_min, z_max, z_range = compute_deltah_curve(elevation, glacier_mask, nodata)

    # Compute delta-h weights for each glacier cell
    # and normalize so total mass change = annual_mb_mwe * area
    total_weight = 0.0
    n_glacier = 0
    for i in range(nrows):
        for j in range(ncols):
            if glacier_mask[i, j] and elevation[i, j] != nodata:
                z_norm = (elevation[i, j] - z_min) / z_range
                w = deltah_pattern(z_norm)
                total_weight += w
                n_glacier += 1

    if total_weight == 0 or n_glacier == 0:
        return new_elev, new_mask, 0.0

    # Scale factor: total dh should equal annual_mb_mwe * n_cells
    # (each cell represents 1 unit area)
    # annual_mb_mwe is in m w.e.; convert to ice thickness change
    # dh_ice = mb_mwe * rho_water / rho_ice = mb_mwe * 1000/900
    rho_ratio = 1000.0 / 900.0
    total_dh_target = annual_mb_mwe * rho_ratio * n_glacier
    scale = total_dh_target / total_weight

    # Apply elevation changes and update mask
    cells_removed = 0
    min_thickness = 5.0  # m, remove cells thinner than this

    for i in range(nrows):
        for j in range(ncols):
            if glacier_mask[i, j] and elevation[i, j] != nodata:
                z_norm = (elevation[i, j] - z_min) / z_range
                w = deltah_pattern(z_norm)
                dh = scale * w

                new_elev[i, j] = elevation[i, j] + dh

                # Remove cells where surface drops below bedrock estimate
                # Simple heuristic: if cumulative lowering puts cell near
                # original minimum, it's likely exposing bedrock
                if dh < 0 and z_norm < 0.1 and abs(dh) > min_thickness:
                    new_mask[i, j] = False
                    cells_removed += 1

    return new_elev, new_mask, -cells_removed


def run_glacier_evolution(elevation, glacier_mask, annual_balances, cell_size,
                          nodata=-9999.0):
    """Run multi-year glacier geometry evolution.

    Parameters
    ----------
    elevation : 2D array, initial DEM
    glacier_mask : 2D bool array, initial glacier extent
    annual_balances : list of float, glacier-wide annual balance (m w.e.)
    cell_size : float, grid cell size (m)

    Returns
    -------
    dict with yearly snapshots of area, volume change, ELA estimate
    """
    history = {
        'year': [],
        'area_km2': [],
        'cum_mb_mwe': [],
        'elevation_range': [],
        'n_cells': [],
    }

    current_elev = elevation.copy()
    current_mask = glacier_mask.copy()
    cum_mb = 0.0

    for yr_idx, mb in enumerate(annual_balances):
        n_cells = int(current_mask.sum())
        area = n_cells * cell_size**2 / 1e6

        glacier_elevs = current_elev[current_mask]
        if len(glacier_elevs) > 0:
            elev_range = (float(glacier_elevs.min()), float(glacier_elevs.max()))
        else:
            elev_range = (0.0, 0.0)

        history['year'].append(yr_idx)
        history['area_km2'].append(area)
        history['cum_mb_mwe'].append(cum_mb)
        history['elevation_range'].append(elev_range)
        history['n_cells'].append(n_cells)

        if n_cells == 0:
            break

        # Apply delta-h
        current_elev, current_mask, _ = apply_deltah(
            current_elev, current_mask, mb, nodata
        )
        cum_mb += mb

    return history, current_elev, current_mask
