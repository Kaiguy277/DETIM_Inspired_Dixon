"""
Calibration diagnostic plots for CAL-010 (D-017).

Produces figures analogous to Geck et al. (2021) J. Glaciol.:
  1. Parameter posterior distributions within search space (cf. Fig. 4)
  2. Modeled vs observed stake balances — 1:1 scatter (cf. Fig. 5/9)
  3. Modeled seasonal balances at each stake with ensemble spread
  4. Glacier-wide annual balance time series 2001–2025 with ensemble spread (cf. Fig. 8)
"""
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import json
import time

PROJECT = Path('/home/kai/Documents/Opus46Dixon_FirstShot')
OUTPUT_DIR = PROJECT / 'calibration_output'
STAKE_PATH = PROJECT / 'stake_observations_dixon.csv'
NUKA_PATH = PROJECT / 'data' / 'climate' / 'nuka_snotel_full.csv'
DEM_PATH = PROJECT / 'ifsar_2010' / 'dixon_glacier_IFSAR_DTM_5m_full.tif'
GLACIER_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_outline_rgi7.geojson'
GEODETIC_PATH = PROJECT / 'geodedic_mb' / 'dixon_glacier_hugonnet.csv'

# Fixed parameters (D-017)
FIXED_LAPSE = -5.0e-3
FIXED_RICE_RATIO = 2.0
FIXED_K_WIND = 0.0

PARAM_NAMES = ['MF', 'MF_grad', 'r_snow', 'precip_grad', 'precip_corr', 'T0']
PARAM_BOUNDS = [
    (1.0, 12.0), (-0.01, 0.0), (0.02e-3, 2.0e-3),
    (0.0002, 0.006), (1.2, 4.0), (0.0, 3.0),
]

N_ENSEMBLE = 200  # number of posterior samples to use


def load_nuka_raw():
    df = pd.read_csv(NUKA_PATH, parse_dates=['Date'])
    df = df.rename(columns={
        'Date': 'date',
        'Air Temperature Average (degF)': 'tavg_f',
        'Precipitation Accumulation (in) Start of Day Values': 'precip_accum_in',
    })
    df['temperature'] = (df['tavg_f'] - 32) * 5 / 9
    bad = (df['temperature'] < -50) | (df['temperature'] > 40)
    df.loc[bad, 'temperature'] = np.nan
    if 'precip_accum_in' in df.columns:
        accum = df['precip_accum_in'].copy()
        diff = accum.diff()
        resets = diff < -1.0
        daily_in = diff.clip(lower=0)
        daily_in.iloc[0] = 0
        daily_in[resets] = 0
        df['precipitation'] = daily_in * 25.4
    else:
        df['precipitation'] = 0.0
    df = df.set_index('date').sort_index()
    df['temperature'] = df['temperature'].interpolate(method='linear', limit=3)
    return df[['temperature', 'precipitation']]


def prepare_water_year_arrays(climate, wy_year):
    start = f'{wy_year - 1}-10-01'
    end = f'{wy_year}-09-30'
    wy = climate.loc[start:end]
    if len(wy) < 300:
        return None
    T = wy['temperature'].ffill().fillna(0).values.astype(np.float64)
    P = wy['precipitation'].fillna(0).values.astype(np.float64)
    doy = np.array([d.timetuple().tm_yday for d in wy.index], dtype=np.int64)
    return T, P, doy


def prepare_period_arrays(climate, start_date, end_date):
    wy = climate.loc[start_date:end_date]
    if len(wy) < 30:
        return None
    T = wy['temperature'].ffill().fillna(0).values.astype(np.float64)
    P = wy['precipitation'].fillna(0).values.astype(np.float64)
    doy = np.array([d.timetuple().tm_yday for d in wy.index], dtype=np.int64)
    return T, P, doy


def sample_to_params(row):
    """Convert a posterior sample row to model params dict."""
    return {
        'MF': row['MF'],
        'MF_grad': row['MF_grad'],
        'r_snow': row['r_snow'],
        'r_ice': FIXED_RICE_RATIO * row['r_snow'],
        'internal_lapse': FIXED_LAPSE,
        'precip_grad': row['precip_grad'],
        'precip_corr': row['precip_corr'],
        'T0': row['T0'],
        'k_wind': FIXED_K_WIND,
    }


