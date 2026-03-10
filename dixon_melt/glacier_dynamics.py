"""
Glacier geometry evolution using the delta-h parameterization.

Implements Huss et al. (2010): empirical redistribution of mass change
across the glacier hypsometry. Thinning is greatest at the terminus and
decreases toward the headwall.  Size-class-dependent coefficients switch
dynamically as the glacier shrinks.

Ice thickness can be:
  (a) loaded from Farinotti et al. (2019) consensus GeoTIFF, or
  (b) estimated from Bahr et al. (1997) volume-area scaling distributed
      by a standard hypsometric shape.

References
----------
Huss, M., Jouvet, G., Farinotti, D., & Bauder, A. (2010). Future
    high-mountain hydrology: a new parameterization of glacier retreat.
    Hydrol. Earth Syst. Sci., 14(5), 815-829.
Bahr, D. B., Meier, M. F., & Peckham, S. D. (1997). The physical basis
    of glacier volume-area scaling. J. Geophys. Res., 102(B9), 20355-20362.
Farinotti, D. et al. (2019). A consensus estimate for the ice thickness
    distribution of all glaciers on Earth. Nature Geosci., 12, 168-173.
"""
import numpy as np
from numba import njit, prange
from . import config


# ── Ice thickness initialization ──────────────────────────────────────

def load_farinotti_thickness(tif_path, dem_info):
    """Load Farinotti et al. (2019) consensus ice thickness and resample
    to the model DEM grid.

    Parameters
    ----------
    tif_path : str, path to the consensus thickness GeoTIFF
    dem_info : dict from terrain.load_and_reproject_dem() — must contain
               transform, nrows, ncols, epsg

    Returns
    -------
    thickness : 2D array (m), ice thickness on the model grid
    """
    import rasterio
    from rasterio.warp import reproject, Resampling

    dst_crs = f"EPSG:{dem_info['epsg']}"

    with rasterio.open(tif_path) as src:
        thickness = np.zeros((dem_info['nrows'], dem_info['ncols']),
                             dtype=np.float64)
        reproject(
            source=rasterio.band(src, 1),
            destination=thickness,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dem_info['transform'],
            dst_crs=dst_crs,
            resampling=Resampling.bilinear,
        )

    # Clean up: NaN/nodata → 0, negatives → 0
    thickness = np.nan_to_num(thickness, nan=0.0)
    thickness[thickness < 0] = 0.0

    return thickness


def estimate_thickness_va(elevation, glacier_mask, cell_size):
    """Estimate ice thickness from volume-area scaling + hypsometric
    distribution.

    Uses Bahr et al. (1997) / Chen & Ohmura (1990):
        V = c * A^gamma

    Thickness is distributed proportional to a parabolic cross-section
    pattern: thickest at mid-elevation, thinning toward terminus and
    headwall.  Normalized so total volume matches V-A prediction.

    Parameters
    ----------
    elevation : 2D array (m)
    glacier_mask : 2D bool array
    cell_size : float (m)

    Returns
    -------
    thickness : 2D array (m), estimated ice thickness
    """
    n_glacier = int(glacier_mask.sum())
    if n_glacier == 0:
        return np.zeros_like(elevation)

    area_km2 = n_glacier * cell_size**2 / 1e6
    volume_km3 = config.VA_C * area_km2 ** config.VA_GAMMA
    mean_thickness_m = volume_km3 * 1e9 / (area_km2 * 1e6)  # km3→m3 / m2

    glacier_elevs = elevation[glacier_mask]
    z_min = glacier_elevs.min()
    z_max = glacier_elevs.max()
    z_range = max(z_max - z_min, 1.0)

    thickness = np.zeros_like(elevation)
    for i in range(elevation.shape[0]):
        for j in range(elevation.shape[1]):
            if glacier_mask[i, j]:
                z_norm = (elevation[i, j] - z_min) / z_range
                # Parabolic: thickest at ~0.4 of elevation range (slightly
                # below center, realistic for valley glaciers)
                h_shape = np.sqrt(max(z_norm * (1.4 - z_norm), 0.0))
                thickness[i, j] = h_shape

    # Normalize to match V-A total volume
    shape_sum = thickness[glacier_mask].sum()
    if shape_sum > 0:
        scale = mean_thickness_m * n_glacier / shape_sum
        thickness[glacier_mask] *= scale

    return thickness


