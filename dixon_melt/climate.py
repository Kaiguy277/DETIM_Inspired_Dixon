"""
Climate data ingestion, cleaning, and multi-station gap-filling for Dixon Glacier.

Sources:
  - Nuka Glacier SNOTEL (site 1037, 375m / 1230 ft elev) — daily T, precip since 1990
  - Middle Fork Bradley (1064, 701m) — best temperature predictor
  - McNeil Canyon (1003, 411m) — covers WY2001 gaps
  - Anchor River Divide (1062, 503m) — longest record
  - Kachemak Creek (1063, 503m) — discontinued 2019
  - Lower Kachemak Creek (1265, 597m) — since 2015
  - Dixon on-glacier AWS — hourly T, precip during summer field seasons (validation only)

Gap-filling strategy (D-025):
  Temperature cascade: Nuka → MFB → McNeil → Anchor → Kachemak → Lower Kach
                       → linear interp (≤3d) → DOY climatology
  Precipitation cascade: Nuka → MFB (monthly ratio) → DOY climatology
"""
import numpy as np
import pandas as pd
from pathlib import Path
from . import config


# ── Nuka SNOTEL ─────────────────────────────────────────────────────

NUKA_ELEV = 375.0  # m (1230 ft; D-013: NRCS reports in feet, not meters)


def load_nuka_snotel(csv_path):
    """Load and clean Nuka SNOTEL daily data from NRCS Report Generator CSV.

    Converts from imperial to metric:
      - Temperature: °F → °C
      - Precipitation accumulation: inches → daily mm
      - Snow depth: inches → cm

    Returns
    -------
    DataFrame with columns: date, tavg_c, tmax_c, tmin_c, precip_mm, snow_depth_cm
    """
    df = pd.read_csv(csv_path, parse_dates=['Date'])
    df = df.rename(columns={'Date': 'date'})

    # Rename columns for clarity
    col_map = {
        'Snow Water Equivalent (in) Start of Day Values': 'swe_in',
        'Snow Depth (in) Start of Day Values': 'snow_depth_in',
        'Precipitation Accumulation (in) Start of Day Values': 'precip_accum_in',
        'Air Temperature Average (degF)': 'tavg_f',
        'Air Temperature Maximum (degF)': 'tmax_f',
        'Air Temperature Minimum (degF)': 'tmin_f',
    }
    df = df.rename(columns=col_map)

    # Convert temperature: °F → °C
    for col_f, col_c in [('tavg_f', 'tavg_c'), ('tmax_f', 'tmax_c'), ('tmin_f', 'tmin_c')]:
        if col_f in df.columns:
            df[col_c] = (df[col_f] - 32) * 5 / 9

    # Convert cumulative precip to daily increments (inches → mm)
    if 'precip_accum_in' in df.columns:
        accum = df['precip_accum_in'].copy()
        # Detect water year resets (big drops in accumulation)
        diff = accum.diff()
        # Reset points: where accumulation drops by more than 1 inch
        resets = diff < -1.0
        # Daily precip = diff, except at resets set to 0
        daily_in = diff.clip(lower=0)
        daily_in.iloc[0] = 0
        daily_in[resets] = 0
        df['precip_mm'] = daily_in * 25.4

    # Snow depth: inches → cm
    if 'snow_depth_in' in df.columns:
        df['snow_depth_cm'] = df['snow_depth_in'] * 2.54

    # QC: flag unreasonable values
    if 'tavg_c' in df.columns:
        bad_t = (df['tavg_c'] < -50) | (df['tavg_c'] > 40)
        df.loc[bad_t, ['tavg_c', 'tmax_c', 'tmin_c']] = np.nan

    if 'precip_mm' in df.columns:
        bad_p = (df['precip_mm'] < 0) | (df['precip_mm'] > 300)
        df.loc[bad_p, 'precip_mm'] = np.nan

    # Select clean columns
    out_cols = ['date']
    for c in ['tavg_c', 'tmax_c', 'tmin_c', 'precip_mm', 'snow_depth_cm', 'swe_in']:
        if c in df.columns:
            out_cols.append(c)

    df = df[out_cols].copy()
    df = df.set_index('date').sort_index()

    return df


# ── Dixon AWS ───────────────────────────────────────────────────────

