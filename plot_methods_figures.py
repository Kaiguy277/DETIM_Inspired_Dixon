#!/usr/bin/env python3
"""
plot_methods_figures.py — Publication-quality methods figures for Dixon Glacier DETIM thesis.

Styled after Geck et al. (2021) on Eklutna Glacier.
Generates Figures 1-4, 7-8. Figures 5-6 (historical mass balance) require a
separate historical run and are left as placeholders.

Usage:
    python plot_methods_figures.py

Output:
    figures/methods/fig_01_parameter_posterior.{png,pdf}
    figures/methods/fig_02_stake_fit.{png,pdf}
    figures/methods/fig_03_geodetic_validation.{png,pdf}
    figures/methods/fig_04_sensitivity_fixed.{png,pdf}
    figures/methods/fig_07_projection_3ssp.{png,pdf}
    figures/methods/fig_08_lapse_sensitivity_bracket.{png,pdf}
"""

import json
import pathlib
import warnings

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = pathlib.Path("/home/kai/Documents/Opus46Dixon_FirstShot")
OUT = ROOT / "figures" / "methods"
OUT.mkdir(parents=True, exist_ok=True)

# Data files
RANKING_CSV = ROOT / "calibration_output" / "ranking_v13_full.csv"
BEST_PARAMS = ROOT / "calibration_output" / "best_params_v13.json"
STAKE_OBS = ROOT / "stake_observations_dixon.csv"
STAKE_CHECK = ROOT / "validation_output" / "stake_predictive_check.csv"
GEODETIC_VAL = ROOT / "validation_output" / "geodetic_subperiod_validation.csv"
SENSITIVITY = ROOT / "validation_output" / "sensitivity_fixed_params.csv"

PROJ_SSP126 = ROOT / "projection_output" / "PROJ-032_top250_ssp126_2026-04-09" / "projection_ssp126_ensemble_2100.csv"
PROJ_SSP245 = ROOT / "projection_output" / "PROJ-033_top250_ssp245_2026-04-09" / "projection_ssp245_ensemble_2100.csv"
PROJ_SSP585 = ROOT / "projection_output" / "PROJ-034_top250_ssp585_2026-04-09" / "projection_ssp585_ensemble_2100.csv"

def _find_lapse_dir(lapse, ssp):
    """Find the most recent lapse sensitivity projection directory."""
    pattern = f"PROJ-*_lapse{lapse:.1f}_{ssp}_*"
    matches = sorted(ROOT.glob(f"projection_output/{pattern}"))
    return matches[-1] if matches else None

# Build LAPSE_DIRS dynamically to pick up new runs
LAPSE_DIRS = {}
for _lapse in [-4.5, -5.0, -5.5]:
    for _ssp in ["ssp126", "ssp245", "ssp585"]:
        d = _find_lapse_dir(_lapse, _ssp)
        if d is not None:
            LAPSE_DIRS[(_lapse, _ssp)] = d

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
warnings.filterwarnings("ignore", category=UserWarning)
plt.style.use("seaborn-v0_8-whitegrid")
mpl.rcParams.update({
    "font.size": 12,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "legend.fontsize": 10,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "pdf.fonttype": 42,      # TrueType in PDFs (editable text)
    "ps.fonttype": 42,
})

# Color palette — consistent across all figures
SSP_COLORS = {
    "ssp126": "#2166ac",   # blue
    "ssp245": "#f4a582",   # salmon/orange
    "ssp585": "#b2182b",   # red
}
SSP_LABELS = {
    "ssp126": "SSP1-2.6",
    "ssp245": "SSP2-4.5",
    "ssp585": "SSP5-8.5",
}
SITE_COLORS = {
    "ABL": "#d73027",
    "ELA": "#fc8d59",
    "ACC": "#4575b4",
}
LAPSE_COLORS = {
    -4.5: "#e66101",
    -5.0: "#404040",
    -5.5: "#5e3c99",
}

INITIAL_AREA_KM2 = 40.11


def save_fig(fig, name):
    """Save figure as PNG and PDF."""
    fig.savefig(OUT / f"{name}.png")
    fig.savefig(OUT / f"{name}.pdf")
    plt.close(fig)
    print(f"  Saved: {OUT / name}.png/pdf")


