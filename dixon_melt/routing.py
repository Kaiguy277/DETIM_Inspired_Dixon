"""
Meltwater routing using parallel linear reservoirs.

Converts distributed glacier melt + rain into outlet discharge.
Three reservoirs represent fast (supraglacial/englacial),
slow (subglacial), and groundwater pathways.

Reference: Hock & Jansson (2005), Jansson et al. (2003).
"""
import numpy as np
from numba import njit


@njit
def route_linear_reservoirs(daily_runoff_mm, glacier_area_m2,
                            k_fast, k_slow, k_gw,
                            f_fast, f_slow):
    """Route glacier runoff through three parallel linear reservoirs.

    Parameters
    ----------
    daily_runoff_mm : 1D array, glacier-mean daily runoff (melt + rain) in mm
    glacier_area_m2 : float, current glacier area (m2)
    k_fast : float, fast reservoir recession coefficient (d-1)
    k_slow : float, slow reservoir recession coefficient (d-1)
    k_gw : float, groundwater reservoir recession coefficient (d-1)
    f_fast : float, fraction of runoff entering fast reservoir
    f_slow : float, fraction entering slow reservoir
        (remainder goes to groundwater: f_gw = 1 - f_fast - f_slow)

    Returns
    -------
    Q_total : 1D array, daily discharge (m3/s)
    Q_fast : 1D array, fast component
    Q_slow : 1D array, slow component
    Q_gw : 1D array, groundwater component
    """
    n = len(daily_runoff_mm)
    f_gw = 1.0 - f_fast - f_slow
    if f_gw < 0:
        f_gw = 0.0

    # Convert mm/day over glacier area to m3/day
    # 1 mm = 0.001 m, so mm * area_m2 * 0.001 = m3
    mm_to_m3 = glacier_area_m2 * 0.001

    # Reservoir storages (m3)
    S_fast = 0.0
    S_slow = 0.0
    S_gw = 0.0

    Q_fast = np.zeros(n, dtype=np.float64)
    Q_slow = np.zeros(n, dtype=np.float64)
    Q_gw = np.zeros(n, dtype=np.float64)
    Q_total = np.zeros(n, dtype=np.float64)

    for t in range(n):
        # Input volume (m3)
        input_m3 = daily_runoff_mm[t] * mm_to_m3

        # Add to reservoirs
        S_fast += f_fast * input_m3
        S_slow += f_slow * input_m3
        S_gw += f_gw * input_m3

        # Outflow = k * S (m3/day)
        out_fast = k_fast * S_fast
        out_slow = k_slow * S_slow
        out_gw = k_gw * S_gw

        # Update storages
        S_fast -= out_fast
        S_slow -= out_slow
        S_gw -= out_gw

        # Convert m3/day to m3/s
        Q_fast[t] = out_fast / 86400.0
        Q_slow[t] = out_slow / 86400.0
        Q_gw[t] = out_gw / 86400.0
        Q_total[t] = Q_fast[t] + Q_slow[t] + Q_gw[t]

    return Q_total, Q_fast, Q_slow, Q_gw


def compute_discharge(model_result, glacier_area_m2, routing_params):
    """Convenience wrapper for routing from a model run result.

    Parameters
    ----------
    model_result : dict from FastDETIM.run()
    glacier_area_m2 : float
    routing_params : dict with k_fast, k_slow, k_gw, f_fast, f_slow

    Returns
    -------
    dict with Q_total, Q_fast, Q_slow, Q_gw (all in m3/s)
    """
    Q_total, Q_fast, Q_slow, Q_gw = route_linear_reservoirs(
        model_result['daily_runoff'],
        glacier_area_m2,
        routing_params['k_fast'],
        routing_params['k_slow'],
        routing_params['k_gw'],
        routing_params['f_fast'],
        routing_params['f_slow'],
    )
    return {
        'Q_total': Q_total,
        'Q_fast': Q_fast,
        'Q_slow': Q_slow,
        'Q_gw': Q_gw,
    }
