#!/usr/bin/env bash
# Replicates: analysis/figures/press_times_example.png, the raw per-participant
# Joy/Happiness button-press raster visualizing press-time sparsity and
# cross-listener spread.
#
# NOTE: a same-content file also exists at
# analysis/figures/press_times_by_movement/press_times_example_Joy.png
# (with a "_Joy" suffix).
#
# Prerequisite: replication/01_build_dataset/run.sh must have been run first
# (reads preprocessing/dataset.csv and the raw pressing CSVs it points
# to under web/userdata/).
#
# Usage: bash run.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ ! -f "$REPO_ROOT/preprocessing/dataset.csv" ]; then
  echo "Missing $REPO_ROOT/preprocessing/dataset.csv -- run replication/01_build_dataset/run.sh first." >&2
  exit 1
fi

source "$REPO_ROOT/preprocessing/.venv_replication/bin/activate" 2>/dev/null || {
  python3 -m venv "$REPO_ROOT/preprocessing/.venv_replication"
  source "$REPO_ROOT/preprocessing/.venv_replication/bin/activate"
  pip install -q -r "$REPO_ROOT/preprocessing/requirements.txt"
}
pip install -q matplotlib

python3 "$REPO_ROOT/analysis/synchrony_reanalysis/build_press_times_figure.py"

deactivate
