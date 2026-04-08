"""
Plot full historical climate record for Dixon Glacier DETIM.

Single multi-panel figure: all raw stations overlaid, gap-filled record
with source coloring, annual summary, and station coverage.
"""
import sys
sys.path.insert(0, '.')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.colors import ListedColormap
from pathlib import Path
from dixon_melt import config
from dixon_melt.climate import load_all_stations, load_gap_filled_climate

PROJECT = Path(__file__).parent

# ── Load everything ──────────────────────────────────────────────────
print("Loading stations...")
stations = load_all_stations(PROJECT)
print("Loading gap-filled record...")
gf = load_gap_filled_climate(project_root=PROJECT)

# Station display config
STATION_STYLE = {
    'nuka':       ('Nuka SNOTEL (375 m)',           '#1f77b4'),
    'mfb':        ('Middle Fork Bradley (701 m)',    '#ff7f0e'),
    'mcneil':     ('McNeil Canyon (411 m)',          '#2ca02c'),
    'anchor':     ('Anchor River Divide (503 m)',    '#d62728'),
    'kachemak':   ('Kachemak Creek (503 m)',         '#9467bd'),
    'lower_kach': ('Lower Kachemak Ck (597 m)',      '#8c564b'),
}

SOURCE_COLORS = {
    'nuka': '#1f77b4', 'mfb': '#ff7f0e', 'mcneil': '#2ca02c',
    'anchor': '#d62728', 'kachemak': '#9467bd', 'lower_kach': '#8c564b',
    'interp': '#e377c2', 'climatology': '#7f7f7f',
}

date_min = pd.Timestamp('1998-10-01')
date_max = pd.Timestamp('2025-09-30')

# Water year aggregations
gf_wy = gf.copy()
gf_wy['wy'] = gf_wy.index.year
gf_wy.loc[gf_wy.index.month >= 10, 'wy'] += 1
annual = gf_wy.groupby('wy').agg(
    mean_T=('temperature', 'mean'),
    total_P=('precipitation', 'sum'),
    nuka_T_frac=('temp_source', lambda x: (x == 'nuka').mean()),
    nuka_P_frac=('precip_source', lambda x: (x == 'nuka').mean()),
)


# ══════════════════════════════════════════════════════════════════════
# BUILD SINGLE FIGURE — 8 panels
# ══════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(20, 32))
gs = fig.add_gridspec(8, 1, height_ratios=[2, 2, 2, 0.6, 2, 0.6, 2, 1.5],
                      hspace=0.35)

panel_label = iter('abcdefgh')


# ── (a) All station temperatures ─────────────────────────────────────
ax_a = fig.add_subplot(gs[0])
for key, (label, color) in STATION_STYLE.items():
    if key in stations and 'tavg_c' in stations[key].columns:
        s = stations[key]['tavg_c'].loc[date_min:date_max]
        s_smooth = s.rolling(30, center=True, min_periods=10).mean()
        ax_a.plot(s_smooth.index, s_smooth.values, color=color, alpha=0.7,
                  linewidth=0.9, label=label)

ax_a.set_xlim(date_min, date_max)
ax_a.set_ylabel('Temperature (°C)')
ax_a.set_title('(a) All SNOTEL Station Temperatures — 30-day Rolling Mean', loc='left', fontweight='bold')
ax_a.legend(loc='upper right', fontsize=7, ncol=3)
ax_a.axhline(0, color='grey', linewidth=0.5, linestyle='--')
ax_a.xaxis.set_major_locator(mdates.YearLocator(2))
ax_a.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax_a.grid(True, alpha=0.3)


# ── (b) All station precipitation ────────────────────────────────────
ax_b = fig.add_subplot(gs[1], sharex=ax_a)
for key, (label, color) in STATION_STYLE.items():
    if key in stations and 'precip_mm' in stations[key].columns:
        s = stations[key]['precip_mm'].loc[date_min:date_max]
        s_monthly = s.resample('ME').sum()
        ax_b.plot(s_monthly.index, s_monthly.values, color=color, alpha=0.7,
                  linewidth=0.9, label=label)

