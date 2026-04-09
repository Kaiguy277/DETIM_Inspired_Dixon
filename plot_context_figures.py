#!/usr/bin/env python3
"""
Generate context/data figures for the interactive methods document.

Figures:
  fig_09_glacier_map       — DEM hillshade with stake locations, outline, contours
  fig_10_outline_retreat   — All 6 digitized outlines overlaid on DEM
  fig_11_climate_forcing   — Temperature and precip time series with gap-fill source
  fig_12_model_response    — Climate inputs + modeled annual balance side by side
"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
from pathlib import Path

ROOT = Path("/home/kai/Documents/Opus46Dixon_FirstShot")
OUT = ROOT / "figures" / "methods"
OUT.mkdir(parents=True, exist_ok=True)

plt.style.use("seaborn-v0_8-whitegrid")
mpl.rcParams.update({
    "font.size": 12, "axes.titlesize": 13, "axes.labelsize": 12,
    "xtick.labelsize": 11, "ytick.labelsize": 11, "legend.fontsize": 10,
    "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight",
    "pdf.fonttype": 42, "ps.fonttype": 42,
})


def save_fig(fig, name):
    fig.savefig(OUT / f"{name}.png")
    fig.savefig(OUT / f"{name}.pdf")
    plt.close(fig)
    print(f"  Saved: {OUT / name}.png/pdf")


# =====================================================================
# Figure 9: Glacier map with stakes and contours
# =====================================================================
def fig_09_glacier_map():
    import rasterio
    from rasterio.windows import from_bounds
    import geopandas as gpd
    from matplotlib.colors import LightSource
    from rasterio.features import geometry_mask

    dem_path = ROOT / "ifsar_2010" / "dixon_glacier_IFSAR_DTM_5m_full.tif"
    outline_path = ROOT / "geodedic_mb" / "dixon_glacier_outline_rgi7.geojson"

    # Load outline to get glacier bounds
    outline = gpd.read_file(outline_path)

    # Glacier bounds in EPSG:4326 (lon/lat)
    gbnds = outline.total_bounds  # minx, miny, maxx, maxy
    buf_x = (gbnds[2] - gbnds[0]) * 0.15
    buf_y = (gbnds[3] - gbnds[1]) * 0.15
    crop_left = gbnds[0] - buf_x
    crop_right = gbnds[2] + buf_x
    crop_bottom = gbnds[1] - buf_y
    crop_top = gbnds[3] + buf_y

    # Windowed read of DEM — crop to glacier + buffer
    with rasterio.open(dem_path) as src:
        crs = src.crs
        window = from_bounds(crop_left, crop_bottom, crop_right, crop_top,
                             src.transform)
        # Clamp window to valid raster extent
        window = window.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
        dem = src.read(1, window=window).astype(float)
        transform = src.window_transform(window)

    dem[dem < 0] = np.nan

    # Ensure outline CRS matches
    if outline.crs != crs:
        outline = outline.to_crs(crs)

    # Cropped extent for imshow (lon, lat)
    rows, cols = dem.shape
    extent = [
        transform[2],                          # left (lon)
        transform[2] + cols * transform[0],    # right (lon)
        transform[5] + rows * transform[4],    # bottom (lat, transform[4] < 0)
        transform[5],                          # top (lat)
    ]

    # Hillshade — dx/dy in degrees, vert_exag compensates
    ls = LightSource(azdeg=315, altdeg=35)
    hillshade = ls.hillshade(np.where(np.isnan(dem), 0, dem), vert_exag=2,
                              dx=abs(transform[0]), dy=abs(transform[4]))

    fig, ax = plt.subplots(figsize=(10, 10))

    # Hillshade background
    ax.imshow(hillshade, extent=extent, cmap="gray", alpha=0.6, origin="upper",
              aspect="auto")

    # Glacier mask from outline
    glacier_mask = ~geometry_mask(outline.geometry, out_shape=dem.shape,
                                   transform=transform, invert=False)
    dem_masked = np.where(glacier_mask, dem, np.nan)
    im = ax.imshow(dem_masked, extent=extent, cmap="terrain", alpha=0.5,
                    origin="upper", vmin=400, vmax=1700, aspect="auto")

    # Contour grid in lon/lat coordinates
    xs = np.linspace(extent[0], extent[1], cols)
    ys = np.linspace(extent[3], extent[2], rows)  # top to bottom
    X, Y = np.meshgrid(xs, ys)
    contour_dem = np.where(glacier_mask, dem, np.nan)
    cs = ax.contour(X, Y, contour_dem, levels=np.arange(500, 1700, 100),
                     colors="0.3", linewidths=0.5, alpha=0.7)
    ax.clabel(cs, cs.levels[::2], inline=True, fontsize=8, fmt="%d m")

    # Glacier outline
    outline.boundary.plot(ax=ax, color="k", linewidth=2, label="RGI7 outline (2000)")

    # Stake locations — surveyed coordinates (Dixon_Spring_2024UTM6WGS84.shp)
    stake_info = [
        ("ABL", 804, -150.894579, 59.676019, "#d6604d", "v"),
        ("ELA", 1078, -150.872020, 59.642104, "#f4a582", "s"),
        ("ACC", 1293, -150.818583, 59.637128, "#4393c3", "^"),
    ]
    for name, elev_target, lon, lat, color, marker in stake_info:
        ax.plot(lon, lat, marker=marker, ms=14, color=color,
                markeredgecolor="k", markeredgewidth=1.5, zorder=10)
        ax.annotate(f"{name}\n({elev_target} m)", (lon, lat),
                   textcoords="offset points", xytext=(15, 5),
                   fontsize=10, fontweight="bold", color=color,
                   bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))

    # Nuka SNOTEL annotation (off-map, NW direction)
    ax.annotate("Nuka SNOTEL\n375 m, ~10 km NW",
               xy=(extent[0] + 0.003, extent[3] - 0.003),
               fontsize=9, color="0.3", style="italic",
               bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

    # Colorbar
    cbar = fig.colorbar(im, ax=ax, shrink=0.5, label="Elevation (m)")

    # Scale bar — compute 2 km in degrees of longitude at this latitude
    import math
    mid_lat = (extent[2] + extent[3]) / 2
    deg_per_km = 1.0 / (111.32 * math.cos(math.radians(mid_lat)))
    bar_len_deg = 2.0 * deg_per_km  # 2 km in degrees longitude
    bar_x = extent[0] + 0.005
    bar_y = extent[2] + 0.005
    ax.plot([bar_x, bar_x + bar_len_deg], [bar_y, bar_y], "k-", lw=3,
            solid_capstyle="butt")
    ax.text(bar_x + bar_len_deg / 2, bar_y + 0.002, "2 km", ha="center",
            fontsize=10, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.7))

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Dixon Glacier — study site and observation network")
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])

    save_fig(fig, "fig_09_glacier_map")


# =====================================================================
# Figure 10: Glacier retreat — all 6 outlines overlaid
# =====================================================================
def fig_10_outline_retreat():
    import rasterio
    from rasterio.windows import from_bounds
    import geopandas as gpd
    from matplotlib.colors import LightSource
    import math

    dem_path = ROOT / "ifsar_2010" / "dixon_glacier_IFSAR_DTM_5m_full.tif"
    outline_dir = ROOT / "data" / "glacier_outlines" / "digitized"
    rgi_path = ROOT / "geodedic_mb" / "dixon_glacier_outline_rgi7.geojson"

    # Use the RGI outline to determine crop bounds (EPSG:4326)
    rgi = gpd.read_file(rgi_path)
    gbnds = rgi.total_bounds  # minx, miny, maxx, maxy
    buf_x = (gbnds[2] - gbnds[0]) * 0.15
    buf_y = (gbnds[3] - gbnds[1]) * 0.15
    crop_left = gbnds[0] - buf_x
    crop_right = gbnds[2] + buf_x
    crop_bottom = gbnds[1] - buf_y
    crop_top = gbnds[3] + buf_y

    # Windowed read of DEM
    with rasterio.open(dem_path) as src:
        crs = src.crs
        window = from_bounds(crop_left, crop_bottom, crop_right, crop_top,
                             src.transform)
        window = window.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
        dem = src.read(1, window=window).astype(float)
        transform = src.window_transform(window)

    dem[dem < 0] = np.nan

    rows, cols = dem.shape
    extent = [
        transform[2],
        transform[2] + cols * transform[0],
        transform[5] + rows * transform[4],
        transform[5],
    ]

    ls = LightSource(azdeg=315, altdeg=35)
    hillshade = ls.hillshade(np.where(np.isnan(dem), 0, dem), vert_exag=2,
                              dx=abs(transform[0]), dy=abs(transform[4]))

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(hillshade, extent=extent, cmap="gray", alpha=0.7, origin="upper",
              aspect="auto")

    # Load and plot all digitized outlines (UTM -> EPSG:4326)
    years = [2000, 2005, 2010, 2015, 2020, 2025]
    areas = {2000: 40.11, 2005: 40.11, 2010: 39.83, 2015: 39.26,
             2020: 38.59, 2025: 38.34}
    cmap_ol = plt.cm.RdYlBu_r
    colors = [cmap_ol(i / (len(years) - 1)) for i in range(len(years))]

    for yr, color in zip(years, colors):
        shp = outline_dir / f"dixon_outline_{yr}.shp"
        if not shp.exists():
            print(f"    WARNING: {shp} not found, skipping")
            continue
        gdf = gpd.read_file(shp)
        # Reproject from UTM (EPSG:32605) to EPSG:4326
        if gdf.crs and gdf.crs != crs:
            gdf = gdf.to_crs(crs)
        lw = 2.5 if yr in [2000, 2025] else 1.5
        ls_style = "-" if yr in [2000, 2025] else "--"
        gdf.boundary.plot(ax=ax, color=color, linewidth=lw, linestyle=ls_style)
        label = f"{yr}: {areas[yr]:.2f} km\u00b2"
        ax.plot([], [], color=color, lw=lw, ls=ls_style, label=label)

    ax.legend(loc="upper left", fontsize=11, framealpha=0.9,
              title="Digitized outlines", title_fontsize=12)

    # Scale bar — 2 km in degrees longitude
    mid_lat = (extent[2] + extent[3]) / 2
    deg_per_km = 1.0 / (111.32 * math.cos(math.radians(mid_lat)))
    bar_len_deg = 2.0 * deg_per_km
    bar_x = extent[0] + 0.005
    bar_y = extent[2] + 0.005
    ax.plot([bar_x, bar_x + bar_len_deg], [bar_y, bar_y], "k-", lw=3,
            solid_capstyle="butt")
    ax.text(bar_x + bar_len_deg / 2, bar_y + 0.002, "2 km", ha="center",
            fontsize=10, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.7))

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Dixon Glacier area retreat (2000\u20132025)\n"
                 f"Total: {areas[2000]:.2f} \u2192 {areas[2025]:.2f} km\u00b2 "
                 f"(\u2212{areas[2000] - areas[2025]:.2f} km\u00b2, "
                 f"\u2212{100*(areas[2000] - areas[2025])/areas[2000]:.1f}%)")
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])

    save_fig(fig, "fig_10_outline_retreat")


# =====================================================================
# Figure 11: Climate forcing with gap-fill source attribution
# =====================================================================
def fig_11_climate_forcing():
    climate = pd.read_csv(ROOT / "data" / "climate" / "dixon_gap_filled_climate.csv",
                          parse_dates=["date"], index_col="date")

    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True,
                              gridspec_kw={"height_ratios": [2, 2, 1]})

    # Temperature
    ax = axes[0]
    # Color by source
    source_colors = {
        "nuka": "#2166ac",
        "mfb": "#4393c3",
        "mcneil": "#92c5de",
        "anchor": "#d1e5f0",
        "kachemak": "#fddbc7",
        "lower_kach": "#f4a582",
        "interp": "#d6604d",
        "climatology": "#b2182b",
    }

    # Plot all temperature, then overlay colored dots for non-nuka sources
    ax.plot(climate.index, climate["temperature"], color="0.7", lw=0.3,
            alpha=0.5, zorder=1)

    # Annual rolling mean
    rolling = climate["temperature"].rolling(365, center=True, min_periods=200).mean()
    ax.plot(rolling.index, rolling, color="#2166ac", lw=2, label="365-day mean")

    # Mark non-Nuka sources
    for source, color in source_colors.items():
        if source == "nuka":
            continue
        mask = climate["temp_source"] == source
        if mask.sum() > 0:
            ax.scatter(climate.index[mask], climate["temperature"][mask],
                      c=color, s=1, alpha=0.6, label=f"{source} ({mask.sum()} days)",
                      zorder=2, rasterized=True)

    ax.set_ylabel("Temperature (°C)")
    ax.set_title("Daily temperature at Nuka SNOTEL (gap-filled, D-025)")
    ax.legend(loc="upper left", fontsize=8, ncol=2, markerscale=5)

    # Precipitation
    ax = axes[1]
    ax.bar(climate.index, climate["precipitation"], width=1, color="#4393c3",
           alpha=0.6, linewidth=0)

    # Annual total as line
    annual_p = climate["precipitation"].resample("YS").sum()
    # Plot as step function spanning each year
    for i, (date, total) in enumerate(annual_p.items()):
        end = date + pd.DateOffset(years=1)
        ax.axhline(total / 365, xmin=0, xmax=1, color="red", lw=0, alpha=0)  # placeholder

    rolling_p = climate["precipitation"].rolling(365, center=True, min_periods=200).sum()
    ax2 = ax.twinx()
    ax2.plot(rolling_p.index, rolling_p, color="#b2182b", lw=2, label="Annual total (rolling)")
    ax2.set_ylabel("Annual precip (mm)", color="#b2182b")
    ax2.tick_params(axis="y", labelcolor="#b2182b")

    ax.set_ylabel("Daily precip (mm)")
    ax.set_title("Daily precipitation at Nuka SNOTEL")

    # Source breakdown
    ax = axes[2]
    source_counts = climate["temp_source"].value_counts()
    total = len(climate)
    sources_ordered = ["nuka", "mfb", "mcneil", "anchor", "kachemak",
                       "lower_kach", "interp", "climatology"]
    bottom = 0
    for src in sources_ordered:
        count = source_counts.get(src, 0)
        if count == 0:
            continue
        color = source_colors.get(src, "0.5")
        pct = 100 * count / total
        ax.barh(0, count, left=bottom, color=color, edgecolor="white",
                label=f"{src} ({pct:.1f}%)")
        if pct > 3:
            ax.text(bottom + count / 2, 0, f"{pct:.0f}%", ha="center", va="center",
                    fontsize=9, fontweight="bold")
        bottom += count

    ax.set_xlim(0, total)
    ax.set_yticks([])
    ax.set_xlabel("Number of days")
    ax.set_title("Temperature source attribution")
    ax.legend(loc="upper right", fontsize=8, ncol=4,
              bbox_to_anchor=(1.0, -0.3))

    plt.tight_layout()
    save_fig(fig, "fig_11_climate_forcing")


# =====================================================================
# Figure 12: Model response — climate + modeled balance
# =====================================================================
def fig_12_model_response():
    climate = pd.read_csv(ROOT / "data" / "climate" / "dixon_gap_filled_climate.csv",
                          parse_dates=["date"], index_col="date")
    hist = pd.read_csv(ROOT / "validation_output" / "historical_ensemble.csv")

    # Aggregate climate by water year
    climate_wy = []
    for wy in range(1999, 2026):
        start = f"{wy-1}-10-01"
        end = f"{wy}-09-30"
        yr = climate.loc[start:end]
        if len(yr) < 300:
            continue
        summer = yr.loc[f"{wy}-06-01":f"{wy}-09-30"]
        winter = yr.loc[start:f"{wy}-05-12"]
        climate_wy.append({
            "water_year": wy,
            "annual_T": yr["temperature"].mean(),
            "summer_T": summer["temperature"].mean() if len(summer) > 0 else np.nan,
            "winter_T": winter["temperature"].mean() if len(winter) > 0 else np.nan,
            "annual_P": yr["precipitation"].sum(),
            "winter_P": winter["precipitation"].sum() if len(winter) > 0 else np.nan,
        })
    cdf = pd.DataFrame(climate_wy)

    # Model balance
    summary = hist.groupby("water_year").agg(
        Ba_mean=("annual_balance", "mean"), Ba_std=("annual_balance", "std"),
        Bw_mean=("winter_balance", "mean"), Bw_std=("winter_balance", "std"),
        Bs_mean=("summer_balance", "mean"), Bs_std=("summer_balance", "std"),
    ).reset_index()

    merged = cdf.merge(summary, on="water_year")
    years = merged["water_year"].values

    fig, axes = plt.subplots(4, 1, figsize=(14, 14), sharex=True,
                              gridspec_kw={"height_ratios": [1.2, 1.2, 1.5, 1.5]})

    # Panel A: Summer temperature
    ax = axes[0]
    ax.bar(years, merged["summer_T"], color="#d6604d", alpha=0.7, edgecolor="none")
    mean_st = merged["summer_T"].mean()
    ax.axhline(mean_st, color="k", ls="--", lw=0.8, alpha=0.5)
    ax.text(years[-1] + 0.3, mean_st, f"mean={mean_st:.1f}°C", fontsize=9, va="bottom")
    ax.set_ylabel("Summer T (°C)\n(Jun–Sep)")
    ax.set_title("Climate forcing and modeled mass balance response (WY1999–2025)")

    # Panel B: Winter precipitation
    ax = axes[1]
    ax.bar(years, merged["winter_P"], color="#4393c3", alpha=0.7, edgecolor="none")
    mean_wp = merged["winter_P"].mean()
    ax.axhline(mean_wp, color="k", ls="--", lw=0.8, alpha=0.5)
    ax.text(years[-1] + 0.3, mean_wp, f"mean={mean_wp:.0f} mm", fontsize=9, va="bottom")
    ax.set_ylabel("Winter precip (mm)\n(Oct–May)")

    # Panel C: Winter and summer balance
    ax = axes[2]
    bar_w = 0.35
    ax.bar(years - bar_w/2, merged["Bw_mean"], bar_w, color="#4393c3", alpha=0.8,
           label="Winter ($B_w$)")
    ax.bar(years + bar_w/2, merged["Bs_mean"], bar_w, color="#d6604d", alpha=0.8,
           label="Summer ($B_s$)")
    ax.axhline(0, color="k", lw=0.5)
    ax.set_ylabel("Seasonal balance\n(m w.e.)")
    ax.legend(loc="lower left", ncol=2)

    # Panel D: Annual balance with climate correlation
    ax = axes[3]
    ax.errorbar(years, merged["Ba_mean"], yerr=merged["Ba_std"],
                fmt="ko-", ms=5, lw=1.5, capsize=3, label="Annual ($B_a$)")
    ax.axhline(0, color="k", lw=0.5)

    # Geodetic reference
    ax.axhline(-0.939, color="#b2182b", ls="--", lw=1.5, alpha=0.7)
    ax.text(years[0] - 0.5, -0.939, "Geodetic\n(−0.94)", fontsize=9,
            color="#b2182b", va="top", ha="right")

    mean_ba = merged["Ba_mean"].mean()
    ax.axhline(mean_ba, color="0.5", ls=":", lw=1)
    ax.text(years[-1] + 0.3, mean_ba, f"model mean={mean_ba:.2f}", fontsize=9, va="bottom")

    ax.set_ylabel("Annual balance\n(m w.e.)")
    ax.set_xlabel("Water year")
    ax.legend(loc="lower left")

    # Annotate correlation
    from scipy.stats import pearsonr
    r_T, p_T = pearsonr(merged["summer_T"], merged["Ba_mean"])
    r_P, p_P = pearsonr(merged["winter_P"], merged["Ba_mean"])
    ax.text(0.98, 0.95,
            f"$B_a$ vs summer T: r={r_T:.2f} (p={p_T:.3f})\n"
            f"$B_a$ vs winter P: r={r_P:.2f} (p={p_P:.3f})",
            transform=ax.transAxes, fontsize=10, va="top", ha="right",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", alpha=0.9))

    plt.tight_layout()
    save_fig(fig, "fig_12_model_response")


# =====================================================================
# Main
# =====================================================================
if __name__ == "__main__":
    print("Generating context figures...\n")

    print("Figure 9: Glacier map...")
    try:
        fig_09_glacier_map()
    except Exception as e:
        print(f"  ERROR: {e}")

    print("Figure 10: Outline retreat...")
    try:
        fig_10_outline_retreat()
    except Exception as e:
        print(f"  ERROR: {e}")

    print("Figure 11: Climate forcing...")
    fig_11_climate_forcing()

    print("Figure 12: Model response...")
    fig_12_model_response()

    print("\nDone.")
