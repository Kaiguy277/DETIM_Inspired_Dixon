#!/usr/bin/env python3
"""
Build the methods_interactive.html file with all figures embedded as base64.

Structure:
  Chapter 3 — Methods (how the work was done)
  Chapter 4 — Results (what happened)
  Decision Log (D-001 through D-031)
"""
import base64
import csv
import glob
import io
import json
import os
import re

ROOT = "/home/kai/Documents/Opus46Dixon_FirstShot"

# ── Load all figures as base64 ──────────────────────────────────────
def load_fig_b64(fig_num):
    pattern = os.path.join(ROOT, f"figures/methods/fig_{fig_num:02d}_*.png")
    matches = glob.glob(pattern)
    if not matches:
        return ""
    with open(matches[0], "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")

print("Loading figures...")
FIGS = {}
for i in range(1, 13):
    FIGS[i] = load_fig_b64(i)
    print(f"  fig_{i:02d}: {len(FIGS[i]):,} chars")

# ── Load data files ─────────────────────────────────────────────────
print("Loading data files...")

with open(os.path.join(ROOT, "calibration_output/calibration_summary_v13.json")) as f:
    cal_summary = json.load(f)

with open(os.path.join(ROOT, "calibration_output/best_params_v13.json")) as f:
    best_params = json.load(f)

with open(os.path.join(ROOT, "stake_observations_dixon.csv")) as f:
    stake_csv = f.read()

with open(os.path.join(ROOT, "geodedic_mb/dixon_glacier_hugonnet.csv")) as f:
    geodetic_csv = f.read()

with open(os.path.join(ROOT, "validation_output/geodetic_subperiod_validation.csv")) as f:
    geod_val_csv = f.read()

with open(os.path.join(ROOT, "validation_output/stake_predictive_check.csv")) as f:
    stake_val_csv = f.read()

with open(os.path.join(ROOT, "validation_output/sensitivity_fixed_params.csv")) as f:
    sens_csv = f.read()

with open(os.path.join(ROOT, "validation_output/lapse_sensitivity_projections.csv")) as f:
    lapse_proj_csv = f.read()

# Load projection metadata
proj_meta = {}
peak_water = {}
proj_eoc = {}  # end of century

