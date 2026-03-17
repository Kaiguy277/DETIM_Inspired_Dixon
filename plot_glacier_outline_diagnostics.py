"""
Generate diagnostic plots for glacier outline delineation.

For each year, shows:
  1. False-color composite (SWIR/NIR/Green) — glacier appears blue/cyan
  2. Red/SWIR band ratio map with threshold contour
  3. NDSI map
  4. Final glacier outline overlaid on true-color

This allows visual assessment of the automated classification and
identification of areas needing manual correction.

Usage:
    python plot_glacier_outline_diagnostics.py
"""
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.features import rasterize
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from pathlib import Path
from scipy import ndimage
import planetary_computer
import pystac_client

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
RGI_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
DEM_PATH = PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif'
OUT_DIR = PROJECT / 'data' / 'glacier_outlines'

BBOX = [-150.96, 59.60, -150.76, 59.71]

SCENES = {
    2000: ('landsat-c2-l2', 'LE07_L2SP_069018_20000809_02_T1'),
    2005: ('landsat-c2-l2', 'LT05_L2SP_068019_20050925_02_T1'),
    2010: ('landsat-c2-l2', 'LT05_L2SP_069018_20100829_02_T1'),
    2015: ('landsat-c2-l2', 'LC08_L2SP_068019_20150820_02_T1'),
    2020: ('sentinel-2-l2a', 'S2B_MSIL2A_20200911T212529_R043_T05VPG_20200913T062439'),
    2025: ('sentinel-2-l2a', 'S2C_MSIL2A_20250930T212541_R043_T05VPG_20250930T225512'),
}


def load_stac_item(collection, scene_id):
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )
    items = list(catalog.search(collections=[collection], ids=[scene_id]).items())
    return items[0]


def read_band(item, band_name, bbox):
    href = item.assets[band_name].href
    with rasterio.open(href) as src:
        from rasterio.warp import transform_bounds
        src_bounds = transform_bounds('EPSG:4326', src.crs, *bbox)
        window = src.window(*src_bounds).round_offsets().round_lengths()
        window = window.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
        data = src.read(1, window=window).astype(np.float32)
        transform = src.window_transform(window)
        nodata = src.nodata
        if nodata is not None:
            data[data == nodata] = np.nan
        if 'landsat' in item.collection_id:
            data = data * 0.0000275 - 0.2
            data[(data < 0) | (data > 1)] = np.nan
        if 'sentinel' in item.collection_id:
            data = data / 10000.0
            data[(data < 0) | (data > 1)] = np.nan
        return data, transform, src.crs


