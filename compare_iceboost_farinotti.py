"""Compare IceBoost v2.0 ice thickness estimate to Farinotti 2019 for Dixon Glacier."""
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import Resampling, reproject
from rasterio.windows import Window
import matplotlib.pyplot as plt

FAR = Path("data/ice_thickness/RGI60-01.18059_thickness.tif")
ICE = Path("data/ice_thickness/iceboost/RGI60-01.18059.tif")
OUT = Path("data/ice_thickness/iceboost/comparison")
OUT.mkdir(exist_ok=True, parents=True)

# Load Farinotti (25m) and IceBoost (100m), both EPSG:32605
with rasterio.open(FAR) as fs:
    far = fs.read(1).astype(np.float32)
    far_transform = fs.transform
    far_crs = fs.crs
    far_bounds = fs.bounds
with rasterio.open(ICE) as ics:
    ice = ics.read(1).astype(np.float32)
    ice_err = ics.read(2).astype(np.float32)
    ice_transform = ics.transform
    ice_crs = ics.crs
    ice_meta = ics.tags()
    ice_bounds = ics.bounds

# Resample Farinotti -> IceBoost 100m grid using average resampling
far_on_100 = np.zeros(ice.shape, dtype=np.float32)
reproject(
    source=far, destination=far_on_100,
    src_transform=far_transform, src_crs=far_crs,
    dst_transform=ice_transform, dst_crs=ice_crs,
    resampling=Resampling.average,
)

# Masks: IceBoost has thickness everywhere on the glacier footprint (min 27m).
# Farinotti has zero outside ice; use >0 as ice mask after resampling.
far_ice = far_on_100 > 1.0  # >1 m after averaging (drops partial-edge pixels)
ice_ice = ice > 0
common = far_ice & ice_ice

px_area_m2 = 100.0 * 100.0
vol_far = np.sum(far_on_100[far_ice]) * px_area_m2 / 1e9  # km^3
vol_ice = np.sum(ice[ice_ice]) * px_area_m2 / 1e9
vol_ice_meta = float(ice_meta["volume"])
vol_ice_err = float(ice_meta["volume_error"])
area_ice_meta = float(ice_meta["area"])

print(f"Farinotti (on 100m):  n_px={far_ice.sum():5d}  area={far_ice.sum()*px_area_m2/1e6:6.2f} km²  "
      f"volume={vol_far:6.3f} km³  mean={np.nanmean(far_on_100[far_ice]):6.1f} m  "
      f"max={np.nanmax(far_on_100[far_ice]):6.1f} m")
print(f"IceBoost:             n_px={ice_ice.sum():5d}  area={ice_ice.sum()*px_area_m2/1e6:6.2f} km²  "
      f"volume={vol_ice:6.3f} km³  mean={np.nanmean(ice[ice_ice]):6.1f} m  "
      f"max={np.nanmax(ice[ice_ice]):6.1f} m  (meta: {vol_ice_meta:.3f} ± {vol_ice_err:.3f} km³, "
      f"area {area_ice_meta:.2f} km²)")

# Paired pixel comparison
diff = ice - far_on_100
paired_far = far_on_100[common]
paired_ice = ice[common]
paired_diff = paired_ice - paired_far
print(f"\nCommon pixels: {common.sum()}")
print(f"  IceBoost − Farinotti mean diff: {paired_diff.mean():+.1f} m   median: {np.median(paired_diff):+.1f} m")
print(f"  RMS diff: {np.sqrt(np.mean(paired_diff**2)):.1f} m")
print(f"  Pearson r: {np.corrcoef(paired_far, paired_ice)[0,1]:.3f}")
pct = 100 * paired_diff.sum() / paired_far.sum()
print(f"  Volume difference on common mask: {pct:+.1f}% (IceBoost vs Farinotti)")

# Elevation-band hypsometry: need surface elevation. IceBoost band 4 is h_wgs84.
with rasterio.open(ICE) as ics:
    h_wgs84 = ics.read(4).astype(np.float32)
    n_geoid = ics.read(5).astype(np.float32)
elev_m = h_wgs84 - n_geoid  # orthometric, roughly MSL

bands = np.arange(400, 1600, 100)
print("\nElevation band  |  Farinotti mean  |  IceBoost mean  |  diff")
print("-" * 65)
for z0, z1 in zip(bands[:-1], bands[1:]):
    m = common & (elev_m >= z0) & (elev_m < z1)
    if m.sum() < 5:
        continue
    fm = far_on_100[m].mean()
    im = ice[m].mean()
    print(f" {z0:4.0f}–{z1:4.0f} m     |   {fm:7.1f} m      |   {im:7.1f} m   |  {im-fm:+.1f} m  (n={m.sum()})")

# --- Plots ---
fig, axes = plt.subplots(2, 2, figsize=(12, 11))
vmax = max(np.nanmax(far_on_100), np.nanmax(ice))

im0 = axes[0, 0].imshow(np.where(far_ice, far_on_100, np.nan), cmap="viridis", vmin=0, vmax=vmax)
axes[0, 0].set_title(f"Farinotti 2019 (100m avg)\nvol = {vol_far:.2f} km³, max = {np.nanmax(far_on_100[far_ice]):.0f} m")
plt.colorbar(im0, ax=axes[0, 0], label="thickness (m)")

im1 = axes[0, 1].imshow(np.where(ice_ice, ice, np.nan), cmap="viridis", vmin=0, vmax=vmax)
axes[0, 1].set_title(f"IceBoost v2.0\nvol = {vol_ice_meta:.2f} ± {vol_ice_err:.2f} km³, max = {np.nanmax(ice):.0f} m")
plt.colorbar(im1, ax=axes[0, 1], label="thickness (m)")

d = np.where(common, diff, np.nan)
dmax = np.nanpercentile(np.abs(d), 99)
im2 = axes[1, 0].imshow(d, cmap="RdBu_r", vmin=-dmax, vmax=dmax)
axes[1, 0].set_title(f"IceBoost − Farinotti\nmean diff = {paired_diff.mean():+.1f} m, r = {np.corrcoef(paired_far, paired_ice)[0,1]:.2f}")
plt.colorbar(im2, ax=axes[1, 0], label="Δ thickness (m)")

ax = axes[1, 1]
ax.hexbin(paired_far, paired_ice, gridsize=40, mincnt=1, cmap="magma")
lim = max(paired_far.max(), paired_ice.max()) * 1.05
ax.plot([0, lim], [0, lim], "k--", lw=1, label="1:1")
ax.set_xlabel("Farinotti 2019 thickness (m)")
ax.set_ylabel("IceBoost v2.0 thickness (m)")
ax.set_xlim(0, lim); ax.set_ylim(0, lim)
ax.set_aspect("equal")
ax.legend(loc="lower right")
ax.set_title("Pixel-wise scatter (100m grid)")

plt.suptitle("Dixon Glacier (RGI60-01.18059): IceBoost v2.0 vs Farinotti 2019", fontsize=13, y=1.00)
plt.tight_layout()
out_png = OUT / "iceboost_vs_farinotti.png"
plt.savefig(out_png, dpi=150, bbox_inches="tight")
print(f"\nWrote {out_png}")
