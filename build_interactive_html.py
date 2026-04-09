#!/usr/bin/env python3
"""
Build the methods_interactive.html file with all figures embedded as base64.
"""
import base64
import glob
import json
import os

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

# ── Load decisions.md ───────────────────────────────────────────────
print("Loading decisions...")
with open(os.path.join(ROOT, "research_log/decisions.md")) as f:
    decisions_raw = f.read()

# Parse decisions into individual entries
import re
decisions = {}
# Split on ## D-NNN headers
parts = re.split(r'^## (D-\d{3}:.+)$', decisions_raw, flags=re.MULTILINE)
for i in range(1, len(parts), 2):
    header = parts[i].strip()
    body = parts[i+1].strip() if i+1 < len(parts) else ""
    # Extract D number
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
<title>Dixon Glacier DETIM -- Interactive Methods</title>
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
  width: 260px;
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
  padding: 6px 12px;
  margin: 2px 0;
  color: var(--text-dim);
  text-decoration: none;
  border-radius: var(--radius);
  font-size: 0.85rem;
  transition: all 0.2s;
}}
nav a:hover, nav a.active {{
  background: var(--bg-hover);
  color: var(--accent-blue);
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
  margin-left: 260px;
  padding: 40px 48px;
  max-width: 1100px;
  width: calc(100% - 260px);
}}

/* Sections */
.section {{
  margin-bottom: 48px;
  scroll-margin-top: 24px;
}}
.section h2 {{
  font-size: 1.6rem;
  margin-bottom: 20px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--border);
}}
.section h3 {{
  font-size: 1.2rem;
  margin: 24px 0 12px;
  color: var(--accent-cyan);
}}
.section h4 {{
  font-size: 1.05rem;
  margin: 16px 0 8px;
  color: var(--accent-purple);
}}

/* Color-coded section borders */
#study-site h2 {{ border-color: var(--accent-green); color: var(--accent-green); }}
#model h2 {{ border-color: var(--accent-blue); color: var(--accent-blue); }}
#input-data h2 {{ border-color: var(--accent-cyan); color: var(--accent-cyan); }}
#calibration h2 {{ border-color: var(--accent-orange); color: var(--accent-orange); }}
#validation h2 {{ border-color: var(--accent-purple); color: var(--accent-purple); }}
#projections h2 {{ border-color: var(--accent-red); color: var(--accent-red); }}
#historical h2 {{ border-color: var(--accent-yellow); color: var(--accent-yellow); }}
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
</style>
</head>
<body>

<!-- Sidebar Navigation -->
<nav>
  <h1>Dixon Glacier DETIM</h1>
  <div class="subtitle">Interactive Methods Document</div>
  <div class="nav-section">Sections</div>
  <a href="#study-site" onclick="setActive(this)">Study Site</a>
  <a href="#model" onclick="setActive(this)">Model Description</a>
  <a href="#input-data" onclick="setActive(this)">Input Data</a>
  <a href="#calibration" onclick="setActive(this)">Calibration</a>
  <a href="#validation" onclick="setActive(this)">Validation</a>
  <a href="#historical" onclick="setActive(this)">Historical Reconstruction</a>
  <a href="#projections" onclick="setActive(this)">Projections</a>
  <div class="nav-section">Reference</div>
  <a href="#decisions" onclick="setActive(this)">Decision Log (D-001..031)</a>
  <div class="nav-section">Quick Stats</div>
  <div style="padding:8px 12px;font-size:0.75rem;color:var(--text-dim);">
    Area: 40.11 km&sup2; (2000)<br>
    Elev: 439 &ndash; 1637 m<br>
    Geodetic: &minus;0.94 m w.e./yr<br>
    CAL-013: 1,656 posterior samples<br>
    31 decisions logged
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
<!-- STUDY SITE -->
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
<!-- MODEL DESCRIPTION -->
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

<h3>3.2.6 Implementation</h3>
<p>Python 3.12 + NumPy + Numba JIT compilation. ~240 ms per water-year simulation
on a 100 m grid (4,011 glacier cells).
<a class="why-btn" onclick="scrollToDecision('D-004')">D-004</a>
</p>
</div>

<!-- ================================================================ -->
<!-- INPUT DATA -->
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

</div>

<!-- ================================================================ -->
<!-- CALIBRATION -->
<!-- ================================================================ -->
<div class="section" id="calibration">
<h2>3.4 Calibration</h2>

<p>Two-phase Bayesian approach: differential evolution finds the MAP estimate,
then MCMC (emcee) maps the posterior distribution for projection uncertainty
quantification.
<a class="why-btn" onclick="scrollToDecision('D-017')">D-017</a>
<a class="why-btn" onclick="scrollToDecision('D-027')">D-027</a>
<a class="why-btn" onclick="scrollToDecision('D-028')">D-028</a>
</p>

<h3>3.4.1 Calibrated Parameters</h3>

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
</div>

