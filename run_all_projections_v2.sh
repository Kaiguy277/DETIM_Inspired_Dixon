#!/bin/bash
# Run ALL projections from WY2001 with 250 params (top-ranked from v13 posterior).
# This replaces all previous projection runs with continuous 2001-2100 trajectories.
#
# Total: 3 baseline + 9 lapse sensitivity = 12 projection runs
# Estimated: ~4 hours at ~20 min per scenario
#
# Usage: bash run_all_projections_v2.sh

set -e
source .venv/bin/activate

PARAMS="calibration_output/filtered_params_v13_top250.json"
echo "========================================"
echo "FULL PROJECTION RERUN — WY2001 to WY2100"
echo "Params: $PARAMS (250 sets)"
echo "Start: $(date)"
echo "========================================"

# ── Baseline projections (3 SSPs) ──────────────────────────
echo ""
echo "=== BASELINE PROJECTIONS ==="

echo ""
echo "--- SSP1-2.6 ---"
python run_projection.py --scenario ssp126 --filtered-params "$PARAMS"

echo ""
echo "--- SSP2-4.5 ---"
python run_projection.py --scenario ssp245 --filtered-params "$PARAMS"

echo ""
echo "--- SSP5-8.5 ---"
python run_projection.py --scenario ssp585 --filtered-params "$PARAMS"

# ── Lapse rate sensitivity (3 lapse × 3 SSPs = 9 runs) ────
echo ""
echo "=== LAPSE RATE SENSITIVITY ==="
python run_lapse_sensitivity_projections.py

# ── Done ───────────────────────────────────────────────────
echo ""
echo "========================================"
echo "ALL PROJECTIONS COMPLETE"
echo "End: $(date)"
echo "========================================"

# Regenerate figures with new data
echo ""
echo "=== REGENERATING FIGURES ==="
python plot_methods_figures.py
python plot_context_figures.py

# Rebuild interactive HTML
echo ""
echo "=== REBUILDING HTML ==="
python build_interactive_html.py

echo ""
echo "DONE. Open methods_interactive.html to review."
