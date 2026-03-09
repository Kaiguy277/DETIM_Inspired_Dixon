"""
DEM loading, reprojection, slope/aspect computation, and glacier mask generation.
Uses rasterio (already installed) instead of GDAL Python bindings.
"""
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.features import rasterize
from rasterio.transform import from_bounds
import json
from . import config


def load_and_reproject_dem(dem_path, target_res=None, target_epsg=None):
    """Load a DEM, reproject to UTM, and resample to target resolution.

    Returns
    -------
    dict with keys: elevation, transform, crs, shape, res, bounds
    """
    if target_res is None:
        target_res = config.TARGET_RESOLUTION
    if target_epsg is None:
        target_epsg = config.UTM_EPSG

    dst_crs = f'EPSG:{target_epsg}'

    with rasterio.open(dem_path) as src:
        # Calculate the transform for the target CRS and resolution
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs,
            src.width, src.height,
            *src.bounds,
            resolution=target_res,
        )

        elevation = np.empty((height, width), dtype=np.float64)

        reproject(
            source=rasterio.band(src, 1),
            destination=elevation,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=dst_crs,
            resampling=Resampling.bilinear,
        )

    return dict(
        elevation=elevation,
        transform=transform,
        x_origin=transform.c,
        y_origin=transform.f,
        res_x=transform.a,
        res_y=transform.e,  # negative
        nrows=height,
        ncols=width,
        epsg=target_epsg,
    )


def compute_slope_aspect(elevation, cell_size):
    """Compute slope (radians) and aspect (radians, clockwise from north) from DEM."""
    dy, dx = np.gradient(elevation, cell_size)
    # Rows go top-to-bottom so dy is dz/d(south), flip for geographic north
    dy = -dy

    slope = np.arctan(np.sqrt(dx**2 + dy**2))

    # Aspect: clockwise from north. atan2(dx, dy) = angle from north
    aspect = np.arctan2(dx, dy)
    aspect = np.where(aspect < 0, aspect + 2 * np.pi, aspect)

    flat = slope < 1e-6
    aspect[flat] = 0.0

    return slope, aspect


def load_glacier_outline_mask(geojson_path, dem_info):
    """Rasterize glacier outline to match DEM grid.

    Returns boolean mask (True = glacier).
    """
    with open(geojson_path) as f:
        gj = json.load(f)

    # Extract geometry/geometries
    geometries = []
    if gj['type'] == 'FeatureCollection':
        for feat in gj['features']:
            geometries.append(feat['geometry'])
    elif gj['type'] == 'Feature':
        geometries.append(gj['geometry'])
    else:
        geometries.append(gj)

    # The GeoJSON is likely in EPSG:4326 — we need to reproject to UTM
    from rasterio.warp import transform_geom
    src_crs = 'EPSG:4326'
    dst_crs = f"EPSG:{dem_info['epsg']}"

    reprojected = []
    for geom in geometries:
        rg = transform_geom(src_crs, dst_crs, geom)
        reprojected.append((rg, 1))

    # Rasterize
    mask = rasterize(
        reprojected,
        out_shape=(dem_info['nrows'], dem_info['ncols']),
        transform=dem_info['transform'],
        fill=0,
        dtype=np.uint8,
    )

    return mask.astype(bool)


def compute_wind_exposure(elevation, cell_size, wind_azimuth_deg, d_max=300.0):
    """Compute Winstral et al. (2002) Sx wind exposure parameter.

    Sx(i,j) = max angle to the horizon along the upwind direction, searched
    up to d_max meters.  Positive Sx = sheltered (lee), negative = exposed.

    Parameters
    ----------
    elevation : 2D array (m)
    cell_size : float (m)
    wind_azimuth_deg : float, direction wind comes FROM (degrees CW from N)
    d_max : float, maximum search distance (m)

    Returns
    -------
    sx : 2D array, same shape as elevation.  Positive = sheltered, negative = exposed.
    """
    nrows, ncols = elevation.shape
    sx = np.full((nrows, ncols), -90.0, dtype=np.float64)

    # Direction the wind blows FROM → upwind search vector
    az_rad = np.radians(wind_azimuth_deg)
    # Step in row/col: wind from N (0°) means search upward (negative row)
    dr = -np.cos(az_rad)  # row increment per meter
    dc = np.sin(az_rad)   # col increment per meter

    n_steps = int(d_max / cell_size) + 1

    for i in range(nrows):
        for j in range(ncols):
            z0 = elevation[i, j]
            if z0 <= 0 or z0 > 5000:
                sx[i, j] = 0.0
                continue
            max_angle = -90.0
            for s in range(1, n_steps + 1):
                dist = s * cell_size
                ri = int(round(i + dr * dist / cell_size))
                ci = int(round(j + dc * dist / cell_size))
                if ri < 0 or ri >= nrows or ci < 0 or ci >= ncols:
                    break
                zt = elevation[ri, ci]
                if zt <= 0 or zt > 5000:
                    continue
                angle = np.degrees(np.arctan2(zt - z0, dist))
                if angle > max_angle:
                    max_angle = angle
            sx[i, j] = max_angle

    return sx


def compute_wind_redistribution(sx, glacier_mask):
    """Convert Sx to a precipitation redistribution factor.

    D_wind(i,j) = 1 + k * Sx_normalized

    where Sx is normalized to [-1, +1] over glacier cells.
    Positive Sx (sheltered) → D > 1 (more snow).
    Negative Sx (exposed) → D < 1 (less snow).
    The factor is mass-conserving over the glacier: mean(D * area) = area.

    Returns
    -------
    sx_norm : 2D array, Sx normalized to approx [-1, +1] over glacier.
    """
    glacier_sx = sx[glacier_mask]
    if len(glacier_sx) == 0:
        return np.zeros_like(sx)

    # Normalize: divide by max absolute value so range is roughly [-1, 1]
    max_abs = np.maximum(np.abs(glacier_sx).max(), 1e-6)
    sx_norm = sx / max_abs

    # Zero-center over glacier (so mean redistribution = 0 → mass conserving)
    glacier_mean = sx_norm[glacier_mask].mean()
    sx_norm -= glacier_mean

    return sx_norm


def prepare_grid(dem_path, glacier_geojson_path, target_res=None):
    """Full grid preparation pipeline.

    Returns
    -------
    grid : dict with elevation, slope, aspect, glacier_mask, and metadata
    """
    dem_info = load_and_reproject_dem(dem_path, target_res=target_res)
    elev = dem_info['elevation']
    cell_size = abs(dem_info['res_x'])

    slope, aspect = compute_slope_aspect(elev, cell_size)

    # Mask invalid elevations
    bad = (elev <= 0) | (elev > 5000)
    elev[bad] = config.NODATA
    slope[bad] = 0.0
    aspect[bad] = 0.0

    glacier_mask = load_glacier_outline_mask(glacier_geojson_path, dem_info)

    # Ensure glacier cells have valid elevation
    glacier_mask = glacier_mask & (elev != config.NODATA)

    # Wind exposure (Sx) for snow redistribution
    sx = compute_wind_exposure(elev, cell_size, config.WIND_AZIMUTH,
                               d_max=config.WIND_SEARCH_DIST)
    sx_norm = compute_wind_redistribution(sx, glacier_mask)

    return dict(
        elevation=elev,
        slope=slope,
        aspect=aspect,
        glacier_mask=glacier_mask,
        sx_norm=sx_norm,
        cell_size=cell_size,
        **{k: v for k, v in dem_info.items() if k != 'elevation'},
    )