ax_b.set_ylabel('Precip (mm/month)')
ax_b.set_title('(b) All SNOTEL Station Precipitation — Monthly Totals', loc='left', fontweight='bold')
ax_b.legend(loc='upper right', fontsize=7, ncol=3)
ax_b.xaxis.set_major_locator(mdates.YearLocator(2))
ax_b.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax_b.grid(True, alpha=0.3)


# ── (c) Gap-filled temperature + fill source dots ────────────────────
ax_c = fig.add_subplot(gs[2], sharex=ax_a)
t_smooth = gf['temperature'].rolling(30, center=True, min_periods=10).mean()
ax_c.plot(t_smooth.index, t_smooth.values, color='#1f77b4', linewidth=0.8, alpha=0.9)

for src, color in SOURCE_COLORS.items():
    if src == 'nuka':
        continue
    mask = gf['temp_source'] == src
    if mask.any():
        ax_c.scatter(gf.index[mask], gf.loc[mask, 'temperature'],
                     color=color, s=2, alpha=0.6, label=src)

ax_c.set_ylabel('Temperature (°C)')
ax_c.set_title('(c) Gap-Filled Temperature — Composite Record (fill sources as dots)', loc='left', fontweight='bold')
ax_c.axhline(0, color='grey', linewidth=0.5, linestyle='--')
ax_c.legend(loc='upper right', fontsize=7, ncol=4, markerscale=4)
ax_c.grid(True, alpha=0.3)


# ── (d) Temperature source bar ───────────────────────────────────────
ax_d = fig.add_subplot(gs[3], sharex=ax_a)
t_unique = sorted(gf['temp_source'].unique())
t_src_num = gf['temp_source'].map({s: i for i, s in enumerate(t_unique)}).values
t_cmap = ListedColormap([SOURCE_COLORS.get(s, '#333') for s in t_unique])
extent = [mdates.date2num(gf.index[0]), mdates.date2num(gf.index[-1]), 0, 1]
ax_d.imshow(t_src_num.reshape(1, -1), aspect='auto', extent=extent,
            cmap=t_cmap, vmin=-0.5, vmax=len(t_unique)-0.5, interpolation='nearest')
ax_d.set_yticks([])
ax_d.set_ylabel('T src', fontsize=8)
ax_d.xaxis_date()
ax_d.xaxis.set_major_locator(mdates.YearLocator(2))
ax_d.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
t_legend = [Line2D([0], [0], marker='s', color='w',
                   markerfacecolor=SOURCE_COLORS.get(s, '#333'),
                   markersize=7, label=s) for s in t_unique]
ax_d.legend(handles=t_legend, loc='center left', fontsize=6, ncol=len(t_unique),
            bbox_to_anchor=(0, -0.6))


# ── (e) Gap-filled precipitation ─────────────────────────────────────
ax_e = fig.add_subplot(gs[4], sharex=ax_a)
gf_copy = gf.copy()
gf_copy['ym'] = gf_copy.index.to_period('M')
monthly_p = gf_copy.groupby('ym')['precipitation'].sum()
monthly_p.index = monthly_p.index.to_timestamp()
monthly_src = gf_copy.groupby('ym')['precip_source'].agg(lambda x: x.value_counts().index[0])
monthly_src.index = monthly_src.index.to_timestamp()
bar_colors = [SOURCE_COLORS.get(s, '#1f77b4') for s in monthly_src.values]
ax_e.bar(monthly_p.index, monthly_p.values, width=25, color=bar_colors, alpha=0.8)
ax_e.set_ylabel('Precip (mm/month)')
ax_e.set_title('(e) Gap-Filled Precipitation — Monthly Totals (colored by dominant source)', loc='left', fontweight='bold')
ax_e.grid(True, alpha=0.3)


# ── (f) Precipitation source bar ─────────────────────────────────────
ax_f = fig.add_subplot(gs[5], sharex=ax_a)
p_unique = sorted(gf['precip_source'].unique())
p_src_num = gf['precip_source'].map({s: i for i, s in enumerate(p_unique)}).values
p_cmap = ListedColormap([SOURCE_COLORS.get(s, '#333') for s in p_unique])
ax_f.imshow(p_src_num.reshape(1, -1), aspect='auto', extent=extent,
            cmap=p_cmap, vmin=-0.5, vmax=len(p_unique)-0.5, interpolation='nearest')
