#!/bin/bash
# Run all 3 SSP projections with CAL-015 filtered params (250 sets).
# Covers WY2001-2100 with historical climate (2001-2025) + CMIP6 (2026-2100).
# Estimated: ~15 min per scenario × 3 = ~45 min total.

set -e
source .venv/bin/activate

PARAMS="calibration_output/filtered_params_v15_top250.json"
echo "========================================"
echo "CAL-015 PROJECTIONS — WY2001 to WY2100"
echo "Params: $PARAMS (250 sets)"
echo "Start: $(date)"
echo "========================================"

for SSP in ssp126 ssp245 ssp585; do
    echo ""
    echo "--- ${SSP^^} ---"
    python run_projection.py --scenario $SSP --filtered-params "$PARAMS"
done

echo ""
echo "========================================"
echo "ALL CAL-015 PROJECTIONS COMPLETE"
echo "End: $(date)"
echo "========================================"
