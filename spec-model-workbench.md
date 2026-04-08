# Model Workbench Skill — Specification

**Status:** Draft v1
**Date:** 2026-04-07
**Purpose:** A Claude Code skill that systematically analyzes scientific modeling codebases and generates an interactive browser-based exploration tool from the findings.

---

## 1. Problem Statement

The Model Workbench Skill (`/model-workbench`) guides Claude through a rigorous, multi-pass analysis of a scientific modeling codebase, then generates a self-contained interactive web application from the structured findings. The skill's primary value is its **exploration methodology** — the detailed instructions for how deeply to look, what to extract, and how to connect the pieces. The UI is a delivery mechanism for the analysis.

### 1.1 Problems It Solves

- **Shallow analysis**: Without explicit guidance, Claude reads code at surface level — function signatures and docstrings, not the actual equations, constants, data shapes, and decision histories buried in the implementation. The skill prescribes line-by-line extraction of equations as they actually appear in code.
- **Missing connections**: A modeling codebase has deep links between equations in code, parameters in configs, observations in CSVs, decisions in logs, and citations in comments. Claude won't trace these unless instructed to build an explicit relationship graph.
- **No systematic methodology**: Each analysis starts from scratch. There is no reusable protocol for "here's how you study a scientific model" that guarantees completeness across projects.
- **Inaccessible to non-technical collaborators**: An adviser who understands glacier dynamics shouldn't need to read Numba-compiled Python to verify the model implements Hock (1999) correctly. The output must be navigable by domain experts who don't write code.
- **Scattered documentation**: Design decisions live in research logs, equations in code, data in CSVs, literature in PDFs. No single place shows how they connect or what evidence supports each choice.

### 1.2 Important Boundaries

The workbench does NOT:
- Run the model or execute simulations
- Modify source code, data files, or documentation
- Make scientific judgments about modeling choices
- Fetch literature from the internet (Phase 2 extension)
- Require a running server — it produces static HTML viewable from `file://`

The workbench is a **read-only explorer**. It extracts, structures, and presents what is already in the codebase.

---

## 2. Goals and Non-Goals

### 2.1 Goals

- The skill prescribes a **multi-pass exploration protocol** that guarantees Claude reads every source file, every data file, every documentation file, and every reference — not just entry points and READMEs
- The protocol is **project-agnostic**: it discovers project structure rather than assuming it. No hardcoded paths like `research_log/decisions.md` — the skill finds decision logs, configs, and data files wherever they live
- A **non-technical domain expert** (e.g., thesis adviser) can open the generated workbench, navigate to an equation, and see: what it does in plain English, the paper it comes from, the code that implements it, the data it operates on, and the evidence base for the choice
- Every modeling decision is a navigable card showing: the decision, the rationale, ALL supporting literature (not just one paper), alternatives considered, and what depends on it
- Actual project data is browsable as **interactive tables and time series charts** (Plotly.js) with pan, zoom, and filtering — not static dumps
- Every equation is rendered in LaTeX with a plain-English explanation, a worked example using real project values, and links to the code and literature
- Intermediate analysis results are saved as structured JSON, so the analysis survives even if the build step fails, and future runs can build incrementally
- When Claude encounters code it cannot cleanly extract (complex kernels, implicit equations), it marks a **confidence level** rather than silently skipping — the output flags what may need manual review

### 2.2 Non-Goals

- Running simulations or parameter sweeps from the UI
- Editing code, data, or research logs through the workbench
- AI chat interface (deferred to Phase 2)
- Automatic literature fetching from the internet (deferred to Phase 2)
- Multi-user collaboration or remote deployment
- Replacing existing documentation — the workbench reads and surfaces it, it doesn't own it
- Supporting extremely large codebases (500+ source files) — the current protocol assumes manageable projects (~50 source files, ~20 data files)

---

## 3. System Overview

### 3.1 Main Components

The skill has two phases: **Explore** (three passes) and **Build** (one pass).

1. `Pass 1 — Survey`
   - Maps the project: file tree, git history, entry points, module dependencies
   - Classifies every file by role: source, data, config, documentation, output, literature
   - Discovers project-specific conventions (decision log format, data directory layout)
   - Output: `_workbench/manifest.json`

