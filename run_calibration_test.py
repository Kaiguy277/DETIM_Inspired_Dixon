"""
Short calibration test: 2023-2024 water year against stake observations.
Uses a small population and few iterations just to verify the pipeline works end-to-end.
"""
import numpy as np
import pandas as pd
from pathlib import Path

# Paths
PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
DEM_PATH = PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif'
GLACIER_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
CLIMATE_PATH = PROJECT / 'data' / 'climate' / 'dixon_model_climate.csv'
STAKE_PATH = PROJECT / 'stake_observations_dixon.csv'

# ── 1. Prepare grid ─────────────────────────────────────────────────
print("=" * 60)
print("STEP 1: Preparing grid (100m resolution for speed)")
print("=" * 60)

from dixon_melt.terrain import prepare_grid
grid = prepare_grid(str(DEM_PATH), str(GLACIER_PATH), target_res=100.0)

print(f"  Grid shape: {grid['elevation'].shape}")
print(f"  Glacier cells: {grid['glacier_mask'].sum()}")
print(f"  Glacier area: {grid['glacier_mask'].sum() * grid['cell_size']**2 / 1e6:.1f} km²")

# ── 2. Load climate data ────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2: Loading climate data")
print("=" * 60)

climate = pd.read_csv(CLIMATE_PATH, index_col='date', parse_dates=True)

# Use water year 2024: Oct 1 2023 → Sep 20 2024 (matches stake obs)
wy_start = '2023-10-01'
wy_end = '2024-09-20'
wy = climate.loc[wy_start:wy_end].copy()

t_valid = wy['temperature'].notna().sum()
print(f"  WY2024 period: {wy_start} to {wy_end}")
print(f"  Days: {len(wy)}, with temperature: {t_valid} ({100*t_valid/len(wy):.0f}%)")
print(f"  Mean T: {wy['temperature'].mean():.1f}°C")
print(f"  Total P: {wy['precipitation'].sum():.0f} mm")

# Fill remaining NaN temps
wy['temperature'] = wy['temperature'].ffill().fillna(0)
wy['precipitation'] = wy['precipitation'].fillna(0)

# ── 3. Load stake observations ──────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3: Stake observations for WY2024")
print("=" * 60)

stakes = pd.read_csv(STAKE_PATH, parse_dates=['date_start', 'date_end'])
wy24_annual = stakes[(stakes['period_type'] == 'annual') & (stakes['year'] == 2024)]
wy24_winter = stakes[(stakes['period_type'] == 'winter') & (stakes['year'] == 2024)]

print("  Annual balance targets:")
for _, row in wy24_annual.iterrows():
    print(f"    {row['site_id']} ({row['elevation_m']}m): {row['mb_obs_mwe']:.2f} m w.e.")

# ── 4. Build model and run calibration ──────────────────────────────
print("\n" + "=" * 60)
print("STEP 4: Running calibration (quick test)")
print("=" * 60)

from dixon_melt.model import DETIMModel
from dixon_melt import config
from scipy.optimize import differential_evolution

model = DETIMModel(grid)

# Stake targets for WY2024 annual
targets = {}
for _, row in wy24_annual.iterrows():
    targets[row['site_id']] = {
        'elev': row['elevation_m'],
        'obs': row['mb_obs_mwe'],
        'unc': row['mb_obs_uncertainty_mwe'],
    }

# Calibrate 6 parameters: melt (3) + climate (3)
bounds = [
    (1.0, 12.0),        # MF (mm/d/K)
    (0.05e-3, 1.5e-3),  # r_snow
    (0.1e-3, 3.0e-3),   # r_ice
    (-8.5e-3, -4.0e-3), # lapse_rate (°C/m)
    (0.0005, 0.005),    # precip_grad (fractional per m)
    (1.0, 3.0),         # precip_corr (gauge correction / orographic factor)
]
param_names = ['MF', 'r_snow', 'r_ice', 'lapse_rate', 'precip_grad', 'precip_corr']