DIXON_AWS_ELEV = 1078.0  # m, at ELA stake site (D-023: was incorrectly 804m/ABL)


def load_dixon_aws(csv_path, year=None):
    """Load Dixon on-glacier AWS data (hourly).

    Returns hourly DataFrame with: timestamp, temperature_c, precip_mm
    """
    df = pd.read_csv(csv_path)

    # Normalize column names
    if 'TIMESTAMP' in df.columns:
        df = df.rename(columns={'TIMESTAMP': 'timestamp'})
    if 'AirTC_Avg' in df.columns:
        df = df.rename(columns={'AirTC_Avg': 'temperature_c'})
    if 'Rain_mm_Tot' in df.columns:
        df = df.rename(columns={'Rain_mm_Tot': 'precip_mm'})

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # QC: remove bad temperatures
    bad = (df['temperature_c'] < -50) | (df['temperature_c'] > 40)
    n_bad = bad.sum()
    if n_bad > 0:
        print(f"  Flagged {n_bad} bad temperature values in Dixon AWS")
        df.loc[bad, 'temperature_c'] = np.nan

    return df[['timestamp', 'temperature_c', 'precip_mm']].copy()


def dixon_aws_to_daily(df):
    """Aggregate hourly Dixon AWS to daily (mean temp, total precip)."""
    df = df.set_index('timestamp')
    daily = pd.DataFrame()
    daily['tavg_c'] = df['temperature_c'].resample('D').mean()
    daily['tmax_c'] = df['temperature_c'].resample('D').max()
    daily['tmin_c'] = df['temperature_c'].resample('D').min()
    daily['precip_mm'] = df['precip_mm'].resample('D').sum()
    daily.index.name = 'date'
    return daily


# ── Generic SNOTEL loader ───────────────────────────────────────────

def load_snotel_station(csv_path):
    """Load any SNOTEL CSV (NRCS format) and return daily DataFrame.

    Returns DataFrame indexed by date with tavg_c, precip_mm columns.
    """
    df = pd.read_csv(csv_path, comment='#', parse_dates=[0])
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


def load_all_stations(project_root=None):
    """Load all SNOTEL stations defined in config.SNOTEL_STATIONS.

    Returns dict of station_key → DataFrame (indexed by date, with tavg_c, precip_mm).
    """
    if project_root is None:
        project_root = Path(__file__).parent.parent

    data = {}
    for key, info in config.SNOTEL_STATIONS.items():
        path = Path(project_root) / info['path']
        if key == 'nuka':
            data[key] = load_nuka_snotel(str(path))
        else:
            data[key] = load_snotel_station(str(path))
    return data


# ── Transfer functions ──────────────────────────────────────────────

def transfer_temp_to_nuka(other_tavg, station_key, month_index):
    """Apply monthly regression to produce Nuka-equivalent temperature.

    Parameters
    ----------
    other_tavg : float or array
        Temperature at the fill station (°C)
    station_key : str
        Key in config.TEMP_TRANSFER_TO_NUKA (e.g., 'mfb')
    month_index : int or array
        0-indexed month (0=Jan, 11=Dec)

    Returns
    -------
    Predicted Nuka temperature (°C)
    """
    coeffs = config.TEMP_TRANSFER_TO_NUKA[station_key]
    slope = coeffs['slopes'][month_index]
    intercept = coeffs['intercepts'][month_index]
    return slope * other_tavg + intercept


def transfer_precip_to_nuka(other_precip, month_index):
    """Apply monthly ratio to produce Nuka-equivalent precipitation.

    Parameters
    ----------
    other_precip : float or array
        Precipitation at MFB station (mm)
    month_index : int or array
        0-indexed month (0=Jan, 11=Dec)

    Returns
    -------
    Predicted Nuka precipitation (mm)
    """
    ratio = config.PRECIP_RATIO_NUKA_OVER_MFB[month_index]
    return ratio * other_precip


# ── Gap-filling ─────────────────────────────────────────────────────