2. `Pass 2 — Extract`
   - Reads every file identified in Pass 1
   - From source: equations, constants, parameter bounds, function signatures, comments referencing papers or decisions
   - From data: schemas, row counts, column types, value ranges, temporal/spatial extent
   - From docs/logs: decision entries, rationale, references to external sources
   - From PDFs/references: filename, title (from metadata), which code files reference it
   - Output: `_workbench/entities.json`

3. `Pass 3 — Connect`
   - Builds a relationship graph across all entities
   - Traces: Parameter → Equation(s) → Decision(s) → Citation(s)
   - Traces: Data file → Code that loads it → What it's used for
   - Traces: Decision → What changed → What depends on it → Evidence base
   - Output: `_workbench/graph.json`

4. `Build`
   - Takes the three JSON files and generates a self-contained HTML application
   - Five views: Architecture, Data Browser, Decision Cards, Equation Reference, Explorer
   - Uses Plotly.js (CDN) for interactive charts, MathJax (CDN) for equation rendering
   - Output: `_workbench/index.html` (+ any supporting JS/CSS files)

### 3.2 Abstraction Layers

| Layer | Concern | Files |
|-------|---------|-------|
| Exploration Protocol | What to look for, how deep, in what order | SKILL.md instructions |
| Structured Findings | Intermediate JSON schema for entities and relationships | manifest.json, entities.json, graph.json |
| Presentation | HTML/JS/CSS rendering of findings into navigable views | index.html, app.js, styles.css |

### 3.3 External Dependencies

- **Plotly.js** (CDN): Interactive charts for time series and scatter plots. ~3MB, loaded from `cdn.plot.ly`
- **MathJax** (CDN): LaTeX equation rendering. Loaded from `cdn.jsdelivr.net`
- **Google Fonts — Fira Code** (CDN): Monospace font for code and ASCII diagrams. Loaded from `fonts.googleapis.com`
- **Claude API** (future, Phase 2 only): For embedded chat. Not required in Phase 1
- **Python `http.server`** (optional): For local serving. Not required — `file://` works for all features except fonts (CORS)

---

## 4. Core Domain Model

### 4.1 Entity: `SourceFile`

A source code file discovered in the project.

Fields:
- `path` (string)
  - Relative path from project root
- `language` (string)
  - Detected language: "python", "r", "matlab", "fortran", "julia", etc.
- `role` (string)
  - Classification: "model_core", "calibration", "analysis", "utility", "test", "config", "entry_point"
- `line_count` (integer)
  - Total lines in file
- `functions` (list of Function)
  - All functions/methods defined in the file
- `equations` (list of Equation)
  - Equations extracted from the code
- `constants` (list of Constant)
  - Named constants and magic numbers
- `imports` (list of string)
  - Internal and external dependencies
- `references` (list of Reference)
  - Citations found in comments (author-year, DOI, URLs)

### 4.2 Entity: `Equation`

A mathematical equation implemented in source code.

Fields:
- `id` (string)
  - Auto-generated unique identifier: `{file}:{start_line}`
- `source_file` (string)
  - Path to the file containing the equation
- `line_range` (tuple of integer)
  - Start and end line numbers
- `function_name` (string, nullable)
  - Function that contains the equation, if applicable
- `latex` (string)
  - LaTeX representation of the equation
- `plain_english` (string)
  - One-paragraph explanation accessible to a non-technical domain expert
- `code_snippet` (string)
  - The actual code implementing the equation (verbatim)
- `variables` (list of Variable)
  - Every variable in the equation: symbol, name, units, typical range, where it comes from
- `worked_example` (string)
  - One concrete calculation using real project values
- `citations` (list of Reference)
  - Papers this equation comes from
- `confidence` (string)
  - "high": equation clearly extracted and verified
  - "medium": equation extracted but involves complex control flow or multiple functions
  - "low": best-effort extraction, may be incomplete — flagged for manual review
- `confidence_note` (string, nullable)
  - Explanation of why confidence is not "high"

### 4.3 Entity: `Parameter`

A calibrated, configured, or fixed model parameter.

Fields:
- `name` (string)
  - Parameter name as it appears in code
- `symbol` (string, nullable)
  - Mathematical symbol (e.g., "MF", "λ", "T₀")
- `value` (float or string)
  - Current/default value
- `units` (string)
  - Physical units
- `bounds` (tuple of float, nullable)
  - Calibration bounds [lower, upper], null if fixed
