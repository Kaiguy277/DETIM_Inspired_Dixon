"""
North-branch snowline comparison for Dixon Glacier DETIM.

Motivation (advisor meeting, Apr 2026): the whole-glacier snowline validation
shows high spatial variability that DETIM cannot reproduce (D-028 structural
finding). The advisor suggested splitting the glacier into sub-branches.
This script restricts both the observed snowline and the modeled snow/ice
boundary to the NORTH BRANCH only (UTM Y above NORTH_Y_THRESHOLD) and
compares mean elevations year-by-year.

Decision: D-029 — north-branch-only snowline comparison.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import json
import re

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
DEM_PATH = PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif'
GLACIER_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
CLIMATE_PATH = PROJECT / 'data' / 'climate' / 'dixon_gap_filled_climate.csv'
SNOWLINE_DIR = PROJECT / 'snowlines_all'
OUTPUT_DIR = PROJECT / 'calibration_output'

# North-branch definition: UTM Zone 5N bounding thresholds.
# Glacier aspect is NW; a pure Y-only cut captures too much central glacier.
# The NE tributary sits above Y=6615000 m AND east of X=622000 m
# (visual inspection; centroids of 2019/2020/2024 NE-arm snowlines:
#  (623843,6616297), (623072,6617063), (624456,6615480); revised D-033).
NORTH_Y_THRESHOLD = 6615000.0
NORTH_X_THRESHOLD = 622000.0


def build_north_branch_mask(grid):
    """Return a bool mask of glacier cells in the NE tributary
    (UTM Y > NORTH_Y_THRESHOLD AND UTM X > NORTH_X_THRESHOLD)."""
    transform = grid['transform']
    nrows, ncols = grid['elevation'].shape
    rows = np.arange(nrows)
    cols = np.arange(ncols)
    # UTM coordinates at cell centres
    y_coords = transform.f + (rows + 0.5) * transform.e  # res_y negative
    x_coords = transform.c + (cols + 0.5) * transform.a
    row_mask = y_coords > NORTH_Y_THRESHOLD
    col_mask = x_coords > NORTH_X_THRESHOLD
    north_2d = row_mask[:, None] & col_mask[None, :]
    return grid['glacier_mask'] & north_2d


def parse_date(shp_path):
    m = re.match(r'(\d{4})_(\d{2})_(\d{2})_', Path(shp_path).stem)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    m = re.match(r'(\d{4})_', Path(shp_path).stem)
    return (int(m.group(1)), 9, 15) if m else (None, None, None)


def load_snowline_raster(shp_path, grid, branch_mask):
    """Rasterize snowline LineStrings (in UTM 5N) onto the model grid,
    keeping only pixels inside the north-branch mask."""
    import geopandas as gpd
    from rasterio.features import rasterize
    from shapely.geometry import mapping

    gdf = gpd.read_file(shp_path).to_crs('EPSG:32605')
    cell_size = grid['cell_size']
    buffered = gdf.geometry.buffer(cell_size * 0.6)

    transform = grid['transform']
    nrows, ncols = grid['elevation'].shape
    shapes = [(mapping(g), 1) for g in buffered]
    raster = rasterize(shapes, out_shape=(nrows, ncols),
                       transform=transform, fill=0, dtype=np.uint8)
    full_mask = (raster == 1) & grid['glacier_mask']
    north_mask = full_mask & branch_mask
    return full_mask, north_mask


def modeled_snowline_elev(cum_accum, cum_melt, elevation, glacier_mask,
                          branch_mask):
    """Mean elevation of the modeled snow/ice boundary within the branch."""
    from scipy.ndimage import binary_dilation
    net = cum_accum - cum_melt
    snow = glacier_mask & (net > 0)
    ice = glacier_mask & (net <= 0)
    if snow.sum() == 0 or ice.sum() == 0:
        return np.nan, np.nan, 0
    boundary = glacier_mask & (
        (snow & binary_dilation(ice)) | (ice & binary_dilation(snow))
    )
    boundary_north = boundary & branch_mask
    if boundary_north.sum() == 0:
        return np.nan, np.nan, 0
    elevs = elevation[boundary_north]
    return float(elevs.mean()), float(elevs.std()), int(boundary_north.sum())


def main():
    from run_projection import load_top_param_sets
    from dixon_melt.terrain import prepare_grid
    from dixon_melt.model import precompute_ipot
    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config
    from dixon_melt.climate import load_gap_filled_climate

    print("=" * 60)
    print("NORTH-BRANCH SNOWLINE VALIDATION — Dixon Glacier")
    print(f"  Branch mask: Y > {NORTH_Y_THRESHOLD:.0f} AND "
          f"X > {NORTH_X_THRESHOLD:.0f} (UTM Zone 5N)")
    print("=" * 60)

    params = load_top_param_sets(n_top=1)[0]
    print(f"\n  MAP params: MF={params['MF']:.3f}, "
          f"r_snow={params['r_snow']:.6f}, T0={params['T0']:.3f}")

    print("\n  Preparing grid...")
    grid = prepare_grid(str(DEM_PATH), str(GLACIER_PATH), target_res=100.0)
    print("  Precomputing I_pot...")
    ipot = precompute_ipot(grid, doy_range=range(1, 366), dt_hours=3.0)

    branch_mask = build_north_branch_mask(grid)
    n_total = int(grid['glacier_mask'].sum())
    n_branch = int(branch_mask.sum())
    print(f"  North-branch mask: {n_branch}/{n_total} cells "
          f"({100*n_branch/n_total:.1f}% of glacier)")
    branch_elevs = grid['elevation'][branch_mask]
    print(f"  Branch elevation range: {branch_elevs.min():.0f}"
          f"–{branch_elevs.max():.0f} m")

    fmodel = FastDETIM(
        grid, ipot,
        transfer_alpha=config.TRANSFER_ALPHA,
        transfer_beta=config.TRANSFER_BETA,
        ref_elev=config.SNOTEL_ELEV,
        stake_names=config.STAKE_NAMES,
        stake_elevs=config.STAKE_ELEVS,
    )

    climate = load_gap_filled_climate(str(CLIMATE_PATH))[
        ['temperature', 'precipitation']]

    # Iterate over snowline shapefiles
    shp_files = sorted(SNOWLINE_DIR.glob('*_snowline*.shp'))
    print(f"\n  Found {len(shp_files)} snowline shapefiles")

    rows = []
    for shp in shp_files:
        yr, mo, dy = parse_date(shp)
        if yr is None:
            continue
        full_mask, north_mask = load_snowline_raster(shp, grid, branch_mask)
        n_obs_north = int(north_mask.sum())
        if n_obs_north == 0:
            print(f"    {yr}-{mo:02d}-{dy:02d}: no observed line on north branch — skip")
            continue

        obs_elev_mean = float(grid['elevation'][north_mask].mean())
        obs_elev_std = float(grid['elevation'][north_mask].std())

        # Run model WY(yr-1)-10-01 → obs date
        start = f'{yr-1}-10-01'
        end = f'{yr}-{mo:02d}-{dy:02d}'
        wy = climate.loc[start:end]
        if len(wy) < 200:
            print(f"    {yr}: insufficient climate days ({len(wy)}) — skip")
            continue
        melt = wy.loc[f'{yr}-05-01':f'{yr}-09-30']
        if len(melt) and melt['temperature'].isna().mean() > 0.30:
            print(f"    {yr}: >30% melt-season T missing — skip")
            continue

        T = np.nan_to_num(wy['temperature'].values.astype(np.float64))
        P = np.nan_to_num(wy['precipitation'].values.astype(np.float64))
        doy = np.array(wy.index.dayofyear, dtype=np.int64)
        res = fmodel.run(T, P, doy, params, 0.0)

        mod_mean, mod_std, n_mod = modeled_snowline_elev(
            res['cum_accum'], res['cum_melt'],
            grid['elevation'], grid['glacier_mask'], branch_mask)
        bias = mod_mean - obs_elev_mean if not np.isnan(mod_mean) else np.nan

        print(f"    {yr}-{mo:02d}-{dy:02d}: "
              f"obs={obs_elev_mean:.0f}±{obs_elev_std:.0f}m  "
              f"mod={mod_mean:.0f}m  bias={bias:+.0f}m  "
              f"(n_obs={n_obs_north}, n_mod={n_mod})")

        rows.append(dict(
            year=yr, obs_date=f'{yr}-{mo:02d}-{dy:02d}',
            obs_snowline_elev=obs_elev_mean,
            obs_snowline_std=obs_elev_std,
            n_obs_pixels=n_obs_north,
            modeled_snowline_elev=mod_mean,
            modeled_snowline_std=mod_std,
            n_modeled_boundary=n_mod,
            elev_bias=bias,
        ))

    if not rows:
        print("\n  No valid years for north-branch comparison.")
        return

    df = pd.DataFrame(rows)
    OUTPUT_DIR.mkdir(exist_ok=True)
    csv_path = OUTPUT_DIR / 'snowline_north_branch.csv'
    df.to_csv(csv_path, index=False)

    valid = df['elev_bias'].dropna()
    summary = dict(
        north_y_threshold=NORTH_Y_THRESHOLD,
        north_x_threshold=NORTH_X_THRESHOLD,
        n_years=int(len(valid)),
        mean_bias_m=float(valid.mean()),
        std_bias_m=float(valid.std()),
        rmse_m=float(np.sqrt((valid**2).mean())),
        mae_m=float(valid.abs().mean()),
        correlation=float(df[['obs_snowline_elev', 'modeled_snowline_elev']]
                          .dropna().corr().iloc[0, 1])
                    if len(df.dropna(subset=['obs_snowline_elev',
                                             'modeled_snowline_elev'])) > 2
                    else float('nan'),
        branch_n_cells=n_branch,
        branch_frac_of_glacier=n_branch / n_total,
    )
    summary_path = OUTPUT_DIR / 'snowline_north_branch_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print("\n  NORTH-BRANCH SUMMARY:")
    for k, v in summary.items():
        print(f"    {k}: {v}")
    print(f"\n  Saved: {csv_path.name}, {summary_path.name}")

    # Plots
    v = df.dropna(subset=['obs_snowline_elev', 'modeled_snowline_elev'])

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.errorbar(v['obs_snowline_elev'], v['modeled_snowline_elev'],
                xerr=v['obs_snowline_std'], yerr=v['modeled_snowline_std'],
                fmt='o', color='#2166ac', ecolor='gray', alpha=0.8,
                elinewidth=0.8, capsize=2)
    for _, r in v.iterrows():
        ax.annotate(str(int(r['year'])),
                    (r['obs_snowline_elev'], r['modeled_snowline_elev']),
                    fontsize=7, xytext=(3, 3), textcoords='offset points')
    lo = min(v['obs_snowline_elev'].min(), v['modeled_snowline_elev'].min()) - 30
    hi = max(v['obs_snowline_elev'].max(), v['modeled_snowline_elev'].max()) + 30
    ax.plot([lo, hi], [lo, hi], 'k--', lw=1, alpha=0.5, label='1:1')
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect('equal')
    ax.set_xlabel('Observed North-Branch Snowline Elevation (m)')
    ax.set_ylabel('Modeled North-Branch Snowline Elevation (m)')
    ax.set_title(f"Dixon — North-Branch Snowline Validation\n"
                 f"RMSE={summary['rmse_m']:.0f}m, "
                 f"bias={summary['mean_bias_m']:+.0f}m, "
                 f"r={summary['correlation']:.2f}, n={summary['n_years']}")
    ax.legend(); ax.grid(True, alpha=0.3)
    fig.savefig(OUTPUT_DIR / 'snowline_north_branch_scatter.png',
                dpi=150, bbox_inches='tight')
    plt.close(fig)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True,
                                   gridspec_kw={'height_ratios': [3, 1]})
    ax1.plot(v['year'], v['obs_snowline_elev'], 'o-', color='#2166ac',
             label='Observed (north branch)', lw=1.5)
    ax1.plot(v['year'], v['modeled_snowline_elev'], 's-', color='#b2182b',
             label='Modeled (north branch)', lw=1.5)
    ax1.fill_between(v['year'], v['obs_snowline_elev'],
                     v['modeled_snowline_elev'], alpha=0.15, color='gray')
    ax1.set_ylabel('Snowline Elevation (m)')
    ax1.set_title('Dixon Glacier — North-Branch Snowline Time Series')
    ax1.legend(); ax1.grid(True, alpha=0.3)
    colors = ['#b2182b' if b > 0 else '#2166ac' for b in v['elev_bias']]
    ax2.bar(v['year'], v['elev_bias'], color=colors, alpha=0.7)
    ax2.axhline(0, color='k', lw=0.5)
    ax2.set_ylabel('Bias (m)'); ax2.set_xlabel('Year')
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / 'snowline_north_branch_timeseries.png',
                dpi=150, bbox_inches='tight')
    plt.close(fig)

    print("  Saved: snowline_north_branch_scatter.png, "
          "snowline_north_branch_timeseries.png")


if __name__ == '__main__':
    main()
