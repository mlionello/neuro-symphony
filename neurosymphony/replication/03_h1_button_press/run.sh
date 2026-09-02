#!/usr/bin/env bash
# Replicates: H1's continuous button-press-activity check on the
# strongly-valenced movement subset (Joy/Happiness and Sadness whole-movement
# proportion-pressed, sign test + Wilcoxon across the 7 truepos exp1/exp2
# movements) and the h1_button_press_slopeplot_exp1exp2_truepos.png figure.
#
# Prerequisite: replication/01_build_dataset/run.sh must have been run first
# (reads preprocessing/dataset_categoricalonly.csv and the raw pressing CSVs it
# points to under web/userdata/).
#
# Usage: bash run.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ ! -f "$REPO_ROOT/preprocessing/dataset_categoricalonly.csv" ]; then
  echo "Missing $REPO_ROOT/preprocessing/dataset_categoricalonly.csv -- run replication/01_build_dataset/run.sh first." >&2
  exit 1
fi

source "$REPO_ROOT/preprocessing/.venv_replication/bin/activate" 2>/dev/null || {
  python3 -m venv "$REPO_ROOT/preprocessing/.venv_replication"
  source "$REPO_ROOT/preprocessing/.venv_replication/bin/activate"
  pip install -q -r "$REPO_ROOT/preprocessing/requirements.txt"
}
pip install -q scipy matplotlib

python3 "$REPO_ROOT/analysis/h1_button_press_reanalysis/button_press_h1_check.py"

deactivate
