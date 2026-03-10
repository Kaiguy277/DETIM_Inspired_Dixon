"""
Download and extract CMIP6 climate projections for Dixon Glacier.

Downloads daily temperature and precipitation from NASA NEX-GDDP-CMIP6
(hosted on AWS S3, no authentication required). For each GCM/scenario/year,
downloads the global NetCDF, extracts the single grid cell nearest to
Dixon Glacier (59.66N, 150.88W), saves to a local CSV, and deletes.

Uses batch downloading: downloads N files concurrently with curl, then
extracts pixels sequentially (avoids xarray/HDF5 threading issues).

Output: data/cmip6/dixon_{gcm}_{scenario}.csv

Usage:
    python download_cmip6.py [--gcms ACCESS-CM2 ...]
                             [--scenarios ssp126 ssp245 ssp585]
                             [--parallel 4]
"""
import subprocess
import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
CMIP6_DIR = PROJECT / 'data' / 'cmip6'
S3_BASE = 'https://nex-gddp-cmip6.s3.us-west-2.amazonaws.com/NEX-GDDP-CMIP6'

DIXON_LAT = 59.66
DIXON_LON_360 = 360.0 - 150.88

DEFAULT_GCMS = [
    'ACCESS-CM2',
    'EC-Earth3',
    'MPI-ESM1-2-HR',
    'MRI-ESM2-0',
    'NorESM2-MM',
]
DEFAULT_SCENARIOS = ['ssp126', 'ssp245', 'ssp585']
ENSEMBLE = 'r1i1p1f1'


def extract_pixel(nc_path, variable):
    """Extract Dixon pixel from global NetCDF. Returns (dates, values)."""
    import xarray as xr
    ds = xr.open_dataset(nc_path)
    point = ds.sel(lat=DIXON_LAT, lon=DIXON_LON_360, method='nearest')
    dates = point['time'].values
    values = point[variable].values.astype(np.float64)
    if variable == 'tas':
        values -= 273.15
    elif variable == 'pr':
        values *= 86400.0
    ds.close()
    return dates, values


def download_gcm_scenario(gcm, scenario, year_start, year_end, n_parallel=4):
    """Download all years for one GCM/scenario.

    Strategy: process in batches of n_parallel years.
    Each batch: download 2*n_parallel files (tas+pr) concurrently via
    background curl processes, then extract pixels sequentially, then delete.
    """
    out_file = CMIP6_DIR / f'dixon_{gcm}_{scenario}.csv'
    if out_file.exists():
        n = sum(1 for _ in open(out_file)) - 1
        print(f'  {gcm}/{scenario}: exists ({n} days), skipping')
        return

    tmp_dir = CMIP6_DIR / 'tmp'
    tmp_dir.mkdir(exist_ok=True)

    years = list(range(year_start, year_end + 1))
    all_dates, all_tas, all_pr = [], [], []
    done = 0

    # Process in batches
    batch_size = n_parallel
    for batch_start in range(0, len(years), batch_size):
        batch_years = years[batch_start:batch_start + batch_size]

        # 1) Launch all downloads for this batch concurrently
        procs = []
        files_to_extract = []
        for year in batch_years:
            for var in ['tas', 'pr']:
                fname = f'{var}_day_{gcm}_{scenario}_{ENSEMBLE}_gn_{year}.nc'
                url = f'{S3_BASE}/{gcm}/{scenario}/{ENSEMBLE}/{var}/{fname}'
                local = tmp_dir / f'{var}_{year}.nc'
                p = subprocess.Popen(
                    ['curl', '-s', '-f', '-o', str(local), url],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                procs.append(p)
                files_to_extract.append((year, var, local))

        # 2) Wait for all downloads to finish
        for p in procs:
            p.wait()

        # 3) Extract pixels sequentially (safe for xarray/HDF5)
        for year, var, local in files_to_extract:
            if not local.exists():
                continue
            try:
                dates, values = extract_pixel(str(local), var)
                if var == 'tas':
                    all_dates.extend(dates)
                    all_tas.extend(values)
                else:
                    all_pr.extend(values)
            except Exception as e:
                print(f'\n    WARN: {var}/{year}: {e}')
            finally:
                local.unlink(missing_ok=True)

        done += len(batch_years)
        pct = 100 * done / len(years)
        sys.stdout.write(f'\r  {gcm}/{scenario}: {done}/{len(years)} years ({pct:.0f}%)')
        sys.stdout.flush()

    print()

    if len(all_dates) == 0:
        print(f'    WARNING: no data for {gcm}/{scenario}')
        return

    # Ensure tas and pr align
    n = min(len(all_dates), len(all_tas), len(all_pr))
    df = pd.DataFrame({
        'date': all_dates[:n],
        'temperature': all_tas[:n],
        'precipitation': all_pr[:n],
    })
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    df.to_csv(out_file, index=False)
    print(f'    Saved {len(df)} days ({len(df)/365:.0f} yrs) to {out_file.name}')

    try:
        tmp_dir.rmdir()
    except OSError:
        pass


def main():
    parser = argparse.ArgumentParser(
        description='Download CMIP6 projections for Dixon Glacier')
    parser.add_argument('--gcms', nargs='+', default=DEFAULT_GCMS)
    parser.add_argument('--scenarios', nargs='+', default=DEFAULT_SCENARIOS)
    parser.add_argument('--year-start', type=int, default=2025)
    parser.add_argument('--year-end', type=int, default=2100)
    parser.add_argument('--parallel', type=int, default=4,
                        help='Batch size for parallel downloads (default: 4)')
    args = parser.parse_args()

    CMIP6_DIR.mkdir(parents=True, exist_ok=True)

    n_combos = len(args.gcms) * len(args.scenarios)
    n_years = args.year_end - args.year_start + 1

    print('=' * 60)
    print('NEX-GDDP-CMIP6 Download for Dixon Glacier')
    print(f'GCMs: {args.gcms}')
    print(f'SSPs: {args.scenarios}')
    print(f'Period: {args.year_start}-{args.year_end} ({n_years} years)')
    print(f'Combos: {n_combos}, batch size: {args.parallel}')
    print('=' * 60)

    for gcm in args.gcms:
        print(f'\n--- {gcm} ---')
        for scenario in args.scenarios:
            download_gcm_scenario(
                gcm, scenario, args.year_start, args.year_end,
                n_parallel=args.parallel,
            )

    # Summary
    csvs = list(CMIP6_DIR.glob('dixon_*.csv'))
    print(f'\nDone! {len(csvs)} files in {CMIP6_DIR}')
    for f in sorted(csvs):
        n = sum(1 for _ in open(f)) - 1
        print(f'  {f.name}: {n} days ({n/365:.0f} yrs)')


if __name__ == '__main__':
    main()
