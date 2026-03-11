"""
Snowline validation for Dixon Glacier DETIM.

Compares modeled end-of-summer snow/ice boundary against digitized
snowline observations (22 years, 1999-2024). Provides both elevation-
based (mean snowline altitude) and spatial (rasterized overlap) metrics.

The modeled snowline is defined as the contour where cumulative net
balance (accum - melt) = 0 at the observation date. Cells above the
snowline have positive net balance (snow-covered); cells below have
negative net balance (bare ice).

References:
    Hock, R. (1999). J. Glaciol., 45(149), 101-111.
    Rabatel, A. et al. (2005). J. Glaciol., 51(172), 539-546.
"""
import numpy as np
import pandas as pd
from pathlib import Path
import re


def parse_snowline_date(shp_path):
    """Extract observation date from shapefile name.

    Naming conventions:
        2013_09_15_snowline.shp -> 2013-09-15
        1999_snowline.shp -> 1999-09-15 (default Sep 15)

    Returns (year, month, day) tuple.
    """
    name = Path(shp_path).stem
    # Try YYYY_MM_DD pattern
    m = re.match(r'(\d{4})_(\d{2})_(\d{2})_', name)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    # Fallback: year-only, assume Sep 15
    m = re.match(r'(\d{4})_', name)
    if m:
        return int(m.group(1)), 9, 15
    raise ValueError(f"Cannot parse date from {name}")


def load_snowline(shp_path, dem_info):
    """Load and rasterize an observed snowline onto the model grid.

    Parameters
    ----------
    shp_path : path to snowline shapefile (LineString, EPSG:32605)
    dem_info : dict with 'elevation', 'glacier_mask', 'transform',
               'cell_size', 'nrows', 'ncols'

    Returns
    -------
    dict with:
        snowline_mask : 2D bool, cells intersected by the snowline
        snowline_elevations : 1D array, elevations at snowline pixels
        mean_elevation : float, mean observed snowline elevation
        n_pixels : int, number of grid cells on the snowline
        year, month, day : observation date
    """
    import geopandas as gpd
    from rasterio.features import rasterize
    from rasterio.transform import from_bounds
    from shapely.geometry import mapping

    gdf = gpd.read_file(shp_path)
    year, month, day = parse_snowline_date(shp_path)

    # Buffer the line slightly (half a cell) to ensure rasterization hits cells
    cell_size = dem_info['cell_size']
    buffered = gdf.geometry.buffer(cell_size * 0.6)

    # Rasterize onto model grid
    transform = dem_info['transform']
    nrows, ncols = dem_info['nrows'], dem_info['ncols']
    shapes = [(mapping(geom), 1) for geom in buffered]
    raster = rasterize(
        shapes, out_shape=(nrows, ncols), transform=transform,
        fill=0, dtype=np.uint8,
    )
    snowline_mask = (raster == 1) & dem_info['glacier_mask']

    # Extract elevations along snowline
    elevations = dem_info['elevation'][snowline_mask]

    return {
        'snowline_mask': snowline_mask,
        'snowline_elevations': elevations,
        'mean_elevation': float(elevations.mean()) if len(elevations) > 0 else np.nan,
        'std_elevation': float(elevations.std()) if len(elevations) > 1 else np.nan,
        'n_pixels': int(snowline_mask.sum()),
        'year': year, 'month': month, 'day': day,
    }


def load_all_snowlines(snowline_dir, dem_info):
    """Load all snowline shapefiles from a directory.

    Returns list of dicts sorted by year.
    """
    snowline_dir = Path(snowline_dir)
    shp_files = sorted(snowline_dir.glob('*_snowline*.shp'))

    results = []
    for shp in shp_files:
        try:
            sl = load_snowline(shp, dem_info)
            sl['file'] = shp.name
            results.append(sl)
        except Exception as e:
            print(f"  WARNING: skipping {shp.name}: {e}")

    results.sort(key=lambda x: (x['year'], x['month'], x['day']))
    return results