# ===================================================================
# Figure 1: Parameter posterior distributions (Geck Fig 4 analog)
# ===================================================================
def fig_01_parameter_posterior():
    print("Generating Figure 1: Parameter posteriors...")

    df = pd.read_csv(RANKING_CSV)
    df_sel = df[df["selected"] == True].head(250).copy()

    with open(BEST_PARAMS) as f:
        best = json.load(f)

    # Parameters to show with display names and units
    params = [
        ("MF", "MF", "mm d$^{-1}$ $^\\circ$C$^{-1}$"),
        ("MF_grad", "MF$_{\\mathrm{grad}}$", "mm d$^{-1}$ $^\\circ$C$^{-1}$ m$^{-1}$"),
        ("r_snow", "$r_{\\mathrm{snow}}$", "mm d$^{-1}$ W$^{-1}$ m$^{2}$ $^\\circ$C$^{-1}$"),
        ("precip_grad", "Precip grad", "m$^{-1}$"),
        ("precip_corr", "Precip corr", "unitless"),
        ("T0", "$T_0$", "$^\\circ$C"),
    ]

    n_params = len(params)
    fig, axes = plt.subplots(n_params, 1, figsize=(8, 1.6 * n_params),
                             gridspec_kw={"hspace": 0.45})

    for ax, (col, label, unit) in zip(axes, params):
        vals = df_sel[col].values

        # Normalize to [0, 1] for horizontal position
        vmin, vmax = vals.min(), vals.max()
        pad = 0.05 * (vmax - vmin) if vmax > vmin else 0.001
        vmin -= pad
        vmax += pad

        # Connected grey lines (draw first, behind dots)
        # Sort by rank to connect parameter sets
        sorted_idx = np.argsort(df_sel["rank"].values)
        sorted_vals = vals[sorted_idx]

        # Strip plot: jitter on y, value on x
        np.random.seed(42)
        jitter = np.random.uniform(-0.3, 0.3, size=len(vals))
        ax.scatter(vals, jitter, s=8, alpha=0.35, color="#636363",
                   edgecolors="none", zorder=2)

        # MAP estimate
        map_val = best[col]
        ax.axvline(map_val, color="#d62728", lw=1.8, ls="--", zorder=3,
                   label="MAP")
        ax.scatter([map_val], [0], s=80, color="#d62728", edgecolors="white",
                   linewidths=1.2, zorder=4, marker="D")

        # Median and 5-95% CI
        p5, p50, p95 = np.percentile(vals, [5, 50, 95])
        ax.axvspan(p5, p95, alpha=0.12, color="#2166ac", zorder=0)
        ax.axvline(p50, color="#2166ac", lw=1.2, ls="-", alpha=0.7, zorder=1)

        ax.set_ylabel("")
        ax.set_yticks([])
        ax.set_xlabel(f"{label}  [{unit}]")
        ax.set_xlim(vmin, vmax)
        ax.set_ylim(-0.6, 0.6)

        # Annotate 5/50/95
        ax.text(p5, 0.55, f"{p5:.4g}", ha="center", va="bottom",
                fontsize=8, color="#2166ac")
        ax.text(p95, 0.55, f"{p95:.4g}", ha="center", va="bottom",
                fontsize=8, color="#2166ac")

    axes[0].set_title("Top-250 posterior parameter distributions (CAL-013)",
                      fontweight="bold")

    # Single legend at top
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    legend_elements = [
        Line2D([0], [0], marker="D", color="#d62728", ls="--", lw=1.5,
               markersize=7, markerfacecolor="#d62728", markeredgecolor="white",
               label="MAP estimate"),
        Patch(facecolor="#2166ac", alpha=0.2, label="5-95% CI"),
    ]
    axes[0].legend(handles=legend_elements, loc="upper right", framealpha=0.9)

    save_fig(fig, "fig_01_parameter_posterior")


