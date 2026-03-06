"""
Test DEM loading, grid preparation, and a short model run with synthetic climate data.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd

DEM_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'ifsar_2010', 'dixon_glacier_IFSAR_DTM_5m_full.tif'
)
GLACIER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'geodedic_mb', 'dixon_glacier_outline_rgi7.geojson'
)


def test_grid_preparation():
    from dixon_melt.terrain import prepare_grid

    print("Loading and reprojecting DEM (50m resolution)...")
    grid = prepare_grid(DEM_PATH, GLACIER_PATH, target_res=50.0)

    print(f"  Grid shape: {grid['elevation'].shape}")
    print(f"  Cell size: {grid['cell_size']}m")
    print(f"  Glacier cells: {grid['glacier_mask'].sum()}")

    elev_glacier = grid['elevation'][grid['glacier_mask']]
    print(f"  Glacier elevation range: {elev_glacier.min():.0f} - {elev_glacier.max():.0f} m")
    print(f"  Glacier area (from cells): {grid['glacier_mask'].sum() * grid['cell_size']**2 / 1e6:.1f} km²")

    slope_deg = np.degrees(grid['slope'][grid['glacier_mask']])
    print(f"  Slope range: {slope_deg.min():.1f} - {slope_deg.max():.1f}°, mean: {slope_deg.mean():.1f}°")

    assert grid['glacier_mask'].sum() > 100, "Too few glacier cells"
    return grid


def test_short_model_run(grid):
    from dixon_melt.model import DETIMModel

    model = DETIMModel(grid)
    model.initialize_swe(2000.0)  # 2m winter snow

    # Synthetic 30-day summer climate
    dates = pd.date_range('2023-06-01', periods=30, freq='D')
    climate = pd.DataFrame({
        'date': dates,
        'temperature': np.random.uniform(5, 15, 30),
        'precipitation': np.random.uniform(0, 5, 30),
    })

    print("\nRunning 30-day synthetic simulation...")
    results = model.run(climate)

    print(f"  Total glacier melt (mean): {results['glacier_melt_mm'].sum():.1f} mm")
    print(f"  Total accumulation (mean): {results['glacier_accum_mm'].sum():.1f} mm")
    print(f"  Final glacier-wide balance: {results['glacier_wide_balance_mwe'].iloc[-1]:.3f} m w.e.")

    stakes = model.get_balance_at_stakes()
    for site, bal in stakes.items():
        print(f"  {site} balance: {bal:.3f} m w.e.")

    assert results['glacier_melt_mm'].sum() > 0, "No melt occurred"
    print("  PASSED: short model run")


if __name__ == '__main__':
    print("Testing grid preparation and model run...\n")
    grid = test_grid_preparation()
    test_short_model_run(grid)
    print("\nAll grid tests passed!")
