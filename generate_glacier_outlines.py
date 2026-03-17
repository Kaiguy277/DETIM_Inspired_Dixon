"""
Generate multi-temporal glacier outlines for Dixon Glacier from satellite imagery.

Downloads Landsat (2000-2015) and Sentinel-2 (2020-2025) end-of-season imagery,
applies band ratio (Red/SWIR) glacier classification, and generates outlines.
The upper glacier boundary is held fixed from the RGI7 outline; only the terminus
and lateral margins are derived from satellite imagery.

Method: Red/SWIR band ratio (Paul et al. 2002, 2015) with threshold,
morphological cleanup, and RGI upper boundary constraint.

Usage:
    python generate_glacier_outlines.py
"""
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.features import rasterize, shapes
from rasterio.transform import from_bounds
from rasterio.mask import mask as rio_mask
import geopandas as gpd
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from pathlib import Path
import json
import planetary_computer
import pystac_client
from scipy import ndimage

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
RGI_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
OUT_DIR = PROJECT / 'data' / 'glacier_outlines'

# Dixon Glacier bounding box (WGS84) with buffer
BBOX = [-150.96, 59.60, -150.76, 59.71]

# Selected scenes: {year: (collection, scene_id)}
SCENES = {
    2000: ('landsat-c2-l2', 'LE07_L2SP_069018_20000809_02_T1'),
    2005: ('landsat-c2-l2', 'LT05_L2SP_068019_20050925_02_T1'),
    2010: ('landsat-c2-l2', 'LT05_L2SP_069018_20100829_02_T1'),
    2015: ('landsat-c2-l2', 'LC08_L2SP_068019_20150820_02_T1'),
    2020: ('sentinel-2-l2a', 'S2B_MSIL2A_20200911T212529_R043_T05VPG_20200913T062439'),
    2025: ('sentinel-2-l2a', 'S2C_MSIL2A_20250930T212541_R043_T05VPG_20250930T225512'),
}

# Band ratio threshold for glacier ice/snow (Paul et al. 2002)
# Red/SWIR > threshold → glacier
RATIO_THRESHOLD = 1.8

# Minimum glacier fragment size (pixels) to keep
MIN_FRAGMENT_PX = 50


def load_stac_item(collection, scene_id):
    """Load a STAC item from Planetary Computer."""
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )
    search = catalog.search(collections=[collection], ids=[scene_id])
    items = list(search.items())
    if not items:
        raise ValueError(f"Scene not found: {scene_id}")
    return items[0]


def read_band_windowed(item, band_name, bbox, target_crs='EPSG:32605'):
    """Read a single band from a STAC item, cropped to bbox, reprojected to UTM."""
    href = item.assets[band_name].href

    with rasterio.open(href) as src:
        # Transform bbox to source CRS
        from rasterio.warp import transform_bounds
        src_bounds = transform_bounds('EPSG:4326', src.crs, *bbox)

        # Create window from bounds
        window = src.window(*src_bounds)
        window = window.round_offsets().round_lengths()

        # Clamp window to dataset bounds
        window = window.intersection(rasterio.windows.Window(
            0, 0, src.width, src.height))

        data = src.read(1, window=window).astype(np.float32)
        win_transform = src.window_transform(window)

        # Handle nodata
        nodata = src.nodata
        if nodata is not None:
            data[data == nodata] = np.nan

        # For Landsat C2 L2 surface reflectance: scale and offset
        if 'landsat' in item.collection_id:
            # L2SP: SR = scale * pixel + offset
            # Scale: 0.0000275, Offset: -0.2
            data = data * 0.0000275 - 0.2
            data[data < 0] = np.nan
            data[data > 1] = np.nan

        # For Sentinel-2 L2A: DN / 10000
        if 'sentinel' in item.collection_id:
            data = data / 10000.0
            data[data < 0] = np.nan
            data[data > 1] = np.nan

        return data, win_transform, src.crs


def compute_glacier_mask(red, swir, green, threshold=RATIO_THRESHOLD):
    """Compute glacier mask using Red/SWIR band ratio.

    Glacier ice and snow have high reflectance in visible (red) and low
    in SWIR, giving high Red/SWIR ratio. Rock, debris, water have low ratio.

    Additional filters:
    - NDSI (green-SWIR)/(green+SWIR) to separate snow/ice from cloud
    - Red reflectance floor to exclude shadow/water
    - SWIR reflectance ceiling to exclude cloud (clouds bright in SWIR)

    Reference: Paul et al. (2002) Annals of Glaciology 34.
    """
    valid = np.isfinite(red) & np.isfinite(swir) & np.isfinite(green)

    # Band ratio
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = np.where((swir > 0) & valid, red / swir, 0)

    glacier = ratio > threshold

    # NDSI: snow/ice > ~0.4, clouds typically < 0.2
    with np.errstate(divide='ignore', invalid='ignore'):
        ndsi = np.where((green + swir) > 0, (green - swir) / (green + swir), 0)
    glacier = glacier & (ndsi > 0.4)

    # Exclude clouds: clouds are bright in SWIR (> 0.2 reflectance)
    # Snow/ice SWIR is typically < 0.15
    glacier = glacier & (swir < 0.25)

    # Exclude shadow/water: need minimum red reflectance
    glacier = glacier & (red > 0.05)

    # Valid data only
    glacier = glacier & valid

    return glacier


