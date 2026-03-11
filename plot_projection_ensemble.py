"""
Plot projection ensemble results with uncertainty bands.

Reads ensemble CSVs from a PROJ-### run directory and creates:
  1. Area + volume evolution (dual y-axis, both scenarios)
  2. Mass balance time series
  3. Discharge + peak water analysis
  4. Per-GCM comparison panel

Usage:
    python plot_projection_ensemble.py projection_output/PROJ-002_top250-params_2026-03-11/
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path
import json
import sys


# Scenario colors and labels
SSP_STYLE = {
    'ssp245': {'color': '#1b9e77', 'label': 'SSP2-4.5'},
    'ssp585': {'color': '#d95f02', 'label': 'SSP5-8.5'},
    'ssp126': {'color': '#7570b3', 'label': 'SSP1-2.6'},
}

GCM_COLORS = {
    'ACCESS-CM2': '#e41a1c',
    'EC-Earth3': '#377eb8',
    'MPI-ESM1-2-HR': '#4daf4a',
    'MRI-ESM2-0': '#984ea3',
    'NorESM2-MM': '#ff7f00',
}


def load_run(run_dir):
    """Load all ensemble CSVs and metadata from a run directory."""
    run_dir = Path(run_dir)
    data = {}
    for f in sorted(run_dir.glob('projection_*_ensemble_*.csv')):
        ssp = f.stem.split('_')[1]  # e.g. 'ssp245'
        data[ssp] = pd.read_csv(f)

    # Load per-GCM files
    gcm_data = {}
    for f in sorted(run_dir.glob('projection_*_2100.csv')):
        parts = f.stem.split('_')
        if 'ensemble' in parts or 'meta' in parts:
            continue
        ssp = parts[1]
        gcm = '_'.join(parts[2:-1])  # handle hyphenated GCM names
        if ssp not in gcm_data:
            gcm_data[ssp] = {}
        gcm_data[ssp][gcm] = pd.read_csv(f)

    # Load metadata
    meta = {}
    for f in run_dir.glob('*_meta_*.json'):
        ssp = f.stem.split('_')[1]
        with open(f) as fh:
            meta[ssp] = json.load(fh)

    # Load peak water
    peak_water = {}
    for f in run_dir.glob('peak_water_*.json'):
        ssp = f.stem.split('_')[-1]
        with open(f) as fh:
            peak_water[ssp] = json.load(fh)

    return data, gcm_data, meta, peak_water


def plot_area_volume(data, meta, run_dir):
    """Plot glacier area and volume evolution with uncertainty bands."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    for ssp, df in data.items():
        style = SSP_STYLE.get(ssp, {'color': 'gray', 'label': ssp})
        c = style['color']
        label = style['label']
        years = df['year']

        # Area
        ax1.plot(years, df['area_km2_p50'], color=c, lw=2, label=label)
        ax1.fill_between(years, df['area_km2_p05'], df['area_km2_p95'],
                         color=c, alpha=0.15, label=f'{label} 5–95%')
        ax1.fill_between(years, df['area_km2_p25'], df['area_km2_p75'],
                         color=c, alpha=0.25)

        # Volume
        ax2.plot(years, df['volume_km3_p50'], color=c, lw=2, label=label)
        ax2.fill_between(years, df['volume_km3_p05'], df['volume_km3_p95'],
                         color=c, alpha=0.15)
        ax2.fill_between(years, df['volume_km3_p25'], df['volume_km3_p75'],
                         color=c, alpha=0.25)

    # Initial conditions
    m = list(meta.values())[0] if meta else {}
    a0 = m.get('initial_area_km2', 0)
    v0 = m.get('initial_volume_km3', 0)

    ax1.axhline(a0, color='k', ls='--', lw=0.8, alpha=0.5)
    ax1.set_ylabel('Glacier Area (km²)')
    ax1.set_title(f'Dixon Glacier — Area & Volume Projections\n'
                  f'{m.get("n_param_samples", "?")} param sets × '
                  f'{m.get("n_total_runs", "?")//max(m.get("n_param_samples",1),1)} GCMs '
                  f'= {m.get("n_total_runs", "?")} runs per scenario')
    ax1.legend(loc='upper right', fontsize=9, ncol=2)
    ax1.grid(True, alpha=0.3)

    ax2.axhline(v0, color='k', ls='--', lw=0.8, alpha=0.5)
    ax2.set_ylabel('Ice Volume (km³)')
    ax2.set_xlabel('Water Year')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    out = run_dir / 'area_volume_projections.png'
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {out.name}")


def plot_mass_balance(data, run_dir):
    """Plot glacier-wide mass balance time series."""
    fig, ax = plt.subplots(figsize=(12, 5))

    for ssp, df in data.items():
        style = SSP_STYLE.get(ssp, {'color': 'gray', 'label': ssp})
        c = style['color']
        years = df['year']

        ax.plot(years, df['glacier_wide_balance_p50'], color=c, lw=2,
                label=style['label'])
        ax.fill_between(years, df['glacier_wide_balance_p05'],
                        df['glacier_wide_balance_p95'],
                        color=c, alpha=0.15)
        ax.fill_between(years, df['glacier_wide_balance_p25'],
                        df['glacier_wide_balance_p75'],
                        color=c, alpha=0.25)

    ax.axhline(0, color='k', ls='-', lw=0.5)
    ax.set_ylabel('Glacier-Wide Balance (m w.e. yr⁻¹)')
    ax.set_xlabel('Water Year')
    ax.set_title('Dixon Glacier — Annual Mass Balance Projections')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = run_dir / 'mass_balance_projections.png'
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {out.name}")


