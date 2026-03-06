"""
Numba-compiled full simulation kernel for DETIM.

Runs the entire time series in a single JIT-compiled function,
eliminating Python loop overhead. Targets ~1000+ runs/second
for calibration with differential_evolution.
"""
import numpy as np
from numba import njit, prange


@njit
def _rain_snow_fraction(T, T0):
    """Snow fraction given temperature and threshold."""
    if T <= T0 - 1.0:
        return 1.0
    elif T >= T0 + 1.0:
        return 0.0
    else:
        return 0.5 * (T0 + 1.0 - T)


@njit(parallel=True)
def run_simulation(
    # Time series (1D arrays, length n_days)
    T_station,       # daily mean temperature at station (°C)
    P_station,       # daily precipitation at station (mm)
    doy_array,       # day of year for each time step
    # Grids (2D arrays, nrows × ncols)
    elevation,       # m
    ipot_lookup,     # 3D: (365, nrows, ncols) — precomputed I_pot per DOY
    glacier_mask,    # bool
    firn_mask,       # bool
    # Scalar parameters
    station_elev,
    MF,
    r_snow,
    r_ice,
    lapse_rate,
    precip_grad,
    precip_corr,
    T0,
    nodata,
    # Initial state
    swe_init,        # 2D array
    # Stake extraction elevations
    stake_elevs,     # 1D array of stake elevations
    stake_tol,       # elevation tolerance for stake extraction
):
    """Run full DETIM simulation.

    Returns
    -------
    cum_melt : 2D array (mm) — cumulative melt over entire period
    cum_accum : 2D array (mm) — cumulative accumulation
    daily_glacier_melt : 1D array (mm) — glacier-mean daily melt
    stake_balances : 1D array — net balance at each stake elevation (m w.e.)
    glacier_wide_balance : float — glacier-wide specific balance (m w.e.)
    """
    n_days = len(T_station)
    nrows, ncols = elevation.shape
    n_stakes = len(stake_elevs)

    # State
    swe = swe_init.copy()
    cum_melt = np.zeros((nrows, ncols), dtype=np.float64)
    cum_accum = np.zeros((nrows, ncols), dtype=np.float64)
    surface_type = np.zeros((nrows, ncols), dtype=np.int32)

    # Initialize surface type
    for i in range(nrows):
        for j in range(ncols):
            if not glacier_mask[i, j]:
                surface_type[i, j] = 0
            elif swe[i, j] > 0:
                surface_type[i, j] = 1  # snow
            elif firn_mask[i, j]:
                surface_type[i, j] = 2  # firn
            else:
                surface_type[i, j] = 3  # ice

    # Output time series
    daily_glacier_melt = np.zeros(n_days, dtype=np.float64)

    # Count glacier cells for averaging
    n_glacier = 0
    for i in range(nrows):
        for j in range(ncols):
            if glacier_mask[i, j]:
                n_glacier += 1

    if n_glacier == 0:
        stake_balances = np.zeros(n_stakes, dtype=np.float64)
        return cum_melt, cum_accum, daily_glacier_melt, stake_balances, 0.0

    # ── Main time loop ──────────────────────────────────────────────
    for t in range(n_days):
        T_s = T_station[t]
        P_s = P_station[t]
        doy = doy_array[t]
        doy_idx = doy - 1  # 0-indexed for ipot_lookup

        if doy_idx < 0:
            doy_idx = 0
        if doy_idx >= 365:
            doy_idx = 364

        day_melt_sum = 0.0

        for i in prange(nrows):
            for j in range(ncols):
                if not glacier_mask[i, j] or elevation[i, j] == nodata:
                    continue

                # Temperature at this cell
                dz = elevation[i, j] - station_elev
                T_cell = T_s + lapse_rate * dz

                # Precipitation at this cell
                P_cell = P_s * precip_corr * (1.0 + precip_grad * dz)
                if P_cell < 0:
                    P_cell = 0.0

                # Rain/snow partition
                snow_frac = _rain_snow_fraction(T_cell, T0)
                snowfall = P_cell * snow_frac

                # Accumulation
                swe[i, j] += snowfall
                cum_accum[i, j] += snowfall

                # Melt (only if T > 0)
                melt = 0.0
                if T_cell > 0:
                    I = ipot_lookup[doy_idx, i, j]
                    st = surface_type[i, j]
                    if st == 1 or st == 2:  # snow or firn
                        r = r_snow
                    else:  # ice
                        r = r_ice
                    melt = (MF + r * I) * T_cell
                    if melt < 0:
                        melt = 0.0

                # Apply melt to snowpack
                if melt > 0:
                    if swe[i, j] > 0:
                        snow_melted = min(swe[i, j], melt)
                        swe[i, j] -= snow_melted
                    cum_melt[i, j] += melt
                    day_melt_sum += melt

                # Update surface type
                if swe[i, j] > 0:
                    surface_type[i, j] = 1
                elif firn_mask[i, j]:
                    surface_type[i, j] = 2
                else:
                    surface_type[i, j] = 3

        daily_glacier_melt[t] = day_melt_sum / n_glacier

    # ── Extract stake balances ──────────────────────────────────────
    stake_balances = np.zeros(n_stakes, dtype=np.float64)
    stake_counts = np.zeros(n_stakes, dtype=np.float64)

    for i in range(nrows):
        for j in range(ncols):
            if not glacier_mask[i, j]:
                continue
            elev = elevation[i, j]
            net = (cum_accum[i, j] - cum_melt[i, j]) / 1000.0  # mm → m w.e.

            for s in range(n_stakes):
                if abs(elev - stake_elevs[s]) <= stake_tol:
                    stake_balances[s] += net
                    stake_counts[s] += 1.0

    for s in range(n_stakes):
        if stake_counts[s] > 0:
            stake_balances[s] /= stake_counts[s]
        else:
            stake_balances[s] = np.nan

    # Glacier-wide balance
    gw_sum = 0.0
    for i in range(nrows):
        for j in range(ncols):
            if glacier_mask[i, j]:
                gw_sum += (cum_accum[i, j] - cum_melt[i, j]) / 1000.0
    glacier_wide_balance = gw_sum / n_glacier

    return cum_melt, cum_accum, daily_glacier_melt, stake_balances, glacier_wide_balance


