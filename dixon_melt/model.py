"""
Main DETIM model runner for Dixon Glacier.

Orchestrates: grid setup → solar → temperature → precip → melt → snowpack → mass balance
for each time step.
"""
import numpy as np
import pandas as pd
from . import config
from .solar import compute_daily_ipot
from .temperature import distribute_temperature
from .precipitation import distribute_precipitation
from .melt import compute_melt
from .snowpack import update_snowpack
from .massbalance import compute_glacier_wide_balance, extract_point_balance


def precompute_ipot(grid, doy_range=range(1, 366), dt_hours=3.0):
    """Precompute daily-mean potential direct radiation for all DOYs.

    This is the most expensive computation and is grid-geometry-dependent
    (not parameter-dependent), so it only needs to run once per grid.

    Parameters
    ----------
    grid : dict from terrain.prepare_grid()
    doy_range : iterable of int
    dt_hours : float, temporal resolution for daily integration

    Returns
    -------
    ipot_table : dict mapping DOY → 2D array (W/m²)
    """
    ipot_table = {}
    n = len(list(doy_range))
    for i, doy in enumerate(doy_range):
        if (i + 1) % 30 == 0 or i == 0:
            print(f"  Precomputing I_pot: DOY {doy}/{n}...")
        ipot_table[doy] = compute_daily_ipot(
            doy, config.LATITUDE,
            grid['elevation'], grid['slope'], grid['aspect'],
            dt_hours=dt_hours,
        )
    return ipot_table


