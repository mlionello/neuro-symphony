# `replication/`: reproducing every result in this repo alone
*Author's Note: the replication analysis pipeline and scripts are generated via CLAUDE (Anthropic)*

Each numbered subfolder is one self-contained result:
a `run.sh` with the exact commands (it can be run from any location), and its captured `bash_script_output.txt`. Run them in order; later
stages depend on earlier stages' outputs (each `run.sh` checks for its
prerequisites and fails fast with a clear message if they're missing).

| # | Result | Status |
|---|---|---|
| [01_build_dataset](01_build_dataset/) | Raw `web/userdata/` -> `final.csv` -> `dataset_categoricalonly.csv`/`dataset.csv` | Verified: byte-identical to the checked-in reference tables in `preprocessing/` |
| [02_h1_h3_mixed_models](02_h1_h3_mixed_models/) | H1-H3 categorical + continuous-valence mixed models (EMMs/deltas/F-tests) and its 9 figures | Verified: every EMM/delta/F/p matches at the reported precision |
| [03_h1_button_press](03_h1_button_press/) | H1 button-press-activity sign/Wilcoxon tests (Joy/Happiness, Sadness) and the slopeplot figure | Verified: 7/7 and 6/7, p-values match exactly |
| [04_press_times_figure](04_press_times_figure/) | `press_times_example.png` | Verified: n=13 Opp/n=11 Coher matches the script's own validated docstring. |
| [05_power_analysis](05_power_analysis/) | Retrospective power percentages (93%/95%/>99%/64%) | Long-running (~36,000 model refits, can take hours) -- launch and check back |
| [06_h4_synchrony](06_h4_synchrony/) | H4 between-listener synchrony (synchrony + bi-coordination tables) | Partially verified: the pure-Python aggregation stage reproduces both tables exactly (byte-identical to checked-in reference, and the reported k values / p-range match exactly) from this repo's checked-in reference toolbox-output CSVs |

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