# ===================================================================
# Figure 2: Modeled vs Observed stake balances
# ===================================================================
def fig_02_stake_fit():
    print("Generating Figure 2: Stake fit comparison...")

    obs = pd.read_csv(STAKE_OBS)
    obs = obs[obs["period_type"] == "annual"].copy()

    mod = pd.read_csv(STAKE_CHECK)

    # Merge on year + site
    merged = mod.merge(obs[["site_id", "year", "mb_obs_mwe", "mb_obs_uncertainty_mwe"]],
                       left_on=["year", "site"], right_on=["year", "site_id"],
                       how="left")

    sites = ["ABL", "ELA", "ACC"]
    years = sorted(merged["year"].unique())

    fig, ax = plt.subplots(figsize=(10, 5.5))

    bar_width = 0.12
    n_years = len(years)
    group_width = bar_width * 3  # obs, modeled, gap per site

    for i, site in enumerate(sites):
        site_data = merged[merged["site"] == site].sort_values("year")
        for j, (_, row) in enumerate(site_data.iterrows()):
            yr_idx = list(years).index(row["year"])
            x_base = yr_idx * 1.0
            x_obs = x_base + i * 0.25 - 0.25
            x_mod = x_obs + bar_width

            color = SITE_COLORS[site]

            # Observed bar
            ax.bar(x_obs, row["obs_mwe"], width=bar_width,
                   color=color, alpha=0.4, edgecolor=color, linewidth=0.8)
            ax.errorbar(x_obs, row["obs_mwe"],
                        yerr=row["obs_unc"], fmt="none",
                        ecolor="black", capsize=3, capthick=1, zorder=5)

            # Modeled bar
            ax.bar(x_mod, row["mod_median"], width=bar_width,
                   color=color, alpha=0.85, edgecolor="black", linewidth=0.5)
            # Model spread (p5-p95)
            ax.errorbar(x_mod, row["mod_median"],
                        yerr=[[row["mod_median"] - row["mod_p5"]],
                              [row["mod_p95"] - row["mod_median"]]],
                        fmt="none", ecolor="black", capsize=2, capthick=0.8,
                        zorder=5)

            # Mark estimated stakes
            if row["estimated"]:
                ax.text(x_obs, row["obs_mwe"] + (0.15 if row["obs_mwe"] > 0 else -0.25),
                        "*", ha="center", fontsize=14, color="grey")

    # X-axis
    ax.set_xticks([yr_idx * 1.0 for yr_idx in range(n_years)])
    ax.set_xticklabels([str(y) for y in years])
    ax.set_ylabel("Annual mass balance (m w.e.)")
    ax.set_title("Modeled vs observed stake balances", fontweight="bold")
    ax.axhline(0, color="black", lw=0.5)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = []
    for site in sites:
        legend_elements.append(
            Patch(facecolor=SITE_COLORS[site], alpha=0.4,
                  edgecolor=SITE_COLORS[site], label=f"{site} observed"))
        legend_elements.append(
            Patch(facecolor=SITE_COLORS[site], alpha=0.85,
                  edgecolor="black", label=f"{site} modeled"))
    legend_elements.append(
        plt.Line2D([0], [0], marker="*", color="grey", ls="none",
                   markersize=12, label="Estimated obs"))
    ax.legend(handles=legend_elements, loc="lower left", ncol=2,
              framealpha=0.9, fontsize=9)

    fig.tight_layout()
    save_fig(fig, "fig_02_stake_fit")


