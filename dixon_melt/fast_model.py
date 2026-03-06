"""
Numba-compiled full simulation kernel for DETIM — v2.

Changes from v1:
  - Statistical temperature transfer (Nuka → on-glacier) via monthly
    regression coefficients, then internal lapse rate for elevation (D-007)
  - Elevation-dependent melt factor: MF(z) = MF + MF_grad * (z - z_ref)
  - Input is raw Nuka SNOTEL temperature (at 1230m), NOT pre-adjusted

See research_log/decisions.md D-007 and project_plan.md Phase 1 & 3.
"""
import numpy as np
from numba import njit, prange


@njit
def _doy_to_month(doy):
    """Convert day-of-year (1-366) to month index (0-11)."""
    # Cumulative days at start of each month (non-leap)
    starts = np.array([1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335])
    for m in range(11, -1, -1):
        if doy >= starts[m]:
            return m
    return 0


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
    T_nuka,          # daily mean temperature at Nuka SNOTEL, RAW (C)
    P_nuka,          # daily precipitation at Nuka SNOTEL (mm)
    doy_array,       # day of year for each time step
    # Grids (2D arrays, nrows x ncols)
    elevation,       # m
    ipot_lookup,     # 3D: (365, nrows, ncols)
    glacier_mask,    # bool
    firn_mask,       # bool
    # Temperature transfer coefficients
    transfer_alpha,  # 1D, length 12 (monthly slope)
    transfer_beta,   # 1D, length 12 (monthly intercept)
    ref_elev,        # reference elevation for transfer (804m)
    # Scalar parameters
    MF,
    MF_grad,         # melt factor elevation gradient (mm d-1 K-1 per m)
    r_snow,
    r_ice,
    internal_lapse,  # on-glacier lapse rate (C/m)
    precip_grad,
    precip_corr,
    T0,
    nodata,
    # Initial state
    swe_init,        # 2D array
    # Stake extraction elevations
    stake_elevs,     # 1D array
    stake_tol,       # elevation tolerance
):
    """Run full DETIM simulation with statistical temperature transfer.

    Returns
    -------
    cum_melt : 2D (mm)
    cum_accum : 2D (mm)
    daily_glacier_melt : 1D (mm) glacier-mean daily melt
    daily_glacier_runoff : 1D (mm) glacier-mean daily runoff (melt + rain)
    stake_balances : 1D, net balance at each stake elevation (m w.e.)
    glacier_wide_balance : float, glacier-wide specific balance (m w.e.)
    """
    n_days = len(T_nuka)
    nrows, ncols = elevation.shape
    n_stakes = len(stake_elevs)

    # State
    swe = swe_init.copy()
    cum_melt = np.zeros((nrows, ncols), dtype=np.float64)
    cum_accum = np.zeros((nrows, ncols), dtype=np.float64)
    surface_type = np.zeros((nrows, ncols), dtype=np.int32)

    for i in range(nrows):
        for j in range(ncols):
            if not glacier_mask[i, j]:
                surface_type[i, j] = 0
            elif swe[i, j] > 0:
                surface_type[i, j] = 1
            elif firn_mask[i, j]:
                surface_type[i, j] = 2
            else:
                surface_type[i, j] = 3

    daily_glacier_melt = np.zeros(n_days, dtype=np.float64)
    daily_glacier_runoff = np.zeros(n_days, dtype=np.float64)

    n_glacier = 0
    for i in range(nrows):
        for j in range(ncols):
            if glacier_mask[i, j]:
                n_glacier += 1

    if n_glacier == 0:
        stake_balances = np.zeros(n_stakes, dtype=np.float64)
        return cum_melt, cum_accum, daily_glacier_melt, daily_glacier_runoff, stake_balances, 0.0

    # ── Main time loop ──────────────────────────────────────────────
    for t in range(n_days):
        T_nuka_t = T_nuka[t]
        P_nuka_t = P_nuka[t]
        doy = doy_array[t]
        doy_idx = doy - 1
        if doy_idx < 0:
            doy_idx = 0
        if doy_idx >= 365:
            doy_idx = 364

        # Month for temperature transfer
        month_idx = _doy_to_month(doy)

        # Statistical transfer: Nuka (1230m) → on-glacier reference (804m)
        alpha = transfer_alpha[month_idx]
        beta = transfer_beta[month_idx]
        T_ref = alpha * T_nuka_t + beta  # temperature at ref_elev on glacier

        day_melt_sum = 0.0
        day_runoff_sum = 0.0

        for i in prange(nrows):
            for j in range(ncols):
                if not glacier_mask[i, j] or elevation[i, j] == nodata:
                    continue

                # Temperature at this cell (internal lapse from ref)
                dz = elevation[i, j] - ref_elev
                T_cell = T_ref + internal_lapse * dz

                # Precipitation at this cell
                P_cell = P_nuka_t * precip_corr * (1.0 + precip_grad * dz)
                if P_cell < 0:
                    P_cell = 0.0

                # Rain/snow partition
                snow_frac = _rain_snow_fraction(T_cell, T0)
                snowfall = P_cell * snow_frac
                rainfall = P_cell * (1.0 - snow_frac)

                # Accumulation
                swe[i, j] += snowfall
                cum_accum[i, j] += snowfall

                # Melt (only if T > 0)
                melt = 0.0
                if T_cell > 0:
                    I = ipot_lookup[doy_idx, i, j]
                    st = surface_type[i, j]
                    if st == 1 or st == 2:
                        r = r_snow
                    else:
                        r = r_ice

                    # Elevation-dependent melt factor
                    MF_cell = MF + MF_grad * dz
                    if MF_cell < 0.1:
                        MF_cell = 0.1

                    melt = (MF_cell + r * I) * T_cell
                    if melt < 0:
                        melt = 0.0

                # Apply melt to snowpack
                if melt > 0:
                    if swe[i, j] > 0:
                        snow_melted = min(swe[i, j], melt)
                        swe[i, j] -= snow_melted
                    cum_melt[i, j] += melt
                    day_melt_sum += melt

                # Runoff = melt + rain
                day_runoff_sum += melt + rainfall

                # Update surface type
                if swe[i, j] > 0:
                    surface_type[i, j] = 1
                elif firn_mask[i, j]:
                    surface_type[i, j] = 2
                else:
                    surface_type[i, j] = 3

        daily_glacier_melt[t] = day_melt_sum / n_glacier
        daily_glacier_runoff[t] = day_runoff_sum / n_glacier

    # ── Extract stake balances ──────────────────────────────────────
    stake_balances = np.zeros(n_stakes, dtype=np.float64)
    stake_counts = np.zeros(n_stakes, dtype=np.float64)

    for i in range(nrows):
        for j in range(ncols):
            if not glacier_mask[i, j]:
                continue
            elev = elevation[i, j]
            net = (cum_accum[i, j] - cum_melt[i, j]) / 1000.0

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

    return cum_melt, cum_accum, daily_glacier_melt, daily_glacier_runoff, stake_balances, glacier_wide_balance


