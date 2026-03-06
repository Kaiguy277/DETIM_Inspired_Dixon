"""
Mass balance integration and comparison with observations.
"""
import numpy as np
import pandas as pd


def compute_glacier_wide_balance(cumulative_melt, cumulative_accum, glacier_mask):
    """Compute glacier-wide specific mass balance (m w.e.).

    Parameters
    ----------
    cumulative_melt : 2D array (mm w.e., positive = mass loss)
    cumulative_accum : 2D array (mm w.e., positive = mass gain)
    glacier_mask : 2D bool array

    Returns
    -------
    float : specific mass balance in m w.e.
    """
    glacier_cells = glacier_mask.sum()
    if glacier_cells == 0:
        return 0.0

    net = cumulative_accum[glacier_mask] - cumulative_melt[glacier_mask]
    return net.mean() / 1000.0  # mm → m w.e.


def extract_point_balance(cumulative_melt, cumulative_accum, elevation,
                          target_elev, glacier_mask, elev_tolerance=25.0):
    """Extract mass balance at a point defined by elevation.

    Averages cells within elev_tolerance of target_elev.
    Returns m w.e.
    """
    mask = (glacier_mask
            & (np.abs(elevation - target_elev) <= elev_tolerance))
    if mask.sum() == 0:
        # Widen tolerance
        mask = (glacier_mask
                & (np.abs(elevation - target_elev) <= elev_tolerance * 3))
    if mask.sum() == 0:
        return np.nan

    net = cumulative_accum[mask] - cumulative_melt[mask]
    return net.mean() / 1000.0  # mm → m w.e.


def load_stake_observations(csv_path):
    """Load stake observation CSV.

    Returns DataFrame with columns: site_id, period_type, year,
    date_start, date_end, mb_obs_mwe, elevation_m, etc.
    """
    df = pd.read_csv(csv_path, parse_dates=['date_start', 'date_end'])
    return df


def load_geodetic_mb(csv_path):
    """Load Hugonnet geodetic mass balance CSV."""
    df = pd.read_csv(csv_path)
    return df