def process_and_plot(year, collection, scene_id):
    print(f"\n  {year}: loading bands...")
    item = load_stac_item(collection, scene_id)
    date = item.properties.get('datetime', '')[:10]
    cloud = item.properties.get('eo:cloud_cover', 0)

    if 'sentinel' in collection:
        band_names = {'red': 'B04', 'nir': 'B08', 'green': 'B03',
                      'swir': 'B11', 'blue': 'B02'}
    else:
        band_names = {'red': 'red', 'nir': 'nir08', 'green': 'green',
                      'swir': 'swir16', 'blue': 'blue'}

    red, transform, crs = read_band(item, band_names['red'], BBOX)
    green, _, _ = read_band(item, band_names['green'], BBOX)
    blue, _, _ = read_band(item, band_names['blue'], BBOX)
    nir, _, _ = read_band(item, band_names['nir'], BBOX)
    swir, _, _ = read_band(item, band_names['swir'], BBOX)

    # Resample if needed (Sentinel-2 mixed resolutions)
    for arr_name in ['swir', 'nir', 'green', 'blue']:
        arr = locals()[arr_name]
        if arr.shape != red.shape:
            zy = red.shape[0] / arr.shape[0]
            zx = red.shape[1] / arr.shape[1]
            locals()[arr_name] = ndimage.zoom(arr, (zy, zx), order=1)
    # Re-assign after zoom
    swir = ndimage.zoom(swir, (red.shape[0]/swir.shape[0], red.shape[1]/swir.shape[1]), order=1) if swir.shape != red.shape else swir
    nir = ndimage.zoom(nir, (red.shape[0]/nir.shape[0], red.shape[1]/nir.shape[1]), order=1) if nir.shape != red.shape else nir
    green = ndimage.zoom(green, (red.shape[0]/green.shape[0], red.shape[1]/green.shape[1]), order=1) if green.shape != red.shape else green
    blue = ndimage.zoom(blue, (red.shape[0]/blue.shape[0], red.shape[1]/blue.shape[1]), order=1) if blue.shape != red.shape else blue

    # Compute indices
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = np.where(swir > 0, red / swir, 0)
        ndsi = np.where((green + swir) > 0, (green - swir) / (green + swir), 0)

    # RGI outline for overlay
    rgi_gdf = gpd.read_file(RGI_PATH).to_crs(crs)
    rgi_raster = rasterize(
        [(geom, 1) for geom in rgi_gdf.geometry],
        out_shape=red.shape, transform=transform, fill=0, dtype=np.uint8,
    ).astype(bool)
    rgi_boundary = rgi_raster ^ ndimage.binary_erosion(rgi_raster, iterations=1)

    # Satellite-derived outline if it exists
    outline_path = OUT_DIR / f'dixon_glacier_{year}.geojson'
    sat_boundary = np.zeros_like(rgi_boundary)
    if outline_path.exists():
        sat_gdf = gpd.read_file(outline_path).to_crs(crs)
        sat_raster = rasterize(
            [(geom, 1) for geom in sat_gdf.geometry],
            out_shape=red.shape, transform=transform, fill=0, dtype=np.uint8,
        ).astype(bool)
        sat_boundary = sat_raster ^ ndimage.binary_erosion(sat_raster, iterations=1)

    # DEM for contours
    dem_data = np.empty(red.shape, dtype=np.float32)
    with rasterio.open(DEM_PATH) as dem_src:
        reproject(
            source=rasterio.band(dem_src, 1),
            destination=dem_data,
            dst_transform=transform,
            dst_crs=crs,
            resampling=Resampling.bilinear,
        )

    # Crop to glacier region with padding
    rows = np.where(rgi_raster.any(axis=1))[0]
    cols = np.where(rgi_raster.any(axis=0))[0]
    pad = 15
    r0 = max(0, rows[0] - pad)
    r1 = min(red.shape[0], rows[-1] + pad + 1)
    c0 = max(0, cols[0] - pad)
    c1 = min(red.shape[1], cols[-1] + pad + 1)

    # Build composites
    def norm(arr, lo=0.02, hi=0.98):
        a = arr[r0:r1, c0:c1].copy()
        a = np.nan_to_num(a, nan=0)
        vmin, vmax = np.percentile(a[a > 0], [2, 98]) if (a > 0).any() else (0, 1)
        return np.clip((a - vmin) / max(vmax - vmin, 1e-6), 0, 1)

    # True color (R, G, B)
    tc = np.dstack([norm(red), norm(green), norm(blue)])
    # False color (SWIR, NIR, Green) — ice appears blue/cyan
    fc = np.dstack([norm(swir), norm(nir), norm(green)])

    ratio_crop = ratio[r0:r1, c0:c1]
    ndsi_crop = ndsi[r0:r1, c0:c1]
    rgi_b = rgi_boundary[r0:r1, c0:c1]
    sat_b = sat_boundary[r0:r1, c0:c1]
    dem_crop = dem_data[r0:r1, c0:c1]

    # Plot
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    fig.suptitle(f'Dixon Glacier — {date}  (cloud: {cloud:.1f}%)',
                 fontsize=16, fontweight='bold')

    # 1. True color + outlines
    ax = axes[0, 0]
    ax.imshow(tc)
    ax.contour(rgi_b, colors='yellow', linewidths=0.8)
    if sat_b.any():
        ax.contour(sat_b, colors='red', linewidths=1.0)
    ax.contour(dem_crop, levels=[1078], colors='cyan', linewidths=0.5,
               linestyles='dashed')
    ax.set_title('True Color + RGI (yellow) + Satellite outline (red)\n'
                 'ELA 1078m (cyan dashed)', fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])

    # 2. False color (SWIR/NIR/Green)
    ax = axes[0, 1]
    ax.imshow(fc)
    ax.contour(rgi_b, colors='yellow', linewidths=0.8)
    ax.contour(dem_crop, levels=np.arange(400, 1800, 200),
               colors='white', linewidths=0.3, alpha=0.5)
    ax.set_title('False Color (SWIR/NIR/Green)\nIce = blue/cyan, Rock = brown/red',
                 fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])

    # 3. Band ratio
    ax = axes[1, 0]
    im = ax.imshow(ratio_crop, cmap='RdYlBu', vmin=0, vmax=4)
    ax.contour(ratio_crop, levels=[1.8], colors='red', linewidths=1.0)
    ax.contour(rgi_b, colors='yellow', linewidths=0.8)
    plt.colorbar(im, ax=ax, shrink=0.7, label='Red/SWIR ratio')
    ax.set_title('Red/SWIR Band Ratio\nThreshold 1.8 (red contour)', fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])

    # 4. NDSI
    ax = axes[1, 1]
    im = ax.imshow(ndsi_crop, cmap='RdYlBu', vmin=-0.5, vmax=1.0)
    ax.contour(ndsi_crop, levels=[0.4], colors='red', linewidths=1.0)
    ax.contour(rgi_b, colors='yellow', linewidths=0.8)
    plt.colorbar(im, ax=ax, shrink=0.7, label='NDSI')
    ax.set_title('NDSI (Green-SWIR)/(Green+SWIR)\nThreshold 0.4 (red contour)',
                 fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])

    plt.tight_layout()
    out_path = OUT_DIR / f'diagnostic_{year}.png'
    fig.savefig(str(out_path), dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {out_path.name}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for year in sorted(SCENES.keys()):
        collection, scene_id = SCENES[year]
        try:
            process_and_plot(year, collection, scene_id)
        except Exception as e:
            print(f"  ERROR {year}: {e}")
            import traceback
            traceback.print_exc()
    print(f"\nAll diagnostics in {OUT_DIR}/")


if __name__ == '__main__':
    main()
