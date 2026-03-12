"""
Compare ALL climate stations against Dixon AWS (the ground truth).

The model predicts conditions on the glacier — so what matters is how well
each station predicts Dixon, not how well they predict each other.

Dixon AWS: 1078m, ELA site (D-023), summer 2024 + 2025
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path


STATIONS = {
    'nuka':       {'name': 'Nuka Glacier',     'elev_m': 375,  'dist_km': 10,
                   'path': 'data/climate/nuka_snotel_full.csv', 'color': 'black'},
    'mfb':        {'name': 'Mid Fork Bradley', 'elev_m': 701,  'dist_km': 16,
                   'path': 'data/climate/snotel_stations/middle_fork_bradley_1064.csv',
                   'color': '#2166ac'},
    'mcneil':     {'name': 'McNeil Canyon',    'elev_m': 411,  'dist_km': 24,
                   'path': 'data/climate/snotel_stations/mcneil_canyon_1003.csv',
                   'color': '#1b7837'},
    'anchor':     {'name': 'Anchor River Div', 'elev_m': 503,  'dist_km': 34,
                   'path': 'data/climate/snotel_stations/anchor_river_divide_1062.csv',
                   'color': '#e08214'},
    'lower_kach': {'name': 'Lower Kachemak',   'elev_m': 597,  'dist_km': 13,
                   'path': 'data/climate/snotel_stations/lower_kachemak_1265.csv',
                   'color': '#c51b7d'},
}

DIXON_ELEV = 1078.0


def load_snotel(path):
    df = pd.read_csv(path, comment='#', parse_dates=[0])
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if 'date' in cl: col_map[c] = 'date'
        elif 'temperature average' in cl: col_map[c] = 'tavg_f'
        elif 'temperature maximum' in cl: col_map[c] = 'tmax_f'
        elif 'temperature minimum' in cl: col_map[c] = 'tmin_f'
        elif 'precipitation' in cl: col_map[c] = 'precip_accum_in'
    df = df.rename(columns=col_map).set_index('date').sort_index()
    for col_f, col_c in [('tavg_f', 'tavg_c'), ('tmax_f', 'tmax_c'), ('tmin_f', 'tmin_c')]:
        if col_f in df.columns:
            df[col_c] = (pd.to_numeric(df[col_f], errors='coerce') - 32) * 5 / 9
            df.loc[(df[col_c] < -50) | (df[col_c] > 40), col_c] = np.nan
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
    parts = []
    for path in ['dixon_observed_raw/Dixon24WX_RAW.csv', 'dixon_observed_raw/Dixon25_WX.csv']:
        d = pd.read_csv(path)
        d = d.rename(columns=lambda c: {'TIMESTAMP': 'timestamp', 'AirTC_Avg': 'temperature_c',
                                         'Rain_mm_Tot': 'precip_mm'}.get(c, c))
        d['timestamp'] = pd.to_datetime(d['timestamp'])
        d.loc[(d['temperature_c'] < -50) | (d['temperature_c'] > 40), 'temperature_c'] = np.nan
        parts.append(d[['timestamp', 'temperature_c', 'precip_mm']])
    df = pd.concat(parts).set_index('timestamp').sort_index()
    daily = pd.DataFrame()
    daily['tavg_c'] = df['temperature_c'].resample('D').mean()
    daily['tmax_c'] = df['temperature_c'].resample('D').max()
    daily['tmin_c'] = df['temperature_c'].resample('D').min()
    daily['precip_mm'] = df['precip_mm'].resample('D').sum()
    counts = df['temperature_c'].resample('D').count()
    daily.loc[counts < 20, :] = np.nan
    daily.index.name = 'date'
    return daily


def get_overlap(stn_df, dixon_df, col='tavg_c'):
    """Get overlapping valid dates between a station and Dixon."""
    common = stn_df.index.intersection(dixon_df.index)
    both = stn_df.loc[common, col].notna() & dixon_df.loc[common, col].notna()
    return common[both]


def main():
    outdir = Path('calibration_output')
    print("Loading all stations...")
    data = {}
    for key, info in STATIONS.items():
        data[key] = load_snotel(info['path'])
    dixon = load_dixon_aws()
    d_valid = dixon['tavg_c'].dropna()
    print(f"Dixon AWS: {d_valid.index.min().date()} to {d_valid.index.max().date()}, {len(d_valid)} days\n")

    # ═══════════════════════════════════════════════════════════════
    # Summary stats: every station vs Dixon
    # ═══════════════════════════════════════════════════════════════
    print("=" * 90)
    print("ALL STATIONS vs DIXON AWS (1078m, ELA site)")
    print("=" * 90)
    print(f"\n{'Station':22s} {'Elev':>5} {'dz':>6} {'r':>6} {'RMSE':>6} {'bias':>7} "
          f"{'slope':>6} {'intcpt':>7} {'n':>5}")
    print("-" * 80)

    results = {}
    for key in ['nuka', 'mfb', 'mcneil', 'anchor', 'lower_kach']:
        info = STATIONS[key]
        dates = get_overlap(data[key], dixon)
        if len(dates) < 10:
            continue
        x = data[key].loc[dates, 'tavg_c'].values
        y = dixon.loc[dates, 'tavg_c'].values
        r = np.corrcoef(x, y)[0, 1]
        rmse = np.sqrt(np.mean((y - x) ** 2))
        bias = np.mean(y - x)
        slope, intercept = np.polyfit(x, y, 1)
        dz = DIXON_ELEV - info['elev_m']
        results[key] = {'r': r, 'rmse': rmse, 'bias': bias, 'slope': slope,
                         'intercept': intercept, 'n': len(dates), 'dz': dz}
        print(f"{info['name']:22s} {info['elev_m']:>4}m {dz:>+5.0f}m {r:>6.3f} {rmse:>5.2f}C "
              f"{bias:>+6.2f}C {slope:>6.3f} {intercept:>+6.2f} {len(dates):>5}")

    # ═══════════════════════════════════════════════════════════════
    # FIGURE 1: Scatter — every station vs Dixon
    # ═══════════════════════════════════════════════════════════════
    print("\nPlot 1: Temperature scatter — all stations vs Dixon...")
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()

    for idx, key in enumerate(['nuka', 'mfb', 'lower_kach', 'mcneil', 'anchor']):
        ax = axes[idx]
        info = STATIONS[key]
        dates = get_overlap(data[key], dixon)
        if len(dates) < 10:
            continue
        x = data[key].loc[dates, 'tavg_c'].values
        y = dixon.loc[dates, 'tavg_c'].values

        # Color by month
        months = dates.month
        summer_colors = {5: '#a6d854', 6: '#66c2a5', 7: '#fc8d62',
                         8: '#e78ac3', 9: '#8da0cb', 10: '#b3b3b3'}
        for m, mc in summer_colors.items():
            mask = months == m
            if mask.sum() > 0:
                ax.scatter(x[mask], y[mask], s=15, alpha=0.7, color=mc,
                           label=f'{["","","","","May","Jun","Jul","Aug","Sep","Oct"][m]}' if mask.sum() > 3 else None)

        # Regression line
        r = results[key]
        xx = np.array([-10, 20])
        ax.plot(xx, r['slope'] * xx + r['intercept'], color=info['color'], lw=2,
                label=f"T_dixon = {r['slope']:.2f}×T_stn {r['intercept']:+.1f}")
        ax.plot(xx, xx, 'k--', lw=0.5, alpha=0.4, label='1:1')

        # Simple lapse line for comparison
        dz = DIXON_ELEV - info['elev_m']
        lapse_offset = -6.5 / 1000 * dz
        ax.plot(xx, xx + lapse_offset, ':', color='grey', lw=1,
                label=f'Lapse -6.5°C/km ({lapse_offset:+.1f}°C)')

        ax.set_xlabel(f"{info['name']} Tavg (°C)")
        ax.set_ylabel('Dixon AWS Tavg (°C)')
        ax.set_title(f"{info['name']} ({info['elev_m']}m, {info['dist_km']}km)\n"
                     f"r={r['r']:.3f}, RMSE={r['rmse']:.1f}°C, bias={r['bias']:+.1f}°C, n={r['n']}",
                     fontsize=10)
        ax.legend(fontsize=7, loc='upper left')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(-10, 18)
        ax.set_ylim(-10, 12)

    # Empty panel — summary text
    ax = axes[5]
    ax.axis('off')
    summary_text = "Summary: Station → Dixon Transfer\n\n"
    summary_text += f"{'Station':20s} {'r':>5} {'RMSE':>6} {'slope':>6}\n"
    summary_text += "-" * 42 + "\n"
    for key in ['nuka', 'mfb', 'lower_kach', 'mcneil', 'anchor']:
        if key in results:
            r = results[key]
            info = STATIONS[key]
            summary_text += f"{info['name']:20s} {r['r']:>5.3f} {r['rmse']:>5.1f}C {r['slope']:>6.3f}\n"
    summary_text += "\n\nSlope < 1 means the station\noverpredicts Dixon variability.\n"
    summary_text += "\nThe glacier dampens temperature\nextremes (boundary layer effect)."
    ax.text(0.1, 0.9, summary_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    plt.suptitle('Temperature: Every SNOTEL Station vs Dixon AWS (on-glacier ground truth)',
                 fontsize=14, y=1.01)
    plt.tight_layout()
    fig.savefig(outdir / 'dixon_vs_all_scatter.png', dpi=150, bbox_inches='tight')
    print(f"  Saved: {outdir / 'dixon_vs_all_scatter.png'}")
    plt.close()

    # ═══════════════════════════════════════════════════════════════
    # FIGURE 2: Monthly regressions — every station vs Dixon
    # ═══════════════════════════════════════════════════════════════
    print("\nPlot 2: Monthly regression coefficients — all stations vs Dixon...")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    month_names = ['May', 'Jun', 'Jul', 'Aug', 'Sep']
    month_nums = [5, 6, 7, 8, 9]

    for key in ['nuka', 'mfb', 'lower_kach', 'mcneil', 'anchor']:
        info = STATIONS[key]
        dates = get_overlap(data[key], dixon)
        if len(dates) < 30:
            continue

        slopes, intercepts, r2s, ns, biases, rmses = [], [], [], [], [], []
        for m in month_nums:
            md = dates[dates.month == m]
            if len(md) < 5:
                slopes.append(np.nan)
                intercepts.append(np.nan)
                r2s.append(np.nan)
                ns.append(0)
                biases.append(np.nan)
                rmses.append(np.nan)
                continue
            x = data[key].loc[md, 'tavg_c'].values
            y = dixon.loc[md, 'tavg_c'].values
            s, i = np.polyfit(x, y, 1)
            r2 = np.corrcoef(x, y)[0, 1] ** 2
            slopes.append(s)
            intercepts.append(i)
            r2s.append(r2)
            ns.append(len(md))
            biases.append(np.mean(y - x))
            rmses.append(np.sqrt(np.mean((y - x) ** 2)))

        dz = DIXON_ELEV - info['elev_m']
        label = f"{info['name']} ({info['elev_m']}m, dz={dz:+.0f}m)"

        axes[0, 0].plot(month_names, slopes, 'o-', color=info['color'], lw=1.5, ms=6, label=label)
        axes[0, 1].plot(month_names, intercepts, 'o-', color=info['color'], lw=1.5, ms=6, label=label)
        axes[1, 0].plot(month_names, r2s, 'o-', color=info['color'], lw=1.5, ms=6, label=label)
        axes[1, 1].plot(month_names, rmses, 'o-', color=info['color'], lw=1.5, ms=6, label=label)

    axes[0, 0].axhline(1.0, color='grey', ls=':', lw=0.5)
    axes[0, 0].set_ylabel('Slope')
    axes[0, 0].set_title('Regression Slope (T_dixon = slope × T_stn + intercept)\n<1 means dampened on glacier')
    axes[0, 0].legend(fontsize=7)
    axes[0, 0].grid(True, alpha=0.3)

    axes[0, 1].axhline(0, color='grey', ls=':', lw=0.5)
    axes[0, 1].set_ylabel('Intercept (°C)')
    axes[0, 1].set_title('Regression Intercept')
    axes[0, 1].legend(fontsize=7)
    axes[0, 1].grid(True, alpha=0.3)

    axes[1, 0].set_ylabel('r²')
    axes[1, 0].set_title('Explained Variance (r²)\nHigher = more predictable')
    axes[1, 0].set_ylim(0, 1)
    axes[1, 0].legend(fontsize=7)
    axes[1, 0].grid(True, alpha=0.3)

    axes[1, 1].set_ylabel('RMSE (°C)')
    axes[1, 1].set_title('Root Mean Square Error\nLower = better prediction')
    axes[1, 1].legend(fontsize=7)
    axes[1, 1].grid(True, alpha=0.3)

    plt.suptitle('Monthly Transfer Coefficients: Station → Dixon AWS', fontsize=14)
    plt.tight_layout()
    fig.savefig(outdir / 'dixon_vs_all_monthly_transfer.png', dpi=150, bbox_inches='tight')
    print(f"  Saved: {outdir / 'dixon_vs_all_monthly_transfer.png'}")
    plt.close()

    # ═══════════════════════════════════════════════════════════════
    # FIGURE 3: Daily time series — Dixon vs each station
    # ═══════════════════════════════════════════════════════════════
    print("\nPlot 3: Daily time series — Dixon vs predictions from each station...")

    fig, axes = plt.subplots(5, 1, figsize=(20, 20), sharex=True)

    for idx, key in enumerate(['nuka', 'mfb', 'lower_kach', 'mcneil', 'anchor']):
        ax = axes[idx]
        info = STATIONS[key]
        dates = get_overlap(data[key], dixon)
        if len(dates) < 10:
            continue
        r = results[key]

        # Raw station temperature
        stn_sub = data[key]['tavg_c'].loc[dixon.index.min():dixon.index.max()]
        ax.plot(stn_sub.index, stn_sub.values, color=info['color'], lw=0.8, alpha=0.5,
                label=f"{info['name']} raw ({info['elev_m']}m)")

        # Station temp transferred to Dixon via regression
        predicted = r['slope'] * stn_sub + r['intercept']
        ax.plot(predicted.index, predicted.values, color=info['color'], lw=1.2, alpha=0.8,
                ls='--', label=f"Predicted Dixon (slope={r['slope']:.2f})")

        # Simple lapse prediction
        dz = DIXON_ELEV - info['elev_m']
        lapse_pred = stn_sub + (-6.5 / 1000 * dz)
        ax.plot(lapse_pred.index, lapse_pred.values, color='grey', lw=0.8, alpha=0.4,
                ls=':', label=f"Lapse -6.5°C/km ({-6.5/1000*dz:+.1f}°C)")

        # Dixon observed
        ax.plot(dixon.index, dixon['tavg_c'], color='red', lw=1.5, alpha=0.9,
                label='Dixon AWS observed')

        # Residuals shading
        on_dates = get_overlap(data[key], dixon)
        pred_on = r['slope'] * data[key].loc[on_dates, 'tavg_c'] + r['intercept']
        residuals = dixon.loc[on_dates, 'tavg_c'] - pred_on
        ax.fill_between(on_dates, pred_on, dixon.loc[on_dates, 'tavg_c'],
                         alpha=0.15, color='red')

        ax.set_ylabel('Temperature (°C)')
        ax.set_title(f"{info['name']} → Dixon  |  r={r['r']:.3f}, RMSE={r['rmse']:.1f}°C, "
                     f"mean residual={residuals.mean():+.1f}°C", fontsize=11)
        ax.legend(fontsize=7, loc='upper right', ncol=2)
        ax.grid(True, alpha=0.3)

    axes[-1].xaxis.set_major_locator(mdates.MonthLocator())
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45)
    plt.suptitle('Temperature Predictions at Dixon: Raw Station, Regression Transfer, and Lapse Rate\n'
                 '(red = observed Dixon, dashed = regression prediction, dotted = simple lapse)',
                 fontsize=13)
    plt.tight_layout()
    fig.savefig(outdir / 'dixon_vs_all_timeseries.png', dpi=150, bbox_inches='tight')
    print(f"  Saved: {outdir / 'dixon_vs_all_timeseries.png'}")
    plt.close()

    # ═══════════════════════════════════════════════════════════════
    # FIGURE 4: Precipitation — Dixon vs each station
    # ═══════════════════════════════════════════════════════════════
    print("\nPlot 4: Precipitation comparison — Dixon vs all stations...")

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Panel A: Scatter — daily precip Dixon vs each station
    ax = axes[0, 0]
    for key in ['nuka', 'mfb', 'lower_kach', 'mcneil']:
        info = STATIONS[key]
        dates = get_overlap(data[key], dixon, col='precip_mm')
        if len(dates) < 10:
            continue
        x = data[key].loc[dates, 'precip_mm'].values
        y = dixon.loc[dates, 'precip_mm'].values
        # Only wet days (either station > 0.5mm)
        wet = (x > 0.5) | (y > 0.5)
        if wet.sum() > 10:
            r = np.corrcoef(x[wet], y[wet])[0, 1]
            ax.scatter(x[wet], y[wet], s=10, alpha=0.4, color=info['color'],
                       label=f"{info['name']} (r={r:.2f}, n={wet.sum()})")

    ax.plot([0, 60], [0, 60], 'k--', lw=0.5, alpha=0.3)
    ax.set_xlabel('Station Daily Precip (mm)')
    ax.set_ylabel('Dixon AWS Daily Precip (mm)')
    ax.set_title('Daily Precipitation: Station vs Dixon (wet days only)', fontsize=11)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 60)
    ax.set_ylim(0, 60)

    # Panel B: Cumulative precip — all stations + Dixon
    ax = axes[0, 1]
    d_start = d_valid.index.min()
    d_end = d_valid.index.max()
    for key in ['nuka', 'mfb', 'lower_kach', 'mcneil', 'anchor']:
        info = STATIONS[key]
        sub = data[key]['precip_mm'].loc[d_start:d_end].fillna(0)
        cum = sub.cumsum()
        ax.plot(cum.index, cum.values, color=info['color'], lw=1.2, alpha=0.7,
                label=f"{info['name']} ({cum.iloc[-1]:.0f}mm)")
    dcum = dixon['precip_mm'].fillna(0).loc[d_start:d_end].cumsum()
    ax.plot(dcum.index, dcum.values, color='red', lw=2, alpha=0.9,
            label=f"Dixon AWS ({dcum.iloc[-1]:.0f}mm)")
    ax.set_ylabel('Cumulative Precip (mm)')
    ax.set_title('Cumulative Precip During Dixon Deployment', fontsize=11)
    ax.legend(fontsize=7, loc='upper left')
    ax.grid(True, alpha=0.3)

    # Panel C: Precip ratio — Dixon / each station (by month)
    ax = axes[1, 0]
    for key in ['nuka', 'mfb', 'lower_kach', 'mcneil']:
        info = STATIONS[key]
        dates = get_overlap(data[key], dixon, col='precip_mm')
        if len(dates) < 30:
            continue
        ratios, months_list = [], []
        for m in [5, 6, 7, 8, 9]:
            md = dates[dates.month == m]
            if len(md) < 10:
                continue
            stn_total = data[key].loc[md, 'precip_mm'].sum()
            dix_total = dixon.loc[md, 'precip_mm'].sum()
            if stn_total > 10:
                ratios.append(dix_total / stn_total)
                months_list.append({5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct'}[m])
        if ratios:
            ax.plot(months_list, ratios, 'o-', color=info['color'], lw=1.5, ms=8,
                    label=f"Dixon/{info['name']} (mean={np.mean(ratios):.2f})")

    ax.axhline(1.0, color='grey', ls=':', lw=0.5)
    ax.set_ylabel('Precipitation Ratio (Dixon / Station)')
    ax.set_title('Monthly Precip Ratio: Dixon vs Each Station\n>1 = Dixon wetter, <1 = Dixon drier',
                 fontsize=11)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # Panel D: Event detection — days where Dixon and stations agree on wet/dry
    ax = axes[1, 1]
    labels, hit_rates, false_alarms = [], [], []
    for key in ['nuka', 'mfb', 'lower_kach', 'mcneil', 'anchor']:
        info = STATIONS[key]
        dates = get_overlap(data[key], dixon, col='precip_mm')
        if len(dates) < 30:
            continue
        x = data[key].loc[dates, 'precip_mm'].values
        y = dixon.loc[dates, 'precip_mm'].values
        # Wet threshold = 1mm
        stn_wet = x > 1.0
        dix_wet = y > 1.0
        # Hit rate: when Dixon is wet, how often is station also wet?
        if dix_wet.sum() > 0:
            hr = (stn_wet & dix_wet).sum() / dix_wet.sum()
        else:
            hr = 0
        # False alarm: when station says wet but Dixon is dry
        if stn_wet.sum() > 0:
            fa = (stn_wet & ~dix_wet).sum() / stn_wet.sum()
        else:
            fa = 0
        labels.append(f"{info['name']}\n({info['elev_m']}m)")
        hit_rates.append(hr)
        false_alarms.append(fa)

    x_pos = np.arange(len(labels))
    width = 0.35
    ax.bar(x_pos - width/2, hit_rates, width, color='#2ca02c', alpha=0.7, label='Hit rate (Dixon wet → station wet)')
    ax.bar(x_pos + width/2, false_alarms, width, color='#d62728', alpha=0.7, label='False alarm (station wet → Dixon dry)')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel('Fraction')
    ax.set_title('Precipitation Event Detection vs Dixon\n(threshold = 1mm/day)', fontsize=11)
    ax.legend(fontsize=8)
    ax.grid(True, axis='y', alpha=0.3)
    ax.set_ylim(0, 1)

    plt.suptitle('Precipitation: Every Station vs Dixon AWS (on-glacier ground truth)', fontsize=14)
    plt.tight_layout()
    fig.savefig(outdir / 'dixon_vs_all_precip.png', dpi=150, bbox_inches='tight')
    print(f"  Saved: {outdir / 'dixon_vs_all_precip.png'}")
    plt.close()

    # ═══════════════════════════════════════════════════════════════
    # Print detailed monthly transfer table
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("MONTHLY TRANSFER COEFFICIENTS: Station → Dixon")
    print("T_dixon = slope × T_station + intercept")
    print("=" * 90)

    for key in ['nuka', 'mfb', 'lower_kach', 'mcneil', 'anchor']:
        info = STATIONS[key]
        dates = get_overlap(data[key], dixon)
        if len(dates) < 30:
            continue
        dz = DIXON_ELEV - info['elev_m']
        print(f"\n  {info['name']} ({info['elev_m']}m, dz={dz:+.0f}m, {info['dist_km']}km):")
        print(f"  {'Month':>5} {'slope':>7} {'intcpt':>7} {'r²':>6} {'RMSE':>6} {'bias':>7} {'n':>5}")

        for m in [5, 6, 7, 8, 9]:
            md = dates[dates.month == m]
            if len(md) < 5:
                continue
            x = data[key].loc[md, 'tavg_c'].values
            y = dixon.loc[md, 'tavg_c'].values
            s, i = np.polyfit(x, y, 1)
            r2 = np.corrcoef(x, y)[0, 1] ** 2
            rmse = np.sqrt(np.mean((y - x) ** 2))
            bias = np.mean(y - x)
            mname = {5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct'}.get(m, str(m))
            print(f"  {mname:>5} {s:>7.3f} {i:>+7.2f} {r2:>6.3f} {rmse:>5.1f}C {bias:>+6.1f}C {len(md):>5}")

    print("\nDone.")


if __name__ == '__main__':
    main()