def modeled_snowline_elevation(cum_accum, cum_melt, elevation, glacier_mask):
    """Compute the modeled snowline elevation from cumulative balance grids.

    The snowline is the elevation where net balance (accum - melt) = 0.
    Returns the mean elevation of cells nearest to the zero-balance contour.

    Parameters
    ----------
    cum_accum, cum_melt : 2D arrays (mm)
    elevation : 2D array (m)
    glacier_mask : 2D bool

    Returns
    -------
    dict with:
        mean_elevation : float (m), mean modeled snowline altitude
        snow_mask : 2D bool, cells with positive net balance (snow-covered)
        ice_mask : 2D bool, glacier cells with negative net balance (bare ice)
    """
    net_balance = cum_accum - cum_melt  # mm
    snow_mask = glacier_mask & (net_balance > 0)
    ice_mask = glacier_mask & (net_balance <= 0)

    if snow_mask.sum() == 0 or ice_mask.sum() == 0:
        # Entire glacier is snow-covered or bare ice
        return {
            'mean_elevation': np.nan,
            'snow_mask': snow_mask,
            'ice_mask': ice_mask,
        }

    # Find cells adjacent to the snow/ice boundary
    # A boundary cell has at least one neighbor of opposite type
    from scipy.ndimage import binary_dilation
    snow_dilated = binary_dilation(snow_mask)
    ice_dilated = binary_dilation(ice_mask)
    boundary = glacier_mask & ((snow_mask & ice_dilated) |
                                (ice_mask & snow_dilated))

    boundary_elevs = elevation[boundary]

    return {
        'mean_elevation': float(boundary_elevs.mean()) if len(boundary_elevs) > 0 else np.nan,
        'std_elevation': float(boundary_elevs.std()) if len(boundary_elevs) > 1 else np.nan,
        'snow_mask': snow_mask,
        'ice_mask': ice_mask,
        'boundary_mask': boundary,
        'n_boundary_cells': int(boundary.sum()),
    }


def validate_snowline_year(fmodel, climate, grid, params, obs_snowline,
                           winter_swe_mm=0.0):
    """Run the model for one water year and compare against observed snowline.

    Parameters
    ----------
    fmodel : FastDETIM instance
    climate : DataFrame with 'temperature', 'precipitation' columns, DatetimeIndex
    grid : dict from prepare_grid
    params : dict of model parameters
    obs_snowline : dict from load_snowline
    winter_swe_mm : float, initial SWE

    Returns
    -------
    dict with observed and modeled snowline metrics, and comparison stats.
    """
    year = obs_snowline['year']
    month = obs_snowline['month']
    day = obs_snowline['day']

    # Run from Oct 1 of previous year to the observation date
    start = f'{year - 1}-10-01'
    end = f'{year}-{month:02d}-{day:02d}'

    wy = climate.loc[start:end]
    if len(wy) < 200:
        return None

    T = wy['temperature'].values.astype(np.float64)
    P = wy['precipitation'].values.astype(np.float64)
    doy = np.array(wy.index.dayofyear, dtype=np.int64)

    # Handle NaN in climate
    T = np.where(np.isnan(T), 0.0, T)
    P = np.where(np.isnan(P), 0.0, P)

    result = fmodel.run(T, P, doy, params, winter_swe_mm)

    # Modeled snowline
    modeled = modeled_snowline_elevation(
        result['cum_accum'], result['cum_melt'],
        grid['elevation'], grid['glacier_mask'])

    # Sample modeled net balance along observed snowline
    net_balance = result['cum_accum'] - result['cum_melt']
    obs_mask = obs_snowline['snowline_mask']
    balance_at_obs = net_balance[obs_mask] / 1000.0  # mm -> m w.e.

    # Compute overlap metrics
    # How much of the observed snowline falls in modeled snow vs ice zones
    obs_in_snow = int((obs_mask & modeled['snow_mask']).sum())
    obs_in_ice = int((obs_mask & modeled['ice_mask']).sum())
    n_obs = int(obs_mask.sum())
    fraction_correct = (obs_in_snow + obs_in_ice) / max(n_obs, 1)
    # Ideal: snowline should be at the boundary, so roughly 50/50
    # But a simpler metric: balance along observed line should be ~0

    return {
        'year': year,
        'obs_date': f'{year}-{month:02d}-{day:02d}',
        'obs_snowline_elev': obs_snowline['mean_elevation'],
        'obs_snowline_std': obs_snowline.get('std_elevation', np.nan),
        'modeled_snowline_elev': modeled['mean_elevation'],
        'modeled_snowline_std': modeled.get('std_elevation', np.nan),
        'elev_bias': modeled['mean_elevation'] - obs_snowline['mean_elevation'],
        'balance_at_obs_mean': float(balance_at_obs.mean()) if len(balance_at_obs) > 0 else np.nan,
        'balance_at_obs_std': float(balance_at_obs.std()) if len(balance_at_obs) > 1 else np.nan,
        'obs_in_snow_frac': obs_in_snow / max(n_obs, 1),
        'obs_in_ice_frac': obs_in_ice / max(n_obs, 1),
        'n_obs_pixels': n_obs,
        'n_modeled_boundary': modeled.get('n_boundary_cells', 0),
        'cum_accum': result['cum_accum'],
        'cum_melt': result['cum_melt'],
        'snow_mask': modeled['snow_mask'],
        'ice_mask': modeled['ice_mask'],
    }


