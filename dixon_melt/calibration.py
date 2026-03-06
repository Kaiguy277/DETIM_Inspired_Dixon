"""
Calibration of DETIM parameters using scipy differential_evolution.

Fits MF, r_snow, r_ice (and optionally lapse_rate, precip_grad, T0)
against stake observations and geodetic mass balance.

Uses numba-compiled model core for speed.
"""
import numpy as np
from scipy.optimize import differential_evolution
from .model import DETIMModel
from .massbalance import load_stake_observations


# Parameter bounds for calibration
PARAM_BOUNDS = {
    'MF':          (1.0, 12.0),       # mm d⁻¹ K⁻¹
    'r_snow':      (0.05e-3, 1.5e-3), # mm m² W⁻¹ d⁻¹ K⁻¹
    'r_ice':       (0.1e-3, 3.0e-3),  # mm m² W⁻¹ d⁻¹ K⁻¹
    'lapse_rate':  (-8.0e-3, -4.0e-3),# °C/m
    'precip_grad': (0.0, 0.002),      # fractional per m
    'T0':          (0.5, 3.0),         # °C
    'precip_corr': (1.0, 1.5),        # dimensionless
}


def build_objective(
    model, climate_df, stake_df,
    geodetic_mb=None,
    param_names=('MF', 'r_snow', 'r_ice'),
    fixed_params=None,
    weight_stakes=1.0,
    weight_geodetic=0.5,
):
    """Build an objective function for differential_evolution.

    Parameters
    ----------
    model : DETIMModel
    climate_df : DataFrame with date, temperature, precipitation
    stake_df : DataFrame from load_stake_observations()
    geodetic_mb : float, optional
        Target glacier-wide specific MB (m w.e./yr)
    param_names : tuple of str
        Which parameters to optimize
    fixed_params : dict, optional
        Fixed parameter values
    weight_stakes, weight_geodetic : float
        Relative weights in objective

    Returns
    -------
    objective : callable for scipy.optimize
    bounds : list of (min, max) tuples
    """
    bounds = [PARAM_BOUNDS[name] for name in param_names]

    # Pre-filter stake data to annual observations
    annual_stakes = stake_df[stake_df['period_type'] == 'annual'].copy()

    def objective(x):
        # Set parameters
        params = dict(fixed_params) if fixed_params else {}
        for name, val in zip(param_names, x):
            params[name] = val

        model.set_params(params)
        model.reset()

        # Initialize SWE with a reasonable winter total
        # Use winter stake data to estimate
        winter_data = stake_df[
            (stake_df['period_type'] == 'winter') &
            (stake_df['site_id'] == 'ELA')
        ]
        if len(winter_data) > 0:
            mean_winter_accum = winter_data['mb_obs_mwe'].mean() * 1000  # m→mm
        else:
            mean_winter_accum = 2000.0  # mm fallback
        model.initialize_swe(mean_winter_accum)

        # Run model
        try:
            results = model.run(climate_df)
        except Exception:
            return 1e6

        # Compare to stake observations
        stake_error = 0.0
        n_stake = 0
        modeled_stakes = model.get_balance_at_stakes()

        for _, obs in annual_stakes.iterrows():
            site = obs['site_id']
            if site in modeled_stakes and not np.isnan(modeled_stakes[site]):
                err = modeled_stakes[site] - obs['mb_obs_mwe']
                stake_error += err ** 2
                n_stake += 1

        if n_stake > 0:
            stake_rmse = np.sqrt(stake_error / n_stake)
        else:
            stake_rmse = 10.0

        # Compare to geodetic MB
        geodetic_error = 0.0
        if geodetic_mb is not None:
            modeled_gw = results['glacier_wide_balance_mwe'].iloc[-1]
            geodetic_error = (modeled_gw - geodetic_mb) ** 2

        total = weight_stakes * stake_rmse + weight_geodetic * np.sqrt(geodetic_error)
        return total

    return objective, bounds


def calibrate(
    model, climate_df, stake_csv, geodetic_mb=None,
    param_names=('MF', 'r_snow', 'r_ice'),
    fixed_params=None,
    maxiter=50, popsize=15, seed=42, workers=-1,
    **de_kwargs,
):
    """Run differential evolution calibration.

    Parameters
    ----------
    model : DETIMModel
    climate_df : DataFrame
    stake_csv : str, path to stake observations CSV
    geodetic_mb : float, optional
    param_names : tuple of str
    fixed_params : dict, optional
    maxiter, popsize, seed : DE parameters
    workers : int, -1 for all cores (NOTE: requires model to be picklable,
              use 1 for safety during development)

    Returns
    -------
    result : scipy OptimizeResult
    best_params : dict
    """
    stake_df = load_stake_observations(stake_csv)

    objective, bounds = build_objective(
        model, climate_df, stake_df,
        geodetic_mb=geodetic_mb,
        param_names=param_names,
        fixed_params=fixed_params,
    )

    result = differential_evolution(
        objective,
        bounds=bounds,
        maxiter=maxiter,
        popsize=popsize,
        seed=seed,
        workers=1,  # numba parallelism handles the inner loop
        disp=True,
        **de_kwargs,
    )

    best_params = {name: val for name, val in zip(param_names, result.x)}
    print(f"\nCalibration complete. Best cost: {result.fun:.4f}")
    print("Best parameters:")
    for k, v in best_params.items():
        print(f"  {k}: {v:.6f}")

    return result, best_params
