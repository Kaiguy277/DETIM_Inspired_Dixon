"""
Smoke tests for DETIM core modules.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np


def test_solar_geometry():
    from dixon_melt.solar import (
        declination, hour_angle, cos_zenith,
        earth_sun_distance_factor, potential_direct_radiation_horizontal,
        compute_ipot_grid
    )

    # Summer solstice, solar noon at 60°N
    doy = 172  # ~June 21
    decl = declination(doy)
    decl_deg = np.degrees(decl)
    print(f"  DOY {doy} declination: {decl_deg:.1f}°")
    assert 20 < decl_deg < 25, f"Summer declination should be ~+23°, got {decl_deg}"

    # Hour angle at solar noon = 0
    h = hour_angle(12.0)
    assert abs(h) < 0.01, f"Noon hour angle should be 0, got {h}"

    # Zenith at noon, 60°N, summer solstice: Z ≈ 60 - 23.4 = 36.6°
    lat_rad = np.radians(60.0)
    cz = cos_zenith(lat_rad, decl, h)
    zenith_deg = np.degrees(np.arccos(cz))
    print(f"  Noon zenith at 60°N: {zenith_deg:.1f}°")
    assert 35 < zenith_deg < 38, f"Expected ~36.6°, got {zenith_deg}"

    # Earth-sun distance factor ~1.0
    r2 = earth_sun_distance_factor(doy)
    assert 0.96 < r2 < 1.04, f"Distance factor off: {r2}"

    # Potential radiation should be > 0 at noon
    I = potential_direct_radiation_horizontal(doy, 12.0, 60.0, 1000.0)
    print(f"  I_pot(noon, 1000m): {I:.1f} W/m²")
    assert 500 < I < 1100, f"Radiation off: {I}"

    # Potential radiation at night should be 0
    I_night = potential_direct_radiation_horizontal(doy, 2.0, 60.0, 1000.0)
    # At 60°N in summer, sun doesn't set fully... but at 2am it might be very low
    print(f"  I_pot(2am, 1000m): {I_night:.1f} W/m²")

    # Grid computation
    elev = np.full((5, 5), 1000.0)
    slope = np.full((5, 5), np.radians(15.0))
    aspect = np.full((5, 5), np.radians(180.0))  # south-facing
    ipot = compute_ipot_grid(doy, 12.0, 60.0, elev, slope, aspect)
    print(f"  Grid I_pot range: {ipot.min():.1f} - {ipot.max():.1f} W/m²")
    assert ipot.mean() > 0

    print("  PASSED: solar geometry")


def test_temperature():
    from dixon_melt.temperature import distribute_temperature

    elev = np.array([[500.0, 1000.0], [1500.0, -9999.0]])
    T = distribute_temperature(10.0, 1000.0, elev, -0.006, -9999.0)

    assert abs(T[0, 0] - 13.0) < 0.01  # 500m: 10 + (-0.006)*(500-1000) = 13
    assert abs(T[0, 1] - 10.0) < 0.01  # 1000m: same as station
    assert abs(T[1, 0] - 7.0) < 0.01   # 1500m: 10 + (-0.006)*(1500-1000) = 7
    assert T[1, 1] == -9999.0           # nodata

    print("  PASSED: temperature distribution")


def test_precipitation():
    from dixon_melt.precipitation import distribute_precipitation
    from dixon_melt.temperature import distribute_temperature

    elev = np.array([[500.0, 1000.0], [1500.0, 2000.0]])
    T = distribute_temperature(5.0, 1000.0, elev, -0.006, -9999.0)
    snow, rain = distribute_precipitation(10.0, T, elev, 1000.0, 0.0005, 1.0, 1.5, -9999.0)

    # At 500m, T=8°C → all rain (precip scaled: 10*(1+0.0005*(-500))=7.5)
    assert snow[0, 0] < 0.1
    assert rain[0, 0] > 7.0

    # At 2000m, T=-1°C → all snow (precip scaled: 10*(1+0.0005*(1000))=15)
    assert snow[1, 1] > 14.0
    assert rain[1, 1] < 0.1

    print("  PASSED: precipitation distribution")


def test_melt():
    from dixon_melt.melt import compute_melt

    T = np.array([[5.0, -2.0], [3.0, 0.0]])
    ipot = np.array([[300.0, 300.0], [200.0, 200.0]])
    stype = np.array([[1, 1], [3, 3]], dtype=np.int32)

    MF = 4.0
    r_snow = 0.3e-3
    r_ice = 0.6e-3

    melt = compute_melt(T, ipot, stype, MF, r_snow, r_ice, -9999.0, 1.0)

    # Cell (0,0): snow, T=5, I=300 → M = (4 + 0.0003*300)*5 = (4+0.09)*5 = 20.45
    expected_00 = (MF + r_snow * 300) * 5.0
    assert abs(melt[0, 0] - expected_00) < 0.01, f"Expected {expected_00}, got {melt[0, 0]}"

    # Cell (0,1): T=-2 → no melt
    assert melt[0, 1] == 0.0

    # Cell (1,0): ice, T=3, I=200 → M = (4 + 0.0006*200)*3 = (4+0.12)*3 = 12.36
    expected_10 = (MF + r_ice * 200) * 3.0
    assert abs(melt[1, 0] - expected_10) < 0.01

    # Cell (1,1): T=0 → no melt
    assert melt[1, 1] == 0.0

    print("  PASSED: melt computation")


if __name__ == '__main__':
    print("Running DETIM core tests...\n")
    test_solar_geometry()
    test_temperature()
    test_precipitation()
    test_melt()
    print("\nAll tests passed!")
