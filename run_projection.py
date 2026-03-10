"""
Future projection runner for Dixon Glacier.

Runs DETIM forward under climate scenarios with evolving glacier geometry
(delta-h parameterization, Huss et al. 2010). Tracks mass balance, area,
volume, discharge, and identifies "peak water" timing.

Ice thickness is initialized from Farinotti et al. (2019) consensus data
if available, otherwise estimated via Bahr et al. (1997) V-A scaling.

Usage:
    python run_projection.py [--scenario historical|warming_low|warming_high]
                             [--end-year 2100]
                             [--params best_params_v10.json]
                             [--thickness path/to/farinotti.tif]

Requires calibrated parameters from calibration run.
Future climate forcing: placeholder using historical perturbation until
UAF SNAP data is integrated.
"""
import numpy as np
import pandas as pd
from pathlib import Path
import json
import time

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
DEM_PATH = PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif'
GLACIER_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
NUKA_PATH = PROJECT / 'data' / 'climate' / 'nuka_snotel_full.csv'
OUTPUT_DIR = PROJECT / 'projection_output'


def load_params(path):
    with open(path) as f:
        return json.load(f)


def make_future_climate(historical_climate, scenario, target_year, base_period=(2000, 2020)):
    """Generate synthetic future climate by perturbing historical record.

    This is a PLACEHOLDER until UAF SNAP downscaled projections are integrated.
    Uses simple delta method: shift temperatures, scale precipitation.

    Parameters
    ----------
    historical_climate : DataFrame with temperature, precipitation
    scenario : str, one of 'historical', 'warming_low', 'warming_high'
    target_year : int, the future year being simulated
    base_period : tuple, reference period for perturbation

    Returns
    -------
    DataFrame with perturbed climate for one water year
    """
    # Sample a random historical water year from base period
    rng = np.random.RandomState(target_year)
    available_years = list(range(base_period[0] + 1, base_period[1] + 1))
    source_year = rng.choice(available_years)

    start = f'{source_year - 1}-10-01'
    end = f'{source_year}-09-30'
    wy = historical_climate.loc[start:end].copy()

    if len(wy) < 300:
        # Try another year
        for fallback in available_years:
            start = f'{fallback - 1}-10-01'
            end = f'{fallback}-09-30'
            wy = historical_climate.loc[start:end].copy()
            if len(wy) >= 300:
                break

    # Apply scenario perturbations
    years_from_now = target_year - 2025

    if scenario == 'historical':
        delta_T = 0.0
        precip_scale = 1.0
    elif scenario == 'warming_low':
        # SSP2-4.5 analog: ~0.03 C/yr warming, slight precip increase
        delta_T = 0.03 * years_from_now
        precip_scale = 1.0 + 0.003 * years_from_now
    elif scenario == 'warming_high':
        # SSP5-8.5 analog: ~0.06 C/yr warming, precip increase
        delta_T = 0.06 * years_from_now
        precip_scale = 1.0 + 0.005 * years_from_now
    else:
        delta_T = 0.0
        precip_scale = 1.0

    wy['temperature'] = wy['temperature'] + delta_T
    wy['precipitation'] = wy['precipitation'] * precip_scale

    return wy


