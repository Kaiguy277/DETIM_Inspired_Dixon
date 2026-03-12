"""
Diagnostic plots for the multi-station gap-filling pipeline (D-025).

Produces 4-panel figure:
  1. Source timeline — color strip showing data source per day
  2. Per-WY quality table — source fractions by water year
  3. Before/after comparison for WY2000, 2001, 2005, 2020
  4. Transfer validation scatter — predicted vs actual Nuka T

Usage:
    python plot_climate_gap_fill_diagnostics.py
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
CLIMATE_PATH = PROJECT / 'data' / 'climate' / 'dixon_gap_filled_climate.csv'
NUKA_RAW_PATH = PROJECT / 'data' / 'climate' / 'nuka_snotel_full.csv'
OUTPUT_DIR = PROJECT / 'calibration_output'

# Source colors
SOURCE_COLORS = {
    'nuka': '#2166ac',
    'mfb': '#d6604d',
    'mcneil': '#4daf4a',
    'anchor': '#ff7f00',
    'kachemak': '#984ea3',
    'lower_kach': '#a65628',
    'interp': '#999999',
    'climatology': '#e41a1c',
}


def main():
    print("Loading gap-filled climate...")
    gf = pd.read_csv(CLIMATE_PATH, parse_dates=['date'], index_col='date')

    print("Loading raw Nuka SNOTEL...")
    from dixon_melt.climate import load_nuka_snotel
    nuka_raw = load_nuka_snotel(str(NUKA_RAW_PATH))

    # Build old-style climate (what the model used to see)
    nuka_old = nuka_raw[['tavg_c', 'precip_mm']].rename(
        columns={'tavg_c': 'temperature', 'precip_mm': 'precipitation'})
    nuka_old['temperature'] = nuka_old['temperature'].interpolate(
        method='linear', limit=3)
    nuka_old['temperature'] = nuka_old['temperature'].ffill().fillna(0)
    nuka_old['precipitation'] = nuka_old['precipitation'].fillna(0)

    # ── Figure 1: Source timeline ────────────────────────────────────
    fig, axes = plt.subplots(4, 1, figsize=(18, 16))

    # Panel 1: Temperature source timeline
    ax = axes[0]
    sources = gf['temp_source'].unique()
    for src in sources:
        mask = gf['temp_source'] == src
        dates = gf.index[mask]
        color = SOURCE_COLORS.get(src, '#333333')
        ax.scatter(dates, np.ones(len(dates)), c=color, s=0.3, marker='|',
                   linewidths=0.5, label=src)

    ax.set_yticks([])
    ax.set_ylabel('T source')
    ax.set_title('Temperature Data Source per Day (D-025)', fontsize=13)
    # Legend
    handles = [Patch(facecolor=SOURCE_COLORS.get(s, '#333'), label=s)
               for s in sources if s]
    ax.legend(handles=handles, loc='upper left', ncol=len(handles), fontsize=8)
    ax.set_xlim(gf.index[0], gf.index[-1])

    # Panel 2: Precip source timeline
    ax = axes[1]
    sources_p = gf['precip_source'].unique()
    for src in sources_p:
        mask = gf['precip_source'] == src
        dates = gf.index[mask]
        color = SOURCE_COLORS.get(src, '#333333')
        ax.scatter(dates, np.ones(len(dates)), c=color, s=0.3, marker='|',
                   linewidths=0.5, label=src)
    ax.set_yticks([])
    ax.set_ylabel('P source')
    ax.set_title('Precipitation Data Source per Day', fontsize=13)
    handles_p = [Patch(facecolor=SOURCE_COLORS.get(s, '#333'), label=s)
                 for s in sources_p if s]
    ax.legend(handles=handles_p, loc='upper left', ncol=len(handles_p), fontsize=8)
    ax.set_xlim(gf.index[0], gf.index[-1])

    # Panel 3: Before/after temperature for gap years
    ax = axes[2]
    gap_wys = [2000, 2001, 2005, 2020]
    colors_ba = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3']

    for i, wy in enumerate(gap_wys):
        start = f'{wy-1}-10-01'
        end = f'{wy}-09-30'

        # Old (fillna(0))
        old_sub = nuka_old.loc[start:end, 'temperature'] if start in nuka_old.index.strftime('%Y-%m-%d').values or True else pd.Series()
        old_sub = nuka_old.loc[start:end, 'temperature']

        # New (gap-filled)
        new_sub = gf.loc[start:end, 'temperature']

        # Monthly means
        if len(old_sub) > 0:
            old_monthly = old_sub.resample('MS').mean()
            new_monthly = new_sub.resample('MS').mean()
            ax.plot(old_monthly.index, old_monthly.values, '--',
                    color=colors_ba[i], alpha=0.5, lw=1)
            ax.plot(new_monthly.index, new_monthly.values, '-',
                    color=colors_ba[i], alpha=0.9, lw=2, label=f'WY{wy}')

    ax.axhline(0, color='k', lw=0.5, alpha=0.5)
    ax.set_ylabel('Monthly Mean T (°C)')
    ax.set_title('Before (dashed) vs After (solid) Gap-Fill — Monthly Mean T',
                 fontsize=13)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Panel 4: Before/after cumulative precip for WY2020
    ax = axes[3]
    start_2020 = '2019-10-01'
    end_2020 = '2020-09-30'

    old_p = nuka_old.loc[start_2020:end_2020, 'precipitation'].cumsum()
    new_p = gf.loc[start_2020:end_2020, 'precipitation'].cumsum()

    ax.plot(old_p.index, old_p.values, 'r-', lw=2, label='Old (fillna=0): '
            f'{old_p.iloc[-1]:.0f}mm')
    ax.plot(new_p.index, new_p.values, 'b-', lw=2, label='Gap-filled (D-025): '
            f'{new_p.iloc[-1]:.0f}mm')
    ax.fill_between(new_p.index, old_p.values, new_p.values, alpha=0.15, color='blue')
    ax.set_ylabel('Cumulative Precip (mm)')
    ax.set_title('WY2020 Cumulative Precipitation: Before vs After Gap-Fill', fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out_path = OUTPUT_DIR / 'climate_gap_fill_diagnostics.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {out_path}")

    # ── Per-WY summary table plot ────────────────────────────────────
    fig, ax = plt.subplots(figsize=(14, 8))

    gf_copy = gf.copy()
    gf_copy['wy'] = gf_copy.index.year
    gf_copy.loc[gf_copy.index.month >= 10, 'wy'] += 1

    wys = sorted(gf_copy['wy'].unique())
    src_order = ['nuka', 'mfb', 'mcneil', 'anchor', 'kachemak', 'lower_kach',
                 'interp', 'climatology']

    bottoms = np.zeros(len(wys))
    for src in src_order:
        fracs = []
        for wy in wys:
            grp = gf_copy[gf_copy['wy'] == wy]
            frac = (grp['temp_source'] == src).mean()
            fracs.append(frac)
        fracs = np.array(fracs)
        if fracs.sum() > 0:
            ax.bar(range(len(wys)), fracs, bottom=bottoms,
                   color=SOURCE_COLORS.get(src, '#333'),
                   label=src, width=0.8)
            bottoms += fracs

    ax.set_xticks(range(len(wys)))
    ax.set_xticklabels(wys, rotation=45, fontsize=8)
    ax.set_ylabel('Fraction of Days')
    ax.set_title('Temperature Source Fraction by Water Year (D-025)', fontsize=13)
    ax.legend(loc='lower right', fontsize=9)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    out_path2 = OUTPUT_DIR / 'climate_gap_fill_by_wy.png'
    fig.savefig(out_path2, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {out_path2}")

    print("Done.")


if __name__ == '__main__':
    main()