print(f"  Calibrating: {param_names}")
print(f"  Targets: {list(targets.keys())}")

call_count = [0]

def objective(x):
    MF, r_snow, r_ice, lapse_rate, precip_grad, precip_corr = x
    call_count[0] += 1

    params = dict(config.DEFAULT_PARAMS)
    params['MF'] = MF
    params['r_snow'] = r_snow
    params['r_ice'] = r_ice
    params['lapse_rate'] = lapse_rate
    params['precip_grad'] = precip_grad
    params['precip_corr'] = precip_corr

    model.set_params(params)
    model.reset()

    # Initialize SWE using the observed winter balance at ELA as reference
    # Scale by precip_corr and precip_grad to be consistent
    winter_swe_mm = 2600.0  # ELA winter obs in mm
    model.initialize_swe(winter_swe_mm)

    try:
        results = model.run(wy)
    except Exception:
        return 1e6

    modeled = model.get_balance_at_stakes()

    # Weighted RMSE against stake observations
    errors = []
    for site, tgt in targets.items():
        if site in modeled and not np.isnan(modeled[site]):
            err = (modeled[site] - tgt['obs']) / tgt['unc']
            errors.append(err ** 2)

    if not errors:
        return 1e6

    cost = np.sqrt(np.mean(errors))

    if call_count[0] % 20 == 0:
        print(f"  eval {call_count[0]:4d}: MF={MF:.2f} lr={lapse_rate*1e3:.2f} pg={precip_grad:.4f} pc={precip_corr:.2f} → cost={cost:.2f}")
        for site in ['ABL', 'ELA', 'ACC']:
            if site in modeled:
                print(f"         {site}: mod={modeled[site]:+.2f} obs={targets[site]['obs']:+.2f}")

    return cost

print("\nRunning differential_evolution (quick test: 15 iter, pop 10)...")
result = differential_evolution(
    objective,
    bounds=bounds,
    maxiter=15,
    popsize=10,
    seed=42,
    tol=0.01,
    disp=True,
)

best = {name: val for name, val in zip(param_names, result.x)}
print(f"\n{'=' * 60}")
print(f"CALIBRATION RESULT (test run)")
print(f"{'=' * 60}")
print(f"  Converged: {result.success}")
print(f"  Cost: {result.fun:.4f}")
print(f"  Evaluations: {call_count[0]}")
print(f"  Best parameters:")
for k, v in best.items():
    if 'r_' in k:
        print(f"    {k}: {v:.6f}")
    else:
        print(f"    {k}: {v:.4f}")

# ── 5. Final run with best parameters ───────────────────────────────
print(f"\n{'=' * 60}")
print("STEP 5: Final run with best parameters")
print(f"{'=' * 60}")

model.set_params(best)
model.reset()
model.initialize_swe(2600.0)
results = model.run(wy)

modeled = model.get_balance_at_stakes()
gw_balance = results['glacier_wide_balance_mwe'].iloc[-1]

print(f"\n  Glacier-wide balance: {gw_balance:.3f} m w.e.")
print(f"  Point balances:")
for site, tgt in targets.items():
    mod = modeled.get(site, np.nan)
    print(f"    {site} ({tgt['elev']}m): modeled={mod:+.2f}, observed={tgt['obs']:+.2f}, diff={mod - tgt['obs']:+.2f}")

# Find peak melt day
peak_idx = results['glacier_melt_mm'].idxmax()
peak_row = results.loc[peak_idx]
print(f"\n  Daily melt peak: {peak_row['glacier_melt_mm']:.1f} mm on {peak_row['date'].strftime('%Y-%m-%d')}")
print(f"  Total melt season melt: {results['glacier_melt_mm'].sum():.0f} mm")

# Save results
results.to_csv(PROJECT / 'data' / 'test_calibration_results.csv', index=False)
print(f"\n  Results saved to data/test_calibration_results.csv")
print("\nDone!")