class DETIMModel:
    """Distributed Enhanced Temperature Index Model for Dixon Glacier."""

    def __init__(self, grid, params=None, ipot_table=None):
        """
        Parameters
        ----------
        grid : dict
            Output of terrain.prepare_grid() — elevation, slope, aspect,
            glacier_mask, cell_size, etc.
        params : dict, optional
            Model parameters. Defaults to config.DEFAULT_PARAMS.
        ipot_table : dict, optional
            Precomputed DOY → I_pot grids from precompute_ipot().
            If None, will compute on-the-fly (slow during calibration).
        """
        self.grid = grid
        self.params = dict(config.DEFAULT_PARAMS)
        if params:
            self.params.update(params)

        self.elevation = grid['elevation']
        self.slope = grid['slope']
        self.aspect = grid['aspect']
        self.glacier_mask = grid['glacier_mask']
        self.nrows, self.ncols = self.elevation.shape

        # Firn mask: approximate as cells above median glacier elevation
        glacier_elevs = self.elevation[self.glacier_mask]
        if len(glacier_elevs) > 0:
            self.firn_elev = np.median(glacier_elevs)
        else:
            self.firn_elev = 1100.0
        self.firn_mask = self.glacier_mask & (self.elevation >= self.firn_elev)

        # State arrays
        self.swe = np.zeros_like(self.elevation)
        self.surface_type = np.ones_like(self.elevation, dtype=np.int32)
        self.surface_type[~self.glacier_mask] = 0

        # Accumulators
        self.cumulative_melt = np.zeros_like(self.elevation)
        self.cumulative_accum = np.zeros_like(self.elevation)

        # Solar radiation: use precomputed table or compute on-the-fly
        self._ipot_table = ipot_table
        self._ipot_cache = {}

    def set_params(self, params):
        """Update parameters (used during calibration)."""
        self.params.update(params)

    def reset(self):
        """Reset state for a new run. Does NOT clear ipot cache (geometry-dependent)."""
        self.swe[:] = 0.0
        self.cumulative_melt[:] = 0.0
        self.cumulative_accum[:] = 0.0
        self.surface_type[:] = 1
        self.surface_type[~self.glacier_mask] = 0

    def initialize_swe(self, winter_precip_mm):
        """Initialize snow water equivalent from total winter precipitation."""
        from .snowpack import initialize_swe
        self.swe = initialize_swe(
            self.elevation, self.glacier_mask,
            winter_precip_mm, self.params['precip_grad'],
            config.SNOTEL_ELEV
        )
        # Update surface type
        self.surface_type[self.glacier_mask & (self.swe > 0)] = 1
        self.surface_type[self.glacier_mask & (self.swe <= 0) & self.firn_mask] = 2
        self.surface_type[self.glacier_mask & (self.swe <= 0) & ~self.firn_mask] = 3

    def get_ipot(self, doy):
        """Get daily-mean potential direct radiation grid.

        Uses precomputed table if available, otherwise computes and caches.
        """
        if self._ipot_table is not None and doy in self._ipot_table:
            return self._ipot_table[doy]
        if doy not in self._ipot_cache:
            self._ipot_cache[doy] = compute_daily_ipot(
                doy, config.LATITUDE,
                self.elevation, self.slope, self.aspect,
                dt_hours=3.0,
            )
        return self._ipot_cache[doy]

    def step(self, doy, T_station, precip_station, dt_days=1.0):
        """Run one time step of the model.

        Parameters
        ----------
        doy : int
            Day of year
        T_station : float
            Air temperature at climate station (°C)
        precip_station : float
            Precipitation at climate station (mm/timestep)
        dt_days : float
            Time step length in days

        Returns
        -------
        dict with step results: melt_grid, snowfall_grid, etc.
        """
        p = self.params

        # 1. Distribute temperature
        T_grid = distribute_temperature(
            T_station, config.SNOTEL_ELEV,
            self.elevation, p['lapse_rate'], config.NODATA
        )

        # 2. Distribute precipitation
        snowfall, rainfall = distribute_precipitation(
            precip_station, T_grid, self.elevation,
            config.SNOTEL_ELEV, p['precip_grad'], p['precip_corr'],
            p['T0'], config.NODATA
        )

        # 3. Get potential direct radiation
        ipot = self.get_ipot(doy)

        # 4. Compute melt
        melt_grid = compute_melt(
            T_grid, ipot, self.surface_type,
            p['MF'], p['r_snow'], p['r_ice'],
            config.NODATA, dt_days
        )

        # 5. Update snowpack and surface type
        self.surface_type, ice_melt, snow_melt = update_snowpack(
            self.swe, snowfall, melt_grid,
            self.glacier_mask, self.firn_mask,
            config.NODATA, self.elevation
        )

        # 6. Accumulate
        self.cumulative_melt += melt_grid
        self.cumulative_accum += snowfall

        return dict(
            T_grid=T_grid,
            melt=melt_grid,
            snowfall=snowfall,
            rainfall=rainfall,
            ice_melt=ice_melt,
            snow_melt=snow_melt,
            total_melt_glacier=melt_grid[self.glacier_mask].sum() * (self.grid['cell_size']**2) / 1e9,  # km³
        )

    def run(self, climate_df, start_date=None, end_date=None):
        """Run the model over a period defined by a climate DataFrame.

        Parameters
        ----------
        climate_df : DataFrame
            Must have columns: date, temperature, precipitation
            Index or 'date' column as datetime.
        start_date, end_date : str or datetime, optional

        Returns
        -------
        results : DataFrame with daily outputs
        """
        df = climate_df.copy()
        if 'date' in df.columns:
            df = df.set_index('date')
        if start_date:
            df = df[df.index >= pd.Timestamp(start_date)]
        if end_date:
            df = df[df.index <= pd.Timestamp(end_date)]

        records = []
        for date, row in df.iterrows():
            doy = date.timetuple().tm_yday
            result = self.step(
                doy=doy,
                T_station=row['temperature'],
                precip_station=row['precipitation'],
                dt_days=1.0
            )

            # Glacier-wide stats
            glacier_melt_mm = result['melt'][self.glacier_mask].mean() if self.glacier_mask.any() else 0
            glacier_accum_mm = result['snowfall'][self.glacier_mask].mean() if self.glacier_mask.any() else 0
            glacier_swe_mm = self.swe[self.glacier_mask].mean() if self.glacier_mask.any() else 0

            records.append(dict(
                date=date,
                doy=doy,
                T_station=row['temperature'],
                precip_station=row['precipitation'],
                glacier_melt_mm=glacier_melt_mm,
                glacier_accum_mm=glacier_accum_mm,
                glacier_swe_mm=glacier_swe_mm,
                glacier_wide_balance_mwe=compute_glacier_wide_balance(
                    self.cumulative_melt, self.cumulative_accum, self.glacier_mask
                ),
            ))

        return pd.DataFrame(records)

    def get_balance_at_stakes(self):
        """Extract current cumulative balance at the three stake elevations."""
        stakes = {
            'ABL': 804.0,
            'ELA': 1078.0,
            'ACC': 1293.0,
        }
        result = {}
        for name, elev in stakes.items():
            result[name] = extract_point_balance(
                self.cumulative_melt, self.cumulative_accum,
                self.elevation, elev, self.glacier_mask
            )
        return result
