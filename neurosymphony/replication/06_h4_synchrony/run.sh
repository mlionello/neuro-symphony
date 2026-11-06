#!/usr/bin/env bash
# Replicates: H4 between-listener synchrony -- within-condition Coordination
# Score, Fisher-combined and permutation-calibrated across movements
# (Table 4: two-sided permutation p range .208-.778, null draws matched on the
# number of movements combined) and the Bi-Coordination Score between-group
# test (Table 5: two-sided p range .45-.90; k=6/4/7 movements meeting the
# toolbox's minimum-cell requirement for Joy/Happiness, Sadness, all6_pca).
#
# Two-part pipeline (see ../analysis/synchrony_reanalysis/README.md):
#   Part A -- always runs here:
#     pca_composite_events.py, which builds the PCA-composite "7th button"
#     signal fed to the MATLAB scoring step below.
#   Part B (+ Finn Upham's Activity Analysis Toolbox 2.1) -- scores
#   Coordination/Bi-Coordination on real button + composite signals. If
#   unavailable, this script SKIPS Part B and instead verifies Part C below
#   against this repo's checked-in reference toolbox-output CSVs
#   (analysis/figures/h4_*_toolbox_exp1-exp2.csv, h4_*permutation_test*.csv).
#   Part C -- always runs here:
#     build_within_synchrony_table.py, build_between_synchrony_table.py,
#     build_bicoordination_table.py, build_bicoordination_between_table.py.
#
# Prerequisite: replication/01_build_dataset/run.sh must have been run first
# (reads preprocessing/dataset.csv and the raw pressing CSVs it
# points to under web/userdata/).
#
# Usage: bash run.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SYNC_DIR="$REPO_ROOT/analysis/synchrony_reanalysis"
TOOLBOX_DIR="$REPO_ROOT/ActivityAnalysisToolbox_2.1-master"

if [ ! -f "$REPO_ROOT/preprocessing/dataset.csv" ]; then
  echo "Missing $REPO_ROOT/preprocessing/dataset.csv -- run replication/01_build_dataset/run.sh first." >&2
  exit 1
fi

source "$REPO_ROOT/preprocessing/.venv_replication/bin/activate" 2>/dev/null || {
  python3 -m venv "$REPO_ROOT/preprocessing/.venv_replication"
  source "$REPO_ROOT/preprocessing/.venv_replication/bin/activate"
  pip install -q -r "$REPO_ROOT/preprocessing/requirements.txt"
}
pip install -q scikit-learn

echo "=== Part A: pca_composite_events.py (pure Python, no MATLAB needed) ==="
python3 "$SYNC_DIR/pca_composite_events.py"

echo
echo "=== Part B: MATLAB + toolbox scoring ==="
if command -v matlab >/dev/null 2>&1 && [ -d "$TOOLBOX_DIR" ]; then
  echo "MATLAB and toolbox found -- running the full scoring chain."
  ( cd "$SYNC_DIR" && matlab -batch "run_h4_pca_composite_table" )
  ( cd "$SYNC_DIR" && matlab -batch "run_h4_pca_composite_permutation_test" )
  ( cd "$SYNC_DIR" && matlab -batch "run_h4_pca_composite_bicoord_permutation_test" )
  ( cd "$SYNC_DIR" && matlab -batch "run_h4_within_condition_table_toolbox" )
  ( cd "$SYNC_DIR" && matlab -batch "run_h4_permutation_test" )
  ( cd "$SYNC_DIR" && matlab -batch "run_h4_bicoord_permutation_test" )
else
  echo "MATLAB and/or $TOOLBOX_DIR not found -- SKIPPING Part B."
  echo "Part C below will instead run against this repo's checked-in reference"
  echo "toolbox-output CSVs (analysis/figures/h4_*_toolbox*.csv, h4_*permutation_test*.csv),"
  echo "verifying the aggregation logic only, not the toolbox scoring step itself."
  echo "See $SYNC_DIR/README.md to supply MATLAB + the toolbox and re-run Part B for a full replication."
fi

echo
echo "=== Part C: aggregation (pure Python, no MATLAB needed) ==="
python3 "$SYNC_DIR/build_within_synchrony_table.py"
python3 "$SYNC_DIR/build_between_synchrony_table.py"
python3 "$SYNC_DIR/build_bicoordination_table.py"
python3 "$SYNC_DIR/build_bicoordination_between_table.py"

deactivate