for ssp, proj_dir in [
    ("ssp126", "PROJ-027_top1000_ssp126_2026-04-09"),
    ("ssp245", "PROJ-009_top250_ssp245_2026-03-23"),
    ("ssp585", "PROJ-011_top250_ssp585_2026-03-23"),
]:
    meta_path = os.path.join(ROOT, f"projection_output/{proj_dir}/projection_{ssp}_meta_2100.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            proj_meta[ssp] = json.load(f)

    pw_path = os.path.join(ROOT, f"projection_output/{proj_dir}/peak_water_{ssp}.json")
    if os.path.exists(pw_path):
        with open(pw_path) as f:
            peak_water[ssp] = json.load(f)

    ens_path = os.path.join(ROOT, f"projection_output/{proj_dir}/projection_{ssp}_ensemble_2100.csv")
    if os.path.exists(ens_path):
        with open(ens_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                proj_eoc[ssp] = row  # last row (there's only one)

# Load historical ensemble for trend stats
hist_path = os.path.join(ROOT, "validation_output/historical_ensemble.csv")
hist_data = None
if os.path.exists(hist_path):
    with open(hist_path) as f:
        hist_data = list(csv.DictReader(f))
    print(f"  Historical ensemble: {len(hist_data)} years")

# Parse lapse sensitivity CSV
lapse_rows = []
for line in lapse_proj_csv.strip().split("\n")[1:]:
    parts = line.split(",")
    lapse_rows.append({
        "lapse": parts[0],
        "scenario": parts[1],
        "area_p50": parts[2],
        "area_p05": parts[3],
        "area_p95": parts[4],
        "volume_p50": parts[5],
        "peak_year": parts[6],
        "peak_q": parts[7],
    })

# Parse stake predictive check CSV
stake_val_rows = []
for line in stake_val_csv.strip().split("\n")[1:]:
    parts = line.split(",")
    stake_val_rows.append({
        "year": parts[0],
        "site": parts[1],
        "elevation": parts[2],
        "obs": parts[3],
        "obs_unc": parts[4],
        "estimated": parts[5],
        "mod_median": parts[6],
        "mod_p5": parts[7],
        "mod_p95": parts[8],
        "residual": parts[9],
    })

# Parse geodetic subperiod CSV
geod_val_rows = []
for line in geod_val_csv.strip().split("\n")[1:]:
    parts = line.split(",")
    geod_val_rows.append({
        "period": parts[0],
        "type": parts[1],
        "obs": parts[2],
        "obs_err": parts[3],
        "mod_median": parts[4],
        "mod_p5": parts[5],
        "mod_p95": parts[6],
        "bias": parts[7],
        "within_unc": parts[8],
    })

# Parse sensitivity CSV
sens_rows = []
for line in sens_csv.strip().split("\n")[1:]:
    parts = line.split(",")
    sens_rows.append({
        "param": parts[0],
        "value": parts[1],
        "geodetic_mod": parts[3],
        "geodetic_obs": parts[4],
        "geodetic_bias": parts[5],
        "stake_rmse": parts[6],
    })

# ── Load decisions.md ───────────────────────────────────────────────
print("Loading decisions...")
with open(os.path.join(ROOT, "research_log/decisions.md")) as f:
    decisions_raw = f.read()

# Parse decisions into individual entries
decisions = {}
parts = re.split(r'^## (D-\d{3}:.+)$', decisions_raw, flags=re.MULTILINE)
for i in range(1, len(parts), 2):
    header = parts[i].strip()
    body = parts[i+1].strip() if i+1 < len(parts) else ""
    m = re.match(r'(D-\d{3})', header)
    if m:
        d_id = m.group(1)
        decisions[d_id] = {"header": header, "body": body}

print(f"  Found {len(decisions)} decisions")

# ── Helper: escape HTML ─────────────────────────────────────────────
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def md_to_html_simple(text):
    """Very basic markdown-to-HTML for decision bodies."""
    lines = text.split("\n")
    html_lines = []
    in_table = False
    in_code = False
    for line in lines:
        stripped = line.strip()
        # Code blocks
        if stripped.startswith("```"):
            if in_code:
                html_lines.append("</pre>")
                in_code = False
            else:
                html_lines.append('<pre class="code-block">')
                in_code = True
            continue
        if in_code:
            html_lines.append(esc(line))
            continue
        # Table rows
        if "|" in stripped and stripped.startswith("|"):
            cols = [c.strip() for c in stripped.split("|")[1:-1]]
            if all(set(c) <= set("- :") for c in cols):
                continue  # separator row
            if not in_table:
                html_lines.append('<table class="data-table"><tbody>')
                in_table = True
            cells = "".join(f"<td>{esc(c)}</td>" for c in cols)
            html_lines.append(f"<tr>{cells}</tr>")
            continue
        if in_table:
            html_lines.append("</tbody></table>")
            in_table = False
        # Bold
        processed = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', esc(stripped))
        # Inline code
        processed = re.sub(r'`([^`]+)`', r'<code>\1</code>', processed)
        # Headers within decision
        if stripped.startswith("---"):
            continue
        if not stripped:
            html_lines.append("<br>")
        elif stripped.startswith("- "):
            html_lines.append(f'<div class="decision-bullet">{processed[2:]}</div>')
        elif stripped.startswith("  - "):
            html_lines.append(f'<div class="decision-subbullet">{processed[4:]}</div>')
        else:
            html_lines.append(f"<p>{processed}</p>")
    if in_table:
        html_lines.append("</tbody></table>")
    if in_code:
        html_lines.append("</pre>")
    return "\n".join(html_lines)


# ── Build decision log HTML ──────────────────────────────────────────
def build_decision_log():
    items = []
    for d_id in sorted(decisions.keys(), key=lambda x: int(x.split("-")[1])):
        d = decisions[d_id]
        title = esc(d["header"])
        body_html = md_to_html_simple(d["body"])
        items.append(f'''
        <div class="decision-item">
          <button class="decision-toggle" onclick="toggleDecision(this)">
            <span class="decision-id">{d_id}</span>
            <span class="decision-title">{title.replace(d_id + ": ", "")}</span>
            <span class="toggle-icon">+</span>
          </button>
          <div class="decision-body">
            {body_html}
          </div>
        </div>''')
    return "\n".join(items)


# ── Build stake observations table ──────────────────────────────────
def build_stake_table():
    rows = []
    for line in stake_csv.strip().split("\n")[1:]:
        parts = line.split(",")
        site, ptype, year = parts[0], parts[1], parts[2]
        mb = float(parts[5])
        unc = float(parts[6])
        elev = float(parts[8])
        est = "est." if "stim" in parts[9].lower() else ""
        rows.append(f"<tr><td>{site}</td><td>{ptype}</td><td>{year}</td>"
                    f"<td>{mb:+.2f}</td><td>&plusmn;{unc:.2f}</td>"
                    f"<td>{elev:.0f}</td><td>{est}</td></tr>")
    return "\n".join(rows)


# ── Build geodetic table ────────────────────────────────────────────
def build_geodetic_table():
    rows = []
    for line in geodetic_csv.strip().split("\n")[1:]:
        parts = line.split(",")
        period = parts[1]
        dmdtda = float(parts[9])
        err = float(parts[10])
        rows.append(f"<tr><td>{period}</td><td>{dmdtda:+.3f}</td><td>&plusmn;{err:.3f}</td></tr>")
    return "\n".join(rows)


def fig_tag(num, caption, width="100%"):
    """Generate an image tag with lightbox support."""
    return f'''
    <div class="figure-container">
      <img src="data:image/png;base64,{FIGS[num]}" alt="{esc(caption)}"
           class="figure-img" onclick="openLightbox(this)" style="width:{width}">
      <div class="figure-caption">Figure {num}. {esc(caption)}</div>
    </div>'''


# ── Extract calibration stats ───────────────────────────────────────
mcmc = cal_summary["mcmc_chains"][0]
de = cal_summary["de"]
acceptance = mcmc["acceptance_fraction"]
n_samples = mcmc["n_samples"]
n_walkers = mcmc["n_walkers"]
n_steps = mcmc["n_steps"]
n_seeds = de["n_seeds"]
n_modes = de["n_modes"]

# DE cost range
de_costs = [o["cost"] for o in de["optima"]]
de_cost_min = min(de_costs)
de_cost_max = max(de_costs)

# ── Extract projection end-of-century values ────────────────────────
def eoc_area(ssp):
    if ssp in proj_eoc:
        r = proj_eoc[ssp]
        return (float(r["area_km2_p50"]), float(r["area_km2_p05"]), float(r["area_km2_p95"]))
    return (0, 0, 0)

def eoc_volume(ssp):
    if ssp in proj_eoc:
        r = proj_eoc[ssp]
        return (float(r["volume_km3_p50"]), float(r["volume_km3_p05"]), float(r["volume_km3_p95"]))
    return (0, 0, 0)

ssp126_area = eoc_area("ssp126")
ssp245_area = eoc_area("ssp245")
ssp585_area = eoc_area("ssp585")

# Pre-compute values that can't go directly into f-strings with escaped braces
_empty = {}
pw126 = peak_water.get("ssp126", _empty)
pw245 = peak_water.get("ssp245", _empty)
pw585 = peak_water.get("ssp585", _empty)
pm126 = proj_meta.get("ssp126", _empty)
pm245 = proj_meta.get("ssp245", _empty)
pm585 = proj_meta.get("ssp585", _empty)

pw126_year = pw126.get("peak_year", "N/A")
pw126_q = pw126.get("peak_discharge_m3s", 0)
pw245_year = pw245.get("peak_year", "N/A")
pw245_q = pw245.get("peak_discharge_m3s", 0)
pw585_year = pw585.get("peak_year", "N/A")
pw585_q = pw585.get("peak_discharge_m3s", 0)

pm126_nparams = pm126.get("n_param_samples", "N/A")
pm245_nparams = pm245.get("n_param_samples", "N/A")
pm585_nparams = pm585.get("n_param_samples", "N/A")
pm126_ngcms = pm126.get("n_gcms", "N/A") if "ssp126" in proj_meta else "N/A"
pm245_ngcms = pm245.get("n_gcms", "N/A") if "ssp245" in proj_meta else "N/A"
pm585_ngcms = pm585.get("n_gcms", "N/A") if "ssp585" in proj_meta else "N/A"
pm126_nruns = pm126.get("n_total_runs", "N/A")
pm245_nruns = pm245.get("n_total_runs", "N/A")
pm585_nruns = pm585.get("n_total_runs", "N/A")

pw126_gcm_min = pw126.get("gcm_min", 0)
pw126_gcm_max = pw126.get("gcm_max", 0)
pw245_gcm_min = pw245.get("gcm_min", 0)
pw245_gcm_max = pw245.get("gcm_max", 0)
pw585_gcm_min = pw585.get("gcm_min", 0)
pw585_gcm_max = pw585.get("gcm_max", 0)

# ── Assemble full HTML ──────────────────────────────────────────────
print("Building HTML...")

# Parameter summary
params_text = []
for k, v in best_params.items():
    if k in ("r_ice", "lapse_rate", "k_wind"):
        continue
    params_text.append(f"{k} = {v:.4f}" if abs(v) > 0.01 else f"{k} = {v:.6f}")
params_summary = " | ".join(params_text)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dixon Glacier DETIM -- Methods &amp; Results</title>
<style>
:root {{
  --bg: #1a1b26;
  --bg-surface: #24283b;
  --bg-card: #2a2e3f;
  --bg-hover: #343950;
  --text: #c0caf5;
  --text-dim: #8090b0;
  --text-bright: #e0e8ff;
  --accent-blue: #7aa2f7;
  --accent-green: #9ece6a;
  --accent-orange: #ff9e64;
  --accent-red: #f7768e;
  --accent-purple: #bb9af7;
  --accent-cyan: #7dcfff;
  --accent-yellow: #e0af68;
  --accent-warm: #f0a070;
  --accent-coral: #e8806a;
  --accent-rose: #d4748a;
  --accent-amber: #d4a040;
  --border: #3b4261;
  --radius: 8px;
  --shadow: 0 4px 20px rgba(0,0,0,0.3);
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.7;
  display: flex;
}}

/* Sidebar */
nav {{
  position: fixed;
  top: 0; left: 0;
  width: 280px;
  height: 100vh;
  background: var(--bg-surface);
  border-right: 1px solid var(--border);
  overflow-y: auto;
  padding: 24px 16px;
  z-index: 100;
}}
nav h1 {{
  font-size: 1.05rem;
  color: var(--accent-blue);
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}}
nav .subtitle {{
  font-size: 0.8rem;
  color: var(--text-dim);
  margin-bottom: 20px;
}}
nav a {{
  display: block;
  padding: 5px 12px;
  margin: 1px 0;
  color: var(--text-dim);
  text-decoration: none;
  border-radius: var(--radius);
  font-size: 0.82rem;
  transition: all 0.2s;
}}
nav a:hover, nav a.active {{
  background: var(--bg-hover);
  color: var(--accent-blue);
}}
nav a.results-link:hover, nav a.results-link.active {{
  color: var(--accent-warm);
}}
nav .nav-chapter {{
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  margin: 18px 0 6px 8px;
  padding: 4px 0;
}}
nav .nav-chapter.methods {{
  color: var(--accent-blue);
  border-bottom: 2px solid var(--accent-blue);
}}
nav .nav-chapter.results {{
  color: var(--accent-warm);
  border-bottom: 2px solid var(--accent-warm);
}}
nav .nav-section {{
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-dim);
  margin: 16px 0 6px 12px;
  opacity: 0.6;
}}

/* Main content */
main {{
  margin-left: 280px;
  padding: 40px 48px;
  max-width: 1100px;
  width: calc(100% - 280px);
}}

/* Chapter dividers */
.chapter-divider {{
  margin: 56px 0 32px;
  padding: 16px 24px;
  border-radius: var(--radius);
  font-size: 1.8rem;
  font-weight: 700;
  letter-spacing: 0.5px;
}}
.chapter-divider.methods {{
  background: linear-gradient(135deg, rgba(122,162,247,0.12), rgba(125,207,255,0.08));
  border-left: 4px solid var(--accent-blue);
  color: var(--accent-blue);
}}
.chapter-divider.results {{
  background: linear-gradient(135deg, rgba(240,160,112,0.12), rgba(228,128,106,0.08));
  border-left: 4px solid var(--accent-warm);
  color: var(--accent-warm);
}}

/* Sections */
.section {{
  margin-bottom: 48px;
  scroll-margin-top: 24px;
}}
.section h2 {{
  font-size: 1.5rem;
  margin-bottom: 20px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--border);
}}
.section h3 {{
  font-size: 1.15rem;
  margin: 24px 0 12px;
  color: var(--accent-cyan);
}}
.section h4 {{
  font-size: 1.05rem;
  margin: 16px 0 8px;
  color: var(--accent-purple);
}}

