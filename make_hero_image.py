"""
Generate hero image for Agent Madness submission.

Top row: WY 2000 vs WY 2100 (two emission scenarios) glacier maps
Bottom row: discharge time series + area/volume change from projection CSVs
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path

PROJ_DIR = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
FRAME_DIR = PROJ_DIR / 'projection_output' / 'PROJ-008_animation-2000-2100_2026-03-14'
SSP245_CSV = PROJ_DIR / 'projection_output' / 'PROJ-004_top250_ssp245_2026-03-14' / 'projection_ssp245_ensemble_2100.csv'
SSP585_CSV = PROJ_DIR / 'projection_output' / 'PROJ-005_top250_ssp585_2026-03-14' / 'projection_ssp585_ensemble_2100.csv'
OUTPUT = PROJ_DIR / 'hero_image.png'

BG = '#1a1a2e'
C245 = '#1b9e77'
C585 = '#d95f02'
CGRAY = '#888888'


def smooth(y, window=11):
    """Simple moving-average smoothing with edge handling."""
    kernel = np.ones(window) / window
    ys = np.convolve(y, kernel, mode='same')
    hw = window // 2
    for k in range(hw):
        ys[k] = y[:2*k+1].mean()
        ys[-(k+1)] = y[-(2*k+1):].mean()
    return ys


def main():
    # ── Load map frames ──────────────────────────────────────────────
    frame_2000 = mpimg.imread(str(FRAME_DIR / 'frame_2000.png'))
    frame_2100 = mpimg.imread(str(FRAME_DIR / 'frame_2100.png'))

    h, w = frame_2000.shape[:2]
    mid_w = w // 2

    # Crop to just map + stats (below original SSP title, above area bars)
    top_frac, bot_frac = 0.16, 0.58
    t, b = int(h * top_frac), int(h * bot_frac)

    panel_2000 = frame_2000[t:b, :mid_w]
    panel_2100_245 = frame_2100[t:b, :mid_w]
    panel_2100_585 = frame_2100[t:b, mid_w:]

    # ── Load projection data ─────────────────────────────────────────
    df245 = pd.read_csv(SSP245_CSV)
    df585 = pd.read_csv(SSP585_CSV)

    years = df245['year'].values
    init_area = 40.11  # km²
    init_vol = 6.872   # km³

    # Smooth discharge
    q245 = smooth(df245['mean_annual_discharge_m3s_mean'].values)
    q585 = smooth(df585['mean_annual_discharge_m3s_mean'].values)

    area245 = df245['area_km2_mean'].values
    area585 = df585['area_km2_mean'].values

    vol245 = df245['volume_km3_mean'].values
    vol585 = df585['volume_km3_mean'].values

    # ── Build figure ─────────────────────────────────────────────────
    fig = plt.figure(figsize=(30, 12), facecolor=BG)

    # Title — compact to save vertical space
    fig.text(0.5, 0.97, 'Meltwater to Megawatts',
             ha='center', va='top', fontsize=44, fontweight='bold',
             color='white', fontfamily='sans-serif')
    fig.text(0.5, 0.925,
             'Modeling Dixon Glacier Peak Water for Renewable Energy Applications',
             ha='center', va='top', fontsize=20, color='#cccccc',
             fontfamily='sans-serif')

    # Layout: top row = 3 map panels, bottom row = 3 data plots
    gs = fig.add_gridspec(2, 3,
                          left=0.04, right=0.96, top=0.85, bottom=0.08,
                          wspace=0.08, hspace=0.22,
                          height_ratios=[1.4, 1])

    # ── Top row: glacier maps ────────────────────────────────────────
    map_panels = [
        (gs[0, 0], panel_2000, 'WY 2000 — Present Day', '#88ccff'),
        (gs[0, 1], panel_2100_245, 'WY 2100 — SSP2-4.5 (moderate)', C245),
        (gs[0, 2], panel_2100_585, 'WY 2100 — SSP5-8.5 (high emissions)', C585),
    ]

    for gspec, img, title, color in map_panels:
        ax = fig.add_subplot(gspec)
        ax.imshow(img, interpolation='lanczos')
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(title, color=color, fontsize=20, fontweight='bold', pad=12)
        for spine in ax.spines.values():
            spine.set_color('#444466')
            spine.set_linewidth(1.5)

    # ── Bottom-left: Mean Annual Discharge ───────────────────────────
    def style_ax(ax, ylabel):
        ax.set_facecolor('#22223a')
        ax.tick_params(colors='white', labelsize=13)
        ax.set_xlabel('Water Year', color='white', fontsize=15)
        ax.set_ylabel(ylabel, color='white', fontsize=15)
        ax.set_xlim(years[0] - 1, years[-1] + 1)
        ax.axvline(2025.5, color='#555555', ls='--', lw=0.8, alpha=0.6)
        for s in ['top', 'right']:
            ax.spines[s].set_visible(False)
        for s in ['bottom', 'left']:
            ax.spines[s].set_color('#555555')

    ax_q = fig.add_subplot(gs[1, 0])
    style_ax(ax_q, 'Mean Discharge (m³/s)')
    ax_q.fill_between(years, q245, alpha=0.15, color=C245)
    ax_q.fill_between(years, q585, alpha=0.15, color=C585)
    ax_q.plot(years, q245, color=C245, lw=2.5, label='SSP2-4.5')
    ax_q.plot(years, q585, color=C585, lw=2.5, label='SSP5-8.5')

    # Mark peak water years
    pk245_yr = years[np.argmax(q245)]
    pk585_yr = years[np.argmax(q585)]
    ax_q.axvline(pk245_yr, color=C245, ls=':', lw=1.5, alpha=0.7)
    ax_q.axvline(pk585_yr, color=C585, ls=':', lw=1.5, alpha=0.7)
    ax_q.annotate(f'Peak Water\nWY {pk245_yr}', xy=(pk245_yr, q245.max()),
                  xytext=(pk245_yr - 18, q245.max() * 1.05),
                  color=C245, fontsize=13, fontweight='bold',
                  arrowprops=dict(arrowstyle='->', color=C245, lw=1.5))
    ax_q.annotate(f'Peak Water\nWY {pk585_yr}', xy=(pk585_yr, q585.max()),
                  xytext=(pk585_yr + 5, q585.max() * 1.02),
                  color=C585, fontsize=13, fontweight='bold',
                  arrowprops=dict(arrowstyle='->', color=C585, lw=1.5))

    ax_q.set_title('Meltwater Discharge', color='white', fontsize=18,
                    fontweight='bold', pad=10)
    ax_q.legend(loc='lower left', fontsize=13, facecolor=BG,
                edgecolor='#555555', labelcolor='white')

    # ── Bottom-center: Glacier Area ──────────────────────────────────
    ax_a = fig.add_subplot(gs[1, 1])
    style_ax(ax_a, 'Area (km²)')
    ax_a.fill_between(years, area245, alpha=0.15, color=C245)
    ax_a.fill_between(years, area585, alpha=0.15, color=C585)
    ax_a.plot(years, area245, color=C245, lw=2.5, label='SSP2-4.5')
    ax_a.plot(years, area585, color=C585, lw=2.5, label='SSP5-8.5')
    ax_a.set_ylim(0, init_area * 1.08)
    ax_a.axhline(init_area, color=CGRAY, ls='--', lw=0.8, alpha=0.5)

    # End-of-century labels
    a245_end = area245[-1]
    a585_end = area585[-1]
    ax_a.annotate(f'{a245_end:.0f} km² ({100*a245_end/init_area:.0f}%)',
                  xy=(years[-1], a245_end), xytext=(-60, 15),
                  textcoords='offset points', color=C245, fontsize=13,
                  fontweight='bold',
                  arrowprops=dict(arrowstyle='->', color=C245, lw=1.2))
    ax_a.annotate(f'{a585_end:.0f} km² ({100*a585_end/init_area:.0f}%)',
                  xy=(years[-1], a585_end), xytext=(-60, -20),
                  textcoords='offset points', color=C585, fontsize=13,
                  fontweight='bold',
                  arrowprops=dict(arrowstyle='->', color=C585, lw=1.2))

    ax_a.set_title('Glacier Area', color='white', fontsize=18,
                    fontweight='bold', pad=10)
    ax_a.legend(loc='upper right', fontsize=13, facecolor=BG,
                edgecolor='#555555', labelcolor='white')

    # ── Bottom-right: Ice Volume ─────────────────────────────────────
    ax_v = fig.add_subplot(gs[1, 2])
    style_ax(ax_v, 'Volume (km³)')
    ax_v.fill_between(years, vol245, alpha=0.15, color=C245)
    ax_v.fill_between(years, vol585, alpha=0.15, color=C585)
    ax_v.plot(years, vol245, color=C245, lw=2.5, label='SSP2-4.5')
    ax_v.plot(years, vol585, color=C585, lw=2.5, label='SSP5-8.5')
    ax_v.set_ylim(0, init_vol * 1.08)
    ax_v.axhline(init_vol, color=CGRAY, ls='--', lw=0.8, alpha=0.5)

    v245_end = vol245[-1]
    v585_end = vol585[-1]
    ax_v.annotate(f'{v245_end:.2f} km³ ({100*v245_end/init_vol:.0f}%)',
                  xy=(years[-1], v245_end), xytext=(-60, 15),
                  textcoords='offset points', color=C245, fontsize=13,
                  fontweight='bold',
                  arrowprops=dict(arrowstyle='->', color=C245, lw=1.2))
    ax_v.annotate(f'{v585_end:.2f} km³ ({100*v585_end/init_vol:.0f}%)',
                  xy=(years[-1], v585_end), xytext=(-60, -20),
                  textcoords='offset points', color=C585, fontsize=13,
                  fontweight='bold',
                  arrowprops=dict(arrowstyle='->', color=C585, lw=1.2))

    ax_v.set_title('Ice Volume', color='white', fontsize=18,
                    fontweight='bold', pad=10)
    ax_v.legend(loc='upper right', fontsize=13, facecolor=BG,
                edgecolor='#555555', labelcolor='white')

    # ── Bottom annotation ────────────────────────────────────────────
    fig.text(0.5, 0.02,
             'Dixon Glacier, Kenai Peninsula, Alaska  ·  250-member Bayesian ensemble  ·  5 CMIP6 GCMs  ·  Hock (1999) DETIM  ·  Built with Claude Code',
             ha='center', va='bottom', fontsize=14, color='#888888',
             fontfamily='sans-serif')

    fig.savefig(str(OUTPUT), dpi=200, facecolor=fig.get_facecolor(),
                bbox_inches='tight', pad_inches=0.3)
    plt.close(fig)
    print(f"Saved: {OUTPUT}")


if __name__ == '__main__':
    main()