def gap_fill_temperature(nuka_t, all_stations):
    """Fill temperature gaps using multi-station cascade.

    Cascade order (config.TEMP_FILL_ORDER):
      Nuka → MFB → McNeil → Anchor → Kachemak → Lower Kach
      → linear interp (≤3d) → DOY climatology

    Parameters
    ----------
    nuka_t : Series
        Nuka tavg_c, DatetimeIndex
    all_stations : dict
        station_key → DataFrame with tavg_c column

    Returns
    -------
    filled_t : Series
        Gap-filled temperature (Nuka-equivalent)
    source_labels : Series
        Source label per day ('nuka', 'mfb', 'interp', 'climatology', etc.)
    """
    filled = nuka_t.copy()
    source = pd.Series('nuka', index=filled.index, dtype='object')
    source[filled.isna()] = ''

    for station_key in config.TEMP_FILL_ORDER:
        still_nan = filled.isna()
        if not still_nan.any():
            break

        if station_key not in all_stations:
            continue

        other = all_stations[station_key]
        if 'tavg_c' not in other.columns:
            continue

        # Find dates where Nuka is NaN but fill station has data
        nan_dates = filled.index[still_nan]
        overlap = nan_dates.intersection(other.index)
        valid = other.loc[overlap, 'tavg_c'].notna()
        fill_dates = overlap[valid]

        if len(fill_dates) == 0:
            continue

        # Apply monthly transfer
        months = fill_dates.month.values - 1  # 0-indexed
        other_vals = other.loc[fill_dates, 'tavg_c'].values
        transferred = np.array([
            transfer_temp_to_nuka(other_vals[i], station_key, months[i])
            for i in range(len(fill_dates))
        ])

        filled.loc[fill_dates] = transferred
        source.loc[fill_dates] = station_key

    # Linear interpolation for remaining gaps ≤ 3 days
    still_nan = filled.isna()
    if still_nan.any():
        filled_interp = filled.interpolate(method='linear', limit=3)
        newly_filled = still_nan & filled_interp.notna()
        filled.loc[newly_filled] = filled_interp.loc[newly_filled]
        source.loc[newly_filled] = 'interp'

    # DOY climatology for anything still remaining
    still_nan = filled.isna()
    if still_nan.any():
        doy_clim = filled.groupby(filled.index.dayofyear).mean()
        nan_dates = filled.index[still_nan]
        doys = nan_dates.dayofyear
        clim_vals = doy_clim.reindex(doys).values
        filled.loc[nan_dates] = clim_vals
        source.loc[nan_dates] = 'climatology'

    return filled, source


def gap_fill_precipitation(nuka_p, all_stations):
    """Fill precipitation gaps using MFB ratio transfer + DOY climatology.

    Cascade: Nuka → MFB (monthly ratio) → DOY climatology

    Parameters
    ----------
    nuka_p : Series
        Nuka precip_mm, DatetimeIndex
    all_stations : dict
        station_key → DataFrame with precip_mm column

    Returns
    -------
    filled_p : Series
        Gap-filled precipitation (Nuka-equivalent, mm)
    source_labels : Series
        Source label per day
    """
    filled = nuka_p.copy()
    source = pd.Series('nuka', index=filled.index, dtype='object')
    source[filled.isna()] = ''

    for station_key in config.PRECIP_FILL_ORDER:
        still_nan = filled.isna()
        if not still_nan.any():
            break

        if station_key not in all_stations:
            continue

        other = all_stations[station_key]
        if 'precip_mm' not in other.columns:
            continue

        nan_dates = filled.index[still_nan]
        overlap = nan_dates.intersection(other.index)
        valid = other.loc[overlap, 'precip_mm'].notna()
        fill_dates = overlap[valid]

        if len(fill_dates) == 0:
            continue

        months = fill_dates.month.values - 1
        other_vals = other.loc[fill_dates, 'precip_mm'].values
        transferred = np.array([
            transfer_precip_to_nuka(other_vals[i], months[i])
            for i in range(len(fill_dates))
        ])

        filled.loc[fill_dates] = transferred
        source.loc[fill_dates] = station_key

    # DOY climatology for remaining
    still_nan = filled.isna()
    if still_nan.any():
        doy_clim = filled.groupby(filled.index.dayofyear).mean()
        nan_dates = filled.index[still_nan]
        doys = nan_dates.dayofyear
        clim_vals = doy_clim.reindex(doys).values
        filled.loc[nan_dates] = clim_vals
        source.loc[nan_dates] = 'climatology'

    # Any still NaN → 0 (shouldn't happen, but safety)
    filled = filled.fillna(0.0)

    return filled, source


