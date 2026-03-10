"""
Download and extract CMIP6 climate projections for Dixon Glacier.

Downloads daily temperature and precipitation from NASA NEX-GDDP-CMIP6
(hosted on AWS S3, no authentication required). For each GCM/scenario/year,
downloads the full global NetCDF, extracts the single grid cell nearest to
Dixon Glacier (59.66N, 150.88W), saves the pixel time series to a local
CSV, and deletes the NetCDF.

Output: data/cmip6/dixon_{gcm}_{scenario}.csv
  Columns: date, temperature (C), precipitation (mm/day)

Usage:
    python download_cmip6.py [--gcms ACCESS-CM2 MRI-ESM2-0 ...]
                             [--scenarios ssp126 ssp245 ssp585]
                             [--years 2025 2100]

Reference: Thrasher et al. (2022), NEX-GDDP-CMIP6, NASA.
"""
import subprocess
import os
import sys
import argparse
import numpy as np
from pathlib import Path

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
CMIP6_DIR = PROJECT / 'data' / 'cmip6'
S3_BASE = 'https://nex-gddp-cmip6.s3.us-west-2.amazonaws.com/NEX-GDDP-CMIP6'

# Dixon Glacier target coordinates
DIXON_LAT = 59.66
DIXON_LON_360 = 360.0 - 150.88  # NEX-GDDP uses 0-360 longitude

# GCMs selected for multi-model ensemble: chosen for good performance in
# high-latitude maritime climates and availability across all 3 SSPs.
# 5 GCMs following Rounce et al. (2023) approach of using a representative
# subset rather than all available models.
DEFAULT_GCMS = [
    'ACCESS-CM2',       # Australian, good Arctic performance
    'EC-Earth3',        # European consortium, high resolution
    'MPI-ESM1-2-HR',    # German, high resolution
    'MRI-ESM2-0',       # Japanese, good precip
    'NorESM2-MM',       # Norwegian, designed for high latitudes
]

# NEX-GDDP-CMIP6 has SSP1-2.6, SSP2-4.5, SSP5-8.5 (no SSP3-7.0)
DEFAULT_SCENARIOS = ['ssp126', 'ssp245', 'ssp585']

# Ensemble member (r1i1p1f1 for all default GCMs)
ENSEMBLE = 'r1i1p1f1'


def extract_pixel(nc_path, variable):
    """Extract the Dixon grid cell from a global NetCDF file.

    Returns (dates, values) where values are in C (tas) or mm/day (pr).
    """
    import xarray as xr

    ds = xr.open_dataset(nc_path)
    point = ds.sel(lat=DIXON_LAT, lon=DIXON_LON_360, method='nearest')

    dates = point['time'].values
    values = point[variable].values.astype(np.float64)

    if variable == 'tas':
        values -= 273.15  # K -> C
    elif variable == 'pr':
        values *= 86400.0  # kg/m2/s -> mm/day

    ds.close()
    return dates, values


def download_and_extract(gcm, scenario, year, variable, tmp_dir):
    """Download one NetCDF, extract pixel, return (dates, values), delete file."""
    filename = f'{variable}_day_{gcm}_{scenario}_{ENSEMBLE}_gn_{year}.nc'
    url = f'{S3_BASE}/{gcm}/{scenario}/{ENSEMBLE}/{variable}/{filename}'
    tmp_file = tmp_dir / filename

    # Download with curl
    result = subprocess.run(
        ['curl', '-s', '-f', '-o', str(tmp_file), url],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f'    SKIP {variable} {year}: download failed')
        return None, None

    try:
        dates, values = extract_pixel(str(tmp_file), variable)
    finally:
        tmp_file.unlink(missing_ok=True)

    return dates, values