def initialize_ice_thickness(grid, farinotti_path=None):
    """Initialize ice thickness, preferring Farinotti data if available.

    Parameters
    ----------
    grid : dict from terrain.prepare_grid()
    farinotti_path : str or None, path to Farinotti GeoTIFF

    Returns
    -------
    thickness : 2D array (m)
    source : str, 'farinotti' or 'va_scaling'
    """
    if farinotti_path is not None:
        from pathlib import Path
        if Path(farinotti_path).exists():
            thickness = load_farinotti_thickness(farinotti_path, grid)
            # Ensure thickness is zero outside glacier mask
            thickness[~grid['glacier_mask']] = 0.0
            if thickness[grid['glacier_mask']].sum() > 0:
                # Fill glacier cells with zero thickness (resampling edge
                # effects) using the mean of their non-zero neighbors, or
                # a minimum of 1m so they aren't immediately deglaciated.
                mask = grid['glacier_mask']
                zero_on_glacier = mask & (thickness <= 0)
                n_zero = int(zero_on_glacier.sum())
                if n_zero > 0:
                    glacier_mean = thickness[mask & (thickness > 0)].mean()
                    thickness[zero_on_glacier] = max(glacier_mean * 0.1, 1.0)
                return thickness, 'farinotti'

    thickness = estimate_thickness_va(
        grid['elevation'], grid['glacier_mask'], grid['cell_size'])
    return thickness, 'va_scaling'


def compute_bedrock(surface_elevation, ice_thickness):
    """Compute bedrock DEM = surface - ice thickness."""
    bedrock = surface_elevation.copy()
    ice_cells = ice_thickness > 0
    bedrock[ice_cells] -= ice_thickness[ice_cells]
    return bedrock


# ── Delta-h parameterization ─────────────────────────────────────────

def _select_size_class(area_km2):
    """Select Huss et al. (2010) size class from current glacier area."""
    lo, hi = config.DELTAH_AREA_THRESHOLDS
    if area_km2 < lo:
        return 'small'
    elif area_km2 < hi:
        return 'medium'
    else:
        return 'large'


@njit
def _deltah_pattern(h_r, gamma, a, b, c):
    """Normalized thinning at relative elevation h_r.

    Parameters
    ----------
    h_r : float, (z_max - z) / (z_max - z_min).  0 = headwall, 1 = terminus.
    gamma, a, b, c : Huss et al. (2010) coefficients for the size class.

    Returns
    -------
    float : relative thinning magnitude (larger = more thinning).
    """
    x = h_r + a
    val = x**gamma + b * x + c
    # Clip to [0, inf) — negative values (near headwall) mean no thinning
    if val < 0.0:
        val = 0.0
    return val