def prepare_gap_filled_climate(project_root=None):
    """Full multi-station gap-filling pipeline.

    Produces a complete daily climate record for WY1999–WY2025 with
    zero NaN values, suitable for model forcing.

    Returns
    -------
    DataFrame with columns: temperature, precipitation, temp_source, precip_source
    """
    if project_root is None:
        project_root = Path(__file__).parent.parent

    print("Loading all SNOTEL stations...")
    all_stations = load_all_stations(project_root)

    nuka = all_stations['nuka']
    print(f"  Nuka: {len(nuka)} days, "
          f"T valid: {nuka['tavg_c'].notna().sum()}, "
          f"P valid: {nuka['precip_mm'].notna().sum()}")

    # Trim to WY range
    wy_start = config.HISTORICAL_WY_START
    wy_end = config.HISTORICAL_WY_END
    start_date = f'{wy_start - 1}-10-01'
    end_date = f'{wy_end}-09-30'

    # Create complete date index
    date_idx = pd.date_range(start_date, end_date, freq='D')

    # Reindex Nuka to full range (introduces NaN for missing dates)
    nuka_t = nuka['tavg_c'].reindex(date_idx)
    nuka_p = nuka['precip_mm'].reindex(date_idx)

    n_t_nan = nuka_t.isna().sum()
    n_p_nan = nuka_p.isna().sum()
    print(f"\n  Period: {start_date} to {end_date} ({len(date_idx)} days)")
    print(f"  Nuka T gaps: {n_t_nan} days ({100*n_t_nan/len(date_idx):.1f}%)")
    print(f"  Nuka P gaps: {n_p_nan} days ({100*n_p_nan/len(date_idx):.1f}%)")

    print("\n  Gap-filling temperature...")
    filled_t, t_source = gap_fill_temperature(nuka_t, all_stations)
    print(f"    Remaining NaN: {filled_t.isna().sum()}")

    print("  Gap-filling precipitation...")
    filled_p, p_source = gap_fill_precipitation(nuka_p, all_stations)
    print(f"    Remaining NaN: {filled_p.isna().sum()}")

    out = pd.DataFrame({
        'temperature': filled_t,
        'precipitation': filled_p,
        'temp_source': t_source,
        'precip_source': p_source,
    }, index=date_idx)
    out.index.name = 'date'

    return out


def climate_quality_report(df):
    """Print per-WY source breakdown for gap-filled climate.

    Parameters
    ----------
    df : DataFrame from prepare_gap_filled_climate()

    Returns
    -------
    summary : DataFrame with per-WY source fractions
    """
    print("\n" + "=" * 70)
    print("CLIMATE GAP-FILL QUALITY REPORT")
    print("=" * 70)

    # Overall
    print(f"\n  Total days: {len(df)}")
    print(f"  Temperature NaN: {df['temperature'].isna().sum()}")
    print(f"  Precipitation NaN: {df['precipitation'].isna().sum()}")

    print(f"\n  Temperature sources (overall):")
    t_counts = df['temp_source'].value_counts()
    for src, count in t_counts.items():
        print(f"    {src:15s}: {count:5d} ({100*count/len(df):5.1f}%)")

    print(f"\n  Precipitation sources (overall):")
    p_counts = df['precip_source'].value_counts()
    for src, count in p_counts.items():
        print(f"    {src:15s}: {count:5d} ({100*count/len(df):5.1f}%)")

    # Per water year
    df = df.copy()
    df['wy'] = df.index.year
    df.loc[df.index.month >= 10, 'wy'] = df.loc[df.index.month >= 10, 'wy'] + 1

    print(f"\n  {'WY':>6} {'days':>5} {'nuka_T%':>8} {'fill_T%':>8} {'nuka_P%':>8} {'fill_P%':>8} {'T_sources':>30}")

    rows = []
    for wy, grp in df.groupby('wy'):
        n = len(grp)
        nuka_t = (grp['temp_source'] == 'nuka').sum()
        nuka_p = (grp['precip_source'] == 'nuka').sum()
        t_sources = grp['temp_source'].value_counts().to_dict()
        # Remove nuka from source summary for readability
        fill_sources = {k: v for k, v in t_sources.items() if k != 'nuka'}
        fill_str = ', '.join(f'{k}:{v}' for k, v in fill_sources.items()) if fill_sources else '-'

        print(f"  {wy:>6} {n:>5} {100*nuka_t/n:>7.1f}% {100*(n-nuka_t)/n:>7.1f}% "
              f"{100*nuka_p/n:>7.1f}% {100*(n-nuka_p)/n:>7.1f}%  {fill_str}")

        rows.append({
            'wy': wy, 'n_days': n,
            'nuka_t_frac': nuka_t / n, 'nuka_p_frac': nuka_p / n,
            **{f't_{k}': v for k, v in t_sources.items()},
        })

    return pd.DataFrame(rows)