def run_projection(params_path, scenario='warming_low', end_year=2100,
                   grid_res=100.0, farinotti_path=None):
    """Run full glacier projection to end_year.

    Returns projection results dict.
    """
    t_start = time.time()
    print("=" * 70)
    print(f"DIXON GLACIER PROJECTION — {scenario}")
    print(f"Period: 2025 to {end_year}")
    print("=" * 70)

    params = load_params(params_path)
    print(f"  Parameters from: {params_path}")

    # Load historical climate (raw Nuka)
    from run_calibration_full import load_nuka_raw
    climate = load_nuka_raw()
    climate['temperature'] = climate['temperature'].ffill().fillna(0)
    climate['precipitation'] = climate['precipitation'].fillna(0)

    # Prepare grid
    from dixon_melt.terrain import prepare_grid
    grid = prepare_grid(str(DEM_PATH), str(GLACIER_PATH), target_res=grid_res)

    from dixon_melt.model import precompute_ipot
    ipot_table = precompute_ipot(grid, doy_range=range(1, 366), dt_hours=3.0)

    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config
    from dixon_melt.glacier_dynamics import (
        initialize_ice_thickness, compute_bedrock, apply_deltah, va_check,
    )

    fmodel = FastDETIM(
        grid, ipot_table,
        transfer_alpha=config.TRANSFER_ALPHA,
        transfer_beta=config.TRANSFER_BETA,
        ref_elev=config.DIXON_AWS_ELEV,
        stake_names=config.STAKE_NAMES,
        stake_elevs=config.STAKE_ELEVS,
    )

    # ── Initialize ice thickness & bedrock ────────────────────────────
    ice_thickness, thickness_source = initialize_ice_thickness(
        grid, farinotti_path=farinotti_path)
    bedrock = compute_bedrock(grid['elevation'], ice_thickness)
    cell_size = grid['cell_size']

    n_init = int(grid['glacier_mask'].sum())
    area_init = n_init * cell_size**2 / 1e6
    mean_thick = ice_thickness[grid['glacier_mask']].mean()
    vol_init = ice_thickness[grid['glacier_mask']].sum() * cell_size**2 / 1e9
    va_init = va_check(area_init, ice_thickness, grid['glacier_mask'], cell_size)

    print(f"\n  Ice thickness source: {thickness_source}")
    print(f"  Initial area: {area_init:.1f} km2")
    print(f"  Initial volume: {vol_init:.3f} km3 "
          f"(V-A: {va_init['va_volume_km3']:.3f} km3, "
          f"ratio: {va_init['ratio']:.2f})")
    print(f"  Mean thickness: {mean_thick:.0f} m")
    print(f"  Bedrock range: {bedrock[grid['glacier_mask']].min():.0f}"
          f"–{bedrock[grid['glacier_mask']].max():.0f} m\n")

    # Projection state
    current_elev = grid['elevation'].copy()
    current_mask = grid['glacier_mask'].copy()

    results = {
        'year': [],
        'glacier_wide_balance': [],
        'area_km2': [],
        'volume_km3': [],
        'mean_thickness_m': [],
        'cum_balance': [],
        'peak_daily_melt_mm': [],
        'peak_daily_runoff_mm': [],
        'total_annual_runoff_mm': [],
        'mean_summer_T_nuka': [],
        'elev_min': [],
        'elev_max': [],
        'size_class': [],
        'va_ratio': [],
        'cells_removed': [],
    }

    cum_balance = 0.0

    for wy_year in range(2026, end_year + 1):
        n_glacier = int(current_mask.sum())
        if n_glacier == 0:
            print(f"\n  WY{wy_year}: Glacier has disappeared!")
            break

        area_km2 = n_glacier * cell_size**2 / 1e6
        glacier_elevs = current_elev[current_mask]
        glacier_thick = ice_thickness[current_mask]
        vol_km3 = glacier_thick.sum() * cell_size**2 / 1e9

        # Generate climate for this year
        wy_climate = make_future_climate(climate, scenario, wy_year)
        if len(wy_climate) < 300:
            print(f"  WY{wy_year}: insufficient climate data, skipping")
            continue

        T = wy_climate['temperature'].values.astype(np.float64)
        P = wy_climate['precipitation'].values.astype(np.float64)
        doy = np.array([d.timetuple().tm_yday for d in wy_climate.index], dtype=np.int64)

        # Update model geometry
        fmodel.update_geometry(current_elev, current_mask)

        # Run model
        r = fmodel.run(T, P, doy, params, 0.0)

        mb = r['glacier_wide_balance']
        cum_balance += mb

        # Summer temp (Jun-Aug DOYs 152-243)
        summer_mask = (doy >= 152) & (doy <= 243)
        mean_summer_T = T[summer_mask].mean() if summer_mask.any() else np.nan

        # V-A check
        va = va_check(area_km2, ice_thickness, current_mask, cell_size)

        # Determine size class
        from dixon_melt.glacier_dynamics import _select_size_class
        size_class = _select_size_class(area_km2)

        results['year'].append(wy_year)
        results['glacier_wide_balance'].append(mb)
        results['area_km2'].append(area_km2)
        results['volume_km3'].append(vol_km3)
        results['mean_thickness_m'].append(float(glacier_thick.mean()))
        results['cum_balance'].append(cum_balance)
        results['peak_daily_melt_mm'].append(float(r['daily_melt'].max()))
        results['peak_daily_runoff_mm'].append(float(r['daily_runoff'].max()))
        results['total_annual_runoff_mm'].append(float(r['daily_runoff'].sum()))
        results['mean_summer_T_nuka'].append(float(mean_summer_T))
        results['elev_min'].append(float(glacier_elevs.min()))
        results['elev_max'].append(float(glacier_elevs.max()))
        results['size_class'].append(size_class)
        results['va_ratio'].append(va['ratio'])
        results['cells_removed'].append(0)

        if wy_year % 10 == 0 or wy_year == 2026:
            print(f"  WY{wy_year}: MB={mb:+.2f} m w.e., Area={area_km2:.1f} km2, "
                  f"Vol={vol_km3:.3f} km3, H_mean={glacier_thick.mean():.0f} m, "
                  f"Class={size_class}")
            if va['warning']:
                print(f"    WARNING: {va['warning']}")

        # Apply delta-h geometry update (modifies ice_thickness in place)
        current_elev, current_mask, cells_removed = apply_deltah(
            current_elev, current_mask, ice_thickness, bedrock,
            mb, cell_size,
        )
        results['cells_removed'][-1] = cells_removed

    elapsed = time.time() - t_start
    print(f"\n  Projection complete in {elapsed:.0f}s")

    # ── Peak water analysis ─────────────────────────────────────────
    if len(results['year']) > 5:
        runoff = np.array(results['total_annual_runoff_mm'])
        # Smooth with 5-year running mean
        kernel = np.ones(5) / 5
        if len(runoff) >= 5:
            smoothed = np.convolve(runoff, kernel, mode='valid')
            peak_idx = np.argmax(smoothed) + 2  # offset for valid convolution
            peak_year = results['year'][peak_idx]
            peak_runoff = smoothed[peak_idx - 2]
            print(f"\n  PEAK WATER: ~WY{peak_year} "
                  f"({peak_runoff:.0f} mm/yr, 5-yr smoothed)")
        else:
            print(f"\n  Insufficient years for peak water analysis")

    # ── Final state summary ──────────────────────────────────────────
    if len(results['year']) > 0:
        print(f"\n  Final state (WY{results['year'][-1]}):")
        print(f"    Area: {results['area_km2'][-1]:.1f} km2 "
              f"({100 * results['area_km2'][-1] / area_init:.0f}% of initial)")
        print(f"    Volume: {results['volume_km3'][-1]:.3f} km3 "
              f"({100 * results['volume_km3'][-1] / max(vol_init, 1e-9):.0f}% of initial)")
        print(f"    Cumulative balance: {cum_balance:+.1f} m w.e.")

    # Save
    OUTPUT_DIR.mkdir(exist_ok=True)
    df = pd.DataFrame(results)
    outfile = OUTPUT_DIR / f'projection_{scenario}_{end_year}.csv'
    df.to_csv(outfile, index=False)
    print(f"  Results saved to {outfile}")

    return results


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', default='warming_low',
                        choices=['historical', 'warming_low', 'warming_high'])
    parser.add_argument('--end-year', type=int, default=2100)
    parser.add_argument('--params', default='calibration_output/best_params_v10.json')
    parser.add_argument('--thickness', default=None,
                        help='Path to Farinotti et al. (2019) ice thickness GeoTIFF')
    args = parser.parse_args()

    run_projection(args.params, args.scenario, args.end_year,
                   farinotti_path=args.thickness)