- `is_fixed` (boolean)
  - Whether this parameter is fixed or calibrated
- `source` (string)
  - Where the value is set: file path and line number
- `calibrated_value` (object, nullable)
  - If calibrated: {median, ci_16, ci_84, map_estimate}
- `decisions` (list of string)
  - Decision IDs that affect this parameter
- `equations` (list of string)
  - Equation IDs that use this parameter
- `rationale` (string, nullable)
  - Why this value/bound was chosen

### 4.4 Entity: `Decision`

A documented modeling decision or design choice.

Fields:
- `id` (string)
  - Identifier as found in the project (e.g., "D-012", "ADR-003", or auto-generated)
- `title` (string)
  - Short description of the decision
- `summary` (string)
  - Plain-English explanation of what was decided and why
- `full_text` (string)
  - Complete decision text as found in the source document
- `source_file` (string)
  - Path to the document containing the decision
- `evidence_base` (list of EvidenceEntry)
  - All supporting references, each with: citation, relevance note, strength
- `alternatives_considered` (list of string)
  - What was tried before or considered and rejected
- `what_changed` (list of string)
  - Files and parameters affected by this decision
- `depends_on` (list of string)
  - Other decision IDs this builds upon
- `depended_on_by` (list of string)
  - Other decision IDs that build upon this one
- `what_would_break` (string, nullable)
  - Description of consequences if this decision were reversed

### 4.5 Entity: `EvidenceEntry`

A single piece of evidence supporting a decision.

Fields:
- `citation` (string)
  - Author-year or full citation (e.g., "Hock (1999)", "Gardner & Sharp 2009")
- `doi` (string, nullable)
  - DOI if found
- `local_path` (string, nullable)
  - Path to local PDF if found
- `relevance` (string)
  - How this source supports the decision
- `strength` (string)
  - "primary": the main source for this decision
  - "supporting": additional evidence
  - "context": background information, not direct support

### 4.6 Entity: `DataFile`

A data file discovered in the project.

Fields:
- `path` (string)
  - Relative path from project root
- `format` (string)
  - "csv", "json", "geotiff", "shapefile", "npy", "npz", "pdf", "other"
- `role` (string)
  - "input", "calibration_target", "calibration_output", "projection_output", "validation", "reference"
- `size_bytes` (integer)
  - File size
- `schema` (object, nullable)
  - For tabular data: {columns: [{name, type, min, max, mean, n_null}], row_count, date_range}
- `loaded_by` (list of string)
  - Source files that read this data (file:line)
- `used_for` (string)
  - Plain-English description of the file's purpose
- `has_timeseries` (boolean)
  - Whether this file contains time series data suitable for interactive charting
- `timeseries_config` (object, nullable)
  - If has_timeseries: {date_column, value_columns, units, suggested_chart_type}

### 4.7 Entity: `Function`

A function or method defined in source code.

Fields:
- `name` (string)
  - Function name
- `file` (string)
  - Source file path
- `line` (integer)
  - Line number of definition
- `signature` (string)
  - Full signature with parameter names and types if available
- `docstring` (string, nullable)
  - Docstring content if present
- `calls` (list of string)
  - Functions this function calls (internal only)
- `called_by` (list of string)
  - Functions that call this function

### 4.8 Normalization Rules

- File paths are always relative to project root, using forward slashes
- Parameter names are compared case-sensitively as they appear in code
- Decision IDs are compared case-insensitively with whitespace stripped
- Citations are normalized to "Author (Year)" format where possible for deduplication
- Equation IDs are formed as `{relative_file_path}:{start_line_number}`

---

## 5. Exploration Protocol — Pass 1: Survey

### 5.1 Discovery

The skill instructs Claude to perform the following, in order:

1. **Project root detection**: Identify the working directory. Check for `.git/`, `setup.py`, `pyproject.toml`, or similar markers.