@njit
def _make_swe_init_jit(elevation, glacier_mask, station_elev, winter_swe_mm, precip_grad, snow_redist):
    nrows, ncols = elevation.shape
    swe = np.zeros((nrows, ncols), dtype=np.float64)
    base = winter_swe_mm * snow_redist
    for i in range(nrows):
        for j in range(ncols):
            if glacier_mask[i, j]:
                dz = elevation[i, j] - station_elev
                val = base * (1.0 + precip_grad * dz)
                if val < 0:
                    val = 0.0
                swe[i, j] = val
    return swe


class FastDETIM:
    """Fast wrapper around the numba-compiled simulation kernel.

    Designed for calibration: precomputes everything that doesn't depend
    on model parameters, then each run() call only executes the JIT kernel.
    """

    def __init__(self, grid, ipot_table, station_elev):
        """
        Parameters
        ----------
        grid : dict from terrain.prepare_grid()
        ipot_table : dict DOY → 2D array, from precompute_ipot()
        station_elev : float, climate station elevation (m)
        """
        self.elevation = grid['elevation'].astype(np.float64)
        self.glacier_mask = grid['glacier_mask']
        self.nrows, self.ncols = self.elevation.shape
        self.station_elev = station_elev
        self.cell_size = grid['cell_size']

        # Firn mask
        glacier_elevs = self.elevation[self.glacier_mask]
        self.firn_elev = np.median(glacier_elevs) if len(glacier_elevs) > 0 else 1100.0
        self.firn_mask = self.glacier_mask & (self.elevation >= self.firn_elev)

        # Pack ipot into 3D array: (365, nrows, ncols)
        self.ipot_3d = np.zeros((365, self.nrows, self.ncols), dtype=np.float64)
        for doy in range(1, 366):
            if doy in ipot_table:
                self.ipot_3d[doy - 1] = ipot_table[doy]

        # Stake elevations
        self.stake_names = ['ABL', 'ELA', 'ACC']
        self.stake_elevs = np.array([804.0, 1078.0, 1293.0], dtype=np.float64)
        self.stake_tol = 50.0  # m

        # NODATA
        self.nodata = -9999.0

    def _make_swe_init(self, winter_swe_mm, precip_grad, precip_corr, snow_redist):
        """Create initial SWE grid scaled by elevation."""
        return _make_swe_init_jit(
            self.elevation, self.glacier_mask, self.station_elev,
            winter_swe_mm, precip_grad, snow_redist
        )

    def run(self, T_station, P_station, doy_array, params, winter_swe_mm):
        """Run simulation with given parameters.

        Parameters
        ----------
        T_station : 1D array, daily temperature (°C)
        P_station : 1D array, daily precipitation (mm)
        doy_array : 1D int array, day of year
        params : dict with MF, r_snow, r_ice, lapse_rate, precip_grad, precip_corr, T0, snow_redist
        winter_swe_mm : float, reference winter SWE at station elevation

        Returns
        -------
        dict with keys: cum_melt, cum_accum, daily_melt, stake_balances, glacier_wide_balance
        """
        swe_init = self._make_swe_init(
            winter_swe_mm,
            params['precip_grad'],
            params['precip_corr'],
            params.get('snow_redist', 1.0),
        )

        cum_melt, cum_accum, daily_melt, stake_bal, gw_bal = run_simulation(
            T_station.astype(np.float64),
            P_station.astype(np.float64),
            doy_array.astype(np.int64),
            self.elevation,
            self.ipot_3d,
            self.glacier_mask,
            self.firn_mask,
            self.station_elev,
            params['MF'],
            params['r_snow'],
            params['r_ice'],
            params['lapse_rate'],
            params['precip_grad'],
            params['precip_corr'],
            params['T0'],
            self.nodata,
            swe_init,
            self.stake_elevs,
            self.stake_tol,
        )

        stakes = {}
        for i, name in enumerate(self.stake_names):
            stakes[name] = stake_bal[i]

        return {
            'cum_melt': cum_melt,
            'cum_accum': cum_accum,
            'daily_melt': daily_melt,
            'stake_balances': stakes,
            'glacier_wide_balance': gw_bal,
        }
