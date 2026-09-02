#!/usr/bin/env bash
# Replicates: the H1-H3 mixed-effects models (EMMs/deltas/F-tests for
# felt positive intensity, felt negative intensity, and text-music linkage;
# both the categorical Coherent/Opposite model and the continuous-valence
# model) and their figures (pos/neg/link_categorical_means.png,
# pos/neg/link_continuous_curve.png, pos/neg/link_low_mid_high.png).
#
# Prerequisite: replication/01_build_dataset/run.sh must have been run first
# (this script reads preprocessing/dataset_categoricalonly.csv and
# preprocessing/dataset.csv, its output).
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

Rscript "$REPO_ROOT/analysis/finalanalysisandplots.R"