def summarize_climate(df):
    """Print a summary of the climate dataset."""
    print("\n=== Climate Data Summary ===")
    print(f"Period: {df.index.min().date()} to {df.index.max().date()}")
    print(f"Total days: {len(df)}")
    print(f"Temperature coverage: {df['temperature'].notna().sum()}/{len(df)}")
    print(f"Precipitation coverage: {df['precipitation'].notna().sum()}/{len(df)}")

    if 'temp_source' in df.columns:
        print(f"\nTemperature sources:")
        print(df['temp_source'].value_counts().to_string())

    by_year = df.groupby(df.index.year).agg(
        mean_T=('temperature', 'mean'),
        total_P=('precipitation', 'sum'),
        coverage=('temperature', lambda x: x.notna().mean()),
    )
    print(f"\nAnnual summary:")
    print(by_year.to_string())


# ── Load gap-filled CSV ─────────────────────────────────────────────

def load_gap_filled_climate(csv_path=None, project_root=None):
    """Load pre-computed gap-filled climate CSV.

    Parameters
    ----------
    csv_path : str or Path, optional
        Explicit path to gap-filled CSV. If None, uses default location.
    project_root : str or Path, optional

    Returns
    -------
    DataFrame with columns: temperature, precipitation, temp_source, precip_source
    """
    if csv_path is None:
        if project_root is None:
            project_root = Path(__file__).parent.parent
        csv_path = Path(project_root) / 'data' / 'climate' / 'dixon_gap_filled_climate.csv'

    df = pd.read_csv(csv_path, parse_dates=['date'], index_col='date')
    return df


# ── Main: generate gap-filled CSV ──────────────────────────────────

if __name__ == '__main__':
    project_root = Path(__file__).parent.parent

    print("=" * 70)
    print("GENERATING GAP-FILLED CLIMATE CSV (D-025)")
    print("=" * 70)

    df = prepare_gap_filled_climate(project_root)
    summary = climate_quality_report(df)

    # Save
    out_path = project_root / 'data' / 'climate' / 'dixon_gap_filled_climate.csv'
    df.to_csv(out_path)
    print(f"\nSaved: {out_path}")
    print(f"  {len(df)} days, T NaN: {df['temperature'].isna().sum()}, "
          f"P NaN: {df['precipitation'].isna().sum()}")

    # Verification checks
    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    assert df['temperature'].isna().sum() == 0, "Temperature has NaN!"
    assert df['precipitation'].isna().sum() == 0, "Precipitation has NaN!"
    print("  [PASS] Zero NaN in output")

    nuka_frac = (df['temp_source'] == 'nuka').mean()
    print(f"  [INFO] Nuka fraction: {100*nuka_frac:.1f}% (want >90%)")
    assert nuka_frac > 0.7, f"Nuka fraction too low: {nuka_frac:.2f}"

    # Check WY2005 summer T (was 0 with old fillna(0))
    wy2005_summer = df.loc['2005-06-01':'2005-08-31', 'temperature']
    mean_t_2005 = wy2005_summer.mean()
    print(f"  [INFO] WY2005 Jun-Aug mean T: {mean_t_2005:.1f}°C (want 8-14°C, was ~0°C)")
    assert mean_t_2005 > 5, f"WY2005 summer T too low: {mean_t_2005:.1f}"

    # Check WY2020 total precip (was ~1176mm with old fillna(0))
    wy2020 = df.loc['2019-10-01':'2020-09-30', 'precipitation']
    total_p_2020 = wy2020.sum()
    print(f"  [INFO] WY2020 total precip: {total_p_2020:.0f}mm (want >1500mm, was ~1176mm)")
    assert total_p_2020 > 1500, f"WY2020 precip too low: {total_p_2020:.0f}"

    print("\n  All checks passed.")