<h3>3.4.2 Multi-Objective Likelihood</h3>
<p>The MCMC likelihood jointly optimizes stakes + geodetic + snowline elevation
(chi-squared, sigma=75 m). Post-hoc area evolution filter applied after MCMC.
<a class="why-btn" onclick="scrollToDecision('D-028')">D-028</a>
</p>

<div class="equation">
ln L(&theta;) = &minus;0.5 &times; &sum;<sub>i</sub> [(m<sub>i</sub>(&theta;) &minus; o<sub>i</sub>) / &sigma;<sub>i</sub>]&sup2;
</div>

<h3>3.4.3 Posterior Distribution (CAL-013)</h3>

<div class="stats-row">
  <div class="stat"><div class="stat-value">5</div><div class="stat-label">DE seeds</div></div>
  <div class="stat"><div class="stat-value">1</div><div class="stat-label">Mode found</div></div>
  <div class="stat"><div class="stat-value">1,656</div><div class="stat-label">Posterior samples</div></div>
  <div class="stat"><div class="stat-value">0.37</div><div class="stat-label">Acceptance fraction</div></div>
  <div class="stat"><div class="stat-value">1,000</div><div class="stat-label">Filtered params</div></div>
  <div class="stat"><div class="stat-value">1,000/1,000</div><div class="stat-label">Passed area filter</div></div>
</div>

{fig_tag(1, "Posterior parameter distributions from CAL-013 (6 calibrated parameters)")}

<h3>3.4.4 Stake Fit</h3>
{fig_tag(2, "Modeled vs observed stake mass balance for calibration targets")}

<h3>3.4.5 Geodetic Fit</h3>
{fig_tag(3, "Geodetic validation: modeled vs Hugonnet et al. (2021) sub-periods")}

<h3>3.4.6 Equifinality and Parameter Constraints</h3>
<p>Lapse rate is fixed at &minus;5.0 &deg;C km&minus;&sup1; to prevent equifinality with
precip_corr. r_ice derived as 2.0 &times; r_snow to preserve albedo feedback.
<a class="why-btn" onclick="scrollToDecision('D-015')">D-015</a>
<a class="why-btn" onclick="scrollToDecision('D-017')">D-017</a>
</p>

</div>

<!-- ================================================================ -->
<!-- VALIDATION -->
<!-- ================================================================ -->
<div class="section" id="validation">
<h2>3.6 Validation</h2>

<h3>3.6.1 Sub-period Geodetic Comparison</h3>
<p>The model is evaluated against Hugonnet sub-periods that were withheld
from calibration. The model reverses the sub-period trend &mdash; underestimates
2000-2010 mass loss, overestimates 2010-2020 &mdash; consistent with Nuka forcing
quality in early years.
<a class="why-btn" onclick="scrollToDecision('D-029')">D-029</a>
</p>

<table class="data-table">
<thead><tr><th>Period</th><th>Type</th><th>Observed</th><th>Modeled (median)</th>
<th>Bias</th><th>Within unc?</th></tr></thead>
<tbody>
<tr><td>2000&ndash;2020</td><td>calibration</td><td>&minus;0.939 &plusmn; 0.122</td><td>&minus;0.765</td><td>+0.174</td><td>No</td></tr>
<tr><td>2000&ndash;2010</td><td>validation</td><td>&minus;1.072 &plusmn; 0.225</td><td>&minus;0.244</td><td>+0.828</td><td>No</td></tr>
<tr><td>2010&ndash;2020</td><td>validation</td><td>&minus;0.806 &plusmn; 0.202</td><td>&minus;1.287</td><td>&minus;0.481</td><td>No</td></tr>
</tbody></table>

<h3>3.6.2 Posterior Predictive Check by Year</h3>
<p>200 posterior parameter sets evaluated against each stake year independently.</p>

<table class="data-table">
<thead><tr><th>Year</th><th>Site</th><th>Obs (m w.e.)</th><th>Mod (median)</th>
<th>Residual</th></tr></thead>
<tbody>
<tr><td>WY2023</td><td>ABL</td><td>&minus;4.50</td><td>&minus;4.12</td><td>+0.38</td></tr>
<tr><td>WY2023</td><td>ACC</td><td>+0.37</td><td>+0.42</td><td>+0.05</td></tr>
<tr><td>WY2023</td><td>ELA</td><td>+0.10</td><td>&minus;1.31</td><td>&minus;1.41</td></tr>
<tr><td>WY2024</td><td>ABL</td><td>&minus;2.63</td><td>&minus;4.24</td><td>&minus;1.61</td></tr>
<tr><td>WY2024</td><td>ACC</td><td>+1.46</td><td>+0.21</td><td>&minus;1.25</td></tr>
<tr><td>WY2024</td><td>ELA</td><td>+0.10</td><td>&minus;1.42</td><td>&minus;1.52</td></tr>
</tbody></table>

<p>The ELA stake shows persistent &minus;1.4 m w.e. bias attributed to wind redistribution
at the measurement site (southern branch is a preferential deposition zone).
<a class="why-btn" onclick="scrollToDecision('D-031')">D-031</a>
</p>

<h3>3.6.3 Sensitivity of Fixed Parameters</h3>
{fig_tag(4, "Sensitivity of geodetic balance and stake RMSE to fixed parameter perturbation")}