def run_all_validation(fmodel, climate, grid, params, snowline_dir,
                       winter_swe_mm=0.0):
    """Validate against all available snowline observations.

    Returns DataFrame with one row per year and summary statistics.
    """
    dem_info = {
        'elevation': grid['elevation'],
        'glacier_mask': grid['glacier_mask'],
        'transform': grid['transform'],
        'cell_size': grid['cell_size'],
        'nrows': grid['elevation'].shape[0],
        'ncols': grid['elevation'].shape[1],
    }

    obs_list = load_all_snowlines(snowline_dir, dem_info)
    print(f"  Loaded {len(obs_list)} observed snowlines")

    results = []
    for obs in obs_list:
        yr = obs['year']
        r = validate_snowline_year(fmodel, climate, grid, params, obs,
                                   winter_swe_mm)
        if r is None:
            print(f"    {yr}: skipped (insufficient climate data)")
            continue

        bias = r['elev_bias']
        bal = r['balance_at_obs_mean']
        print(f"    {yr} ({r['obs_date']}): "
              f"obs={r['obs_snowline_elev']:.0f}m, "
              f"mod={r['modeled_snowline_elev']:.0f}m, "
              f"bias={bias:+.0f}m, "
              f"bal@obs={bal:+.2f} m w.e.")
        results.append(r)

    if not results:
        return pd.DataFrame(), {}

    # Summary table (drop spatial grids for the DataFrame)
    scalar_keys = [k for k in results[0] if k not in
                   ('cum_accum', 'cum_melt', 'snow_mask', 'ice_mask')]
    df = pd.DataFrame([{k: r[k] for k in scalar_keys} for r in results])

    valid = df['elev_bias'].dropna()
    summary = {
        'n_years': len(valid),
        'mean_bias_m': float(valid.mean()),
        'std_bias_m': float(valid.std()),
        'rmse_m': float(np.sqrt((valid**2).mean())),
        'mae_m': float(valid.abs().mean()),
        'mean_balance_at_obs': float(df['balance_at_obs_mean'].dropna().mean()),
        'correlation': float(df[['obs_snowline_elev', 'modeled_snowline_elev']]
                             .dropna().corr().iloc[0, 1])
                       if len(df.dropna(subset=['obs_snowline_elev',
                                                'modeled_snowline_elev'])) > 2
                       else np.nan,
    }

    print(f"\n  SNOWLINE VALIDATION SUMMARY ({summary['n_years']} years):")
    print(f"    Mean bias:  {summary['mean_bias_m']:+.0f} m "
          f"(positive = modeled too high)")
    print(f"    RMSE:       {summary['rmse_m']:.0f} m")
    print(f"    MAE:        {summary['mae_m']:.0f} m")
    print(f"    Correlation: r={summary['correlation']:.2f}")
    print(f"    Mean balance at observed snowline: "
          f"{summary['mean_balance_at_obs']:+.2f} m w.e. (ideal = 0)")

    return df, summary, results