def main():
    t0 = time.time()
    print("Loading data and model...")

    # Load posterior samples
    posterior = pd.read_csv(OUTPUT_DIR / 'posterior_samples_v10.csv')
    print(f"  Posterior samples: {len(posterior)}")

    # Subsample for ensemble runs
    np.random.seed(42)
    idx = np.random.choice(len(posterior), size=min(N_ENSEMBLE, len(posterior)), replace=False)
    ensemble = posterior.iloc[idx].reset_index(drop=True)
    print(f"  Using {len(ensemble)} samples for plots")

    # Load MAP params
    with open(OUTPUT_DIR / 'best_params_v10.json') as f:
        map_params_raw = json.load(f)

    # Load climate
    climate = load_nuka_raw()
    climate['temperature'] = climate['temperature'].ffill().fillna(0)
    climate['precipitation'] = climate['precipitation'].fillna(0)

    # Load stakes
    stakes = pd.read_csv(STAKE_PATH, parse_dates=['date_start', 'date_end'])

    # Load geodetic
    geodetic = pd.read_csv(GEODETIC_PATH)

    # Initialize model
    from dixon_melt.terrain import prepare_grid
    from dixon_melt.model import precompute_ipot
    from dixon_melt.fast_model import FastDETIM
    from dixon_melt import config

    grid = prepare_grid(str(DEM_PATH), str(GLACIER_PATH), target_res=100.0)
    ipot_table = precompute_ipot(grid, doy_range=range(1, 366), dt_hours=3.0)

    fmodel = FastDETIM(
        grid, ipot_table,
        transfer_alpha=config.TRANSFER_ALPHA,
        transfer_beta=config.TRANSFER_BETA,
        ref_elev=config.SNOTEL_ELEV,
        stake_names=config.STAKE_NAMES,
        stake_elevs=config.STAKE_ELEVS,
        stake_tol=config.STAKE_TOL,
    )

    # JIT warm-up
    test_params = sample_to_params(ensemble.iloc[0])
    test_arrays = prepare_water_year_arrays(climate, 2023)
    _ = fmodel.run(test_arrays[0], test_arrays[1], test_arrays[2], test_params, 0.0)
    print(f"  Model initialized in {time.time()-t0:.1f}s")

    # ══════════════════════════════════════════════════════════════════
    # RUN ENSEMBLE FOR ALL YEARS
    # ══════════════════════════════════════════════════════════════════
    print("\nRunning ensemble simulations...")

    # Water years for geodetic period + stake years
    wy_years = list(range(2001, 2026))
    stake_years = [2023, 2024, 2025]

    # Pre-compute arrays for all water years
    wy_arrays = {}
    for yr in wy_years:
        arr = prepare_water_year_arrays(climate, yr)
        if arr is not None:
            wy_arrays[yr] = arr

    # Pre-compute arrays for seasonal stake periods
    stake_period_arrays = {}
    for _, row in stakes.iterrows():
        key = (row['site_id'], row['period_type'], row['year'])
        start_str = row['date_start'].strftime('%Y-%m-%d')
        end_str = row['date_end'].strftime('%Y-%m-%d')
        arr = prepare_period_arrays(climate, start_str, end_str)
        if arr is not None:
            stake_period_arrays[key] = arr

    # Storage
    # Glacier-wide annual balance: (n_ensemble, n_years)
    gw_balances = np.full((len(ensemble), len(wy_years)), np.nan)
    # Stake balances: dict of (site, period_type, year) -> array of n_ensemble values
    stake_modeled = {}

    for i, (_, sample) in enumerate(ensemble.iterrows()):
        params = sample_to_params(sample)

        # Annual water years (glacier-wide + stake annual)
        for j, yr in enumerate(wy_years):
            if yr not in wy_arrays:
                continue
            T, P, doy = wy_arrays[yr]
            r = fmodel.run(T, P, doy, params, 0.0)
            gw_balances[i, j] = r['glacier_wide_balance']

            # Extract annual stake balances for stake years
            if yr in stake_years:
                for site in ['ABL', 'ELA', 'ACC']:
                    key = (site, 'annual', yr)
                    if key not in stake_modeled:
                        stake_modeled[key] = np.full(len(ensemble), np.nan)
                    stake_modeled[key][i] = r['stake_balances'].get(site, np.nan)

        # Seasonal stake periods
        for _, srow in stakes.iterrows():
            key = (srow['site_id'], srow['period_type'], srow['year'])
            if key in stake_period_arrays and srow['period_type'] != 'annual':
                T, P, doy = stake_period_arrays[key]
                if srow['period_type'] == 'summer':
                    yr = srow['year']
                    w_ela = stakes[(stakes['year']==yr) & (stakes['site_id']=='ELA')
                                   & (stakes['period_type']=='winter')]
                    wswe = w_ela['mb_obs_mwe'].values[0] * 1000 if len(w_ela) else 2500.0
                else:
                    wswe = 0.0
                r = fmodel.run(T, P, doy, params, wswe)
                if key not in stake_modeled:
                    stake_modeled[key] = np.full(len(ensemble), np.nan)
                stake_modeled[key][i] = r['stake_balances'].get(srow['site_id'], np.nan)

        if (i + 1) % 20 == 0:
            elapsed = time.time() - t0
            print(f"    {i+1}/{len(ensemble)} samples done ({elapsed:.0f}s)")

    print(f"  Ensemble runs complete in {time.time()-t0:.0f}s")

    # ══════════════════════════════════════════════════════════════════
    # PLOT 1: Parameter posterior distributions (cf. Geck Fig. 4)
    # ══════════════════════════════════════════════════════════════════
    print("\nGenerating plots...")

    param_labels = [
        'MF\n(mm d$^{-1}$ K$^{-1}$)',
        'MF$_{grad}$\n(mm d$^{-1}$ K$^{-1}$ m$^{-1}$)',
        'r$_{snow}$ (×10$^{-3}$)\n(mm m$^2$ W$^{-1}$ d$^{-1}$ K$^{-1}$)',
        '$\\gamma_p$\n(m$^{-1}$)',
        'C$_p$\n(—)',
        'T$_0$\n(°C)',
    ]

    fig, axes = plt.subplots(1, 6, figsize=(16, 3.5))
    fig.suptitle('Posterior parameter distributions (n = 2,760)', fontsize=13, y=1.02)

    for i, (ax, name, label) in enumerate(zip(axes, PARAM_NAMES, param_labels)):
        lo, hi = PARAM_BOUNDS[i]
        vals = posterior[name].values
        if name == 'r_snow':
            vals = vals * 1e3
            lo, hi = lo * 1e3, hi * 1e3

        ax.hist(vals, bins=50, color='steelblue', alpha=0.7, edgecolor='none', density=True)
        ax.axvline(np.median(vals), color='k', lw=1.5, ls='-', label='Median')
        ax.axvline(np.percentile(vals, 16), color='k', lw=1, ls='--', alpha=0.5)
        ax.axvline(np.percentile(vals, 84), color='k', lw=1, ls='--', alpha=0.5)
        ax.set_xlim(lo, hi)
        ax.set_xlabel(label, fontsize=9)
        ax.set_yticks([])
        # Add bound markers
        ax.axvline(lo, color='red', lw=0.8, ls=':', alpha=0.5)
        ax.axvline(hi, color='red', lw=0.8, ls=':', alpha=0.5)

    axes[0].legend(fontsize=7, loc='upper right')
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / 'param_posteriors_v10.png', dpi=200, bbox_inches='tight')
    print(f"  Saved param_posteriors_v10.png")
    plt.close()

    # ══════════════════════════════════════════════════════════════════
    # PLOT 2: Modeled vs Observed 1:1 scatter (all stake obs)
    # ══════════════════════════════════════════════════════════════════
    fig, ax = plt.subplots(1, 1, figsize=(7, 7))

    colors = {'annual': '#2c3e50', 'summer': '#e74c3c', 'winter': '#3498db'}
    markers = {'ABL': 'o', 'ELA': 's', 'ACC': '^'}

    obs_vals = []
    mod_medians = []
    mod_16 = []
    mod_84 = []
    plot_colors = []
    plot_markers = []
    plot_labels_done = set()

    for _, srow in stakes.iterrows():
        key = (srow['site_id'], srow['period_type'], srow['year'])
        if key not in stake_modeled:
            continue
        vals = stake_modeled[key]
        valid = vals[~np.isnan(vals)]
        if len(valid) < 10:
            continue

        obs = srow['mb_obs_mwe']
        med = np.median(valid)
        q16, q84 = np.percentile(valid, [16, 84])

        obs_vals.append(obs)
        mod_medians.append(med)
        mod_16.append(q16)
        mod_84.append(q84)
        plot_colors.append(colors[srow['period_type']])
        plot_markers.append(markers[srow['site_id']])

        # Plot with error bars
        label_key = f"{srow['period_type']}"
        label = label_key.capitalize() if label_key not in plot_labels_done else None
        plot_labels_done.add(label_key)

        ax.errorbar(obs, med, yerr=[[med - q16], [q84 - med]],
                    fmt=markers[srow['site_id']], color=colors[srow['period_type']],
                    markersize=8, capsize=3, label=label, alpha=0.8)

    # 1:1 line
    all_vals = obs_vals + mod_medians
    lo = min(all_vals) - 0.5
    hi = max(all_vals) + 0.5
    ax.plot([lo, hi], [lo, hi], 'k--', lw=1, alpha=0.5, label='1:1')
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel('Observed (m w.e.)', fontsize=12)
    ax.set_ylabel('Modeled (m w.e.)', fontsize=12)
    ax.set_title('Modeled vs Observed Stake Mass Balance', fontsize=13)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)

    # Add marker legend
    from matplotlib.lines import Line2D
    site_handles = [Line2D([0], [0], marker=m, color='gray', linestyle='', markersize=8, label=s)
                    for s, m in markers.items()]
    first_legend = ax.legend(loc='upper left', fontsize=10)
    ax.add_artist(first_legend)
    ax.legend(handles=site_handles, loc='lower right', fontsize=10)

    # RMSE annotation
    obs_arr = np.array(obs_vals)
    mod_arr = np.array(mod_medians)
    rmse = np.sqrt(np.mean((mod_arr - obs_arr)**2))
    bias = np.mean(mod_arr - obs_arr)
    r2 = np.corrcoef(obs_arr, mod_arr)[0, 1]**2
    ax.text(0.05, 0.85, f'RMSE = {rmse:.2f} m w.e.\nBias = {bias:+.2f} m w.e.\n$r^2$ = {r2:.2f}',
            transform=ax.transAxes, fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / 'modeled_vs_observed_v10.png', dpi=200, bbox_inches='tight')
    print(f"  Saved modeled_vs_observed_v10.png")
    plt.close()

    # ══════════════════════════════════════════════════════════════════
    # PLOT 3: Seasonal stake balances with ensemble spread
    # ══════════════════════════════════════════════════════════════════
    fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    sites = ['ABL', 'ELA', 'ACC']
    site_elevs = {'ABL': 804, 'ELA': 1078, 'ACC': 1293}

    for ax, site in zip(axes, sites):
        for ptype, color, offset in [('winter', '#3498db', -0.15),
                                      ('summer', '#e74c3c', 0.0),
                                      ('annual', '#2c3e50', 0.15)]:
            obs_years = []
            obs_vals_s = []
            obs_unc = []
            mod_med = []
            mod_q16 = []
            mod_q84 = []

            for _, srow in stakes[(stakes['site_id'] == site) & (stakes['period_type'] == ptype)].iterrows():
                key = (srow['site_id'], srow['period_type'], srow['year'])
                if key not in stake_modeled:
                    continue
                valid = stake_modeled[key][~np.isnan(stake_modeled[key])]
                if len(valid) < 10:
                    continue

                obs_years.append(srow['year'] + offset)
                obs_vals_s.append(srow['mb_obs_mwe'])
                obs_unc.append(srow['mb_obs_uncertainty_mwe'])
                mod_med.append(np.median(valid))
                mod_q16.append(np.percentile(valid, 16))
                mod_q84.append(np.percentile(valid, 84))

            if not obs_years:
                continue

            obs_years = np.array(obs_years)
            obs_vals_s = np.array(obs_vals_s)
            obs_unc = np.array(obs_unc)
            mod_med = np.array(mod_med)
            mod_q16 = np.array(mod_q16)
            mod_q84 = np.array(mod_q84)

            # Observed: markers with error bars
            ax.errorbar(obs_years, obs_vals_s, yerr=obs_unc,
                       fmt='o', color=color, markersize=7, capsize=4, alpha=0.9,
                       label=f'{ptype.capitalize()} obs')

            # Modeled: filled range
            ax.fill_between(obs_years, mod_q16, mod_q84, color=color, alpha=0.2)
            ax.plot(obs_years, mod_med, 'x', color=color, markersize=9, mew=2,
                    label=f'{ptype.capitalize()} mod')

        ax.axhline(0, color='k', lw=0.5, alpha=0.3)
        ax.set_ylabel('Mass balance (m w.e.)', fontsize=11)
        ax.set_title(f'{site} stake ({site_elevs[site]} m)', fontsize=12)
        ax.legend(fontsize=8, ncol=3, loc='lower left')
        ax.grid(True, alpha=0.2)

    axes[-1].set_xlabel('Water Year', fontsize=11)
    axes[-1].set_xticks([2023, 2024, 2025])
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / 'stake_seasonal_v10.png', dpi=200, bbox_inches='tight')
    print(f"  Saved stake_seasonal_v10.png")
    plt.close()

    # ══════════════════════════════════════════════════════════════════
    # PLOT 4: Glacier-wide annual balance time series (cf. Geck Fig. 8)
    # ══════════════════════════════════════════════════════════════════
    fig, ax = plt.subplots(1, 1, figsize=(12, 5))

    valid_years = []
    for j, yr in enumerate(wy_years):
        if not np.all(np.isnan(gw_balances[:, j])):
            valid_years.append(j)

    years_plot = np.array([wy_years[j] for j in valid_years])
    gw_valid = gw_balances[:, valid_years]

    med = np.nanmedian(gw_valid, axis=0)
    q16 = np.nanpercentile(gw_valid, 16, axis=0)
    q84 = np.nanpercentile(gw_valid, 84, axis=0)
    q05 = np.nanpercentile(gw_valid, 5, axis=0)
    q95 = np.nanpercentile(gw_valid, 95, axis=0)

    ax.fill_between(years_plot, q05, q95, color='steelblue', alpha=0.15, label='5th–95th pctl')
    ax.fill_between(years_plot, q16, q84, color='steelblue', alpha=0.3, label='16th–84th pctl')
    ax.plot(years_plot, med, 'o-', color='steelblue', markersize=4, lw=1.5, label='Median')

    # Geodetic reference
    for _, row in geodetic.iterrows():
        period = row['period']
        start_yr = int(period.split('_')[0][:4])
        end_yr = int(period.split('_')[1][:4])
        mid_yr = (start_yr + end_yr) / 2
        ax.errorbar(mid_yr, row['dmdtda'], yerr=row['err_dmdtda'],
                    fmt='D', color='red', markersize=10, capsize=5, capthick=2,
                    label=f"Geodetic ({period.replace('_', ' to ')[:9]}...)" if start_yr == 2000 and end_yr == 2020 else None,
                    zorder=5)
        # Horizontal span for geodetic period
        ax.hlines(row['dmdtda'], start_yr, end_yr, colors='red', alpha=0.3, lw=2)

    # Mean line
    mean_bal = np.nanmean(med)
    ax.axhline(mean_bal, color='steelblue', ls=':', lw=1, alpha=0.5)
    ax.text(2001.5, mean_bal + 0.1, f'Mean: {mean_bal:+.2f} m w.e./yr', fontsize=9, color='steelblue')

    ax.axhline(0, color='k', lw=0.5, alpha=0.3)
    ax.set_xlabel('Water Year', fontsize=12)
    ax.set_ylabel('Glacier-wide mass balance (m w.e.)', fontsize=12)
    ax.set_title('Dixon Glacier — Modeled Annual Mass Balance (ensemble of 200 parameter sets)', fontsize=13)
    ax.legend(fontsize=10, loc='lower left')
    ax.grid(True, alpha=0.2)
    ax.set_xlim(2000.5, 2025.5)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / 'glacier_wide_balance_v10.png', dpi=200, bbox_inches='tight')
    print(f"  Saved glacier_wide_balance_v10.png")
    plt.close()

    # ══════════════════════════════════════════════════════════════════
    # PLOT 5: Cumulative mass balance (cf. Geck Fig. 10 concept)
    # ══════════════════════════════════════════════════════════════════
    fig, ax = plt.subplots(1, 1, figsize=(12, 5))

    cum_bal = np.nancumsum(gw_valid, axis=1)
    cum_med = np.nanmedian(cum_bal, axis=0)
    cum_q16 = np.nanpercentile(cum_bal, 16, axis=0)
    cum_q84 = np.nanpercentile(cum_bal, 84, axis=0)
    cum_q05 = np.nanpercentile(cum_bal, 5, axis=0)
    cum_q95 = np.nanpercentile(cum_bal, 95, axis=0)

    ax.fill_between(years_plot, cum_q05, cum_q95, color='steelblue', alpha=0.15, label='5th–95th pctl')
    ax.fill_between(years_plot, cum_q16, cum_q84, color='steelblue', alpha=0.3, label='16th–84th pctl')
    ax.plot(years_plot, cum_med, '-', color='steelblue', lw=2, label='Median')

    # Geodetic cumulative for reference (2000-2020 = 20 years × -0.939)
    ax.plot([2001, 2020], [0, 20 * -0.939], 'r--', lw=2, alpha=0.7,
            label=f'Geodetic trend ({-0.939:+.3f} m w.e./yr)')

    ax.axhline(0, color='k', lw=0.5, alpha=0.3)
    ax.set_xlabel('Water Year', fontsize=12)
    ax.set_ylabel('Cumulative mass balance (m w.e.)', fontsize=12)
    ax.set_title('Dixon Glacier — Cumulative Mass Balance 2001–2025', fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.2)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / 'cumulative_balance_v10.png', dpi=200, bbox_inches='tight')
    print(f"  Saved cumulative_balance_v10.png")
    plt.close()

    total = time.time() - t0
    print(f"\nAll plots generated in {total:.0f}s ({total/60:.1f} min)")
    print("Done!")


if __name__ == '__main__':
    main()
