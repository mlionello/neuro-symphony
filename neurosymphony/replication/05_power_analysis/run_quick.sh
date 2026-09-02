#!/usr/bin/env bash
# Faster alternative to run.sh: reproduces only the retrospective power
# percentages: "93% in the categorical model, 95% in the continuous-valence
# model" (positive intensity), ">99% in both models" (text-music linkage),
# "64% in the categorical model" (negative intensity) -- at the current
# sample size (N=36) only, skipping the 0.5x-2x sample-size projection curve
# and the one non-significant combination (continuous negative intensity,
# F=3.09, p=.080) that isn't included above. ~5,000 glmmTMB
# refits instead of run.sh's 36,000 -- no curve figures are produced (a
# single point isn't a curve). Writes
# analysis/figures/power_reported_effects_currentN.csv.
#
# Prerequisite: replication/01_build_dataset/run.sh must have been run first
# (reads preprocessing/dataset_categoricalonly.csv and preprocessing/dataset.csv).
#
# Usage: bash run_quick.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

for f in "$REPO_ROOT/preprocessing/dataset_categoricalonly.csv" "$REPO_ROOT/preprocessing/dataset.csv"; do
  if [ ! -f "$f" ]; then
    echo "Missing $f -- run replication/01_build_dataset/run.sh first." >&2
    exit 1
  fi
done

Rscript "$REPO_ROOT/analysis/power_analysis/power_parametric_curve_all_outcomes.R" --curve=FALSE