def morphological_cleanup(mask, min_size=MIN_FRAGMENT_PX):
    """Clean up glacier mask: fill holes, remove small fragments."""
    # Close small gaps (1 pixel)
    struct = ndimage.generate_binary_structure(2, 1)
    mask = ndimage.binary_closing(mask, structure=struct, iterations=1)

    # Open to remove thin connections/noise
    mask = ndimage.binary_opening(mask, structure=struct, iterations=1)

    # Remove small fragments
    labeled, n_features = ndimage.label(mask)
    for i in range(1, n_features + 1):
        if (labeled == i).sum() < min_size:
            mask[labeled == i] = False

    # Fill small holes within the glacier
    filled = ndimage.binary_fill_holes(mask)
    # Only fill holes smaller than min_size
    holes = filled & ~mask
    labeled_holes, n_holes = ndimage.label(holes)
    for i in range(1, n_holes + 1):
        if (labeled_holes == i).sum() < min_size:
            mask[labeled_holes == i] = True

    return mask


def constrain_with_rgi(sat_mask, rgi_gdf, transform, crs, shape_2d,
                       dem_path=None):
    """Constrain satellite-derived mask with RGI upper boundary.

    Uses elevation to split the glacier into two zones:
    - Upper zone (above ELA ~1078m): keep RGI boundary fixed (connects
      to other glaciers, hard to delineate from satellite)
    - Lower zone (below ELA): use satellite-derived mask (shows terminus
      retreat and lateral margin changes)

    The satellite mask is also intersected with a buffered RGI to prevent
    false glacier detection on surrounding terrain.
    """
    # Rasterize RGI outline
    rgi_reproj = rgi_gdf.to_crs(crs)
    rgi_raster = rasterize(
        [(geom, 1) for geom in rgi_reproj.geometry],
        out_shape=shape_2d,
        transform=transform,
        fill=0,
        dtype=np.uint8,
    ).astype(bool)

    # Load DEM for elevation-based splitting
    elev_cutoff = 1078.0  # ELA elevation — above this, keep RGI fixed
    if dem_path is not None:
        with rasterio.open(dem_path) as dem_src:
            # Read DEM at the same grid as the satellite data
            from rasterio.warp import reproject, Resampling
            dem_data = np.empty(shape_2d, dtype=np.float32)
            reproject(
                source=rasterio.band(dem_src, 1),
                destination=dem_data,
                dst_transform=transform,
                dst_crs=crs,
                resampling=Resampling.bilinear,
            )
    else:
        # No DEM — fall back to keeping full RGI
        dem_data = np.zeros(shape_2d, dtype=np.float32)

    upper_zone = dem_data >= elev_cutoff
    lower_zone = ~upper_zone

    # Buffer RGI by 3 pixels — satellite mask must be near the known glacier
    rgi_buffered = ndimage.binary_dilation(rgi_raster, iterations=3)

    # Upper zone: always use RGI (fixed boundary)
    # Lower zone: use satellite where it overlaps buffered RGI
    #             (allows retreat but prevents spurious detections far away)
    combined = np.zeros_like(rgi_raster)
    combined[upper_zone] = rgi_raster[upper_zone]
    combined[lower_zone] = sat_mask[lower_zone] & rgi_buffered[lower_zone]

    return combined


def mask_to_polygon(mask, transform, crs, min_area_m2=10000):
    """Convert boolean mask to polygon GeoDataFrame."""
    mask_uint8 = mask.astype(np.uint8)

    polys = []
    for geom_dict, value in shapes(mask_uint8, transform=transform):
        if value == 1:
            poly = shape(geom_dict)
            if poly.area > min_area_m2:
                polys.append(poly)

    if not polys:
        return None

    merged = unary_union(polys)
    gdf = gpd.GeoDataFrame({'geometry': [merged]}, crs=crs)
    return gdf


