# Neuro-Symphony preprocessing pipeline

This folder contains the data extraction pipeline used to
process the data collected by the web app (stored in `../web/userdata/`).

## Quick start

From **this folder** (`preprocessing/`, the one containing `core/` and `scripts/`):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # numpy, pandas, matplotlib, scikit-learn
export PYTHONPATH="$PWD"                 # core/ is a package, importable as `core.*`
```

Optional feedback-rating step needs `pip install -r requirements-openai.txt` and
`OPENAI_API_KEY` set.

## Pipeline stages, run in this order

### 1) Extract, compute metrics, and QC

`scripts.extract_final` walks `../web/userdata/user_*/*.json` + per-track pressing
CSVs, joins in `../web/data/framework.json` metadata and a ratings folder
(via `--ratings`), computes per-row button-press metrics, and applies
exclusion/QC logic (poor button activity / not engaged / skipped
description reading, including a "grace rule" for multi-symphony
participants).

```bash
python -m scripts.extract_final \
  --userdata ../web/userdata \
  --framework ../web/data/framework.json \
  --ratings ../data/programnotes/ratings \
  --out merged_exp_data_with_metrics.csv \
  --out-final final.csv
```

Omit `--feedback` to stop after the QC'd table (the default). Pass
`--feedback <csv>` (the output of stage 2 below) to merge in feedback ratings via
`core.merge.merge_feedback`.

### 2) Rate open-ended feedback text (off by default)

Uses `core/openai_feedback.py` to LLM-rate open-ended feedback text for
valence/arousal and narrativity. Needs `OPENAI_API_KEY`.

```bash
python -m scripts.process_feedback_openai \
  --in merged_exp_data_with_metrics.csv \
  --framework ../web/data/framework.json \
  --descriptions ../web/data \
  --out feedbacks_metrics.csv
```

Its output is what stage 1's `--feedback` flag merges in.

### 3) Build the analysis-ready tables

`scripts.build_dataset` takes stage 1's `final.csv` and produces the
`final_aggr*.csv` variants the downstream mixed-effects models
(`../analysis/finalanalysisandplots.R`) and power analysis read:

```bash
python -m scripts.build_dataset --in final.csv --mode both
```

- `dataset_categoricalonly.csv` (`--mode positive`) — movement-level positive-valence
  gate + row QC; the categorical mixed-effects model's dataset.
- `dataset.csv` (`--mode raw`) — passthrough, no QC filtering; the
  continuous-valence model's dataset.
- `final_aggr_allmovements_qc.csv` (`--mode all`) — row QC only, no movement-level
  gate.

`dataset.csv` and `dataset_categoricalonly.csv` are checked into this folder as
the exact tables the R scripts were run against.

## Project layout

```
preprocessing/
  README.md
  requirements.txt              # minimal dependencies
  requirements-openai.txt       # optional (feedback processing)
  core/                         # reusable functions (the schema/QC authority)
  scripts/                      # CLI stages (extract_final, process_feedback_openai, build_dataset)
  dataset.csv            # continuous-valence model's input table
  dataset_categoricalonly.csv        # categorical model's input table
```

## Notes
- The scripts assume the same raw-data schema produced by the web app (JSON user
  profiles + per-track CSV logs) — see `core/extract.py` for the schema details.
- There is no test suite; correctness is verified by comparing outputs against
  reference CSVs.