2. **File tree**: List all files in the project, excluding:
   - `.git/`, `__pycache__/`, `.venv/`, `venv/`, `node_modules/`
   - Files matching `.gitignore` patterns
   - Binary files > 50MB (log their existence but don't read)

3. **Git history**: `git log --oneline -50` for recent activity. `git shortlog -sn` for contributors.

4. **Entry points**: Find all files with `if __name__` blocks, `main()` functions, or script-like structure. These are the execution roots.

5. **File classification**: For every file, assign a role:
   - `source`: `.py`, `.r`, `.m`, `.f90`, `.jl` files containing model logic
   - `config`: Files defining constants, parameters, settings (often named `config.*`, `settings.*`, `params.*`)
   - `data_input`: CSV, JSON, GeoTIFF, shapefiles in data directories
   - `data_output`: Files in output directories (calibration_output, results, etc.)
   - `documentation`: Markdown, text, notebook files (.md, .txt, .ipynb)
   - `literature`: PDF files, BibTeX files (.bib)
   - `test`: Files in test directories or with `test_` prefix
   - `other`: Everything else

6. **Convention detection**: Look for project-specific patterns:
   - Decision log format (numbered entries? dated entries? ADRs?)
   - Data directory structure (flat? organized by type?)
   - Configuration approach (single config file? scattered constants?)
   - Documentation format (research log? README only? wiki?)

### 5.2 Output Schema: `manifest.json`

```json
{
  "project_root": "/absolute/path",
  "project_name": "detected or dirname",
  "vcs": "git",
  "recent_commits": [{"hash": "abc123", "message": "...", "date": "..."}],
  "contributors": [{"name": "...", "commits": 42}],
  "file_tree": {
    "path": "relative/path.py",
    "role": "source",
    "size_bytes": 1234,
    "language": "python"
  },
  "entry_points": ["run_calibration_v13.py", "run_projection.py"],
  "conventions": {
    "decision_log_format": "numbered (D-001 through D-028) in research_log/decisions.md",
    "data_layout": "data/ for inputs, calibration_output/ for outputs",
    "config_approach": "single dixon_melt/config.py with all constants"
  }
}
```

### 5.3 Validation

- Every file in the project must be classified. No file should be silently ignored.
- Entry points must be verified by checking for `if __name__` or equivalent.
- If no decision log is found, note this in conventions as `"decision_log_format": "none detected"`.

---

## 6. Exploration Protocol — Pass 2: Extract

### 6.1 Source File Extraction

For EVERY source file identified in Pass 1, Claude must:

1. **Read the entire file**, not just the first N lines or function signatures.

2. **Extract equations**: Look for mathematical operations that implement physical or statistical equations. Signs of an equation:
   - Multiple arithmetic operations in sequence
   - Comments mentioning "equation", "formula", references to papers
   - Variable names matching physical quantities (temperature, melt, flux, etc.)
   - NumPy/SciPy operations that implement matrix equations

   For each equation found:
   - Write the LaTeX representation
   - Write a plain-English explanation that a non-coder domain expert can understand
   - Record the exact code snippet
   - List every variable: name, what it represents, units, where its value comes from
   - Create a worked example using real values from the project (pull constants from config, sample data from data files)
   - Assign confidence: high/medium/low with explanation

3. **Extract constants**: Every named constant, magic number, or hardcoded value:
   - Name, value, units
   - Where it's defined (file:line)
   - Where it's used
   - Whether it's configurable or truly fixed
   - Source/rationale if stated in comments

4. **Extract parameters**: Every calibrated or configurable value:
   - Name, bounds, default, units
   - Whether it's currently free (calibrated) or fixed
   - Decision history (which decisions affected it)
   - Calibrated posterior if available (median, CI)

5. **Extract references**: Every mention of external sources in comments:
   - Author-year citations (e.g., "Hock 1999", "Gardner & Sharp 2009")
   - DOIs
   - URLs
   - References to other tools or models ("following PyGEM", "OGGM convention")

6. **Extract function signatures**: Every function/method with:
   - Full signature including parameter names and types
   - Docstring if present
   - Call graph (what it calls, what calls it)
   - Line number

### 6.2 Data File Extraction

For EVERY data file identified in Pass 1:

**Tabular data (CSV, TSV, JSON arrays):**
- Column names, inferred types (date, float, int, string, categorical)
- Row count
- For numeric columns: min, max, mean, std, n_null
- For date columns: earliest, latest, frequency
- First 3 rows and last 3 rows as sample data
- Whether it contains time series data (has a date column + numeric columns)

**Geospatial data (GeoTIFF, shapefiles):**
- CRS, extent (bounding box), resolution
- Band count, data type, nodata value
- Min/max/mean of data values
- File size

**NumPy files (.npy, .npz):**
- Shape, dtype
- Min/max/mean if numeric
- Key names if .npz

**PDF files:**
- Title from metadata (or first line of first page)
- Page count
- Which source files or decisions reference this PDF

### 6.3 Documentation Extraction

For EVERY documentation/log file:

**Decision logs** (any format):
- Parse each decision entry: ID, title, full text
- Extract all citations within each decision
- Extract references to code files or parameters
- Extract alternatives considered (look for "tried", "rejected", "instead of", "previously")
- Extract dependency language (look for "because of D-xxx", "building on", "following")

**Research logs, READMEs, notebooks:**
- Extract any structured information about the model
- Note cross-references to code, data, or papers

### 6.4 Output Schema: `entities.json`

```json
{
  "source_files": [
    {
      "path": "dixon_melt/melt.py",
      "language": "python",
      "role": "model_core",
      "line_count": 71,
      "functions": [...],
      "equations": [...],
      "constants": [...],
      "references": [...]
    }
  ],
  "data_files": [
    {
      "path": "data/stake_observations_dixon.csv",
      "format": "csv",
      "role": "calibration_target",
      "schema": {
        "columns": [
          {"name": "site_id", "type": "string", "unique_values": ["ABL","ELA","ACC"]},
          {"name": "mb_obs_mwe", "type": "float", "min": -5.35, "max": 3.53, "mean": -0.24}
        ],
        "row_count": 25
      },
      "has_timeseries": false,
      "loaded_by": ["run_calibration_v13.py:513"]
    }
  ],
  "decisions": [...],
  "all_equations": [...],
  "all_parameters": [...],
  "all_references": [...]
}
```

### 6.5 Confidence Marking

Every equation extraction must include a confidence level:

- **high**: The equation is clearly stated in a single code block, variables are well-named, and there is a direct mapping to a known formula. Example: `melt = (MF + r * I_pot) * max(T, 0)` — obvious DETIM Method 2.
- **medium**: The equation is spread across multiple lines or functions, involves conditional logic, or uses intermediate variables that require tracing. Example: the solar radiation computation that spans helper functions.
- **low**: The equation involves complex Numba kernels, implicit iteration, or code patterns that resist clean mathematical extraction. Example: the delta-h glacier dynamics loop with conditional deglaciation.

If confidence is not "high", the `confidence_note` field must explain what Claude was unsure about and what a human reviewer should check.

---

## 7. Exploration Protocol — Pass 3: Connect

### 7.1 Relationship Tracing

Claude builds a graph connecting entities from Pass 2:

**Parameter → Equation**: For each parameter, find every equation that uses it. Trace through variable assignments and function arguments.

**Parameter → Decision**: For each parameter, find every decision that discusses it (by name or by concept). Include decisions that set its value, changed its bounds, fixed it, or removed it from calibration.

**Decision → Citation**: For each decision, collect all citations. For each citation, determine its role:
- "primary": The paper that directly motivates the decision
- "supporting": Additional evidence
- "context": Background that informed the decision

**Decision → Decision**: Find dependency chains. D-015 (fix lapse rate) enabled D-017 (reduce free params) which enabled D-027 (multi-seed DE). These chains explain why decisions were made in a particular order.

**Data File → Code**: For each data file, find every code location that loads, reads, or references it.

**Data File → Purpose**: Classify what each data file is used for in the modeling workflow (forcing data, calibration target, validation, output).

### 7.2 Evidence Aggregation

For each decision, aggregate the evidence base:

- Count: how many distinct sources support this decision
- Classify: all primary, all supporting, all context
- Flag: decisions with only 1 source (may need more evidence)
- Flag: decisions with only "context" sources (no direct evidence)
- Note: if the decision explicitly states it's based on the author's judgment rather than literature

### 7.3 Output Schema: `graph.json`

```json
{
  "param_to_equations": {
    "MF": ["dixon_melt/melt.py:67", "dixon_melt/fast_model.py:174"]
  },
  "param_to_decisions": {
    "MF": ["D-008", "D-017"]
  },
  "decision_to_citations": {
    "D-012": [
      {"citation": "Hock (1999)", "role": "context"},
      {"citation": "Braithwaite (2008)", "role": "supporting"}
    ]
  },
  "decision_dependencies": {
    "D-017": {"depends_on": ["D-015"], "depended_on_by": ["D-027", "D-028"]}
  },
  "data_to_code": {
    "data/stake_observations_dixon.csv": ["run_calibration_v13.py:513"]
  },
  "evidence_flags": [
    {"decision": "D-011", "flag": "single_source", "note": "Only Winstral (2002) cited"}
  ]
}
```

---

## 8. Build Phase — Generated Application

### 8.1 Output Structure

```
_workbench/
  index.html          # Main application (single page, tabbed views)
  manifest.json       # Pass 1 output
  entities.json       # Pass 2 output
  graph.json          # Pass 3 output
```

The application is a single HTML file with embedded CSS and JavaScript. It loads `entities.json` and `graph.json` at startup (via inline `<script>` tags or fetch from same directory). External dependencies (Plotly.js, MathJax, Fira Code font) are loaded from CDN.

### 8.2 View: Architecture

Auto-generated ASCII diagram using the Python `L()`/`hit()` approach from the existing architecture-diagram skill. The diagram is generated from `manifest.json` entry points and module structure.

Detail panels are populated from `entities.json` — every module's equations, parameters, and data dependencies are auto-populated, not hand-authored.

Progressive disclosure (collapsible sections) for dense content.

### 8.3 View: Data Browser

Every data file in `entities.json` with a schema gets a browsable view:

**Tabular data:**
- Sortable, filterable table showing all rows
- Column headers show type and units
- Search/filter bar for text columns
- Sort by clicking column headers

**Time series data** (any table with `has_timeseries: true`):
- Plotly.js chart with:
  - X-axis: date column
  - Y-axis: numeric columns (selectable)
  - Pan, zoom, range slider
  - Hover tooltips showing exact values
  - Ability to toggle series on/off
- Chart configuration derived from `timeseries_config` in entities.json

**Non-tabular data:**
- Metadata card showing: path, format, size, CRS, extent, resolution
- Used by: list of code files that reference this data

### 8.4 View: Decision Cards

Each decision from `entities.json` rendered as a card:

**Card layout:**
1. **Header**: Decision ID + title
2. **Summary**: Plain-English explanation (2-3 sentences)
3. **Evidence Base**: Collapsible list of all citations with:
   - Citation text
   - Role badge: "primary" (blue), "supporting" (green), "context" (gray)
   - Relevance note explaining how this source supports the decision
   - Link to local PDF if available
   - Count header: "Supported by N sources"
4. **What Changed**: List of files and parameters affected (clickable → jump to equation or parameter)
5. **Alternatives Considered**: Collapsible section showing what was tried before and why it was rejected
6. **Dependencies**: Visual chain showing which decisions this builds on and which build on it
7. **Impact Assessment**: "What would break" note if available

**Flags:**
- Decisions with only 1 citation get a subtle "single source" indicator
- Decisions based on author judgment (not literature) get a "judgment call" indicator

### 8.5 View: Equation Reference

Each equation from `entities.json` rendered as a reference card:

**Card layout:**
1. **Equation**: LaTeX rendered by MathJax, centered, prominent
2. **In Plain English**: 1-2 paragraph explanation accessible to domain experts. No jargon. Uses analogies where helpful.
3. **Variables**: Table with columns: Symbol, Name, Units, Typical Range, Source (clickable → parameter or constant)
4. **Worked Example**: Box showing one calculation with real project values. E.g., "On a 10°C day at 804m elevation with I_pot = 250 W/m²: M = (7.11 + 0.00196 × 250) × 10 = 75.9 mm/day"
5. **Code**: Collapsible section showing the actual code snippet with file:line reference
6. **Literature**: Citations with links, showing which paper this equation comes from
7. **Confidence**: Badge showing high/medium/low with explanation if not high

### 8.6 View: Explorer

A search interface across all entity types:

- Single search bar at top
- As user types, results appear grouped by type: Equations, Parameters, Decisions, Data Files, Functions
- Each result shows: entity name, type badge, one-line summary, file location
- Clicking a result navigates to the appropriate view (equation card, decision card, data browser, etc.)
- Search matches against: names, descriptions, plain-English explanations, decision text, citation text

Implementation: Vanilla JavaScript text matching against entities.json content. No server required.

---

## 9. Failure Model

### 9.1 Failure Classes

1. **Extraction Failure**: Claude cannot parse a source file (encoding issue, binary file misclassified, extremely long file)
   - **Recovery**: Log the file as "extraction_failed" in entities.json with error message. Continue to next file. Flag in the generated output.

2. **Equation Confidence**: Claude cannot cleanly extract an equation
   - **Recovery**: Extract best-effort with confidence "low". Include the raw code snippet. Add to a "Needs Review" section in the output.

3. **Data File Unreadable**: CSV with encoding issues, corrupted GeoTIFF, etc.
   - **Recovery**: Record metadata (path, size, format) but skip schema extraction. Note "schema extraction failed" in entities.json.

4. **Missing Conventions**: No decision log found, no research log, no literature directory
   - **Recovery**: Note absence in manifest.json conventions. The workbench generates without those views (Decision Cards tab is empty or shows "No decision log found").

5. **Build Failure**: HTML generation fails (template error, JSON too large for inline embedding)
   - **Recovery**: The three JSON files in `_workbench/` survive. User can inspect raw analysis even if the UI doesn't build.

### 9.2 Graceful Degradation

The generated workbench should work with partial data:
- No decisions found → Decision Cards tab shows explanatory message, not an error
- No PDFs found → Literature links show "no local copy" instead of breaking
- No time series data → Data Browser shows tables only, no chart tab
- Equation confidence all "low" → Equation Reference shows all cards with prominent review flags

---

## 10. Security

### 10.1 Trust Boundary

- The skill reads from the project directory only. It does not access files outside the project root.
- Generated HTML loads external resources only from CDN (Plotly.js, MathJax, Google Fonts). No data is sent to external services.
- The `_workbench/` directory contains project data in JSON format. It should be treated as potentially sensitive (may contain file paths, data values, parameter values).

### 10.2 Filesystem Safety

- All file reads are relative to the project root
- The skill writes only to `_workbench/` within the project root
- No file outside `_workbench/` is modified or created
- Binary files > 50MB are noted but not read

### 10.3 HTML Safety

- All content in the generated HTML is built using safe DOM methods (`createElement`, `textContent`), not `innerHTML`
- No user input is rendered unsanitized — all content comes from the pre-built JSON

---

## 11. Reference Algorithm: Exploration Protocol

```
function explore_and_build(project_root):
    
    # Pass 1: Survey
    manifest = {}
    manifest.file_tree = list_all_files(project_root, exclude=[".git", "__pycache__", ".venv"])
    manifest.git_log = run("git log --oneline -50")
    manifest.entry_points = find_files_with_main_block(manifest.file_tree)
    
    for file in manifest.file_tree:
        file.role = classify_file(file.path, file.extension, file.parent_dir)
    
    manifest.conventions = detect_conventions(manifest.file_tree)
    save("_workbench/manifest.json", manifest)
    
    # Pass 2: Extract
    entities = {source_files: [], data_files: [], decisions: [], equations: [], parameters: [], references: []}
    
    for file in manifest.file_tree where file.role == "source":
        content = read_entire_file(file.path)
        file_entity = extract_source_file(content, file.path)
        # extract_source_file reads line by line, finding:
        #   - function definitions (name, signature, docstring, line)
        #   - equations (latex, plain_english, code, variables, worked_example, confidence)
        #   - constants (name, value, units, line)
        #   - references in comments (author-year, DOI, URL)
        entities.source_files.append(file_entity)
        entities.equations.extend(file_entity.equations)
        entities.parameters.extend(file_entity.parameters)
    
    for file in manifest.file_tree where file.role in ["data_input", "data_output", "calibration_target"]:
        data_entity = extract_data_file(file.path, file.format)
        # extract_data_file reads the file and extracts:
        #   - schema (columns, types, ranges, row_count)
        #   - sample values
        #   - time series detection
        entities.data_files.append(data_entity)
    
    for file in manifest.file_tree where file.role == "documentation":
        decisions = extract_decisions(file.path, manifest.conventions.decision_log_format)
        entities.decisions.extend(decisions)
    
    for file in manifest.file_tree where file.role == "literature":
        ref = extract_literature_metadata(file.path)
        entities.references.append(ref)
    
    save("_workbench/entities.json", entities)
    
    # Pass 3: Connect
    graph = {}
    
    for param in entities.parameters:
        graph.param_to_equations[param.name] = find_equations_using(param, entities.equations)
        graph.param_to_decisions[param.name] = find_decisions_mentioning(param, entities.decisions)
    
    for decision in entities.decisions:
        graph.decision_to_citations[decision.id] = classify_citations(decision.evidence_base)
        graph.decision_dependencies[decision.id] = find_decision_dependencies(decision, entities.decisions)
    
    for data_file in entities.data_files:
        graph.data_to_code[data_file.path] = find_code_loading(data_file.path, entities.source_files)
    
    graph.evidence_flags = flag_weak_evidence(graph.decision_to_citations)
    
    save("_workbench/graph.json", graph)
    
    # Build
    html = generate_workbench_html(manifest, entities, graph)
    save("_workbench/index.html", html)
    open_in_browser("_workbench/index.html")
```

---

## 12. Test and Validation Matrix

### 12.1 Core Conformance

**Pass 1 — Survey:**
- [ ] Every file in the project is classified (no file silently ignored)
- [ ] Entry points are correctly identified
- [ ] Convention detection finds decision log format if one exists
- [ ] manifest.json is valid JSON and can be loaded

**Pass 2 — Extract:**
- [ ] Every source file is read in its entirety (not truncated)
- [ ] Equations are extracted with LaTeX, plain English, code snippet, and variables
- [ ] Every extracted equation has a confidence level
- [ ] Data file schemas include all columns with types and ranges
- [ ] Time series data is correctly detected (has date column + numeric columns)
- [ ] Decisions include full text, not just summaries
- [ ] References are extracted from comments in source files

**Pass 3 — Connect:**
- [ ] Every parameter links to at least one equation
- [ ] Every decision links to its citations
- [ ] Decision dependency chains are traced (A depends on B)
- [ ] Evidence flags identify single-source decisions
- [ ] Data files link to code that loads them

**Build:**
- [ ] Generated HTML opens in browser without errors
- [ ] Architecture view renders with clickable modules
- [ ] Data Browser shows interactive Plotly.js charts for time series
- [ ] Decision Cards render with evidence base
- [ ] Equation Reference renders LaTeX via MathJax
- [ ] Explorer search returns results across entity types
- [ ] Progressive disclosure (collapsible sections) works

### 12.2 Quality Checks

- [ ] Plain-English equation explanations are understandable by a non-coder with domain knowledge
- [ ] Worked examples use actual project values, not placeholders
- [ ] No "...", "e.g.", "various", or other summary shortcuts in data tables — all rows shown
- [ ] Confidence levels are assigned honestly (not everything marked "high")
- [ ] Decision cards show ALL cited papers, not just the first one found

---

## 13. Implementation Checklist

### 13.1 MVP (Phase 1)

- [ ] SKILL.md with complete exploration protocol (Pass 1, 2, 3 instructions)
- [ ] Pass 1: file tree, entry points, git log, convention detection → manifest.json
- [ ] Pass 2: source files → equations, constants, params, functions, references
- [ ] Pass 2: data files → schemas, row counts, time series detection
- [ ] Pass 2: documentation → decisions, evidence bases
- [ ] Pass 2: literature → PDF metadata
- [ ] Pass 3: parameter-equation-decision-citation graph
- [ ] Pass 3: evidence aggregation and flagging
- [ ] Build: Architecture view (auto-generated from manifest)
- [ ] Build: Data Browser with Plotly.js interactive time series
- [ ] Build: Decision Cards with evidence base and dependency chains
- [ ] Build: Equation Reference with LaTeX + plain English + worked examples
- [ ] Build: Explorer search
- [ ] Build: single self-contained HTML output
- [ ] Confidence marking on all equation extractions
- [ ] Graceful degradation for missing components

### 13.2 Phase 2 Extensions

- [ ] AI chat interface (Claude API) grounded in entities.json
- [ ] PDF content extraction (parse abstracts, relevant sections from local PDFs)
- [ ] Active literature fetching (search by DOI/title, download abstracts)
- [ ] Diff view: compare two calibration runs or model versions
- [ ] Export: generate thesis-ready Methods section from equations + decisions
- [ ] Incremental update: re-run only passes whose source files changed (via git diff)
- [ ] Large project support: heuristic for switching from "read everything" to "targeted exploration"
