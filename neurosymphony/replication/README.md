# `replication/`: reproducing every result in this repo alone
*Author's Note: the replication analysis pipeline and scripts are generated via CLAUDE (Anthropic)*

Each numbered subfolder is one self-contained result:
a `run.sh` with the exact commands (it can be run from any location), and its captured `bash_script_output.txt`. Run them in order; later
stages depend on earlier stages' outputs (each `run.sh` checks for its
prerequisites and fails fast with a clear message if they're missing).

## Before running: unpack the data archives

The data folders are distributed as compressed archives. From the
`neurosymphony/` folder:

```bash
tar -xJf web/userdata.tar.xz -C web/                             # web/userdata/ (raw logs)
tar -xJf web/data.tar.xz -C web/                                 # web/data/ (program-note corpus, framework.json)
tar -xJf data/programnotes/ratings.tar.xz -C data/programnotes/  # data/programnotes/ratings/
tar -xJf data/programnotes/preprocessing.tar.xz                  # preprocessing/dataset*.csv (reference tables)
tar -xJf analysis/figures/csv_out.tar.xz -C analysis/figures/    # reference outputs (06 without MATLAB)
```

## Results

| # | Result | Status |
|---|---|---|
| [01_build_dataset](01_build_dataset/) | Raw `web/userdata/` -> `final.csv` -> `dataset_categoricalonly.csv`/`dataset.csv` | Verified from `web/userdata.tar.xz`: reproduces the reference tables in `data/programnotes/preprocessing.tar.xz` (same 374/288 rows, exclusions and values). Row order follows the filesystem's folder listing, which also shifts ties in the unused `groups_gf` tertile column; `activation_rate`/`event_rate` can differ in the last digit across numpy/pandas versions |
| [02_h1_h3_mixed_models](02_h1_h3_mixed_models/) | H1-H3 categorical + continuous-valence mixed models (EMMs/deltas/F-tests), effect estimates with 95% CIs and closed-form sensitivity (Table 3, Figure 5), and the model figures | Verified: every EMM/delta/F/p, 95% CI and MDE matches the manuscript; `effect_estimates_ci.csv` and the figures are byte-identical to the manuscript's |
| [03_h1_button_press](03_h1_button_press/) | H1 button-press-activity sign/Wilcoxon tests (Joy/Happiness, Sadness) and the slopeplot figure | Verified: 7/7 and 6/7, p-values match exactly |
| [04_press_times_figure](04_press_times_figure/) | `press_times_example.png` | Verified: n=13 Opp/n=11 Coher matches the script's own validated docstring. |
| [05_power_analysis](05_power_analysis/) | Retrospective power simulation (93%/95%/>99%/64%) | Long-running (~36,000 model refits) -- launch and check back |
| [06_h4_synchrony](06_h4_synchrony/) | H4 between-listener synchrony (synchrony + bi-coordination tables) | Verified end-to-end (MATLAB R2024a + toolbox, 999 permutations): every toolbox output, both tables and the PC1 loadings (Table 6) are byte-identical to the checked-in reference outputs; the k values and two-sided p ranges match the manuscript. Part C reproduces both tables from the reference outputs in `csv_out.tar.xz` |

## External prerequisites

Every script resolves the repo's own data/code relative to its own file
location -- no absolute paths need editing, and everything reads only from
`web/userdata/`, `web/data/`, `preprocessing/`, `data/programnotes/ratings/`,
and `analysis/figures/` inside this repo. Two things remain genuine *external*
prerequisites (documented, not silently worked around):

- **MATLAB + Finn Upham's Activity Analysis Toolbox 2.1**, for the H4
  toolbox-scoring step (stage 06). See `../analysis/synchrony_reanalysis/README.md`.
- **`OPENAI_API_KEY`**, for the optional LLM feedback-rating stage
  (`preprocessing/scripts/process_feedback_openai.py`) -- not needed for any
  result above; it only feeds a separate exploratory feedback-valence
  reanalysis, not cited by any numbered result here.