@njit(parallel=True)
def _apply_deltah_kernel(
    elevation, glacier_mask, ice_thickness, bedrock,
    annual_mb_mwe, gamma, a, b, c, nodata,
):
    """Apply one year of delta-h redistribution.

    Parameters
    ----------
    elevation : 2D, current surface DEM (m)
    glacier_mask : 2D bool
    ice_thickness : 2D (m), current thickness (updated in-place)
    bedrock : 2D (m), fixed bedrock DEM
    annual_mb_mwe : float, glacier-wide specific balance (m w.e., negative=loss)
    gamma, a, b, c : delta-h coefficients
    nodata : float

    Returns
    -------
    new_elevation : 2D (m)
    new_mask : 2D bool (cells removed where ice runs out)
    cells_removed : int
    """
    nrows, ncols = elevation.shape
    new_elev = elevation.copy()
    new_mask = glacier_mask.copy()

    if abs(annual_mb_mwe) < 1e-4:
        return new_elev, new_mask, 0

    # Find glacier elevation range
    z_min = 1e10
    z_max = -1e10
    n_glacier = 0
    for i in range(nrows):
        for j in range(ncols):
            if glacier_mask[i, j] and elevation[i, j] != nodata:
                z = elevation[i, j]
                if z < z_min:
                    z_min = z
                if z > z_max:
                    z_max = z
                n_glacier += 1

    if n_glacier == 0:
        return new_elev, new_mask, 0

    z_range = z_max - z_min
    if z_range < 1.0:
        z_range = 1.0

    # Pass 1: compute delta-h weights and their sum for normalization
    total_weight = 0.0
    for i in range(nrows):
        for j in range(ncols):
            if glacier_mask[i, j] and elevation[i, j] != nodata:
                # h_r: 0=headwall, 1=terminus (Huss convention)
                h_r = (z_max - elevation[i, j]) / z_range
                w = _deltah_pattern(h_r, gamma, a, b, c)
                total_weight += w

    if total_weight < 1e-10:
        return new_elev, new_mask, 0

    # Scale factor: convert m w.e. to ice-equivalent thickness change,
    # then distribute so total change across all cells matches the
    # glacier-wide balance.
    rho_ratio = 1000.0 / 900.0  # water→ice density
    total_dh_target = annual_mb_mwe * rho_ratio * n_glacier
    scale = total_dh_target / total_weight

    # Pass 2: apply elevation changes and check for deglaciation
    cells_removed = 0
    min_ice = 1.0  # m, remove cells thinner than this

    for i in prange(nrows):
        for j in range(ncols):
            if not glacier_mask[i, j] or elevation[i, j] == nodata:
                continue

            h_r = (z_max - elevation[i, j]) / z_range
            w = _deltah_pattern(h_r, gamma, a, b, c)
            dh = scale * w  # negative for mass loss

            # Update ice thickness
            new_thick = ice_thickness[i, j] + dh
            if new_thick < min_ice:
                # Ice is gone → expose bedrock, remove from glacier
                new_elev[i, j] = bedrock[i, j]
                ice_thickness[i, j] = 0.0
                new_mask[i, j] = False
                cells_removed += 1
            else:
                ice_thickness[i, j] = new_thick
                new_elev[i, j] = bedrock[i, j] + new_thick

    return new_elev, new_mask, cells_removed


def apply_deltah(elevation, glacier_mask, ice_thickness, bedrock,
                 annual_mb_mwe, cell_size, nodata=-9999.0):
    """Apply delta-h redistribution with size-class-aware coefficients.

    Parameters
    ----------
    elevation : 2D array, current surface DEM (m)
    glacier_mask : 2D bool array
    ice_thickness : 2D array (m), current thickness (MODIFIED IN PLACE)
    bedrock : 2D array (m), fixed bedrock surface
    annual_mb_mwe : float, glacier-wide specific balance (m w.e.)
    cell_size : float (m)
    nodata : float

    Returns
    -------
    new_elevation : 2D array
    new_mask : 2D bool array
    cells_removed : int
    """
    n_glacier = int(glacier_mask.sum())
    area_km2 = n_glacier * cell_size**2 / 1e6
    size_class = _select_size_class(area_km2)
    p = config.DELTAH_PARAMS[size_class]

    new_elev, new_mask, cells_removed = _apply_deltah_kernel(
        elevation, glacier_mask, ice_thickness, bedrock,
        annual_mb_mwe,
        p['gamma'], p['a'], p['b'], p['c'],
        nodata,
    )

    return new_elev, new_mask, cells_removed


# ── Volume-area consistency check ────────────────────────────────────