@njit
def _make_swe_init_jit(elevation, glacier_mask, ref_elev, winter_swe_mm, precip_grad):
    nrows, ncols = elevation.shape
    swe = np.zeros((nrows, ncols), dtype=np.float64)
    for i in range(nrows):
        for j in range(ncols):
            if glacier_mask[i, j]:
                dz = elevation[i, j] - ref_elev
                val = winter_swe_mm * (1.0 + precip_grad * dz)
                if val < 0:
                    val = 0.0
                swe[i, j] = val
    return swe


class FastDETIM:
    """Fast wrapper around the numba-compiled simulation kernel (v2).

    Changes from v1:
      - Accepts raw Nuka SNOTEL temperatures
      - Applies statistical transfer internally
      - Supports elevation-dependent melt factor
      - Tracks daily runoff (melt + rain) for routing
    """

    def __init__(self, grid, ipot_table, transfer_alpha, transfer_beta,
                 ref_elev, stake_names, stake_elevs, stake_tol=50.0):
        self.elevation = grid['elevation'].astype(np.float64)
        self.glacier_mask = grid['glacier_mask']
        self.nrows, self.ncols = self.elevation.shape
        self.ref_elev = ref_elev
        self.cell_size = grid['cell_size']

        # Transfer coefficients
        self.transfer_alpha = transfer_alpha.astype(np.float64)
        self.transfer_beta = transfer_beta.astype(np.float64)

        # Firn mask (above median glacier elevation)
        glacier_elevs = self.elevation[self.glacier_mask]
        self.firn_elev = np.median(glacier_elevs) if len(glacier_elevs) > 0 else 1100.0
        self.firn_mask = self.glacier_mask & (self.elevation >= self.firn_elev)

        # Pack ipot into 3D array
        self.ipot_3d = np.zeros((365, self.nrows, self.ncols), dtype=np.float64)
        for doy in range(1, 366):
            if doy in ipot_table:
                self.ipot_3d[doy - 1] = ipot_table[doy]

        # Stakes
        self.stake_names = list(stake_names)
        self.stake_elevs = stake_elevs.astype(np.float64)
        self.stake_tol = stake_tol

        self.nodata = -9999.0

    def run(self, T_nuka, P_nuka, doy_array, params, winter_swe_mm):
        """Run simulation with given parameters.

        Parameters
        ----------
        T_nuka : 1D array, daily temperature at Nuka SNOTEL RAW (C)
        P_nuka : 1D array, daily precipitation at Nuka SNOTEL (mm)
        doy_array : 1D int array, day of year
        params : dict with MF, MF_grad, r_snow, r_ice, internal_lapse,
                 precip_grad, precip_corr, T0
        winter_swe_mm : float, reference winter SWE at ref elevation (mm)

        Returns
        -------
        dict with keys: cum_melt, cum_accum, daily_melt, daily_runoff,
                        stake_balances, glacier_wide_balance
        """
        swe_init = _make_swe_init_jit(
            self.elevation, self.glacier_mask, self.ref_elev,
            winter_swe_mm, params['precip_grad'],
        )

        results = run_simulation(
            T_nuka.astype(np.float64),
            P_nuka.astype(np.float64),
            doy_array.astype(np.int64),
            self.elevation,
            self.ipot_3d,
            self.glacier_mask,
            self.firn_mask,
            self.transfer_alpha,
            self.transfer_beta,
            self.ref_elev,
            params['MF'],
            params.get('MF_grad', 0.0),
            params['r_snow'],
            params['r_ice'],
            params['internal_lapse'],
            params['precip_grad'],
            params['precip_corr'],
            params['T0'],
            self.nodata,
            swe_init,
            self.stake_elevs,
            self.stake_tol,
        )

        cum_melt, cum_accum, daily_melt, daily_runoff, stake_bal, gw_bal = results

        stakes = {}
        for i, name in enumerate(self.stake_names):
            stakes[name] = stake_bal[i]

        return {
            'cum_melt': cum_melt,
            'cum_accum': cum_accum,
            'daily_melt': daily_melt,
            'daily_runoff': daily_runoff,
            'stake_balances': stakes,
            'glacier_wide_balance': gw_bal,
        }

    def update_geometry(self, new_elevation, new_glacier_mask):
        """Update DEM and glacier mask for glacier retreat simulations."""
        self.elevation = new_elevation.astype(np.float64)
        self.glacier_mask = new_glacier_mask
        self.nrows, self.ncols = self.elevation.shape

        glacier_elevs = self.elevation[self.glacier_mask]
        if len(glacier_elevs) > 0:
            self.firn_elev = np.median(glacier_elevs)
        self.firn_mask = self.glacier_mask & (self.elevation >= self.firn_elev)