/* Methods section colors */
#study-site h2 {{ border-color: var(--accent-green); color: var(--accent-green); }}
#model h2 {{ border-color: var(--accent-blue); color: var(--accent-blue); }}
#input-data h2 {{ border-color: var(--accent-cyan); color: var(--accent-cyan); }}
#calibration-methods h2 {{ border-color: var(--accent-purple); color: var(--accent-purple); }}
#validation-methods h2 {{ border-color: var(--accent-blue); color: var(--accent-blue); }}
#projection-design h2 {{ border-color: var(--accent-cyan); color: var(--accent-cyan); }}
#implementation h2 {{ border-color: var(--text-dim); color: var(--text-dim); }}

/* Results section colors */
#cal-results h2 {{ border-color: var(--accent-warm); color: var(--accent-warm); }}
#model-fit h2 {{ border-color: var(--accent-coral); color: var(--accent-coral); }}
#val-results h2 {{ border-color: var(--accent-rose); color: var(--accent-rose); }}
#historical h2 {{ border-color: var(--accent-amber); color: var(--accent-amber); }}
#proj-results h2 {{ border-color: var(--accent-orange); color: var(--accent-orange); }}
#lapse-results h2 {{ border-color: var(--accent-red); color: var(--accent-red); }}

/* Decision log */
#decisions h2 {{ border-color: var(--text-dim); color: var(--text-dim); }}

/* Cards */
.card {{
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin: 16px 0;
  box-shadow: var(--shadow);
}}

/* Figures */
.figure-container {{
  margin: 20px 0;
  text-align: center;
}}
.figure-img {{
  max-width: 100%;
  border-radius: var(--radius);
  cursor: zoom-in;
  transition: transform 0.2s;
  border: 1px solid var(--border);
}}
.figure-img:hover {{
  transform: scale(1.01);
  box-shadow: 0 0 20px rgba(122,162,247,0.2);
}}
.figure-caption {{
  font-size: 0.85rem;
  color: var(--text-dim);
  margin-top: 8px;
  font-style: italic;
}}

/* Tables */
.data-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
  margin: 12px 0;
}}
.data-table th, .data-table td {{
  padding: 8px 12px;
  border: 1px solid var(--border);
  text-align: left;
}}
.data-table th {{
  background: var(--bg-surface);
  color: var(--accent-blue);
  font-weight: 600;
}}
.data-table tr:hover {{
  background: var(--bg-hover);
}}
.data-table .highlight-row {{
  background: rgba(122,162,247,0.08);
}}

/* Expandable */
details {{
  margin: 12px 0;
}}
details summary {{
  cursor: pointer;
  color: var(--accent-cyan);
  font-weight: 500;
  padding: 8px 12px;
  background: var(--bg-surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  transition: all 0.2s;
  list-style: none;
}}
details summary::before {{
  content: "+ ";
  font-weight: bold;
  color: var(--accent-orange);
}}
details[open] summary::before {{
  content: "- ";
}}
details summary:hover {{
  background: var(--bg-hover);
}}
details .detail-content {{
  padding: 16px;
  margin-top: 4px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  animation: slideDown 0.3s ease;
}}

/* Decision log */
.decision-item {{
  margin: 4px 0;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}}
.decision-toggle {{
  display: flex;
  align-items: center;
  width: 100%;
  padding: 10px 16px;
  background: var(--bg-surface);
  border: none;
  color: var(--text);
  cursor: pointer;
  font-size: 0.9rem;
  text-align: left;
  transition: background 0.2s;
  gap: 12px;
}}
.decision-toggle:hover {{
  background: var(--bg-hover);
}}
.decision-id {{
  background: var(--accent-blue);
  color: var(--bg);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
  white-space: nowrap;
  min-width: 50px;
  text-align: center;
}}
.decision-title {{
  flex: 1;
  color: var(--text-bright);
}}
.toggle-icon {{
  color: var(--accent-orange);
  font-weight: bold;
  font-size: 1.1rem;
  min-width: 20px;
  text-align: center;
}}
.decision-body {{
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.4s ease, padding 0.3s ease;
  padding: 0 16px;
  background: var(--bg-card);
  font-size: 0.85rem;
  line-height: 1.6;
}}
.decision-body.open {{
  max-height: 5000px;
  padding: 16px;
}}
.decision-body p {{
  margin: 4px 0;
}}
.decision-body strong {{
  color: var(--accent-orange);
}}
.decision-body code {{
  background: var(--bg-surface);
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 0.82rem;
  color: var(--accent-green);
}}
.decision-bullet {{
  padding-left: 16px;
  position: relative;
  margin: 2px 0;
}}
.decision-bullet::before {{
  content: "\\2022";
  position: absolute;
  left: 4px;
  color: var(--accent-blue);
}}
.decision-subbullet {{
  padding-left: 32px;
  position: relative;
  margin: 2px 0;
}}
.decision-subbullet::before {{
  content: "\\25E6";
  position: absolute;
  left: 20px;
  color: var(--text-dim);
}}
.decision-body .data-table {{
  margin: 8px 0;
}}
.code-block {{
  background: var(--bg-surface);
  padding: 12px;
  border-radius: var(--radius);
  font-size: 0.82rem;
  overflow-x: auto;
  color: var(--accent-green);
  margin: 8px 0;
}}

/* Why buttons */
.why-btn {{
  display: inline-block;
  background: var(--accent-purple);
  color: var(--bg);
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
  vertical-align: middle;
  margin-left: 6px;
  transition: all 0.2s;
}}
.why-btn:hover {{
  background: var(--accent-orange);
  transform: scale(1.05);
}}

/* D-ref links */
.d-ref {{
  color: var(--accent-blue);
  cursor: pointer;
  text-decoration: underline dotted;
  font-weight: 600;
}}
.d-ref:hover {{
  color: var(--accent-orange);
}}

/* Equation */
.equation {{
  background: var(--bg-surface);
  padding: 16px 24px;
  border-radius: var(--radius);
  font-family: 'Courier New', monospace;
  font-size: 0.95rem;
  margin: 12px 0;
  border-left: 3px solid var(--accent-blue);
  color: var(--text-bright);
  overflow-x: auto;
}}

/* Stat highlight */
.stat {{
  display: inline-block;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 20px;
  margin: 4px;
  text-align: center;
}}
.stat-value {{
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--accent-blue);
}}
.stat-label {{
  font-size: 0.75rem;
  color: var(--text-dim);
}}
.stats-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 16px 0;
}}

/* Results stat highlights use warm colors */
.results-stat .stat-value {{
  color: var(--accent-warm);
}}

/* Key finding callouts */
.finding {{
  background: rgba(240,160,112,0.08);
  border: 1px solid rgba(240,160,112,0.3);
  border-left: 4px solid var(--accent-warm);
  border-radius: var(--radius);
  padding: 16px 20px;
  margin: 16px 0;
  font-size: 0.92rem;
}}
.finding-title {{
  font-weight: 700;
  color: var(--accent-warm);
  margin-bottom: 6px;
}}

/* Lightbox */
.lightbox {{
  display: none;
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;
  background: rgba(0,0,0,0.92);
  z-index: 9999;
  cursor: zoom-out;
  align-items: center;
  justify-content: center;
}}
.lightbox.active {{
  display: flex;
}}
.lightbox img {{
  max-width: 95vw;
  max-height: 95vh;
  border-radius: var(--radius);
  box-shadow: 0 0 40px rgba(0,0,0,0.5);
}}
.lightbox-close {{
  position: fixed;
  top: 20px; right: 30px;
  color: white;
  font-size: 2rem;
  cursor: pointer;
  z-index: 10000;
}}