# ===================================================================
# Figure 3: Geodetic sub-period validation
# ===================================================================
def fig_03_geodetic_validation():
    print("Generating Figure 3: Geodetic sub-period validation...")

    df = pd.read_csv(GEODETIC_VAL)

    # Order: 2000-2010, 2000-2020, 2010-2020
    period_order = ["2000-2010", "2000-2020", "2010-2020"]
    df["period"] = pd.Categorical(df["period"], categories=period_order, ordered=True)
    df = df.sort_values("period")

    fig, ax = plt.subplots(figsize=(7, 5))

    x = np.arange(len(df))
    bar_w = 0.3

    # Observed bars
    obs_bars = ax.bar(x - bar_w / 2, df["obs_dmdtda"], width=bar_w,
                      color="#4575b4", alpha=0.5, edgecolor="#4575b4",
                      label="Observed (Hugonnet)")
    ax.errorbar(x - bar_w / 2, df["obs_dmdtda"], yerr=df["obs_err"],
                fmt="none", ecolor="black", capsize=4, capthick=1.2, zorder=5)

    # Modeled bars
    mod_bars = ax.bar(x + bar_w / 2, df["mod_median"], width=bar_w,
                      color="#d73027", alpha=0.7, edgecolor="#d73027",
                      label="Modeled (median)")
    # Model uncertainty (p5-p95)
    ax.errorbar(x + bar_w / 2, df["mod_median"],
                yerr=[df["mod_median"] - df["mod_p5"],
                      df["mod_p95"] - df["mod_median"]],
                fmt="none", ecolor="black", capsize=3, capthick=0.8, zorder=5)

    # Annotate calibration vs validation
    for i, (_, row) in enumerate(df.iterrows()):
        label_text = "CAL" if row["type"] == "calibration" else "VAL"
        color = "#2166ac" if row["type"] == "calibration" else "#b2182b"
        ax.text(i, 0.05, label_text, ha="center", va="bottom",
                fontsize=10, fontweight="bold", color=color,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                          edgecolor=color, alpha=0.8))

    ax.set_xticks(x)
    ax.set_xticklabels(df["period"].values)
    ax.set_ylabel("$\\dot{m}$ (m w.e. yr$^{-1}$)")
    ax.set_title("Geodetic mass balance: sub-period validation", fontweight="bold")
    ax.axhline(0, color="black", lw=0.5)
    ax.legend(loc="lower left", framealpha=0.9)

    fig.tight_layout()
    save_fig(fig, "fig_03_geodetic_validation")


# ===================================================================
# Figure 4: Sensitivity of fixed parameters (two panels)
# ===================================================================
def fig_04_sensitivity_fixed():
    print("Generating Figure 4: Fixed parameter sensitivity...")

    df = pd.read_csv(SENSITIVITY)
    df_lapse = df[df["parameter"] == "lapse_rate"].copy()
    df_rice = df[df["parameter"] == "rice_ratio"].copy()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # --- Panel a: Lapse rate ---
    color_bias = "#2166ac"
    color_rmse = "#d73027"

    ln1 = ax1.plot(df_lapse["value"], df_lapse["geodetic_bias"],
                   "o-", color=color_bias, lw=2, markersize=7,
                   label="Geodetic bias (m w.e. yr$^{-1}$)")
    ax1.set_xlabel("Lapse rate ($^\\circ$C km$^{-1}$)")
    ax1.set_ylabel("Geodetic bias (m w.e. yr$^{-1}$)", color=color_bias)
    ax1.tick_params(axis="y", labelcolor=color_bias)
    ax1.axhline(0, color=color_bias, ls=":", lw=0.8, alpha=0.5)

    ax1b = ax1.twinx()
    ln2 = ax1b.plot(df_lapse["value"], df_lapse["stake_rmse"],
                    "s--", color=color_rmse, lw=2, markersize=7,
                    label="Stake RMSE (m w.e.)")
    ax1b.set_ylabel("Stake RMSE (m w.e.)", color=color_rmse)
    ax1b.tick_params(axis="y", labelcolor=color_rmse)

    # Highlight chosen value (-5.0)
    ax1.axvline(-5.0, color="#404040", ls="--", lw=1.5, alpha=0.6)
    ax1.text(-5.0, ax1.get_ylim()[1] * 0.9, "chosen\n$-5.0$",
             ha="center", va="top", fontsize=9, color="#404040",
             bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                       edgecolor="#404040", alpha=0.8))

    # Combined legend
    lns = ln1 + ln2
    labs = [l.get_label() for l in lns]
    ax1.legend(lns, labs, loc="upper left", fontsize=9, framealpha=0.9)
    ax1.set_title("(a) Lapse rate sensitivity", fontweight="bold")

    # --- Panel b: r_ice/r_snow ratio ---
    ln3 = ax2.plot(df_rice["value"], df_rice["geodetic_bias"],
                   "o-", color=color_bias, lw=2, markersize=7,
                   label="Geodetic bias")
    ax2.set_xlabel("$r_{ice}$ / $r_{snow}$ ratio")
    ax2.set_ylabel("Geodetic bias (m w.e. yr$^{-1}$)", color=color_bias)
    ax2.tick_params(axis="y", labelcolor=color_bias)
    ax2.axhline(0, color=color_bias, ls=":", lw=0.8, alpha=0.5)

    ax2b = ax2.twinx()
    ln4 = ax2b.plot(df_rice["value"], df_rice["stake_rmse"],
                    "s--", color=color_rmse, lw=2, markersize=7,
                    label="Stake RMSE")
    ax2b.set_ylabel("Stake RMSE (m w.e.)", color=color_rmse)
    ax2b.tick_params(axis="y", labelcolor=color_rmse)

    # Highlight chosen value (2.0)
    ax2.axvline(2.0, color="#404040", ls="--", lw=1.5, alpha=0.6)
    ax2.text(2.0, ax2.get_ylim()[1] * 0.9, "chosen\n$2.0$",
             ha="center", va="top", fontsize=9, color="#404040",
             bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                       edgecolor="#404040", alpha=0.8))

    lns = ln3 + ln4
    labs = [l.get_label() for l in lns]
    ax2.legend(lns, labs, loc="upper left", fontsize=9, framealpha=0.9)
    ax2.set_title("(b) $r_{ice}/r_{snow}$ ratio sensitivity", fontweight="bold")

    fig.tight_layout()
    save_fig(fig, "fig_04_sensitivity_fixed")