ax_f.set_yticks([])
ax_f.set_ylabel('P src', fontsize=8)
ax_f.xaxis_date()
ax_f.xaxis.set_major_locator(mdates.YearLocator(2))
ax_f.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
p_legend = [Line2D([0], [0], marker='s', color='w',
                   markerfacecolor=SOURCE_COLORS.get(s, '#333'),
                   markersize=7, label=s) for s in p_unique]
ax_f.legend(handles=p_legend, loc='center left', fontsize=6, ncol=len(p_unique),
            bbox_to_anchor=(0, -0.6))


# ── (g) Annual WY summary: mean T, total P, Nuka fraction ───────────
ax_g1 = fig.add_subplot(gs[6])
ax_g2 = ax_g1.twinx()

# Temperature bars
colors_t = plt.cm.RdYlBu_r((annual['mean_T'] - annual['mean_T'].min()) /
                             (annual['mean_T'].max() - annual['mean_T'].min()))
bars_t = ax_g1.bar(annual.index - 0.2, annual['mean_T'], width=0.4,
                   color=colors_t, edgecolor='k', linewidth=0.3, label='Mean T')
ax_g1.axhline(annual['mean_T'].mean(), color='red', linewidth=0.8, linestyle='--', alpha=0.6)
ax_g1.set_ylabel('Mean T (°C)', color='#d62728')
ax_g1.tick_params(axis='y', labelcolor='#d62728')

# Precipitation bars
ax_g2.bar(annual.index + 0.2, annual['total_P'], width=0.4,
          color='steelblue', edgecolor='k', linewidth=0.3, alpha=0.7, label='Total P')
ax_g2.axhline(annual['total_P'].mean(), color='steelblue', linewidth=0.8, linestyle='--', alpha=0.6)
ax_g2.set_ylabel('Total P (mm)', color='steelblue')
ax_g2.tick_params(axis='y', labelcolor='steelblue')

ax_g1.set_title('(g) Water Year Summary — Mean Temperature & Total Precipitation', loc='left', fontweight='bold')
ax_g1.set_xlabel('Water Year')
ax_g1.grid(True, alpha=0.2)

# Combined legend
h1, l1 = ax_g1.get_legend_handles_labels()
h2, l2 = ax_g2.get_legend_handles_labels()
ax_g1.legend(h1 + h2, l1 + l2, loc='upper right', fontsize=8)


# ── (h) Station data coverage timeline ───────────────────────────────
ax_h = fig.add_subplot(gs[7])
station_keys = ['nuka', 'mfb', 'mcneil', 'anchor', 'kachemak', 'lower_kach']

for i, key in enumerate(station_keys):
    if key not in stations:
        continue
    st = stations[key]
    label, color = STATION_STYLE[key]

    # Temperature: filled marker at y = i
    if 'tavg_c' in st.columns:
        valid = st['tavg_c'].loc[date_min:date_max].dropna()
        ax_h.scatter(valid.index, [i + 0.15] * len(valid), color=color,
                     s=0.2, alpha=0.4, marker='|')

    # Precip: hollow marker at y = i - 0.15
    if 'precip_mm' in st.columns:
        valid = st['precip_mm'].loc[date_min:date_max].dropna()
        ax_h.scatter(valid.index, [i - 0.15] * len(valid), color=color,
                     s=0.2, alpha=0.25, marker='|')

ax_h.set_yticks(range(len(station_keys)))
ax_h.set_yticklabels([STATION_STYLE[k][0] for k in station_keys], fontsize=8)
ax_h.set_title('(h) Station Data Coverage (top = T, bottom = P per station)', loc='left', fontweight='bold')
ax_h.set_xlim(date_min, date_max)
ax_h.xaxis.set_major_locator(mdates.YearLocator(2))
ax_h.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax_h.grid(True, alpha=0.3, axis='x')
ax_h.set_ylim(-0.5, len(station_keys) - 0.5)


# ── Save ─────────────────────────────────────────────────────────────
fig.suptitle('Dixon Glacier DETIM — Climate Data Overview (WY1999–WY2025)',
             fontsize=16, fontweight='bold', y=0.995)
fig.savefig('climate_overview_all_panels.png', dpi=150, bbox_inches='tight')
print("\nSaved: climate_overview_all_panels.png")
plt.show()