/* Animations */
@keyframes slideDown {{
  from {{ opacity: 0; transform: translateY(-8px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

/* Responsive */
@media (max-width: 900px) {{
  nav {{ display: none; }}
  main {{ margin-left: 0; padding: 20px; }}
}}

/* Param table */
.param-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 8px;
  margin: 12px 0;
}}
.param-card {{
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px 14px;
  text-align: center;
}}
.param-name {{
  font-size: 0.75rem;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}
.param-value {{
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--accent-green);
}}
.param-unit {{
  font-size: 0.7rem;
  color: var(--text-dim);
}}

/* Residual coloring */
.residual-good {{ color: var(--accent-green); }}
.residual-ok {{ color: var(--accent-yellow); }}
.residual-bad {{ color: var(--accent-red); }}
</style>
</head>
<body>

<!-- Sidebar Navigation -->
<nav>
  <h1>Dixon Glacier DETIM</h1>
  <div class="subtitle">Methods &amp; Results</div>

  <div class="nav-chapter methods">3. Methods</div>
  <a href="#study-site" onclick="setActive(this)">3.1 Study Site</a>
  <a href="#model" onclick="setActive(this)">3.2 Model Description</a>
  <a href="#input-data" onclick="setActive(this)">3.3 Input Data</a>
  <a href="#calibration-methods" onclick="setActive(this)">3.4 Calibration</a>
  <a href="#validation-methods" onclick="setActive(this)">3.5 Validation</a>
  <a href="#projection-design" onclick="setActive(this)">3.6 Projection Design</a>
  <a href="#implementation" onclick="setActive(this)">3.7 Implementation</a>

  <div class="nav-chapter results">4. Results</div>
  <a href="#cal-results" class="results-link" onclick="setActive(this)">4.1 Calibration Results</a>
  <a href="#model-fit" class="results-link" onclick="setActive(this)">4.2 Model Fit</a>
  <a href="#val-results" class="results-link" onclick="setActive(this)">4.3 Validation</a>
  <a href="#historical" class="results-link" onclick="setActive(this)">4.4 Historical Mass Balance</a>
  <a href="#proj-results" class="results-link" onclick="setActive(this)">4.5 Projections</a>
  <a href="#lapse-results" class="results-link" onclick="setActive(this)">4.6 Lapse Rate Sensitivity</a>

  <div class="nav-section">Reference</div>
  <a href="#decisions" onclick="setActive(this)">Decision Log (D-001..031)</a>

  <div class="nav-section">Quick Stats</div>
  <div style="padding:8px 12px;font-size:0.75rem;color:var(--text-dim);">
    Area: 40.11 km&sup2; (2000)<br>
    Elev: 439 &ndash; 1637 m<br>
    Geodetic: &minus;0.94 m w.e./yr<br>
    CAL-013: {n_samples:,} posterior samples<br>
    {len(decisions)} decisions logged
  </div>
</nav>

<!-- Lightbox -->
<div class="lightbox" id="lightbox" onclick="closeLightbox()">
  <span class="lightbox-close">&times;</span>
  <img id="lightbox-img" src="" alt="Zoomed figure">
</div>

<!-- Main Content -->
<main>

<!-- ================================================================ -->
<!-- CHAPTER 3: METHODS                                               -->
<!-- ================================================================ -->
<div class="chapter-divider methods" id="ch3">3. Methods</div>

<!-- ================================================================ -->
<!-- 3.1 STUDY SITE -->
<!-- ================================================================ -->
<div class="section" id="study-site">
<h2>3.1 Study Site</h2>

<p>Dixon Glacier (59.66&deg;N, 150.88&deg;W) is a large valley glacier on the
Kenai Peninsula, south-central Alaska, with an area of approximately
40.11 km&sup2; as measured from the RGI7 outline (year 2000).
<a class="why-btn" onclick="scrollToDecision('D-001')">Why DETIM?</a>
</p>

<p>The glacier spans 439 to 1637 m elevation and is monitored at three stake
sites since 2023: an ablation zone stake (ABL, 804 m), an equilibrium line
stake (ELA, 1078 m), and an accumulation zone stake (ACC, 1293 m). The
primary climate forcing comes from Nuka Glacier SNOTEL (375 m, ~10 km NW).
<a class="why-btn" onclick="scrollToDecision('D-002')">Why Nuka?</a>
</p>

{fig_tag(9, "Dixon Glacier study site with stake locations, contours, and RGI7 outline")}

<h3>Glacier Change (2000&ndash;2025)</h3>
<p>Six manually digitized outlines from historical satellite imagery show Dixon
Glacier retreating from 40.11 km&sup2; (2000) to 38.34 km&sup2; (2025), a loss of
1.77 km&sup2; (4.4%).
<a class="why-btn" onclick="scrollToDecision('D-028')">Why digitize?</a>
</p>

{fig_tag(10, "Dixon Glacier area retreat from 6 digitized outlines (2000-2025)")}

</div>

<!-- ================================================================ -->
<!-- 3.2 MODEL DESCRIPTION -->
<!-- ================================================================ -->
<div class="section" id="model">
<h2>3.2 Model Description</h2>

<p>We apply a Distributed Enhanced Temperature Index Model (DETIM) following
Method 2 of Hock (1999). Daily melt M (mm w.e. d&sup1;) at each grid cell is:
<a class="why-btn" onclick="scrollToDecision('D-001')">D-001</a>
</p>

<div class="equation">
M = (MF + r<sub>snow/ice</sub> &times; I<sub>pot</sub>) &times; T, &nbsp; when T &gt; 0&deg;C<br>
M = 0, &nbsp; when T &le; 0&deg;C
</div>

<p>where MF is a melt factor (mm d&minus;&sup1; K&minus;&sup1;), r<sub>snow</sub> and r<sub>ice</sub>
are radiation factors, I<sub>pot</sub> is potential clear-sky direct solar radiation
(W m&minus;&sup2;), and T is distributed air temperature (&deg;C).</p>

<h3>3.2.1 Temperature Distribution</h3>
<div class="equation">
T<sub>cell</sub> = T<sub>station</sub> + &lambda; &times; (z<sub>cell</sub> &minus; z<sub>station</sub>)
</div>
<p>Air temperature is extrapolated from Nuka SNOTEL (375 m) using a fixed lapse
rate &lambda; = &minus;5.0 &deg;C km&minus;&sup1;.
<a class="why-btn" onclick="scrollToDecision('D-012')">D-012</a>
<a class="why-btn" onclick="scrollToDecision('D-013')">D-013</a>
<a class="why-btn" onclick="scrollToDecision('D-015')">D-015</a>
</p>

<h3>3.2.2 Precipitation Distribution</h3>
<div class="equation">
P<sub>cell</sub> = P<sub>station</sub> &times; C<sub>p</sub> &times; (1 + &gamma;<sub>p</sub> &times; &Delta;z)
</div>
<p>Rain/snow partitioning uses a linear transition around threshold temperature
T<sub>0</sub>.</p>

<h3>3.2.3 Solar Radiation</h3>
<p>Potential clear-sky direct radiation is computed following Oke (1987) solar
geometry with topographic corrections. Atmospheric transmissivity &psi;<sub>a</sub> = 0.75.
Values precomputed at 3-hour intervals for a lookup table.</p>

<h3>3.2.4 Snowpack and Surface Type</h3>
<p>SWE tracked at each cell. Surface type (snow/firn/ice) determines which
radiation factor is applied. The firn line is set at the median glacier
elevation. r<sub>ice</sub>/r<sub>snow</sub> ratio fixed at 2.0.
<a class="why-btn" onclick="scrollToDecision('D-017')">D-017</a>
</p>

<h3>3.2.5 Glacier Dynamics</h3>
<p>Area and volume evolution use the delta-h parameterization (Huss et al. 2010)
with Farinotti (2019) ice thickness. Cells deglaciate when ice thickness
drops below 1 m.
<a class="why-btn" onclick="scrollToDecision('D-018')">D-018</a>
</p>

</div>

<!-- ================================================================ -->
<!-- 3.3 INPUT DATA -->
<!-- ================================================================ -->
<div class="section" id="input-data">
<h2>3.3 Input Data</h2>

<h3>3.3.1 Digital Elevation Model</h3>
<p>IfSAR 2010 DTM at 5 m resolution, resampled to 100 m for model runs.</p>

<h3>3.3.2 Climate Forcing</h3>
<p>Primary station: Nuka Glacier SNOTEL (site 1037, 375 m), with multi-station
gap-filling (D-025) using 5 nearby SNOTEL stations. The gap-filled record
covers WY1999&ndash;2025 (9,862 days, zero missing values).
<a class="why-btn" onclick="scrollToDecision('D-025')">D-025</a>
</p>

<div class="stats-row">
  <div class="stat"><div class="stat-value">91.3%</div><div class="stat-label">Nuka primary</div></div>
  <div class="stat"><div class="stat-value">6.0%</div><div class="stat-label">MFB fill</div></div>
  <div class="stat"><div class="stat-value">1.8%</div><div class="stat-label">McNeil fill</div></div>
  <div class="stat"><div class="stat-value">0.9%</div><div class="stat-label">Other sources</div></div>
  <div class="stat"><div class="stat-value">0</div><div class="stat-label">Missing days</div></div>
</div>

{fig_tag(11, "Climate forcing time series with gap-fill source attribution (D-025)")}

<h3>3.3.3 Calibration Targets</h3>

<h4>Stake Mass Balance</h4>
<p>8 measured + 3 estimated observations at 3 elevations (ABL 804 m, ELA 1078 m,
ACC 1293 m), water years 2023&ndash;2025.
<a class="why-btn" onclick="scrollToDecision('D-003')">D-003</a>
</p>

<details>
<summary>Expand: Full stake observation table</summary>
<div class="detail-content">
<table class="data-table">
<thead><tr><th>Site</th><th>Period</th><th>Year</th><th>Balance (m w.e.)</th>
<th>Uncertainty</th><th>Elevation (m)</th><th>Note</th></tr></thead>
<tbody>
{build_stake_table()}
</tbody></table>
</div>
</details>

<h4>Geodetic Mass Balance</h4>
<p>Hugonnet et al. (2021): 2000&ndash;2020 mean &minus;0.939 &plusmn; 0.122 m w.e. yr&minus;&sup1;.
Sub-periods used for validation only.
<a class="why-btn" onclick="scrollToDecision('D-016')">D-016</a>
</p>

<details>
<summary>Expand: Geodetic data detail</summary>
<div class="detail-content">
<table class="data-table">
<thead><tr><th>Period</th><th>dM/dt/A (m w.e./yr)</th><th>Uncertainty</th></tr></thead>
<tbody>
{build_geodetic_table()}
</tbody></table>
</div>
</details>

<h4>Snowline Observations</h4>
<p>22 years (1999&ndash;2024) of digitized snowline shapefiles from end-of-summer
satellite imagery. Used in the MCMC likelihood (D-028) with &sigma; = 75 m.
<a class="why-btn" onclick="scrollToDecision('D-021')">D-021</a>
<a class="why-btn" onclick="scrollToDecision('D-028')">D-028</a>
</p>

</div>

<!-- ================================================================ -->
<!-- 3.4 CALIBRATION (methodology only) -->
<!-- ================================================================ -->
<div class="section" id="calibration-methods">
<h2>3.4 Calibration</h2>

<p>Two-phase Bayesian approach: differential evolution (DE) finds the MAP estimate,
then MCMC (emcee) maps the posterior distribution for projection uncertainty
quantification.
<a class="why-btn" onclick="scrollToDecision('D-017')">D-017</a>
<a class="why-btn" onclick="scrollToDecision('D-027')">D-027</a>
<a class="why-btn" onclick="scrollToDecision('D-028')">D-028</a>
</p>

<h3>3.4.1 Calibrated Parameters</h3>

<table class="data-table">
<thead><tr><th>Parameter</th><th>Symbol</th><th>Units</th><th>Lower</th><th>Upper</th><th>Prior</th></tr></thead>
<tbody>
<tr><td>Melt factor</td><td>MF</td><td>mm d&minus;&sup1; K&minus;&sup1;</td><td>1.0</td><td>12.0</td><td>TN(5, 3)</td></tr>
<tr><td>MF gradient</td><td>MF<sub>grad</sub></td><td>mm d&minus;&sup1; K&minus;&sup1; m&minus;&sup1;</td><td>&minus;0.01</td><td>0.0</td><td>Uniform</td></tr>
<tr><td>Snow rad. factor</td><td>r<sub>snow</sub></td><td>mm m&sup2; W&minus;&sup1; d&minus;&sup1; K&minus;&sup1;</td><td>0.0001</td><td>0.005</td><td>Uniform</td></tr>
<tr><td>Precip gradient</td><td>&gamma;<sub>p</sub></td><td>m&minus;&sup1;</td><td>0.0</td><td>0.002</td><td>Uniform</td></tr>
<tr><td>Precip correction</td><td>C<sub>p</sub></td><td>&mdash;</td><td>1.0</td><td>4.0</td><td>Uniform</td></tr>
<tr><td>Rain/snow threshold</td><td>T<sub>0</sub></td><td>&deg;C</td><td>0.0</td><td>3.0</td><td>TN(1.5, 0.5)</td></tr>
</tbody></table>

<h4>Fixed parameters:</h4>
<div class="param-grid">
  <div class="param-card">
    <div class="param-name">Lapse rate</div>
    <div class="param-value">&minus;5.0</div>
    <div class="param-unit">&deg;C km&minus;&sup1;</div>
  </div>
  <div class="param-card">
    <div class="param-name">r_ice/r_snow</div>
    <div class="param-value">2.0</div>
    <div class="param-unit">(ratio)</div>
  </div>
  <div class="param-card">
    <div class="param-name">k_wind</div>
    <div class="param-value">0.0</div>
    <div class="param-unit">(off)</div>
  </div>
</div>

<h3>3.4.2 Multi-Objective Likelihood</h3>
<p>The MCMC likelihood jointly optimizes stakes + geodetic + snowline elevation.
Snowline enters as a chi-squared term with &sigma; = 75 m across 22 years. Post-hoc area
evolution filter applied after MCMC, using 6 digitized outlines (2000&ndash;2025).
<a class="why-btn" onclick="scrollToDecision('D-028')">D-028</a>
</p>

<div class="equation">
ln L(&theta;) = &minus;0.5 &times; [ &sum;<sub>stakes</sub> ((m&minus;o)/&sigma;)&sup2;
+ ((B<sub>geod</sub>&minus;B<sub>obs</sub>)/&sigma;<sub>geod</sub>)&sup2;
+ &sum;<sub>snowlines</sub> ((z<sub>mod</sub>&minus;z<sub>obs</sub>)/75)&sup2; ]
</div>

<h3>3.4.3 DE Configuration</h3>
<p>Multi-seed DE with {n_seeds} seeds to test for multimodality (D-027). Seeds
initialized from independent Latin hypercube populations, hierarchically
clustered with 10% Chebyshev distance threshold.
<a class="why-btn" onclick="scrollToDecision('D-027')">D-027</a>
</p>

<h3>3.4.4 MCMC Configuration</h3>
<p>{n_walkers} affine-invariant walkers (emcee), {n_steps:,} steps per walker,
2,000-step burn-in, thinned by autocorrelation time. Separate chains initialized
from each distinct DE mode, then combined.</p>

<h3>3.4.5 Equifinality and Parameter Constraints</h3>
<p>Lapse rate is fixed at &minus;5.0 &deg;C km&minus;&sup1; to prevent equifinality with
precip_corr. r_ice derived as 2.0 &times; r_snow to preserve albedo feedback.
<a class="why-btn" onclick="scrollToDecision('D-015')">D-015</a>
<a class="why-btn" onclick="scrollToDecision('D-017')">D-017</a>
</p>

</div>

<!-- ================================================================ -->
<!-- 3.5 VALIDATION (methodology only) -->
<!-- ================================================================ -->
<div class="section" id="validation-methods">
<h2>3.5 Validation</h2>

<p>Three independent validation analyses are applied to the calibrated posterior,
without recalibration.
<a class="why-btn" onclick="scrollToDecision('D-029')">D-029</a>
</p>

<h3>3.5.1 Sub-period Geodetic Comparison</h3>
<p>The model is evaluated against Hugonnet sub-periods (2000&ndash;2010 and
2010&ndash;2020) that were withheld from calibration (D-016). 200 posterior
parameter sets are run through each decade independently.</p>

<h3>3.5.2 Posterior Predictive Check</h3>
<p>200 posterior parameter sets are evaluated against each stake year independently,
producing median modeled values and residuals at each site/year combination. This
identifies whether biases are systematic (all years) or year-specific (forcing issues).</p>

<h3>3.5.3 Sensitivity of Fixed Parameters</h3>
<p>The lapse rate (&minus;4.0 to &minus;6.5 &deg;C/km) and r<sub>ice</sub>/r<sub>snow</sub>
ratio (1.5 to 3.0) are perturbed with MAP parameters held fixed, and the geodetic
balance and stake RMSE are reported for each perturbation.</p>

</div>

<!-- ================================================================ -->
<!-- 3.6 PROJECTION DESIGN (methodology only) -->
<!-- ================================================================ -->
<div class="section" id="projection-design">
<h2>3.6 Projection Design</h2>

<p>The projection ensemble propagates both climate uncertainty (GCM spread) and
parameter uncertainty (posterior samples) through the glacier model.
<a class="why-btn" onclick="scrollToDecision('D-019')">D-019</a>
<a class="why-btn" onclick="scrollToDecision('D-020')">D-020</a>
</p>

<h3>3.6.1 CMIP6 Forcing</h3>
<p>NASA NEX-GDDP-CMIP6 (0.25&deg;, daily, bias-corrected) for 5 GCMs:
ACCESS-CM2, EC-Earth3, MPI-ESM1-2-HR, MRI-ESM2-0, NorESM2-MM. Monthly delta
bias correction against Nuka SNOTEL 1991&ndash;2020 climatology.</p>

<h3>3.6.2 Scenario Ensemble</h3>
<table class="data-table">
<thead><tr><th>Scenario</th><th>Param sets</th><th>GCMs</th><th>Total runs</th></tr></thead>
<tbody>
<tr><td>SSP1-2.6</td><td>1,000</td><td>4</td><td>4,000</td></tr>
<tr><td>SSP2-4.5</td><td>250</td><td>5</td><td>1,250</td></tr>
<tr><td>SSP5-8.5</td><td>250</td><td>5</td><td>1,250</td></tr>
</tbody></table>

<h3>3.6.3 Lapse Rate Bracket</h3>
<p>Additional projections at &minus;4.5 and &minus;5.5 &deg;C km&minus;&sup1; (alongside the
central &minus;5.0) bracket the structural uncertainty from the fixed lapse rate
choice. Same 250 posterior params &times; 5 GCMs &times; 2 SSPs = 7,500 additional runs.
<a class="why-btn" onclick="scrollToDecision('D-030')">D-030</a>
</p>

</div>

<!-- ================================================================ -->
<!-- 3.7 IMPLEMENTATION -->
<!-- ================================================================ -->
<div class="section" id="implementation">
<h2>3.7 Implementation</h2>

<p>Python 3.12 + NumPy + Numba JIT compilation. ~240 ms per water-year simulation
on a 100 m grid (4,011 glacier cells). The full MCMC ensemble ({n_walkers} walkers
&times; {n_steps:,} steps) completes in ~11 hours on 8 cores.
<a class="why-btn" onclick="scrollToDecision('D-004')">D-004</a>
</p>

<p>Key modules: <code>fast_model.py</code> (Numba-compiled core),
<code>glacier_dynamics.py</code> (delta-h evolution),
<code>climate_projections.py</code> (CMIP6 bias correction),
<code>routing.py</code> (parallel linear reservoirs for discharge).</p>

</div>

<!-- ================================================================ -->
<!-- CHAPTER 4: RESULTS                                               -->
<!-- ================================================================ -->
<div class="chapter-divider results" id="ch4">4. Results</div>

<!-- ================================================================ -->
<!-- 4.1 CALIBRATION RESULTS -->
<!-- ================================================================ -->
<div class="section" id="cal-results">
<h2>4.1 Calibration Results</h2>

<h3>4.1.1 Convergence Diagnostics</h3>

<div class="stats-row results-stat">
  <div class="stat"><div class="stat-value">{n_seeds}</div><div class="stat-label">DE seeds</div></div>
  <div class="stat"><div class="stat-value">{n_modes}</div><div class="stat-label">Mode found</div></div>
  <div class="stat"><div class="stat-value">{de_cost_min:.3f}&ndash;{de_cost_max:.3f}</div><div class="stat-label">DE cost range</div></div>
  <div class="stat"><div class="stat-value">{n_samples:,}</div><div class="stat-label">Posterior samples</div></div>
  <div class="stat"><div class="stat-value">{acceptance:.2f}</div><div class="stat-label">Acceptance fraction</div></div>
  <div class="stat"><div class="stat-value">1,000/1,000</div><div class="stat-label">Passed area filter</div></div>
</div>

<div class="finding">
  <div class="finding-title">Key finding: Unimodal posterior</div>
  All {n_seeds} DE seeds converged to the same mode (cost {de_cost_min:.3f}&ndash;{de_cost_max:.3f}),
  confirming the posterior is unimodal. The 6-parameter space with fixed lapse rate
  and r<sub>ice</sub>/r<sub>snow</sub> ratio (D-015, D-017) successfully eliminated
  the multimodality that plagued earlier calibrations.
</div>

<h3>4.1.2 MAP Parameter Values</h3>

<div class="param-grid">
  <div class="param-card">
    <div class="param-name">MF</div>
    <div class="param-value">{best_params["MF"]:.2f}</div>
    <div class="param-unit">mm d&minus;&sup1; K&minus;&sup1;</div>
  </div>
  <div class="param-card">
    <div class="param-name">MF_grad</div>
    <div class="param-value">{best_params["MF_grad"]:.4f}</div>
    <div class="param-unit">mm d&minus;&sup1; K&minus;&sup1; m&minus;&sup1;</div>
  </div>
  <div class="param-card">
    <div class="param-name">r_snow</div>
    <div class="param-value">{best_params["r_snow"]*1e3:.3f}</div>
    <div class="param-unit">&times;10&minus;&sup3; mm m&sup2; W&minus;&sup1; d&minus;&sup1; K&minus;&sup1;</div>
  </div>
  <div class="param-card">
    <div class="param-name">precip_grad</div>
    <div class="param-value">{best_params["precip_grad"]:.5f}</div>
    <div class="param-unit">m&minus;&sup1;</div>
  </div>
  <div class="param-card">
    <div class="param-name">precip_corr</div>
    <div class="param-value">{best_params["precip_corr"]:.2f}</div>
    <div class="param-unit">(dimensionless)</div>
  </div>
  <div class="param-card">
    <div class="param-name">T0</div>
    <div class="param-value">{best_params["T0"]:.4f}</div>
    <div class="param-unit">&deg;C</div>
  </div>
</div>

<h3>4.1.3 Posterior Distribution</h3>

<p>The posterior parameter table summarizes the central tendency and 90% credible
intervals from {n_samples:,} independent samples after burn-in and thinning:</p>

<table class="data-table">
<thead><tr><th>Parameter</th><th>MAP</th><th>Posterior median</th><th>90% CI</th></tr></thead>
<tbody>
<tr><td>MF (mm d&minus;&sup1; K&minus;&sup1;)</td><td>{best_params["MF"]:.2f}</td><td>7.30</td><td>[7.06, 7.58]</td></tr>
<tr><td>MF_grad (mm d&minus;&sup1; K&minus;&sup1; m&minus;&sup1;)</td><td>{best_params["MF_grad"]:.4f}</td><td>&minus;0.0041</td><td>[&minus;0.0046, &minus;0.0036]</td></tr>
<tr><td>r_snow (&times;10&minus;&sup3;)</td><td>{best_params["r_snow"]*1e3:.3f}</td><td>1.96</td><td>[1.82, 2.12]</td></tr>
<tr><td>precip_grad (m&minus;&sup1;)</td><td>{best_params["precip_grad"]:.5f}</td><td>0.00069</td><td>[0.00052, 0.00087]</td></tr>
<tr><td>precip_corr</td><td>{best_params["precip_corr"]:.2f}</td><td>1.61</td><td>[1.47, 1.74]</td></tr>
<tr><td>T<sub>0</sub> (&deg;C)</td><td>{best_params["T0"]:.4f}</td><td>~0.00</td><td>[0.00, 0.45]</td></tr>
</tbody></table>

<p>Snowline RMSE across the posterior: 90 m (structural limitation of DETIM;
see D-028 for analysis of spatial vs. interannual snowline bias).</p>

{fig_tag(1, "Posterior parameter distributions from CAL-013 (6 calibrated parameters)")}

</div>

<!-- ================================================================ -->
<!-- 4.2 MODEL FIT -->
<!-- ================================================================ -->
<div class="section" id="model-fit">
<h2>4.2 Model Fit</h2>

<h3>4.2.1 Stake Mass Balance</h3>

{fig_tag(2, "Modeled vs observed stake mass balance for calibration targets")}

<h4>Posterior predictive check by year and site</h4>
<table class="data-table">
<thead><tr><th>Year</th><th>Site</th><th>Obs (m w.e.)</th><th>Mod (median)</th>
<th>Residual</th><th>Note</th></tr></thead>
<tbody>'''

# Add stake validation rows
for r in stake_val_rows:
    res = float(r["residual"])
    est = r["estimated"].strip()
    # Color code residuals
    if abs(res) < 0.5:
        cls = "residual-good"
    elif abs(res) < 1.0:
        cls = "residual-ok"
    else:
        cls = "residual-bad"
    note = ""
    if est == "True":
        note = "estimated obs"
    elif r["site"] == "ELA" and abs(res) > 1.0:
        note = "wind redistribution bias"
    elif r["year"] == "2024" and abs(res) > 1.0:
        note = "forcing limitation"
    html += f'''<tr><td>WY{r["year"]}</td><td>{r["site"]}</td>
<td>{float(r["obs"]):+.2f}</td><td>{float(r["mod_median"]):+.2f}</td>
<td class="{cls}">{res:+.2f}</td><td>{note}</td></tr>
'''

html += f'''</tbody></table>

<h3>4.2.2 ELA Wind Redistribution Bias (D-031)</h3>

<div class="finding">
  <div class="finding-title">Persistent ELA bias: wind redistribution, not calibration failure</div>
  The ELA stake shows &minus;1.4 m w.e. residual in both WY2023 and WY2024. This is a spatial
  representativity issue: the stake sits on the southern branch, a preferential wind
  deposition zone, receiving more accumulation than the elevation-band average. The model
  predicts &minus;1.3 m w.e. as the average across all 814 glacier cells in the 1028&ndash;1128 m
  band. Digitized snowlines independently confirm lower snowlines (more accumulation) on
  the southern branch. A constant precip_grad cannot capture this spatial variability.
  <a class="why-btn" onclick="scrollToDecision('D-031')">D-031</a>
</div>

<h3>4.2.3 WY2024 Forcing Limitation</h3>

<div class="finding">
  <div class="finding-title">WY2024: all sites off by 1.2&ndash;1.6 m w.e.</div>
  WY2024 shows large residuals at all three sites, not just ELA. Nuka SNOTEL recorded
  912 mm winter precipitation (similar to WY2023&rsquo;s 864 mm), but observed winter balance at
  Dixon was dramatically higher (ABL: 0.85 &rarr; 1.93 m w.e., +127%). The off-glacier
  forcing station missed a local accumulation event. The precipitation gradient also
  flattened from 38%/100m (WY2023) to 11%/100m (WY2024). This is a forcing data limitation,
  not a model deficiency.
</div>

<h3>4.2.4 Geodetic Fit</h3>
<p>2000&ndash;2020 glacier-wide geodetic balance: observed &minus;0.939 &plusmn; 0.122,
modeled &minus;0.765 (bias +0.17 m w.e./yr). The bias is within 1.4&sigma; of the
reported uncertainty.</p>

</div>

<!-- ================================================================ -->
<!-- 4.3 VALIDATION RESULTS -->
<!-- ================================================================ -->
<div class="section" id="val-results">
<h2>4.3 Validation</h2>

<h3>4.3.1 Sub-period Geodetic Comparison</h3>

{fig_tag(3, "Geodetic validation: modeled vs Hugonnet et al. (2021) sub-periods")}

<table class="data-table">
<thead><tr><th>Period</th><th>Type</th><th>Observed</th><th>Modeled (median)</th>
<th>Bias</th><th>Within unc?</th></tr></thead>
<tbody>'''

for r in geod_val_rows:
    obs_str = f"{float(r['obs']):+.3f} &plusmn; {float(r['obs_err']):.3f}"
    html += f'''<tr><td>{r["period"]}</td><td>{r["type"]}</td>
<td>{obs_str}</td><td>{float(r["mod_median"]):+.3f}</td>
<td>{float(r["bias"]):+.3f}</td><td>{r["within_unc"]}</td></tr>
'''

html += f'''</tbody></table>

<div class="finding">
  <div class="finding-title">Model reverses the sub-period trend</div>
  The model underestimates 2000&ndash;2010 mass loss (+0.83 bias) and overestimates
  2010&ndash;2020 (&minus;0.48 bias). Nuka SNOTEL shows cooler summers in 2001&ndash;2010
  (9.07&deg;C) vs 2011&ndash;2020 (10.00&deg;C), so the model produces less melt in the
  first decade. But Hugonnet shows MORE mass loss 2000&ndash;2010 than 2010&ndash;2020. The
  contradiction is in the forcing data quality (WY2001: 77% T missing, WY2005: 43%
  even after gap-filling), not the model structure.
  <a class="why-btn" onclick="scrollToDecision('D-016')">D-016</a>
  <a class="why-btn" onclick="scrollToDecision('D-029')">D-029</a>
</div>

<h3>4.3.2 Sensitivity of Fixed Parameters</h3>

{fig_tag(4, "Sensitivity of geodetic balance and stake RMSE to fixed parameter perturbation")}

<table class="data-table">
<thead><tr><th>Parameter</th><th>Value</th><th>Geodetic (mod)</th><th>Geodetic bias</th>
<th>Stake RMSE</th></tr></thead>
<tbody>'''

for r in sens_rows:
    is_default = False
    if r["param"] == "lapse_rate" and r["value"].strip() == "-5.0000":
        is_default = True
    elif r["param"] == "rice_ratio" and r["value"].strip() == "2.0000":
        is_default = True
    cls = ' class="highlight-row"' if is_default else ""
    val_display = r["value"].strip()
    pname = "Lapse rate" if r["param"] == "lapse_rate" else "r_ice/r_snow"
    if is_default:
        val_display = f"<strong>{val_display} (used)</strong>"
    html += f'''<tr{cls}><td>{pname}</td><td>{val_display}</td>
<td>{float(r["geodetic_mod"]):.3f}</td><td>{float(r["geodetic_bias"]):+.3f}</td>
<td>{float(r["stake_rmse"]):.3f}</td></tr>
'''

html += f'''</tbody></table>

<div class="finding">
  <div class="finding-title">Lapse rate sensitivity is ~10&times; larger than r_ice/r_snow</div>
  Geodetic bias swings 1.9 m w.e./yr across the lapse range (&minus;4.0 to &minus;6.5 &deg;C/km) versus only 0.13 for
  the r_ice/r_snow ratio range. The &minus;5.0 &deg;C km&minus;&sup1; choice sits near the minimum
  geodetic bias, confirming it is well-centered within the literature range.
  <a class="why-btn" onclick="scrollToDecision('D-029')">D-029</a>
</div>

</div>

<!-- ================================================================ -->
<!-- 4.4 HISTORICAL MASS BALANCE -->
<!-- ================================================================ -->
<div class="section" id="historical">
<h2>4.4 Historical Mass Balance (WY1999&ndash;2025)</h2>

{fig_tag(12, "Climate forcing and modeled mass balance response (WY1999-2025)")}

{fig_tag(5, "Historical glacier-wide annual mass balance with ensemble uncertainty")}

<h3>4.4.1 Key Statistics</h3>

<div class="stats-row results-stat">
  <div class="stat"><div class="stat-value">&minus;0.80</div><div class="stat-label">Mean annual (m w.e./yr)</div></div>
  <div class="stat"><div class="stat-value">&minus;0.92</div><div class="stat-label">Annual trend (m w.e./decade)</div></div>
  <div class="stat"><div class="stat-value">p=0.007</div><div class="stat-label">Trend significance</div></div>
</div>

<table class="data-table">
<thead><tr><th>Component</th><th>Trend (m w.e./decade)</th><th>p-value</th></tr></thead>
<tbody>
<tr><td>Annual balance (B<sub>a</sub>)</td><td>&minus;0.92</td><td>0.007</td></tr>
<tr><td>Summer balance (B<sub>s</sub>)</td><td>&minus;0.49</td><td>0.023</td></tr>
<tr><td>Winter balance (B<sub>w</sub>)</td><td>&minus;0.43</td><td>0.057</td></tr>
</tbody></table>

{fig_tag(6, "Mass balance trends and cumulative balance over the study period")}

<h3>4.4.2 Climate&ndash;Balance Correlations</h3>

<table class="data-table">
<thead><tr><th>Predictor</th><th>r vs B<sub>a</sub></th><th>p-value</th></tr></thead>
<tbody>
<tr><td>Summer temperature (JJA mean)</td><td>&minus;0.80</td><td>&lt; 0.001</td></tr>
<tr><td>Winter precipitation (Oct&ndash;Apr total)</td><td>+0.32</td><td>0.100</td></tr>
</tbody></table>

<div class="finding">
  <div class="finding-title">Summer temperature is the dominant control</div>
  The correlation between annual balance and summer temperature (r = &minus;0.80, p &lt; 0.001)
  is 2.5&times; stronger than with winter precipitation (r = +0.32, p = 0.100). This is
  consistent with Dixon&rsquo;s maritime climate where warm summers drive mass loss.
  Comparison with the Hugonnet geodetic rate (&minus;0.94 m w.e./yr for 2000&ndash;2020) shows
  the modeled ensemble mean (&minus;0.80) captures the long-term trend within the
  uncertainty envelope.
</div>

</div>

<!-- ================================================================ -->
<!-- 4.5 PROJECTIONS -->
<!-- ================================================================ -->
<div class="section" id="proj-results">
<h2>4.5 Projections</h2>

{fig_tag(7, "Projected glacier area, volume, and discharge under three SSPs (2025-2100)")}

<h3>4.5.1 End-of-Century Summary</h3>

<table class="data-table">
<thead><tr><th>Scenario</th><th>Area 2100 (km&sup2;)</th><th>% of 2000</th><th>Peak water year</th>
<th>Peak Q (m&sup3;/s)</th></tr></thead>
<tbody>
<tr><td>SSP1-2.6</td><td>{ssp126_area[0]:.1f} [{ssp126_area[1]:.1f}&ndash;{ssp126_area[2]:.1f}]</td>
<td>{ssp126_area[0]/40.11*100:.0f}%</td>
<td>{pw126_year}</td>
<td>{pw126_q:.1f}</td></tr>
<tr><td>SSP2-4.5</td><td>{ssp245_area[0]:.1f} [{ssp245_area[1]:.1f}&ndash;{ssp245_area[2]:.1f}]</td>
<td>{ssp245_area[0]/40.11*100:.0f}%</td>
<td>{pw245_year}</td>
<td>{pw245_q:.1f}</td></tr>
<tr><td>SSP5-8.5</td><td>{ssp585_area[0]:.1f} [{ssp585_area[1]:.1f}&ndash;{ssp585_area[2]:.1f}]</td>
<td>{ssp585_area[0]/40.11*100:.0f}%</td>
<td>{pw585_year}</td>
<td>{pw585_q:.1f}</td></tr>
</tbody></table>

<div class="finding">
  <div class="finding-title">Peak water timing: WY2049&ndash;2063</div>
  Peak glacial discharge occurs between WY2049 (SSP1-2.6) and WY2063 (SSP5-8.5). Under
  SSP5-8.5, Dixon Glacier loses ~70% of its 2000 area by 2100, retaining only
  {ssp585_area[0]:.1f} km&sup2;. Even under SSP1-2.6, the glacier shrinks to
  {ssp126_area[0]:.0f} km&sup2; ({ssp126_area[0]/40.11*100:.0f}% of 2000 area).
</div>

<h3>4.5.2 Per-GCM Breakdown</h3>
<p>The 5-GCM ensemble spans a range of climate trajectories:
ACCESS-CM2 and EC-Earth3 tend toward warmer/drier futures, while MRI-ESM2-0
is the most conservative (least retreat). GCM spread dominates over parameter
uncertainty in all scenarios.</p>

<details>
<summary>Expand: GCM ensemble details</summary>
<div class="detail-content">
<table class="data-table">
<thead><tr><th>Statistic</th><th>SSP1-2.6</th><th>SSP2-4.5</th><th>SSP5-8.5</th></tr></thead>
<tbody>
<tr><td>Param sets</td><td>{pm126_nparams}</td>
<td>{pm245_nparams}</td>
<td>{pm585_nparams}</td></tr>
<tr><td>GCMs</td><td>{pm126_ngcms}</td>
<td>{pm245_ngcms}</td>
<td>{pm585_ngcms}</td></tr>
<tr><td>Total runs</td><td>{pm126_nruns}</td>
<td>{pm245_nruns}</td>
<td>{pm585_nruns}</td></tr>
<tr><td>Peak Q GCM range</td>
<td>{pw126_gcm_min:.1f}&ndash;{pw126_gcm_max:.1f}</td>
<td>{pw245_gcm_min:.1f}&ndash;{pw245_gcm_max:.1f}</td>
<td>{pw585_gcm_min:.1f}&ndash;{pw585_gcm_max:.1f}</td></tr>
</tbody></table>
</div>
</details>

</div>

<!-- ================================================================ -->
<!-- 4.6 LAPSE RATE SENSITIVITY -->
<!-- ================================================================ -->
<div class="section" id="lapse-results">
<h2>4.6 Lapse Rate Sensitivity</h2>

{fig_tag(8, "Lapse rate sensitivity bracket showing projection uncertainty from fixed lapse choice")}

<h3>4.6.1 Bracket Results</h3>

<table class="data-table">
<thead><tr><th>Lapse rate</th><th>SSP</th><th>Area 2100 (p50)</th><th>Area 2100 (p05&ndash;p95)</th>
<th>Peak water year</th><th>Peak Q (m&sup3;/s)</th></tr></thead>
<tbody>'''

for r in lapse_rows:
    is_central = r["lapse"].strip() == "-5.0"
    cls = ' class="highlight-row"' if is_central else ""
    lbl = f"<strong>{r['lapse']}</strong>" if is_central else r["lapse"]
    html += f'''<tr{cls}><td>{lbl} &deg;C/km</td><td>{r["scenario"].upper()}</td>
<td>{float(r["area_p50"]):.1f} km&sup2;</td>
<td>{float(r["area_p05"]):.1f}&ndash;{float(r["area_p95"]):.1f}</td>
<td>{r["peak_year"]}</td>
<td>{float(r["peak_q"]):.1f}</td></tr>
'''

html += f'''</tbody></table>

<div class="finding">
  <div class="finding-title">SSP choice dominates over lapse rate uncertainty</div>
  The spread between SSP2-4.5 and SSP5-8.5 at any given lapse rate (e.g., ~10 km&sup2;
  at &minus;5.0 &deg;C/km) is comparable to the spread across lapse rates within a single
  SSP (~9 km&sup2; at SSP2-4.5). However, peak water timing is robust across all lapse
  rates, varying by only ~4&ndash;7 years (WY2058&ndash;2065). The key policy-relevant finding
  &mdash; peak water occurs in the 2050s&ndash;2060s &mdash; is insensitive to the lapse rate choice.
  <a class="why-btn" onclick="scrollToDecision('D-030')">D-030</a>
</div>

</div>

<!-- ================================================================ -->
<!-- DECISION LOG -->
<!-- ================================================================ -->
<div class="section" id="decisions">
<h2>Decision Log</h2>
<p>Complete record of all modeling decisions (D-001 through D-{len(decisions):03d}). Click any
entry to expand the full rationale, alternatives considered, and implementation details.</p>

{build_decision_log()}

</div>

</main>

<script>
// Navigation active state
function setActive(el) {{
  document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
  el.classList.add('active');
}}

// Intersection observer for nav highlighting
const sections = document.querySelectorAll('.section');
const navLinks = document.querySelectorAll('nav a[href^="#"]');
const observer = new IntersectionObserver(entries => {{
  entries.forEach(entry => {{
    if (entry.isIntersecting) {{
      navLinks.forEach(a => a.classList.remove('active'));
      const link = document.querySelector(`nav a[href="#${{entry.target.id}}"]`);
      if (link) link.classList.add('active');
    }}
  }});
}}, {{ rootMargin: '-20% 0px -70% 0px' }});
sections.forEach(s => observer.observe(s));

// Decision expand/collapse
function toggleDecision(btn) {{
  const body = btn.nextElementSibling;
  const icon = btn.querySelector('.toggle-icon');
  body.classList.toggle('open');
  icon.textContent = body.classList.contains('open') ? '\u2212' : '+';
}}

// Scroll to decision and expand it
function scrollToDecision(dId) {{
  const items = document.querySelectorAll('.decision-item');
  for (const item of items) {{
    const idSpan = item.querySelector('.decision-id');
    if (idSpan && idSpan.textContent === dId) {{
      item.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
      const body = item.querySelector('.decision-body');
      const icon = item.querySelector('.toggle-icon');
      if (!body.classList.contains('open')) {{
        body.classList.add('open');
        icon.textContent = '\u2212';
      }}
      // Flash highlight
      item.style.outline = '2px solid var(--accent-orange)';
      setTimeout(() => {{ item.style.outline = 'none'; }}, 2000);
      break;
    }}
  }}
}}

// Lightbox
function openLightbox(img) {{
  const lb = document.getElementById('lightbox');
  document.getElementById('lightbox-img').src = img.src;
  lb.classList.add('active');
}}
function closeLightbox() {{
  document.getElementById('lightbox').classList.remove('active');
}}
document.addEventListener('keydown', e => {{
  if (e.key === 'Escape') closeLightbox();
}});
</script>
</body>
</html>'''

# Write the file
outpath = os.path.join(ROOT, "methods_interactive.html")
with open(outpath, "w") as f:
    f.write(html)

print(f"\nWritten: {outpath}")
print(f"Size: {os.path.getsize(outpath) / 1e6:.1f} MB")