def download_gcm_scenario(gcm, scenario, year_start, year_end):
    """Download all years for one GCM/scenario combination."""
    import pandas as pd

    out_file = CMIP6_DIR / f'dixon_{gcm}_{scenario}.csv'
    if out_file.exists():
        print(f'  {gcm}/{scenario}: already exists, skipping')
        return

    tmp_dir = CMIP6_DIR / 'tmp'
    tmp_dir.mkdir(exist_ok=True)

    all_dates = []
    all_tas = []
    all_pr = []

    for year in range(year_start, year_end + 1):
        sys.stdout.write(f'\r  {gcm}/{scenario}: {year}')
        sys.stdout.flush()

        dates_t, tas = download_and_extract(gcm, scenario, year, 'tas', tmp_dir)
        dates_p, pr = download_and_extract(gcm, scenario, year, 'pr', tmp_dir)

        if dates_t is None or dates_p is None:
            continue

        all_dates.extend(dates_t)
        all_tas.extend(tas)
        all_pr.extend(pr)

    print()

    if len(all_dates) == 0:
        print(f'    WARNING: no data for {gcm}/{scenario}')
        return

    df = pd.DataFrame({
        'date': all_dates,
        'temperature': all_tas,
        'precipitation': all_pr,
    })
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    df.to_csv(out_file, index=False)
    print(f'    Saved {len(df)} days to {out_file.name}')

    # Cleanup
    try:
        tmp_dir.rmdir()
    except OSError:
        pass


def download_historical(gcm, year_start=1990, year_end=2014):
    """Download historical period for bias correction."""
    import pandas as pd

    out_file = CMIP6_DIR / f'dixon_{gcm}_historical.csv'
    if out_file.exists():
        print(f'  {gcm}/historical: already exists, skipping')
        return

    tmp_dir = CMIP6_DIR / 'tmp'
    tmp_dir.mkdir(exist_ok=True)

    all_dates = []
    all_tas = []
    all_pr = []

    for year in range(year_start, year_end + 1):
        sys.stdout.write(f'\r  {gcm}/historical: {year}')
        sys.stdout.flush()

        dates_t, tas = download_and_extract(
            gcm, 'historical', year, 'tas', tmp_dir)
        dates_p, pr = download_and_extract(
            gcm, 'historical', year, 'pr', tmp_dir)

        if dates_t is None or dates_p is None:
            continue

        all_dates.extend(dates_t)
        all_tas.extend(tas)
        all_pr.extend(pr)

    print()

    if len(all_dates) == 0:
        print(f'    WARNING: no data for {gcm}/historical')
        return

    df = pd.DataFrame({
        'date': all_dates,
        'temperature': all_tas,
        'precipitation': all_pr,
    })
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    df.to_csv(out_file, index=False)
    print(f'    Saved {len(df)} days to {out_file.name}')


def main():
    parser = argparse.ArgumentParser(
        description='Download CMIP6 projections for Dixon Glacier')
    parser.add_argument('--gcms', nargs='+', default=DEFAULT_GCMS)
    parser.add_argument('--scenarios', nargs='+', default=DEFAULT_SCENARIOS)
    parser.add_argument('--year-start', type=int, default=2025)
    parser.add_argument('--year-end', type=int, default=2100)
    parser.add_argument('--include-historical', action='store_true',
                        help='Also download 1990-2014 historical for bias correction')
    args = parser.parse_args()

    CMIP6_DIR.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('NEX-GDDP-CMIP6 Download for Dixon Glacier')
    print(f'  GCMs: {args.gcms}')
    print(f'  SSPs: {args.scenarios}')
    print(f'  Period: {args.year_start}-{args.year_end}')
    n_files = len(args.gcms) * len(args.scenarios) * (args.year_end - args.year_start + 1) * 2
    est_gb = n_files * 0.235 / 1000
    print(f'  Files to process: {n_files} (~{est_gb:.0f} GB download, extracted to ~KB)')
    print('=' * 60)

    for gcm in args.gcms:
        print(f'\n--- {gcm} ---')

        if args.include_historical:
            download_historical(gcm)

        for scenario in args.scenarios:
            download_gcm_scenario(gcm, scenario, args.year_start, args.year_end)

    print('\nDone!')
    print(f'Output files in: {CMIP6_DIR}')


if __name__ == '__main__':
    main()
