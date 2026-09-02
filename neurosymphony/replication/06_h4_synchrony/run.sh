#!/usr/bin/env bash
# Replicates: H4 between-listener synchrony -- within-condition Coordination
# Score, Fisher-combined and permutation-calibrated across movements
# (permutation p range .424-.951, i.e. no scope-by-condition combination
# exceeded its null's 95th percentile) and the Bi-Coordination Score
# between-group test: k=7/4/8 movements meeting the toolbox's minimum-cell
# requirement for Joy/Happiness, Sadness, all6_pca respectively.
#
# Two-part pipeline (see ../analysis/synchrony_reanalysis/README.md):
#   Part A (pure Python, no MATLAB) -- always runs here:
#     pca_composite_events.py, which builds the PCA-composite "7th button"
#     signal fed to the MATLAB scoring step below.
#   Part B (MATLAB + Finn Upham's Activity Analysis Toolbox 2.1, an external
#   prerequisite NOT bundled in this repo -- see the README above) -- scores
#   Coordination/Bi-Coordination on real button + composite signals. If
#   unavailable, this script SKIPS Part B and instead verifies Part C below
#   against this repo's checked-in reference toolbox-output CSVs
#   (analysis/figures/h4_*_toolbox_exp1-exp2.csv, h4_*permutation_test*.csv)
#   -- i.e. it verifies the Fisher-combination/aggregation logic exactly
#   reproduces both tables from already-scored data, while being
#   explicit that the toolbox-scoring step itself could not be re-verified
#   in this environment.
#   Part C (pure Python, no MATLAB) -- always runs here:
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
