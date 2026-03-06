"""
Climate data ingestion, cleaning, and merging for Dixon Glacier.

Sources:
  - Nuka Glacier SNOTEL (site 1037, 1230m elev) — daily T, precip since 1990
  - Dixon on-glacier AWS — hourly T, precip during summer field seasons
"""
import numpy as np
import pandas as pd
from pathlib import Path


# ── Nuka SNOTEL ─────────────────────────────────────────────────────

NUKA_ELEV = 1230.0  # m


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

DIXON_AWS_ELEV = 804.0  # m, approximate (near ABL stake)


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


# ── Merging / Gap-filling ───────────────────────────────────────────

def merge_climate_data(nuka_df, dixon_daily_df=None, lapse_rate=-0.0065):
    """Merge Nuka SNOTEL with Dixon AWS data.

    Strategy:
    - Use Dixon AWS data directly during overlap periods
    - Use Nuka SNOTEL (adjusted by lapse rate) to fill gaps
    - Nuka is the backbone for the full historical record

    Parameters
    ----------
    nuka_df : DataFrame (daily, indexed by date)
        From load_nuka_snotel()
    dixon_daily_df : DataFrame (daily, indexed by date), optional
        From dixon_aws_to_daily()
    lapse_rate : float
        °C/m, for adjusting Nuka temp to Dixon station elevation

    Returns
    -------
    DataFrame with columns: temperature, precipitation (at Dixon AWS elevation)
    """
    # Adjust Nuka temps to Dixon AWS elevation
    dz = DIXON_AWS_ELEV - NUKA_ELEV  # negative (Dixon lower)
    nuka_adj = nuka_df.copy()
    nuka_adj['tavg_c'] = nuka_adj['tavg_c'] + lapse_rate * dz

    # Build output at Nuka backbone dates
    out = pd.DataFrame(index=nuka_adj.index)
    out['temperature'] = nuka_adj['tavg_c']
    out['precipitation'] = nuka_adj['precip_mm']
    out['source'] = 'nuka'

    # Overlay Dixon AWS where available
    if dixon_daily_df is not None:
        overlap = out.index.intersection(dixon_daily_df.index)
        if len(overlap) > 0:
            # For temperature: prefer Dixon AWS
            valid_t = dixon_daily_df.loc[overlap, 'tavg_c'].notna()
            valid_dates = overlap[valid_t]
            out.loc[valid_dates, 'temperature'] = dixon_daily_df.loc[valid_dates, 'tavg_c']
            out.loc[valid_dates, 'source'] = 'dixon_aws'

            # For precip: prefer Dixon AWS (it's on the glacier)
            valid_p = dixon_daily_df.loc[overlap, 'precip_mm'].notna()
            valid_p_dates = overlap[valid_p]
            out.loc[valid_p_dates, 'precipitation'] = dixon_daily_df.loc[valid_p_dates, 'precip_mm']

    # Interpolate small gaps (up to 3 days)
    out['temperature'] = out['temperature'].interpolate(method='linear', limit=3)
    out['precipitation'] = out['precipitation'].fillna(0)

    return out


def prepare_model_climate(nuka_csv, dixon_csv_paths=None, lapse_rate=-0.0065):
    """Full climate preparation pipeline.

    Parameters
    ----------
    nuka_csv : str
        Path to nuka_snotel_full.csv
    dixon_csv_paths : list of str, optional
        Paths to Dixon AWS CSVs
    lapse_rate : float

    Returns
    -------
    climate_df : DataFrame ready for model.run()
    """
    print("Loading Nuka SNOTEL data...")
    nuka = load_nuka_snotel(nuka_csv)
    print(f"  {len(nuka)} days, {nuka['tavg_c'].notna().sum()} with temperature")

    dixon_daily = None
    if dixon_csv_paths:
        parts = []
        for path in dixon_csv_paths:
            print(f"Loading Dixon AWS: {Path(path).name}")
            hourly = load_dixon_aws(path)
            daily = dixon_aws_to_daily(hourly)
            print(f"  {len(daily)} days, {daily['tavg_c'].notna().sum()} with temperature")
            parts.append(daily)
        dixon_daily = pd.concat(parts)
        dixon_daily = dixon_daily[~dixon_daily.index.duplicated(keep='last')]

    print("Merging climate data...")
    merged = merge_climate_data(nuka, dixon_daily, lapse_rate=lapse_rate)

    valid = merged['temperature'].notna()
    print(f"  Final: {len(merged)} days, {valid.sum()} with temperature ({100*valid.mean():.0f}%)")
    print(f"  Date range: {merged.index.min()} to {merged.index.max()}")

    return merged


def summarize_climate(df):
    """Print a summary of the climate dataset."""
    print("\n=== Climate Data Summary ===")
    print(f"Period: {df.index.min().date()} to {df.index.max().date()}")
    print(f"Total days: {len(df)}")
    print(f"Temperature coverage: {df['temperature'].notna().sum()}/{len(df)}")
    print(f"Precipitation coverage: {df['precipitation'].notna().sum()}/{len(df)}")

    if 'source' in df.columns:
        print(f"\nData sources:")
        print(df['source'].value_counts().to_string())

    by_year = df.groupby(df.index.year).agg(
        mean_T=('temperature', 'mean'),
        total_P=('precipitation', 'sum'),
        coverage=('temperature', lambda x: x.notna().mean()),
    )
    print(f"\nAnnual summary:")
    print(by_year.to_string())