# ===================================================================
# Figure 5: Historical mass balance reconstruction — PLACEHOLDER
# ===================================================================
def fig_05_historical_mb():
    """Historical winter, summer, and annual mass balance (Geck Fig 8 analog)."""
    hist_path = ROOT / "validation_output" / "historical_ensemble.csv"
    if not hist_path.exists():
        print("Figure 5: SKIPPED — run run_historical_ensemble.py first")
        return

    df = pd.read_csv(hist_path)
    summary = df.groupby("water_year").agg(
        Bw_mean=("winter_balance", "mean"), Bw_std=("winter_balance", "std"),
        Bs_mean=("summer_balance", "mean"), Bs_std=("summer_balance", "std"),
        Ba_mean=("annual_balance", "mean"), Ba_std=("annual_balance", "std"),
    ).reset_index()
    years = summary["water_year"].values

    fig, ax = plt.subplots(figsize=(12, 5))

    bar_w = 0.35
    # Winter bars (positive, blue)
    ax.bar(years - bar_w / 2, summary["Bw_mean"], bar_w,
           yerr=summary["Bw_std"], capsize=2, color="#4393c3", alpha=0.85,
           label="Winter ($B_w$)", error_kw={"lw": 0.8, "color": "0.4"})
    # Summer bars (negative, red)
    ax.bar(years + bar_w / 2, summary["Bs_mean"], bar_w,
           yerr=summary["Bs_std"], capsize=2, color="#d6604d", alpha=0.85,
           label="Summer ($B_s$)", error_kw={"lw": 0.8, "color": "0.4"})
    # Annual line
    ax.errorbar(years, summary["Ba_mean"], yerr=summary["Ba_std"],
                fmt="ko-", ms=4, lw=1.5, capsize=3, capthick=1,
                label="Annual ($B_a$)", zorder=5)

    ax.axhline(0, color="k", lw=0.5)
    ax.set_xlabel("Water year")
    ax.set_ylabel("Mass balance (m w.e.)")
    ax.set_title("Modeled winter, summer, and annual mass balance (1999–2025)")
    ax.legend(loc="lower left", ncol=3)
    ax.set_xlim(years[0] - 0.8, years[-1] + 0.8)

    # Annotate period mean
    mean_ba = summary["Ba_mean"].mean()
    ax.axhline(mean_ba, color="k", ls="--", lw=0.8, alpha=0.5)
    ax.text(years[-1] + 0.3, mean_ba, f"mean = {mean_ba:.2f}",
            va="bottom", fontsize=9, color="0.3")

    save_fig(fig, "fig_05_historical_mb")


