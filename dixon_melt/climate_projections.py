"""
Climate projection handling for Dixon Glacier DETIM.

Loads bias-corrected CMIP6 projections (from NEX-GDDP-CMIP6, extracted
by download_cmip6.py) and prepares daily forcing for the melt model.

Bias correction uses the delta method: adjust GCM output so that its
historical climatology matches the Nuka SNOTEL observed climatology.
This preserves the GCM's projected trend while removing systematic bias.

Reference: Maraun & Widmann (2018), Statistical Downscaling and Bias
    Correction for Climate Research, Cambridge University Press.
"""
import numpy as np
import pandas as pd
from pathlib import Path


# ── Available GCMs and scenarios ──────────────────────────────────────

GCMS = [
    'ACCESS-CM2',
    'EC-Earth3',
    'MPI-ESM1-2-HR',
    'MRI-ESM2-0',
    'NorESM2-MM',
]

SCENARIOS = {
    'ssp126': 'SSP1-2.6 (strong mitigation)',
    'ssp245': 'SSP2-4.5 (moderate mitigation)',
    'ssp585': 'SSP5-8.5 (high emissions)',
}


def load_nuka_historical(nuka_csv, period=(1991, 2020)):
    """Load Nuka SNOTEL observations for the reference period.

    Handles both raw Nuka format (Date, long column names, degF/inches)
    and pre-processed format (date, temperature, precipitation in C/mm).

    Returns DataFrame with 'temperature' and 'precipitation' columns,
    daily, with month and day-of-year columns for climatology matching.
    """
    df = pd.read_csv(nuka_csv)

    # Detect date column
    date_col = [c for c in df.columns if c.lower() == 'date'][0]
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col)

    # Detect and convert columns
    col_map = {}
    is_raw = False
    for c in df.columns:
        cl = c.lower()
        if 'air temperature average' in cl:
            col_map[c] = 'temperature'
            is_raw = True
        elif 'precipitation accumulation' in cl:
            col_map[c] = 'precip_accum'
            is_raw = True
        elif cl in ('tavg', 'temperature'):
            col_map[c] = 'temperature'
        elif cl in ('prec', 'precipitation'):
            col_map[c] = 'precipitation'
    df = df.rename(columns=col_map)

    if is_raw:
        # Convert degF -> C
        df['temperature'] = (df['temperature'] - 32.0) * 5.0 / 9.0
        # Convert cumulative inches -> daily mm
        accum = df['precip_accum']
        daily_in = accum.diff()
        # Reset negatives (gauge resets) to 0
        daily_in[daily_in < 0] = 0.0
        df['precipitation'] = daily_in * 25.4  # inches -> mm

    start = f'{period[0]}-01-01'
    end = f'{period[1]}-12-31'
    cols = ['temperature', 'precipitation']
    df = df.loc[start:end, [c for c in cols if c in df.columns]].copy()

    df['month'] = df.index.month
    df['doy'] = df.index.dayofyear

    return df


def compute_monthly_climatology(df):
    """Compute monthly mean temperature and total precipitation."""
    monthly = df.groupby('month').agg(
        T_mean=('temperature', 'mean'),
        P_mean=('precipitation', 'mean'),
    )
    return monthly


def load_gcm_projection(cmip6_dir, gcm, scenario):
    """Load a single GCM/scenario CSV produced by download_cmip6.py.

    Returns DataFrame with 'temperature' (C) and 'precipitation' (mm/day).
    """
    path = Path(cmip6_dir) / f'dixon_{gcm}_{scenario}.csv'
    if not path.exists():
        raise FileNotFoundError(
            f'GCM data not found: {path}\n'
            f'Run: python download_cmip6.py --gcms {gcm} --scenarios {scenario}')

    df = pd.read_csv(path, parse_dates=['date'], index_col='date')
    df['month'] = df.index.month
    df['doy'] = df.index.dayofyear
    return df