def process_year(year, collection, scene_id):
    """Process one year: download bands, compute mask, generate outline."""
    print(f"\n{'='*60}")
    print(f"Processing {year}: {scene_id}")
    print(f"{'='*60}")

    item = load_stac_item(collection, scene_id)
    date = item.properties.get('datetime', '')[:10]
    cloud = item.properties.get('eo:cloud_cover', '?')
    platform = item.properties.get('platform', '?')
    print(f"  Date: {date}, Cloud: {cloud}%, Platform: {platform}")

    # Determine band names
    if 'sentinel' in collection:
        red_band, swir_band, green_band = 'B04', 'B11', 'B03'
    else:
        red_band, swir_band, green_band = 'red', 'swir16', 'green'

    # Read bands
    print(f"  Reading {red_band}...")
    red, transform, crs = read_band_windowed(item, red_band, BBOX)
    print(f"  Reading {swir_band}...")
    swir, _, _ = read_band_windowed(item, swir_band, BBOX)
    print(f"  Reading {green_band}...")
    green, _, _ = read_band_windowed(item, green_band, BBOX)

    # Handle resolution mismatch (Sentinel-2: B04=10m, B11=20m)
    if red.shape != swir.shape:
        zoom_y = red.shape[0] / swir.shape[0]
        zoom_x = red.shape[1] / swir.shape[1]
        print(f"  Resampling SWIR {swir.shape} → {red.shape}")
        swir = ndimage.zoom(swir, (zoom_y, zoom_x), order=1)

    print(f"  Grid: {red.shape}, CRS: {crs}")

    # Handle green resolution mismatch too (Sentinel-2)
    if red.shape != green.shape:
        zoom_y = red.shape[0] / green.shape[0]
        zoom_x = red.shape[1] / green.shape[1]
        green = ndimage.zoom(green, (zoom_y, zoom_x), order=1)

    # Compute glacier mask
    print(f"  Computing band ratio + NDSI (threshold={RATIO_THRESHOLD})...")
    raw_mask = compute_glacier_mask(red, swir, green, RATIO_THRESHOLD)
    raw_px = int(raw_mask.sum())
    print(f"  Raw glacier pixels: {raw_px}")

    # Morphological cleanup
    print(f"  Morphological cleanup...")
    clean_mask = morphological_cleanup(raw_mask)
    clean_px = int(clean_mask.sum())
    print(f"  Clean glacier pixels: {clean_px}")

    # Load RGI and constrain using elevation
    print(f"  Constraining with RGI upper boundary (above ELA=1078m)...")
    rgi_gdf = gpd.read_file(RGI_PATH)
    dem_path = str(PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif')
    final_mask = constrain_with_rgi(clean_mask, rgi_gdf, transform, crs,
                                     red.shape, dem_path=dem_path)
    final_px = int(final_mask.sum())

    # Compute area
    # Get pixel size from transform
    px_x = abs(transform.a)
    px_y = abs(transform.e)
    area_km2 = final_px * px_x * px_y / 1e6
    print(f"  Final glacier pixels: {final_px}")
    print(f"  Area: {area_km2:.2f} km²")

    # Convert to polygon
    print(f"  Vectorizing...")
    gdf = mask_to_polygon(final_mask, transform, crs)
    if gdf is None:
        print(f"  ERROR: No glacier polygon generated!")
        return None

    # Reproject to WGS84 for storage
    gdf_wgs = gdf.to_crs('EPSG:4326')
    gdf_wgs['year'] = year
    gdf_wgs['source_date'] = date
    gdf_wgs['source'] = platform
    gdf_wgs['scene_id'] = scene_id
    gdf_wgs['area_km2'] = area_km2
    gdf_wgs['method'] = 'Red/SWIR band ratio'
    gdf_wgs['threshold'] = RATIO_THRESHOLD

    # Also save in UTM for direct comparison with model grid
    gdf_utm = gdf.copy()
    gdf_utm['year'] = year
    gdf_utm['source_date'] = date
    gdf_utm['area_km2'] = area_km2

    # Save
    out_wgs = OUT_DIR / f'dixon_glacier_{year}.geojson'
    gdf_wgs.to_file(out_wgs, driver='GeoJSON')
    print(f"  Saved: {out_wgs.name}")

    out_utm = OUT_DIR / f'dixon_glacier_{year}_utm.geojson'
    gdf_utm.to_file(out_utm, driver='GeoJSON')

    # Save the band ratio as a diagnostic GeoTIFF
    ratio = np.where(swir > 0, red / swir, 0).astype(np.float32)
    ratio_path = OUT_DIR / f'band_ratio_{year}.tif'
    with rasterio.open(
        ratio_path, 'w', driver='GTiff',
        height=ratio.shape[0], width=ratio.shape[1],
        count=1, dtype='float32', crs=crs, transform=transform,
    ) as dst:
        dst.write(ratio, 1)

    return {
        'year': year,
        'date': date,
        'area_km2': area_km2,
        'platform': platform,
        'cloud_cover': cloud,
        'n_pixels': final_px,
        'pixel_size_m': px_x,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for year in sorted(SCENES.keys()):
        collection, scene_id = SCENES[year]
        try:
            r = process_year(year, collection, scene_id)
            if r:
                results.append(r)
        except Exception as e:
            print(f"  ERROR processing {year}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY — Dixon Glacier Multi-Temporal Outlines")
    print(f"{'='*60}")
    print(f"{'Year':>6s}  {'Date':>12s}  {'Area (km²)':>10s}  {'Source':>12s}  {'Cloud':>6s}")
    print("-" * 60)
    for r in results:
        print(f"{r['year']:>6d}  {r['date']:>12s}  {r['area_km2']:>10.2f}  "
              f"{r['platform']:>12s}  {r['cloud_cover']:>5.1f}%")

    # Save summary
    summary_path = OUT_DIR / 'outline_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nSummary: {summary_path}")
    print(f"Outlines: {OUT_DIR}/")


if __name__ == '__main__':
    main()