# ===================================================================
# Figure 6: Mass balance trends (Geck Fig 9 analog)
# ===================================================================
def fig_06_mb_trends():
    """Annual, summer, and winter balance trends with significance."""
    from scipy.stats import linregress

    hist_path = ROOT / "validation_output" / "historical_ensemble.csv"
    if not hist_path.exists():
        print("Figure 6: SKIPPED — run run_historical_ensemble.py first")
        return

    df = pd.read_csv(hist_path)
    summary = df.groupby("water_year").agg(
        Bw_mean=("winter_balance", "mean"), Bw_std=("winter_balance", "std"),
        Bs_mean=("summer_balance", "mean"), Bs_std=("summer_balance", "std"),
        Ba_mean=("annual_balance", "mean"), Ba_std=("annual_balance", "std"),
    ).reset_index()
    years = summary["water_year"].values

    fig, ax = plt.subplots(figsize=(12, 5.5))

    components = [
        ("Bw_mean", "Bw_std", "#4393c3", "Winter", "o"),
        ("Ba_mean", "Ba_std", "k",       "Annual", "s"),
        ("Bs_mean", "Bs_std", "#d6604d", "Summer", "^"),
    ]

    for col, std_col, color, label, marker in components:
        y = summary[col].values
        y_std = summary[std_col].values
        ax.fill_between(years, y - y_std, y + y_std, color=color, alpha=0.15)
        ax.plot(years, y, marker=marker, ms=5, color=color, lw=1.2,
                label=label, zorder=4)

        # Trend
        res = linregress(years, y)
        trend_line = res.slope * years + res.intercept
        ax.plot(years, trend_line, "--", color=color, lw=1.5, alpha=0.7)

        # Annotate
        p_str = f"p={res.pvalue:.3f}" if res.pvalue >= 0.001 else f"p<0.001"
        slope_decade = res.slope * 10
        ax.text(years[-1] + 0.5, trend_line[-1],
                f"{label}: {slope_decade:+.2f} m w.e. decade⁻¹\n{p_str}",
                fontsize=9, color=color, va="center")

    ax.axhline(0, color="k", lw=0.5)
    ax.set_xlabel("Water year")
    ax.set_ylabel("Mass balance (m w.e.)")
    ax.set_title("Mass balance trends (1999–2025)")
    ax.legend(loc="upper left", ncol=3)
    ax.set_xlim(years[0] - 0.5, years[-1] + 5)

    save_fig(fig, "fig_06_mb_trends")


# ===================================================================
# Figure 7: Projection ensemble — 3 SSPs
# ===================================================================
def fig_07_projection_3ssp():
    print("Generating Figure 7: Projection ensemble (3 SSPs) with historical...")

    ssp_files = {
        "ssp126": PROJ_SSP126,
        "ssp245": PROJ_SSP245,
        "ssp585": PROJ_SSP585,
    }

    fig, ax = plt.subplots(figsize=(12, 6.5))

    # --- Plot full model trajectory (2001-2100) for each SSP ---
    # The ensemble CSVs now contain historical (2001-2025) + projection (2026-2100)
    # The historical period is identical across SSPs (same observed climate)
    for ssp, fpath in ssp_files.items():
        if not fpath.exists():
            print(f"  WARNING: {fpath.name} not found, skipping {ssp}")
            continue
        df = pd.read_csv(fpath)
        yr = df["year"]

        ax.plot(yr, df["area_km2_p50"], color=SSP_COLORS[ssp], lw=2,
                label=SSP_LABELS[ssp])
        ax.fill_between(yr, df["area_km2_p05"], df["area_km2_p95"],
                        color=SSP_COLORS[ssp], alpha=0.15)
        ax.fill_between(yr, df["area_km2_p25"], df["area_km2_p75"],
                        color=SSP_COLORS[ssp], alpha=0.25)

    # --- Observed outlines as validation points ---
    outline_years = [2000, 2005, 2010, 2015, 2020, 2025]
    outline_areas = [40.11, 40.11, 39.83, 39.26, 38.59, 38.34]
    ax.plot(outline_years, outline_areas, "ko", ms=8, zorder=10,
            label="Observed (digitized outlines)")

    # Vertical line at GCM divergence point
    ax.axvline(2025, color="0.5", ls="--", lw=1, alpha=0.5)
    ax.text(2025.5, ax.get_ylim()[1] * 0.98 if ax.get_ylim()[1] > 35 else 39,
            "GCM scenarios\ndiverge",
            ha="left", va="top", fontsize=9, color="0.5", style="italic")

    ax.set_xlabel("Year")
    ax.set_ylabel("Glacier area (km$^2$)")
    ax.set_title("Dixon Glacier area: observations (2000–2025) and projections (2026–2100)",
                 fontweight="bold")
    ax.set_xlim(1999, 2101)
    ax.legend(loc="lower left", framealpha=0.9)

    ax.xaxis.set_minor_locator(mticker.MultipleLocator(5))
    ax.yaxis.set_minor_locator(mticker.AutoMinorLocator())
    ax.grid(which="minor", alpha=0.3, ls=":")

    fig.tight_layout()
    save_fig(fig, "fig_07_projection_3ssp")