def va_check(area_km2, ice_thickness, glacier_mask, cell_size):
    """Compare modeled volume against Bahr et al. (1997) V-A scaling.

    Returns
    -------
    dict with model_volume_km3, va_volume_km3, ratio, warning (str or None)
    """
    model_vol_m3 = ice_thickness[glacier_mask].sum() * cell_size**2
    model_vol_km3 = model_vol_m3 / 1e9
    va_vol_km3 = config.VA_C * area_km2 ** config.VA_GAMMA

    ratio = model_vol_km3 / va_vol_km3 if va_vol_km3 > 0 else float('inf')

    warning = None
    if ratio < 0.3 or ratio > 3.0:
        warning = (f"V-A scaling mismatch: modeled {model_vol_km3:.3f} km3 vs "
                   f"V-A {va_vol_km3:.3f} km3 (ratio {ratio:.2f})")

    return {
        'model_volume_km3': model_vol_km3,
        'va_volume_km3': va_vol_km3,
        'ratio': ratio,
        'warning': warning,
    }


# ── Multi-year evolution ─────────────────────────────────────────────

def run_glacier_evolution(elevation, glacier_mask, ice_thickness, bedrock,
                          annual_balances, cell_size, nodata=-9999.0):
    """Run multi-year glacier geometry evolution with full tracking.

    Parameters
    ----------
    elevation : 2D array, initial surface DEM
    glacier_mask : 2D bool array, initial glacier extent
    ice_thickness : 2D array (m), initial thickness (will be copied)
    bedrock : 2D array (m), fixed bedrock DEM
    annual_balances : list of float, glacier-wide annual balance (m w.e.)
    cell_size : float, grid cell size (m)

    Returns
    -------
    history : dict of lists (year, area_km2, volume_km3, cum_mb_mwe,
              elev_range, n_cells, size_class, va_ratio)
    final_elevation : 2D array
    final_mask : 2D bool array
    final_thickness : 2D array
    """
    history = {
        'year': [],
        'area_km2': [],
        'volume_km3': [],
        'cum_mb_mwe': [],
        'mean_thickness_m': [],
        'elevation_range': [],
        'n_cells': [],
        'size_class': [],
        'va_ratio': [],
        'cells_removed': [],
    }

    current_elev = elevation.copy()
    current_mask = glacier_mask.copy()
    current_thick = ice_thickness.copy()
    cum_mb = 0.0

    for yr_idx, mb in enumerate(annual_balances):
        n_cells = int(current_mask.sum())
        area_km2 = n_cells * cell_size**2 / 1e6

        if n_cells == 0:
            history['year'].append(yr_idx)
            history['area_km2'].append(0.0)
            history['volume_km3'].append(0.0)
            history['cum_mb_mwe'].append(cum_mb)
            history['mean_thickness_m'].append(0.0)
            history['elevation_range'].append((0.0, 0.0))
            history['n_cells'].append(0)
            history['size_class'].append('gone')
            history['va_ratio'].append(0.0)
            history['cells_removed'].append(0)
            break

        glacier_elevs = current_elev[current_mask]
        elev_range = (float(glacier_elevs.min()), float(glacier_elevs.max()))

        glacier_thick = current_thick[current_mask]
        vol_m3 = glacier_thick.sum() * cell_size**2
        vol_km3 = vol_m3 / 1e9
        mean_thick = glacier_thick.mean()

        size_class = _select_size_class(area_km2)
        va = va_check(area_km2, current_thick, current_mask, cell_size)

        history['year'].append(yr_idx)
        history['area_km2'].append(area_km2)
        history['volume_km3'].append(vol_km3)
        history['cum_mb_mwe'].append(cum_mb)
        history['mean_thickness_m'].append(float(mean_thick))
        history['elevation_range'].append(elev_range)
        history['n_cells'].append(n_cells)
        history['size_class'].append(size_class)
        history['va_ratio'].append(va['ratio'])
        history['cells_removed'].append(0)

        # Apply delta-h
        current_elev, current_mask, removed = apply_deltah(
            current_elev, current_mask, current_thick, bedrock,
            mb, cell_size, nodata,
        )
        history['cells_removed'][-1] = removed
        cum_mb += mb

    return history, current_elev, current_mask, current_thick