def plot_discharge(data, peak_water, run_dir):
    """Plot mean annual discharge with peak water markers."""
    fig, ax = plt.subplots(figsize=(12, 5))

    for ssp, df in data.items():
        style = SSP_STYLE.get(ssp, {'color': 'gray', 'label': ssp})
        c = style['color']
        years = df['year']

        ax.plot(years, df['mean_annual_discharge_m3s_p50'], color=c, lw=2,
                label=style['label'])
        ax.fill_between(years, df['mean_annual_discharge_m3s_p05'],
                        df['mean_annual_discharge_m3s_p95'],
                        color=c, alpha=0.15)
        ax.fill_between(years, df['mean_annual_discharge_m3s_p25'],
                        df['mean_annual_discharge_m3s_p75'],
                        color=c, alpha=0.25)

        # Peak water marker
        if ssp in peak_water:
            pw = peak_water[ssp]
            ax.axvline(pw['peak_year'], color=c, ls=':', lw=1.5, alpha=0.7)
            ax.annotate(f"Peak ~{pw['peak_year']}",
                        xy=(pw['peak_year'], pw['peak_discharge_m3s']),
                        xytext=(10, 15), textcoords='offset points',
                        fontsize=9, color=c, fontweight='bold',
                        arrowprops=dict(arrowstyle='->', color=c, lw=1.2))

    ax.set_ylabel('Mean Annual Discharge (m³/s)')
    ax.set_xlabel('Water Year')
    ax.set_title('Dixon Glacier — Discharge Projections & Peak Water')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = run_dir / 'discharge_peak_water.png'
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {out.name}")


def plot_gcm_comparison(gcm_data, meta, run_dir):
    """Plot per-GCM area trajectories for each scenario."""
    scenarios = list(gcm_data.keys())
    n_ssp = len(scenarios)
    if n_ssp == 0:
        return

    fig, axes = plt.subplots(1, n_ssp, figsize=(7 * n_ssp, 5), sharey=True,
                             squeeze=False)

    for i, ssp in enumerate(scenarios):
        ax = axes[0, i]
        style = SSP_STYLE.get(ssp, {'color': 'gray', 'label': ssp})

        for gcm, df in gcm_data[ssp].items():
            gc = GCM_COLORS.get(gcm, 'gray')
            years = df['year']
            ax.plot(years, df['area_km2_p50'], color=gc, lw=1.8, label=gcm)
            ax.fill_between(years, df['area_km2_p25'], df['area_km2_p75'],
                            color=gc, alpha=0.12)

        m = meta.get(ssp, {})
        a0 = m.get('initial_area_km2', 0)
        ax.axhline(a0, color='k', ls='--', lw=0.8, alpha=0.5)
        ax.set_title(f"{style['label']}", fontsize=13, fontweight='bold')
        ax.set_xlabel('Water Year')
        ax.grid(True, alpha=0.3)
        if i == 0:
            ax.set_ylabel('Glacier Area (km²)')
        ax.legend(fontsize=8, loc='lower left')

    fig.suptitle('Dixon Glacier — Per-GCM Area Projections\n'
                 '(median with 25–75% band from parameter uncertainty)',
                 fontsize=13, y=1.02)
    plt.tight_layout()
    out = run_dir / 'gcm_comparison.png'
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {out.name}")


def plot_peak_discharge(gcm_data, run_dir):
    """Plot peak daily discharge for each scenario."""
    scenarios = list(gcm_data.keys())
    n_ssp = len(scenarios)
    if n_ssp == 0:
        return

    fig, axes = plt.subplots(1, n_ssp, figsize=(7 * n_ssp, 5), sharey=True,
                             squeeze=False)

    for i, ssp in enumerate(scenarios):
        ax = axes[0, i]
        style = SSP_STYLE.get(ssp, {'color': 'gray', 'label': ssp})

        for gcm, df in gcm_data[ssp].items():
            gc = GCM_COLORS.get(gcm, 'gray')
            years = df['year']
            ax.plot(years, df['peak_daily_discharge_m3s_p50'], color=gc,
                    lw=1.5, label=gcm, alpha=0.8)

        ax.set_title(f"{style['label']}", fontsize=13, fontweight='bold')
        ax.set_xlabel('Water Year')
        ax.grid(True, alpha=0.3)
        if i == 0:
            ax.set_ylabel('Peak Daily Discharge (m³/s)')
        ax.legend(fontsize=8, loc='upper right')

    fig.suptitle('Dixon Glacier — Peak Daily Discharge by GCM', fontsize=13,
                 y=1.02)
    plt.tight_layout()
    out = run_dir / 'peak_discharge_gcm.png'
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {out.name}")


def main():
    if len(sys.argv) < 2:
        # Default to most recent PROJ-### folder
        base = Path('projection_output')
        dirs = sorted([d for d in base.iterdir()
                       if d.is_dir() and d.name.startswith('PROJ-')])
        if not dirs:
            print("Usage: python plot_projection_ensemble.py <run_dir>")
            sys.exit(1)
        run_dir = dirs[-1]
    else:
        run_dir = Path(sys.argv[1])

    print(f"Plotting: {run_dir.name}")
    data, gcm_data, meta, peak_water = load_run(run_dir)

    if not data:
        print("  No ensemble CSVs found!")
        sys.exit(1)

    print(f"  Scenarios: {list(data.keys())}")

    plot_area_volume(data, meta, run_dir)
    plot_mass_balance(data, run_dir)
    plot_discharge(data, peak_water, run_dir)
    plot_gcm_comparison(gcm_data, meta, run_dir)
    plot_peak_discharge(gcm_data, run_dir)

    print(f"\nAll plots saved to {run_dir}/")


if __name__ == '__main__':
    main()