<table class="data-table">
<thead><tr><th>Parameter</th><th>Value</th><th>Geodetic (mod)</th><th>Geodetic bias</th>
<th>Stake RMSE</th></tr></thead>
<tbody>
<tr><td>Lapse rate</td><td>&minus;4.0 &deg;C/km</td><td>&minus;1.631</td><td>&minus;0.692</td><td>1.800</td></tr>
<tr><td>Lapse rate</td><td>&minus;4.5</td><td>&minus;1.216</td><td>&minus;0.277</td><td>1.497</td></tr>
<tr><td>Lapse rate</td><td><strong>&minus;5.0 (used)</strong></td><td>&minus;0.817</td><td>+0.122</td><td>1.227</td></tr>
<tr><td>Lapse rate</td><td>&minus;5.5</td><td>&minus;0.434</td><td>+0.505</td><td>1.005</td></tr>
<tr><td>Lapse rate</td><td>&minus;6.0</td><td>&minus;0.063</td><td>+0.876</td><td>0.850</td></tr>
<tr><td>r_ice/r_snow</td><td>1.50</td><td>&minus;0.773</td><td>+0.166</td><td>1.188</td></tr>
<tr><td>r_ice/r_snow</td><td><strong>2.00 (used)</strong></td><td>&minus;0.817</td><td>+0.122</td><td>1.227</td></tr>
<tr><td>r_ice/r_snow</td><td>3.00</td><td>&minus;0.906</td><td>+0.033</td><td>1.318</td></tr>
</tbody></table>

<p>Lapse rate sensitivity is ~10&times; larger than r_ice/r_snow. The &minus;5.0 &deg;C/km
choice sits near the minimum geodetic bias, confirming it is well-centered
within the literature range.
<a class="why-btn" onclick="scrollToDecision('D-029')">D-029</a>
</p>

</div>

<!-- ================================================================ -->
<!-- HISTORICAL RECONSTRUCTION -->
<!-- ================================================================ -->
<div class="section" id="historical">
<h2>3.5 Historical Reconstruction (WY1999&ndash;2025)</h2>

{fig_tag(12, "Climate forcing and modeled mass balance response (WY1999-2025)")}

{fig_tag(5, "Historical glacier-wide annual mass balance with ensemble uncertainty")}

{fig_tag(6, "Mass balance trends and cumulative balance over the study period")}

</div>

<!-- ================================================================ -->
<!-- PROJECTIONS -->
<!-- ================================================================ -->
<div class="section" id="projections">
<h2>3.5 Projection Ensemble</h2>

<p>250 posterior parameter sets &times; 5 CMIP6 GCMs = 1,250 runs per scenario.
Three SSPs: SSP1-2.6, SSP2-4.5, SSP5-8.5.
<a class="why-btn" onclick="scrollToDecision('D-019')">D-019</a>
<a class="why-btn" onclick="scrollToDecision('D-020')">D-020</a>
</p>

{fig_tag(7, "Projected glacier area, volume, and discharge under three SSPs (2025-2100)")}

<h3>Lapse Rate Sensitivity Bracket</h3>
<p>Projections at &minus;4.5, &minus;5.0, &minus;5.5 &deg;C/km bracket the structural
uncertainty from the fixed lapse rate.
<a class="why-btn" onclick="scrollToDecision('D-030')">D-030</a>
</p>

{fig_tag(8, "Lapse rate sensitivity bracket showing projection uncertainty from fixed lapse choice")}

<table class="data-table">
<thead><tr><th>Lapse rate</th><th>SSP</th><th>Area 2100 (p50)</th><th>Area 2100 (p05&ndash;p95)</th>
<th>Peak water year</th></tr></thead>
<tbody>
<tr><td>&minus;4.5 &deg;C/km</td><td>SSP2-4.5</td><td>18.2 km&sup2;</td><td>15.8&ndash;23.9</td><td>2058</td></tr>
<tr><td>&minus;4.5</td><td>SSP5-8.5</td><td>8.6</td><td>6.2&ndash;21.5</td><td>2061</td></tr>
<tr><td><strong>&minus;5.0</strong></td><td>SSP2-4.5</td><td>22.0</td><td>18.9&ndash;29.3</td><td>2058</td></tr>
<tr><td><strong>&minus;5.0</strong></td><td>SSP5-8.5</td><td>12.1</td><td>11.3&ndash;25.9</td><td>2063</td></tr>
<tr><td>&minus;5.5</td><td>SSP2-4.5</td><td>27.2</td><td>22.5&ndash;33.6</td><td>2061</td></tr>
<tr><td>&minus;5.5</td><td>SSP5-8.5</td><td>14.9</td><td>14.1&ndash;31.2</td><td>2065</td></tr>
</tbody></table>

</div>

<!-- ================================================================ -->
<!-- DECISION LOG -->
<!-- ================================================================ -->
<div class="section" id="decisions">
<h2>Decision Log</h2>
<p>Complete record of all modeling decisions (D-001 through D-031). Click any
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