def bias_correct_delta(gcm_df, obs_climatology, gcm_hist_climatology=None):
    """Apply monthly delta bias correction.

    For temperature (additive):
        T_corrected = T_gcm + (T_obs_clim - T_gcm_hist_clim) for each month

    For precipitation (multiplicative):
        P_corrected = P_gcm * (P_obs_clim / P_gcm_hist_clim) for each month

    If gcm_hist_climatology is None, uses the first 20 years of gcm_df
    (2025-2044) as the GCM reference period — a common approach when
    historical GCM data isn't separately available.

    Parameters
    ----------
    gcm_df : DataFrame with temperature, precipitation, month columns
    obs_climatology : DataFrame from compute_monthly_climatology(nuka)
    gcm_hist_climatology : DataFrame or None

    Returns
    -------
    DataFrame with bias-corrected temperature and precipitation
    """
    corrected = gcm_df.copy()

    if gcm_hist_climatology is None:
        # Use first 20 years of projection as reference
        first_year = gcm_df.index.year.min()
        ref_end = first_year + 19
        ref_data = gcm_df[gcm_df.index.year <= ref_end]
        gcm_hist_climatology = compute_monthly_climatology(ref_data)

    for month in range(1, 13):
        mask = corrected['month'] == month

        # Temperature: additive correction
        delta_T = (obs_climatology.loc[month, 'T_mean'] -
                   gcm_hist_climatology.loc[month, 'T_mean'])
        corrected.loc[mask, 'temperature'] += delta_T

        # Precipitation: multiplicative correction
        gcm_p = gcm_hist_climatology.loc[month, 'P_mean']
        if gcm_p > 0.01:
            ratio_P = obs_climatology.loc[month, 'P_mean'] / gcm_p
        else:
            ratio_P = 1.0
        # Cap extreme corrections
        ratio_P = np.clip(ratio_P, 0.2, 5.0)
        corrected.loc[mask, 'precipitation'] *= ratio_P

    # Ensure non-negative precipitation
    corrected['precipitation'] = corrected['precipitation'].clip(lower=0.0)

    return corrected


def extract_water_year(df, wy_year):
    """Extract water year (Oct 1 to Sep 30) from a daily DataFrame.

    Parameters
    ----------
    df : DataFrame with datetime index
    wy_year : int, e.g. 2050 means Oct 2049 - Sep 2050

    Returns
    -------
    DataFrame for the water year, or None if insufficient data
    """
    start = f'{wy_year - 1}-10-01'
    end = f'{wy_year}-09-30'
    wy = df.loc[start:end]
    if len(wy) < 300:
        return None
    return wy


def prepare_gcm_ensemble(cmip6_dir, nuka_csv, scenario,
                         gcms=None, ref_period=(1991, 2020)):
    """Load and bias-correct all GCMs for a given scenario.

    Parameters
    ----------
    cmip6_dir : str, path to data/cmip6/
    nuka_csv : str, path to Nuka SNOTEL CSV
    scenario : str, e.g. 'ssp245'
    gcms : list of str or None (uses GCMS default)
    ref_period : tuple, observation reference period for bias correction

    Returns
    -------
    dict : {gcm_name: bias_corrected_DataFrame}
    """
    if gcms is None:
        gcms = GCMS

    # Observed climatology
    obs = load_nuka_historical(nuka_csv, ref_period)
    obs_clim = compute_monthly_climatology(obs)

    ensemble = {}
    for gcm in gcms:
        try:
            gcm_df = load_gcm_projection(cmip6_dir, gcm, scenario)
        except FileNotFoundError as e:
            print(f'  WARNING: {e}')
            continue

        # Try to load GCM historical for better bias correction
        hist_clim = None
        hist_path = Path(cmip6_dir) / f'dixon_{gcm}_historical.csv'
        if hist_path.exists():
            hist_df = pd.read_csv(hist_path, parse_dates=['date'],
                                  index_col='date')
            hist_df['month'] = hist_df.index.month
            hist_clim = compute_monthly_climatology(hist_df)

        corrected = bias_correct_delta(gcm_df, obs_clim, hist_clim)
        ensemble[gcm] = corrected

    return ensemble