# ===================================================================
# Figure 8: Lapse rate sensitivity bracket (2 panels)
# ===================================================================
def fig_08_lapse_sensitivity():
    print("Generating Figure 8: Lapse rate sensitivity bracket...")

    # Determine which SSPs have lapse data
    available_ssps = sorted(set(ssp for (_, ssp) in LAPSE_DIRS.keys()))
    n_panels = len(available_ssps)
    if n_panels == 0:
        print("  No lapse sensitivity data found, skipping")
        return

    fig, axes = plt.subplots(1, n_panels, figsize=(5.5 * n_panels, 5.5), sharey=True,
                              squeeze=False)
    axes = axes[0]

    for i, ssp in enumerate(available_ssps):
        ax = axes[i]
        for lapse in [-4.5, -5.0, -5.5]:
            key = (lapse, ssp)
            proj_dir = LAPSE_DIRS.get(key)
            if proj_dir is None:
                continue
            csv_file = proj_dir / f"projection_{ssp}_ensemble_2100.csv"
            if not csv_file.exists():
                print(f"  WARNING: {csv_file} not found, skipping")
                continue

            df = pd.read_csv(csv_file)
            yr = df["year"]
            color = LAPSE_COLORS[lapse]
            label = f"$\\Gamma$ = {lapse} $^\\circ$C km$^{{-1}}$"

            ax.plot(yr, df["area_km2_p50"], color=color, lw=2, label=label)
            ax.fill_between(yr, df["area_km2_p05"], df["area_km2_p95"],
                            color=color, alpha=0.15)
            ax.fill_between(yr, df["area_km2_p25"], df["area_km2_p75"],
                            color=color, alpha=0.22)

        ax.axhline(INITIAL_AREA_KM2, color="black", ls=":", lw=1, alpha=0.6)
        ax.set_xlabel("Year")
        ax.set_title(f"{SSP_LABELS.get(ssp, ssp)}", fontweight="bold")
        ax.set_xlim(2026, 2100)
        ax.legend(loc="lower left", fontsize=9, framealpha=0.9)
        ax.xaxis.set_minor_locator(mticker.MultipleLocator(5))
        ax.yaxis.set_minor_locator(mticker.AutoMinorLocator())
        ax.grid(which="minor", alpha=0.3, ls=":")

    axes[0].set_ylabel("Glacier area (km$^2$)")
    fig.suptitle("Lapse rate sensitivity: projected glacier area",
                 fontweight="bold", y=1.01)
    fig.tight_layout()
    save_fig(fig, "fig_08_lapse_sensitivity_bracket")


# ===================================================================
# Main
# ===================================================================
if __name__ == "__main__":
    print(f"Output directory: {OUT}\n")

    fig_01_parameter_posterior()
    fig_02_stake_fit()
    fig_03_geodetic_validation()
    fig_04_sensitivity_fixed()
    fig_05_historical_mb()
    fig_06_mb_trends()
    fig_07_projection_3ssp()
    fig_08_lapse_sensitivity()

    print(f"\nDone. All figures saved to {OUT}/")
