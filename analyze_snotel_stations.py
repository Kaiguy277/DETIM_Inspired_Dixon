"""
Analyze all nearby SNOTEL stations + Dixon AWS for gap-filling potential.

Compares temperature and precipitation across:
  - Nuka Glacier (1037, 375m) — current forcing station
  - Middle Fork Bradley (1064, 701m) — 16km, same mountain group
  - McNeil Canyon (1003, 411m) — 24km
  - Anchor River Divide (1062, 503m) — 34km
  - Kachemak Creek (1063, 503m) — 14km, discontinued 2019
  - Lower Kachemak Creek (1265, 597m) — 13km, since 2015
  - Dixon AWS (1078m) — on-glacier, summer only (2024, 2025)
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

# ── Station metadata ──────────────────────────────────────────────
STATIONS = {
    'nuka': {
        'name': 'Nuka Glacier', 'site': 1037, 'elev_m': 375,
        'path': 'data/climate/nuka_snotel_full.csv',
    },
    'mfb': {
        'name': 'Middle Fork Bradley', 'site': 1064, 'elev_m': 701,
        'path': 'data/climate/snotel_stations/middle_fork_bradley_1064.csv',
    },
    'mcneil': {
        'name': 'McNeil Canyon', 'site': 1003, 'elev_m': 411,
        'path': 'data/climate/snotel_stations/mcneil_canyon_1003.csv',
    },
    'anchor': {
        'name': 'Anchor River Divide', 'site': 1062, 'elev_m': 503,
        'path': 'data/climate/snotel_stations/anchor_river_divide_1062.csv',
    },
    'kachemak': {
        'name': 'Kachemak Creek', 'site': 1063, 'elev_m': 503,
        'path': 'data/climate/snotel_stations/kachemak_creek_1063.csv',
    },
    'lower_kach': {
        'name': 'Lower Kachemak Ck', 'site': 1265, 'elev_m': 597,
        'path': 'data/climate/snotel_stations/lower_kachemak_1265.csv',
    },
}

DIXON_AWS = {
    'elev_m': 1078,
    'paths': [
        'dixon_observed_raw/Dixon24WX_RAW.csv',
        'dixon_observed_raw/Dixon25_WX.csv',
    ],
}


# ── Load functions ────────────────────────────────────────────────
def load_snotel(path):
    """Load SNOTEL CSV (NRCS format), return daily DataFrame with tavg_c, precip_mm."""
    df = pd.read_csv(path, comment='#', parse_dates=[0])
    # Map columns by content, not position (column order varies between stations)
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if 'date' in cl:
            col_map[c] = 'date'
        elif 'temperature average' in cl:
            col_map[c] = 'tavg_f'
        elif 'temperature maximum' in cl:
            col_map[c] = 'tmax_f'
        elif 'temperature minimum' in cl:
            col_map[c] = 'tmin_f'
        elif 'precipitation' in cl:
            col_map[c] = 'precip_accum_in'
        elif 'snow depth' in cl:
            col_map[c] = 'snow_depth_in'
        elif 'snow water' in cl:
            col_map[c] = 'swe_in'
    df = df.rename(columns=col_map)
    df = df.set_index('date').sort_index()

    # Temperature: °F → °C
    for col_f, col_c in [('tavg_f', 'tavg_c'), ('tmax_f', 'tmax_c'), ('tmin_f', 'tmin_c')]:
        if col_f in df.columns:
            df[col_c] = (df[col_f].astype(float) - 32) * 5 / 9
            bad = (df[col_c] < -50) | (df[col_c] > 40)
            df.loc[bad, col_c] = np.nan

    # Daily precip from accumulation
    if 'precip_accum_in' in df.columns:
        accum = pd.to_numeric(df['precip_accum_in'], errors='coerce')
        diff = accum.diff()
        resets = diff < -1.0
        daily_in = diff.clip(lower=0)
        daily_in.iloc[0] = 0
        daily_in[resets] = 0
        df['precip_mm'] = daily_in * 25.4

    return df


def load_dixon_aws():
    """Load Dixon AWS hourly data, aggregate to daily."""
    parts = []
    for path in DIXON_AWS['paths']:
        d = pd.read_csv(path)
        if 'TIMESTAMP' in d.columns:
            d = d.rename(columns={'TIMESTAMP': 'timestamp'})
        d['timestamp'] = pd.to_datetime(d['timestamp'])
        d = d.rename(columns={'AirTC_Avg': 'temperature_c', 'Rain_mm_Tot': 'precip_mm'})
        parts.append(d[['timestamp', 'temperature_c', 'precip_mm']])

    df = pd.concat(parts).set_index('timestamp').sort_index()
    # QC: remove sensor error values (-100 = logger fault)
    bad = (df['temperature_c'] < -50) | (df['temperature_c'] > 40)
    df.loc[bad, 'temperature_c'] = np.nan
    daily = pd.DataFrame()
    daily['tavg_c'] = df['temperature_c'].resample('D').mean()
    daily['tmax_c'] = df['temperature_c'].resample('D').max()
    daily['tmin_c'] = df['temperature_c'].resample('D').min()
    daily['precip_mm'] = df['precip_mm'].resample('D').sum()
    daily.index.name = 'date'
    # Drop days with < 20 hours of data
    hourly_counts = df['temperature_c'].resample('D').count()
    daily.loc[hourly_counts < 20, :] = np.nan
    return daily


# ── Main analysis ─────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("SNOTEL MULTI-STATION ANALYSIS + DIXON AWS COMPARISON")
    print("=" * 70)

    # Load all stations
    data = {}
    for key, info in STATIONS.items():
        print(f"\nLoading {info['name']} ({info['site']}, {info['elev_m']}m)...")
        df = load_snotel(info['path'])
        data[key] = df
        n_days = len(df)
        t_valid = df['tavg_c'].notna().sum() if 'tavg_c' in df.columns else 0
        p_valid = df['precip_mm'].notna().sum() if 'precip_mm' in df.columns else 0
        print(f"  {n_days} days ({df.index.min().date()} to {df.index.max().date()})")
        print(f"  Temp valid: {t_valid}/{n_days} ({100*t_valid/max(n_days,1):.0f}%)")
        print(f"  Precip valid: {p_valid}/{n_days} ({100*p_valid/max(n_days,1):.0f}%)")

    print(f"\nLoading Dixon AWS (on-glacier, {DIXON_AWS['elev_m']}m)...")
    dixon = load_dixon_aws()
    print(f"  {len(dixon)} days ({dixon.index.min().date()} to {dixon.index.max().date()})")
    print(f"  Temp valid: {dixon['tavg_c'].notna().sum()}")

    # ── 1. Gap coverage analysis ──────────────────────────────────
    print("\n" + "=" * 70)
    print("1. NUKA GAP COVERAGE BY OTHER STATIONS")
    print("=" * 70)

    nuka = data['nuka']
    nuka_t_nan = nuka['tavg_c'].isna()
    nuka_p_nan = nuka['precip_mm'].isna()

    for key in ['mfb', 'mcneil', 'anchor', 'kachemak', 'lower_kach']:
        info = STATIONS[key]
        other = data[key]
        # How many Nuka NaN days does this station cover?
        common_idx = nuka_t_nan.index.intersection(other.index)
        nuka_nan_dates = nuka_t_nan[nuka_t_nan].index
        other_covers_t = nuka_nan_dates.intersection(
            other.loc[other['tavg_c'].notna()].index if 'tavg_c' in other.columns else pd.DatetimeIndex([])
        )
        nuka_nan_p_dates = nuka_p_nan[nuka_p_nan].index
        other_covers_p = nuka_nan_p_dates.intersection(
            other.loc[other['precip_mm'].notna()].index if 'precip_mm' in other.columns else pd.DatetimeIndex([])
        )
        print(f"\n  {info['name']} ({info['elev_m']}m):")
        print(f"    Covers {len(other_covers_t)}/{len(nuka_nan_dates)} Nuka temp NaN days "
              f"({100*len(other_covers_t)/max(len(nuka_nan_dates),1):.0f}%)")
        print(f"    Covers {len(other_covers_p)}/{len(nuka_nan_p_dates)} Nuka precip NaN days "
              f"({100*len(other_covers_p)/max(len(nuka_nan_p_dates),1):.0f}%)")

    # ── 2. Temperature correlations (overlapping periods) ─────────
    print("\n" + "=" * 70)
    print("2. TEMPERATURE CORRELATIONS (daily Tavg)")
    print("=" * 70)

    corr_results = {}
    for key in ['mfb', 'mcneil', 'anchor', 'kachemak', 'lower_kach']:
        info = STATIONS[key]
        other = data[key]
        common = nuka.index.intersection(other.index)
        both_valid = nuka.loc[common, 'tavg_c'].notna() & other.loc[common, 'tavg_c'].notna()
        n_both = both_valid.sum()
        if n_both > 30:
            x = nuka.loc[common][both_valid]['tavg_c'].values
            y = other.loc[common][both_valid]['tavg_c'].values
            r = np.corrcoef(x, y)[0, 1]
            bias = np.mean(y - x)
            rmse = np.sqrt(np.mean((y - x) ** 2))
            # Linear regression
            slope, intercept = np.polyfit(x, y, 1)
            corr_results[key] = {'r': r, 'bias': bias, 'rmse': rmse,
                                  'slope': slope, 'intercept': intercept, 'n': n_both}
            print(f"  {info['name']:25s} r={r:.4f}  bias={bias:+.2f}C  "
                  f"RMSE={rmse:.2f}C  n={n_both:>5}  "
                  f"y={slope:.3f}x{intercept:+.2f}")
        else:
            print(f"  {info['name']:25s} insufficient overlap (n={n_both})")

    # Dixon AWS vs Nuka
    common = nuka.index.intersection(dixon.index)
    both_valid = nuka.loc[common, 'tavg_c'].notna() & dixon.loc[common, 'tavg_c'].notna()
    n_both = both_valid.sum()
    if n_both > 10:
        x = nuka.loc[common][both_valid]['tavg_c'].values
        y = dixon.loc[common][both_valid]['tavg_c'].values
        r = np.corrcoef(x, y)[0, 1]
        bias = np.mean(y - x)
        rmse = np.sqrt(np.mean((y - x) ** 2))
        slope, intercept = np.polyfit(x, y, 1)
        print(f"\n  {'Dixon AWS (1078m)':25s} r={r:.4f}  bias={bias:+.2f}C  "
              f"RMSE={rmse:.2f}C  n={n_both:>5}  "
              f"y={slope:.3f}x{intercept:+.2f}")
        corr_results['dixon'] = {'r': r, 'bias': bias, 'rmse': rmse,
                                  'slope': slope, 'intercept': intercept, 'n': n_both}

    # Dixon AWS vs each SNOTEL
    print("\n  --- Dixon AWS vs other SNOTEL stations ---")
    for key in ['mfb', 'mcneil', 'anchor', 'lower_kach']:
        info = STATIONS[key]
        other = data[key]
        common = dixon.index.intersection(other.index)
        both_valid = dixon.loc[common, 'tavg_c'].notna() & other.loc[common, 'tavg_c'].notna()
        n_both = both_valid.sum()
        if n_both > 10:
            x = other.loc[common][both_valid]['tavg_c'].values
            y = dixon.loc[common][both_valid]['tavg_c'].values
            r = np.corrcoef(x, y)[0, 1]
            bias = np.mean(y - x)
            print(f"  Dixon vs {info['name']:20s} r={r:.4f}  bias={bias:+.2f}C  n={n_both}")

    # ── 3. Monthly temperature transfer coefficients ──────────────
    print("\n" + "=" * 70)
    print("3. MONTHLY TEMPERATURE REGRESSIONS (Nuka → each station)")
    print("=" * 70)

    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    for key in ['mfb', 'mcneil', 'anchor']:
        info = STATIONS[key]
        other = data[key]
        common = nuka.index.intersection(other.index)
        both_valid = nuka.loc[common, 'tavg_c'].notna() & other.loc[common, 'tavg_c'].notna()
        valid_dates = common[both_valid]

        print(f"\n  {info['name']} ({info['elev_m']}m, dz={info['elev_m']-375:+.0f}m from Nuka):")
        print(f"  {'Mon':>5} {'slope':>7} {'intcpt':>7} {'r²':>6} {'n':>6} {'impld_lapse':>12}")

        for m in range(1, 13):
            month_mask = valid_dates.month == m
            md = valid_dates[month_mask]
            if len(md) < 10:
                continue
            x = nuka.loc[md, 'tavg_c'].values
            y = other.loc[md, 'tavg_c'].values
            slope, intercept = np.polyfit(x, y, 1)
            r2 = np.corrcoef(x, y)[0, 1] ** 2
            # Implied lapse rate at mean T
            mean_diff = np.mean(y - x)
            dz = info['elev_m'] - 375
            implied_lapse = mean_diff / dz * 1000 if dz != 0 else np.nan
            print(f"  {month_names[m-1]:>5} {slope:>7.3f} {intercept:>+7.2f} {r2:>6.3f} {len(md):>6} "
                  f"{implied_lapse:>+10.1f} C/km")

    # ── 4. Precipitation comparison ───────────────────────────────
    print("\n" + "=" * 70)
    print("4. ANNUAL PRECIPITATION COMPARISON (WY totals, mm at station)")
    print("=" * 70)

    print(f"\n  {'WY':>6}", end='')
    for key in ['nuka', 'mfb', 'mcneil', 'anchor', 'kachemak']:
        print(f"  {STATIONS[key]['name'][:12]:>12}", end='')
    print()

    for wy in range(2000, 2025):
        start = pd.Timestamp(f'{wy-1}-10-01')
        end = pd.Timestamp(f'{wy}-09-30')
        print(f"  {wy:>6}", end='')
        for key in ['nuka', 'mfb', 'mcneil', 'anchor', 'kachemak']:
            stn = data[key]
            sub = stn.loc[start:end]
            if 'precip_mm' in sub.columns and len(sub) > 300:
                p = sub['precip_mm'].sum()
                nan_pct = sub['precip_mm'].isna().mean() * 100
                flag = '*' if nan_pct > 10 else ' '
                print(f"  {p:>10.0f}{flag}", end='')
            else:
                print(f"  {'---':>12}", end='')
        print()

    print("\n  * = >10% precip NaN days in that water year")

    # ── 5. Dixon AWS comparison ───────────────────────────────────
    print("\n" + "=" * 70)
    print("5. DIXON AWS vs ALL SNOTEL (Summer overlap)")
    print("=" * 70)

    for key in ['nuka', 'mfb', 'mcneil', 'anchor', 'lower_kach']:
        info = STATIONS[key]
        other = data[key]
        common = dixon.index.intersection(other.index)
        both_t = dixon.loc[common, 'tavg_c'].notna() & other.loc[common, 'tavg_c'].notna()
        both_p = dixon.loc[common, 'precip_mm'].notna() & other.loc[common, 'precip_mm'].notna()

        if both_t.sum() > 10:
            x = other.loc[common][both_t]['tavg_c'].values
            y = dixon.loc[common][both_t]['tavg_c'].values
            r = np.corrcoef(x, y)[0, 1]
            slope, intercept = np.polyfit(x, y, 1)
            rmse = np.sqrt(np.mean((y - x) ** 2))
            dz = DIXON_AWS['elev_m'] - info['elev_m']
            implied_lapse = np.mean(y - x) / dz * 1000 if dz != 0 else np.nan
            print(f"\n  Dixon vs {info['name']} ({info['elev_m']}m, dz={dz:+.0f}m):")
            print(f"    T: r={r:.4f}, y={slope:.3f}x{intercept:+.2f}, RMSE={rmse:.2f}C, "
                  f"implied lapse={implied_lapse:+.1f} C/km, n={both_t.sum()}")

        if both_p.sum() > 10:
            xp = other.loc[common][both_p]['precip_mm'].values
            yp = dixon.loc[common][both_p]['precip_mm'].values
            rp = np.corrcoef(xp, yp)[0, 1]
            ratio = yp.sum() / max(xp.sum(), 0.01)
            print(f"    P: r={rp:.4f}, Dixon/Station ratio={ratio:.2f}, n={both_p.sum()}")

    # ── 6. Key gap years: what other stations have ────────────────
    print("\n" + "=" * 70)
    print("6. NUKA GAP YEARS — COVERAGE BY OTHER STATIONS")
    print("=" * 70)

    gap_years = {
        2000: 'T: 56d gap Jun-Aug',
        2001: 'T: 282d gap Dec-Sep',
        2002: 'T: 102d gap Oct-Feb',
        2005: 'T: 157d gap May-Sep',
        2020: 'P: 192d gap Nov-Jun',
    }

    for wy, desc in gap_years.items():
        start = pd.Timestamp(f'{wy-1}-10-01')
        end = pd.Timestamp(f'{wy}-09-30')
        print(f"\n  WY{wy}: {desc}")

        nuka_sub = data['nuka'].loc[start:end]
        nuka_t_nan_dates = nuka_sub[nuka_sub['tavg_c'].isna()].index
        nuka_p_nan_dates = nuka_sub[nuka_sub['precip_mm'].isna()].index

        for key in ['mfb', 'mcneil', 'anchor', 'kachemak']:
            info = STATIONS[key]
            other = data[key]
            other_sub = other.loc[start:end]

            if len(other_sub) < 30:
                print(f"    {info['name']:25s} no data for this WY")
                continue

            # How many Nuka T NaN days does this station cover?
            if len(nuka_t_nan_dates) > 0:
                covers_t = nuka_t_nan_dates.intersection(
                    other_sub[other_sub['tavg_c'].notna()].index
                )
                print(f"    {info['name']:25s} covers {len(covers_t):>4}/{len(nuka_t_nan_dates)} "
                      f"temp NaN days ({100*len(covers_t)/max(len(nuka_t_nan_dates),1):.0f}%)", end='')
            else:
                print(f"    {info['name']:25s} (no temp gaps)", end='')

            if len(nuka_p_nan_dates) > 0:
                covers_p = nuka_p_nan_dates.intersection(
                    other_sub[other_sub['precip_mm'].notna()].index
                )
                print(f"  | precip: {len(covers_p):>4}/{len(nuka_p_nan_dates)} "
                      f"({100*len(covers_p)/max(len(nuka_p_nan_dates),1):.0f}%)")
            else:
                print()

    # ── 7. Plots ──────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("7. GENERATING COMPARISON PLOTS")
    print("=" * 70)

    outdir = Path('calibration_output')

    # Plot A: Temperature scatter — Nuka vs each station
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    axes = axes.flatten()
    for idx, key in enumerate(['mfb', 'mcneil', 'anchor', 'kachemak', 'lower_kach']):
        ax = axes[idx]
        info = STATIONS[key]
        other = data[key]
        common = nuka.index.intersection(other.index)
        bv = nuka.loc[common, 'tavg_c'].notna() & other.loc[common, 'tavg_c'].notna()
        if bv.sum() > 10:
            x = nuka.loc[common][bv]['tavg_c'].values
            y = other.loc[common][bv]['tavg_c'].values
            ax.scatter(x, y, s=1, alpha=0.2)
            ax.plot([-30, 25], [-30, 25], 'r--', lw=1, label='1:1')
            slope, intercept = np.polyfit(x, y, 1)
            xx = np.array([-30, 25])
            ax.plot(xx, slope * xx + intercept, 'b-', lw=1,
                    label=f'y={slope:.2f}x{intercept:+.1f}')
            r = np.corrcoef(x, y)[0, 1]
            ax.set_title(f'{info["name"]}\n({info["elev_m"]}m, r={r:.3f}, n={bv.sum()})',
                         fontsize=10)
            ax.legend(fontsize=8)
        ax.set_xlabel('Nuka Tavg (°C)')
        ax.set_ylabel(f'{info["name"][:15]} Tavg (°C)')
        ax.set_xlim(-30, 25)
        ax.set_ylim(-30, 25)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)

    # Dixon AWS vs Nuka
    ax = axes[5]
    common = nuka.index.intersection(dixon.index)
    bv = nuka.loc[common, 'tavg_c'].notna() & dixon.loc[common, 'tavg_c'].notna()
    if bv.sum() > 10:
        x = nuka.loc[common][bv]['tavg_c'].values
        y = dixon.loc[common][bv]['tavg_c'].values
        ax.scatter(x, y, s=3, alpha=0.5, c='green')
        ax.plot([-10, 25], [-10, 25], 'r--', lw=1, label='1:1')
        slope, intercept = np.polyfit(x, y, 1)
        xx = np.array([-10, 25])
        ax.plot(xx, slope * xx + intercept, 'b-', lw=1,
                label=f'y={slope:.2f}x{intercept:+.1f}')
        r = np.corrcoef(x, y)[0, 1]
        ax.set_title(f'Dixon AWS (1078m)\nr={r:.3f}, n={bv.sum()}', fontsize=10)
        ax.legend(fontsize=8)
    ax.set_xlabel('Nuka Tavg (°C)')
    ax.set_ylabel('Dixon AWS Tavg (°C)')
    ax.grid(True, alpha=0.3)

    plt.suptitle('Temperature Correlations: Nuka SNOTEL vs Nearby Stations', fontsize=14)
    plt.tight_layout()
    fig.savefig(outdir / 'snotel_temperature_scatter.png', dpi=150, bbox_inches='tight')
    print(f"  Saved: {outdir / 'snotel_temperature_scatter.png'}")

    # Plot B: Time series of monthly mean T — all stations, highlighting gaps
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 10))

    for key, color in [('nuka', 'black'), ('mfb', 'blue'), ('mcneil', 'green'),
                        ('anchor', 'orange'), ('kachemak', 'purple')]:
        info = STATIONS[key]
        ts = data[key]['tavg_c'].resample('MS').mean()
        ax1.plot(ts.index, ts.values, color=color, alpha=0.7, lw=1,
                 label=f'{info["name"]} ({info["elev_m"]}m)')

    # Mark Nuka gap periods
    nuka_gaps = nuka['tavg_c'].isna()
    gap_months = nuka_gaps.resample('MS').mean()
    for date, frac in gap_months.items():
        if frac > 0.3:
            ax1.axvspan(date, date + pd.Timedelta(days=30), alpha=0.2, color='red')

    ax1.set_ylabel('Monthly Mean Tavg (°C)')
    ax1.set_title('Monthly Temperature: All Stations (red shading = Nuka gap months)')
    ax1.legend(loc='upper left', fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(pd.Timestamp('1998-01-01'), pd.Timestamp('2025-06-01'))

    # Plot B2: Annual precip comparison
    for key, color in [('nuka', 'black'), ('mfb', 'blue'), ('mcneil', 'green'),
                        ('anchor', 'orange')]:
        info = STATIONS[key]
        precip = data[key]['precip_mm']
        wy_totals = []
        wy_years = []
        for wy in range(1991, 2025):
            sub = precip.loc[f'{wy-1}-10-01':f'{wy}-09-30']
            if len(sub) > 300 and sub.notna().mean() > 0.8:
                wy_totals.append(sub.sum())
                wy_years.append(wy)
        ax2.plot(wy_years, wy_totals, 'o-', color=color, alpha=0.7, lw=1.5, ms=4,
                 label=f'{info["name"]} ({info["elev_m"]}m)')

    ax2.set_ylabel('Water Year Total Precip (mm)')
    ax2.set_xlabel('Water Year')
    ax2.set_title('Annual Precipitation: SNOTEL Stations')
    ax2.legend(loc='upper left', fontsize=8)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    fig.savefig(outdir / 'snotel_multistation_timeseries.png', dpi=150, bbox_inches='tight')
    print(f"  Saved: {outdir / 'snotel_multistation_timeseries.png'}")

    # Plot C: Dixon AWS vs Nuka — daily temperature time series
    fig, ax = plt.subplots(1, 1, figsize=(16, 5))
    common = nuka.index.intersection(dixon.index)
    ax.plot(nuka.loc[common].index, nuka.loc[common, 'tavg_c'], 'k-', alpha=0.7, lw=1,
            label=f'Nuka (375m)')
    ax.plot(dixon.index, dixon['tavg_c'], 'g-', alpha=0.7, lw=1,
            label=f'Dixon AWS (1078m)')
    # Also plot MFB for same period
    mfb_overlap = data['mfb'].loc[dixon.index.min():dixon.index.max()]
    ax.plot(mfb_overlap.index, mfb_overlap['tavg_c'], 'b-', alpha=0.5, lw=1,
            label=f'Middle Fork Bradley (701m)')
    ax.set_ylabel('Daily Tavg (°C)')
    ax.set_title('Dixon AWS vs SNOTEL Stations — Summer 2024-2025')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(outdir / 'dixon_aws_vs_snotel.png', dpi=150, bbox_inches='tight')
    print(f"  Saved: {outdir / 'dixon_aws_vs_snotel.png'}")

    plt.close('all')
    print("\nDone.")


if __name__ == '__main__':
    main()
