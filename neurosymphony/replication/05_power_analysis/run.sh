#!/usr/bin/env bash
# Replicates: the retrospective power percentages: "93% in the categorical
# model, 95% in the continuous-valence model" (positive intensity), ">99% in
# both models" (text-music linkage), "64% in the categorical model" (negative
# intensity) -- via power_parametric_curve_all_outcomes.R's multiplier=1
# (current N=36) rows in power_curve_all_outcomes.csv -- plus the full
# 0.5x-2x sample-size projection curve and its two figures
# (power_curve_categorical_by_outcome.png, power_curve_continuous_by_outcome.png).
#
# WARNING: this simulates 6 (outcome x model type) x 6000 = 36,000
# glmmTMB refits and can take a long time (hours) to complete. For just the
# percentages above, without the size-projection curve, use run_quick.sh
# instead (~1/6th the runtime).
#
# Prerequisite: replication/01_build_dataset/run.sh must have been run first
# (reads preprocessing/dataset_categoricalonly.csv and preprocessing/dataset.csv).
#
# Usage: bash run.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

for f in "$REPO_ROOT/preprocessing/dataset_categoricalonly.csv" "$REPO_ROOT/preprocessing/dataset.csv"; do
  if [ ! -f "$f" ]; then
    echo "Missing $f -- run replication/01_build_dataset/run.sh first." >&2
    exit 1
  fi
done

Rscript "$REPO_ROOT/analysis/power_analysis/power_parametric_curve_all_outcomes.R"
