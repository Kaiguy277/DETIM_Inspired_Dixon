"""
Compute monthly transfer coefficients for multi-station gap-filling (D-025).

For each fill station, computes:
  - Temperature: reverse regression T_nuka = slope * T_other + intercept (monthly)
  - Precipitation (MFB only): monthly sum(P_nuka) / sum(P_mfb) on wet-day pairs

These coefficients go into config.py as hardcoded arrays.

Usage:
    python compute_transfer_coefficients.py
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')

# ── Station metadata ──────────────────────────────────────────────
STATIONS = {
    'nuka': {
        'name': 'Nuka Glacier', 'site': 1037, 'elev_m': 375,
        'path': PROJECT / 'data' / 'climate' / 'nuka_snotel_full.csv',
    },
    'mfb': {
        'name': 'Middle Fork Bradley', 'site': 1064, 'elev_m': 701,
        'path': PROJECT / 'data' / 'climate' / 'snotel_stations' / 'middle_fork_bradley_1064.csv',
    },
    'mcneil': {
        'name': 'McNeil Canyon', 'site': 1003, 'elev_m': 411,
        'path': PROJECT / 'data' / 'climate' / 'snotel_stations' / 'mcneil_canyon_1003.csv',
    },
    'anchor': {
        'name': 'Anchor River Divide', 'site': 1062, 'elev_m': 503,
        'path': PROJECT / 'data' / 'climate' / 'snotel_stations' / 'anchor_river_divide_1062.csv',
    },
    'kachemak': {
        'name': 'Kachemak Creek', 'site': 1063, 'elev_m': 503,
        'path': PROJECT / 'data' / 'climate' / 'snotel_stations' / 'kachemak_creek_1063.csv',
    },
    'lower_kach': {
        'name': 'Lower Kachemak Ck', 'site': 1265, 'elev_m': 597,
        'path': PROJECT / 'data' / 'climate' / 'snotel_stations' / 'lower_kachemak_1265.csv',
    },
}


def load_snotel(path):
    """Load SNOTEL CSV (NRCS format), return daily DataFrame with tavg_c, precip_mm."""
    df = pd.read_csv(path, comment='#', parse_dates=[0])
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


def main():
    print("=" * 70)
    print("TRANSFER COEFFICIENT COMPUTATION (D-025)")
    print("=" * 70)

    # Load all stations
    data = {}
    for key, info in STATIONS.items():
        df = load_snotel(info['path'])
        data[key] = df
        print(f"  Loaded {info['name']}: {len(df)} days")

    nuka = data['nuka']
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # ── Temperature transfer: T_nuka = slope * T_other + intercept ────
    fill_stations = ['mfb', 'mcneil', 'anchor', 'kachemak', 'lower_kach']

    print("\n" + "=" * 70)
    print("TEMPERATURE TRANSFER: T_nuka = slope * T_other + intercept")
    print("(reverse regression: predicting Nuka from each fill station)")
    print("=" * 70)

    temp_coeffs = {}
    all_rows = []

    for key in fill_stations:
        info = STATIONS[key]
        other = data[key]
        common = nuka.index.intersection(other.index)
        both_valid = nuka.loc[common, 'tavg_c'].notna() & other.loc[common, 'tavg_c'].notna()
        valid_dates = common[both_valid]

        slopes = np.zeros(12)
        intercepts = np.zeros(12)

        print(f"\n  {info['name']} ({info['elev_m']}m):")
        print(f"  {'Mon':>5} {'slope':>7} {'intcpt':>7} {'r²':>6} {'RMSE':>6} {'n':>6}")

        for m in range(1, 13):
            month_mask = valid_dates.month == m
            md = valid_dates[month_mask]
            if len(md) < 30:
                # Fallback: use annual regression for this month
                x_all = other.loc[valid_dates, 'tavg_c'].values
                y_all = nuka.loc[valid_dates, 'tavg_c'].values
                slope, intercept = np.polyfit(x_all, y_all, 1)
                slopes[m - 1] = slope
                intercepts[m - 1] = intercept
                print(f"  {month_names[m-1]:>5} {slope:>7.4f} {intercept:>+7.2f} {'N/A':>6} {'N/A':>6} {len(md):>6} (fallback)")
                continue

            # x = fill station, y = nuka (we want to PREDICT nuka)
            x = other.loc[md, 'tavg_c'].values
            y = nuka.loc[md, 'tavg_c'].values
            slope, intercept = np.polyfit(x, y, 1)
            r2 = np.corrcoef(x, y)[0, 1] ** 2
            predicted = slope * x + intercept
            rmse = np.sqrt(np.mean((predicted - y) ** 2))

            slopes[m - 1] = slope
            intercepts[m - 1] = intercept

            all_rows.append({
                'station': key, 'month': m, 'month_name': month_names[m-1],
                'slope': slope, 'intercept': intercept, 'r2': r2,
                'rmse': rmse, 'n': len(md),
            })

            print(f"  {month_names[m-1]:>5} {slope:>7.4f} {intercept:>+7.2f} {r2:>6.3f} {rmse:>6.2f} {len(md):>6}")

        temp_coeffs[key] = {'slopes': slopes, 'intercepts': intercepts}

    # ── Precipitation ratio: Nuka / MFB ─────────────────────────────
    print("\n" + "=" * 70)
    print("PRECIPITATION RATIO: P_nuka / P_mfb (monthly, wet-day pairs)")
    print("=" * 70)

    mfb = data['mfb']
    common = nuka.index.intersection(mfb.index)
    both_p = (nuka.loc[common, 'precip_mm'].notna() &
              mfb.loc[common, 'precip_mm'].notna())
    valid_p_dates = common[both_p]

    precip_ratios = np.zeros(12)
    print(f"\n  {'Mon':>5} {'ratio':>7} {'n_wet':>7} {'nuka_sum':>10} {'mfb_sum':>10}")

    for m in range(1, 13):
        month_mask = valid_p_dates.month == m
        md = valid_p_dates[month_mask]
        if len(md) < 30:
            precip_ratios[m - 1] = 1.0
            print(f"  {month_names[m-1]:>5} {'N/A':>7} {len(md):>7}")
            continue

        nuka_p = nuka.loc[md, 'precip_mm'].values
        mfb_p = mfb.loc[md, 'precip_mm'].values

        # Wet-day pairs: both > 0.5mm
        wet = (nuka_p > 0.5) & (mfb_p > 0.5)
        if wet.sum() < 10:
            precip_ratios[m - 1] = 1.0
            continue

        ratio = nuka_p[wet].sum() / mfb_p[wet].sum()
        precip_ratios[m - 1] = ratio

        all_rows.append({
            'station': 'mfb_precip', 'month': m, 'month_name': month_names[m-1],
            'slope': ratio, 'intercept': 0, 'r2': np.nan,
            'rmse': np.nan, 'n': wet.sum(),
        })

        print(f"  {month_names[m-1]:>5} {ratio:>7.3f} {wet.sum():>7} "
              f"{nuka_p[wet].sum():>10.1f} {mfb_p[wet].sum():>10.1f}")

    # ── Print config.py arrays ──────────────────────────────────────
    print("\n" + "=" * 70)
    print("CONFIG.PY ARRAYS (copy-paste ready)")
    print("=" * 70)

    print("\nTEMP_TRANSFER_TO_NUKA = {")
    for key in fill_stations:
        c = temp_coeffs[key]
        slope_str = ', '.join(f'{s:.4f}' for s in c['slopes'])
        intc_str = ', '.join(f'{i:+.2f}' for i in c['intercepts'])
        print(f"    '{key}': {{")
        print(f"        'slopes': np.array([{slope_str}]),")
        print(f"        'intercepts': np.array([{intc_str}]),")
        print(f"    }},")
    print("}")

    ratio_str = ', '.join(f'{r:.3f}' for r in precip_ratios)
    print(f"\nPRECIP_RATIO_NUKA_OVER_MFB = np.array([{ratio_str}])")

    # ── Save CSV ────────────────────────────────────────────────────
    outdir = Path('calibration_output')
    outdir.mkdir(exist_ok=True)
    coeffs_df = pd.DataFrame(all_rows)
    csv_path = outdir / 'transfer_coefficients.csv'
    coeffs_df.to_csv(csv_path, index=False)
    print(f"\nSaved: {csv_path}")

    # ── Validation scatter plot ─────────────────────────────────────
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    axes = axes.flatten()

    for idx, key in enumerate(fill_stations):
        ax = axes[idx]
        info = STATIONS[key]
        other = data[key]
        c = temp_coeffs[key]

        common = nuka.index.intersection(other.index)
        both_valid = nuka.loc[common, 'tavg_c'].notna() & other.loc[common, 'tavg_c'].notna()
        vd = common[both_valid]

        if len(vd) == 0:
            continue

        x = other.loc[vd, 'tavg_c'].values
        y_actual = nuka.loc[vd, 'tavg_c'].values
        months = vd.month.values

        # Predict nuka from other using monthly coefficients
        y_pred = np.zeros_like(y_actual)
        for i in range(len(x)):
            m = months[i] - 1  # 0-indexed
            y_pred[i] = c['slopes'][m] * x[i] + c['intercepts'][m]

        rmse = np.sqrt(np.mean((y_pred - y_actual) ** 2))
        r = np.corrcoef(y_pred, y_actual)[0, 1]

        ax.scatter(y_actual, y_pred, s=1, alpha=0.15)
        lo, hi = -30, 25
        ax.plot([lo, hi], [lo, hi], 'r--', lw=1, label='1:1')
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_aspect('equal')
        ax.set_xlabel('Actual Nuka T (°C)')
        ax.set_ylabel('Predicted Nuka T (°C)')
        ax.set_title(f'{info["name"]}\nRMSE={rmse:.2f}°C, r={r:.3f}, n={len(vd)}',
                     fontsize=10)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    axes[5].set_visible(False)

    plt.suptitle('Transfer Validation: Predicted vs Actual Nuka T\n'
                 '(monthly regression coefficients)', fontsize=14)
    plt.tight_layout()
    fig.savefig(outdir / 'transfer_validation_scatter.png', dpi=150, bbox_inches='tight')
    print(f"Saved: {outdir / 'transfer_validation_scatter.png'}")
    plt.close('all')

    print("\nDone.")


if __name__ == '__main__':
    main()
