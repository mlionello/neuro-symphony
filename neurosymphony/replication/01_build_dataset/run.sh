#!/usr/bin/env bash
# Replicates: building the analysis-ready dataset from the raw per-participant
# logs in web/userdata/, i.e. the input tables (dataset_categoricalonly.csv,
# dataset.csv) that every downstream result (H1-H4 models, figures, power
# analysis) is computed from. Uses only files present in this repository
# (neuro-symphony).
#
# Usage: bash run.sh   (run from this script's own directory, or anywhere --
# it cd's into preprocessing/ itself)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PREPROC_DIR="$REPO_ROOT/preprocessing"

cd "$PREPROC_DIR"

echo "=== [1/3] venv + dependencies ==="
python3 -m venv .venv_replication
source .venv_replication/bin/activate
pip install -q -r requirements.txt
export PYTHONPATH="$PREPROC_DIR"

echo
echo "=== [2/3] stage 1: extract, compute pressing metrics, QC ==="
echo "(raw input: web/userdata/ ; stimulus metadata: web/data/framework.json ;"
echo " description ratings: data/programnotes/ratings/)"
# No --feedback: the optional LLM feedback-rating stage (process_feedback_openai,
# scripts.process_feedback_openai) needs OPENAI_API_KEY + network access and is
# off by default (see preprocessing/README.md); it only adds rating_feedback_*
# columns used by the separate feedback_valence_reanalysis exploratory script,
# not by any H1-H4 model in analysis/finalanalysisandplots.R. Without
# --feedback, extract_final stops after the QC'd table
# (merged_exp_data_with_metrics_filtered.csv) instead of writing final.csv.
python -m scripts.extract_final \
  --userdata ../web/userdata \
  --framework ../web/data/framework.json \
  --ratings ../data/programnotes/ratings \
  --out merged_exp_data_with_metrics.csv

# build_dataset only reads columns from the QC'd extraction (track_condition,
# description_score_mvt_valence, goldsmi_gf_score, track_q3_*, ...), none of
# which are feedback-derived, so the QC'd table is the correct "final.csv"-
# equivalent input here.
cp merged_exp_data_with_metrics_filtered.csv final.csv

echo
echo "=== [3/3] stage 3: build dataset* analysis-ready tables ==="
# --mode positive: dataset_categoricalonly.csv, the categorical models' input
# (movement-level positive-valence gate + row QC). Not --mode both/all: the
# "all" variant (row QC only, no movement gate) isn't read by any downstream
# script -- see scripts/build_dataset.py's docstring -- so it's skipped here
# (still available via --mode all/--out-all).
python -m scripts.build_dataset --in final.csv --mode positive
# --mode raw: dataset.csv, the continuous-valence model's input
# (no QC filtering) -- opt-in, not part of the "positive" default.
python -m scripts.build_dataset --in final.csv --mode raw

echo
echo "=== Output tables ==="
ls -la final.csv dataset_categoricalonly.csv dataset.csv

deactivate
