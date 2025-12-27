# Music Context — analysis utilities (gpt-adaptation, manually checked and fixed)

This folder contains a gpt-cleaned version of the data extraction scripts used to process the data collected by the web app (stored in `web/userdata/`).

## Quick start

From the **project root** (the folder that contains `web/`):

```bash
# create venv (recommended)
python -m venv .venv
source .venv/bin/activate

pip install -r code_cleaned/requirements.txt

# make the package visible
export PYTHONPATH="$PWD/code_cleaned/src"
```

## Commands

### 1) Extract and merge experiment data
Build a single flat CSV (`merged_exp_data.csv`) from the per-user JSON/CSV logs.

```bash
python -m scripts.extract_data \
  --userdata web/userdata \
  --framework web/data/framework.json \
  --out merged_exp_data.csv
```

### 2) Compute pressing-task metrics (optional)
Adds button-press metrics (activation rate, event rate, durations, total events) to the merged table.

```bash
python -m scripts.add_pressing_metrics \
  --in merged_exp_data.csv \
  --out merged_exp_data_with_metrics.csv
```

### 3) Detect Participants to exclude

Detects low-quality/abnormal participants using the **same filtering logic as the original** `anomaly_detector(final_df)`, the “Poor Buttons Activity” GMM-based thresholding on a chosen metric (default use: `total_events`).

- Fits a **2-component GMM** on the selected `--column` (e.g., `total_events`) within an optional `--upper-limit` cap.
- Reproduces legacy exclusion criteria and outputs:
  - `*_excluded_rows.csv` — row-level data for excluded participants with boolean flags per criterion
  - `*_excluded_users.csv` — user-level summary of exclusion flags
  - `*_filtered.csv` — dataset with excluded participants removed
- With `--plot`, generates the **original histogram format** and the **venn3 overlap** plot for excluded participants.

```bash
python -m scripts.pressing_qc \
  --in merged_exp_data_with_metrics.csv \
  --column total_events \
  --upper-limit 80 \
  --plot
```

### 4) Process open-ended feedback with OpenAI (optional)
This is **off by default**. It requires an API key and installs extra dependencies.

```bash
pip install -r code_cleaned/requirements-openai.txt
export OPENAI_API_KEY="..."

python -m scripts.process_feedback_openai \
  --in merged_exp_data.csv \
  --framework web/data/framework.json \
  --descriptions path/to/descriptions_folder \
  --out processed_feedback_results.csv
```

### 5) Merge the two datasets into a final one


```bash
python -m scripts.merge_feedback \
  --base merged_exp_data.csv \
  --feedback processed_feedback_results.csv \
  --out final_dataset.csv
```

## Project layout

```
code_cleaned/
  README.md
  requirements.txt              # minimal dependencies
  requirements-openai.txt       # optional (feedback processing)
  src/neurosymphony_context/    # reusable functions
  scripts/                      # CLI scripts
```

## Notes
- The scripts assume the **same data schema** produced by the web app (JSON user profiles + per-track CSV logs).
- Any plots are optional and never required to run the pipeline.
