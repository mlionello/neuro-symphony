# Neuro-Symphony
This repository contains the web application used to collect behavioral data, the preprocessing/analysis pipeline, and the replication scripts for the contextual information manipulation study.

In the study, participants complete an online, multi-session listening paradigm in which brief program-note descriptions (manipulated in valence and narrative authenticity) are shown before each symphonic movement; during listening, participants continuously report felt affect via a six-button task, followed by post-movement questionnaires.

## Repository map

```
neurosymphony/
  web/                  # PHP/JS data-collection app
    userdata/           # raw per-participant JSON logs + button-press CSVs (see Data below)
    data/                # stimulus manifests (framework.json, audio-path CSVs, <symphony>_processed.csv); in data.tar.xz
    php/ css/ js/ content/ security/ reset_password/
    README.MD            # app architecture, setup, deployment, security checklist

  data/
    audio/               #  audio stimulus files
    programnotes/
      ratings.tar.xz       # -> ratings/sorted_<symphony>_rating.csv — LLM valence/arousal scores per stimulus text
      preprocessing.tar.xz # -> preprocessing/dataset.csv, dataset_categoricalonly.csv (reference tables)
      README.md            # archive contents and extraction commands

  preprocessing/         # Python pipeline: raw web/userdata/ -> analysis-ready CSVs
    core/                 # reusable functions (extract, metrics, qc, merge, goldmsi, openai_feedback)
    scripts/              # CLI stages: extract_final, process_feedback_openai, build_dataset
    dataset.csv, dataset_categoricalonly.csv   # reference output tables (in data/programnotes/preprocessing.tar.xz)
    README.md             # pipeline stages and quick start

  analysis/               # R/MATLAB/Python statistical analyses run on preprocessing's output
    finalanalysisandplots.R        # H1-H3 mixed-effects models + figures
    button_tseries_analysis_and_rendering.m
    h1_button_press_reanalysis/    # H1 button-press-activity sign/Wilcoxon tests
    synchrony_reanalysis/          # H4 between-listener synchrony (MATLAB toolbox + Python aggregation)
    power_analysis/                # retrospective power analysis (R)
    feedback_valence_reanalysis/   # LLM-rating feedback (needs OPENAI_API_KEY to replicate from scratch)
    figures/                       # checked-in reference outputs (CSVs + PNGs) the above are validated against

  replication/            # one numbered folder per pipeline result, each a self-contained run.sh
    01_build_dataset/ .. 06_h4_synchrony/
    README.md             # what each stage reproduces and its verification status
```

## Data

The raw per-participant anonymized data collected through the web app is saved in
`neurosymphony/web/userdata/` (distributed as `neurosymphony/web/userdata.tar.xz`)
session log per participant plus one continuous button-press CSV per
movement, together containing:

- the exact program-note text presented to that participant before each
  movement (the full text),
- the Coherent/Opposite × Reference/Injected condition assigned to each
  movement of that session, and
- the continuous button-press activity recorded during listening (one
  CSV per movement, six emotion buttons).

See that folder's own `README.md` for the exact field-by-field schema and
how to decode the condition assignment.

The stimulus text corpus itself (the program notes shown, independent of
any one participant) lives in
`neurosymphony/web/data/` (distributed as `neurosymphony/web/data.tar.xz`)
— see its `README.md` for the row layout. The valence/arousal statistics
for each individual text stimulus (from the LLM affective-scoring pipeline
step) are available separately in
`neurosymphony/data/programnotes/ratings/` (distributed as
`neurosymphony/data/programnotes/ratings.tar.xz`), one CSV per symphony,
row-aligned with that symphony's stimulus file. The processed tables the
mixed-effects models were run against (`dataset.csv`,
`dataset_categoricalonly.csv`) are distributed as
`neurosymphony/data/programnotes/preprocessing.tar.xz` and extract into
`neurosymphony/preprocessing/`. See
[`neurosymphony/data/programnotes/README.md`](neurosymphony/data/programnotes/README.md)
for both archives' contents and extraction commands, and
[`neurosymphony/replication/README.md`](neurosymphony/replication/README.md)
for the full unpack sequence.

## Pipeline: from raw data to published results

1. [`web/`](neurosymphony/web/) collects the raw data (see its own `README.MD` for setup/deployment).
2. [`preprocessing/`](neurosymphony/preprocessing/) turns `web/userdata/` into analysis-ready tables (`dataset.csv`, `dataset_categoricalonly.csv`).
3. [`analysis/`](neurosymphony/analysis/) runs the statistical models and produces figures/tables from those tables.
4. [`replication/`](neurosymphony/replication/) ties 2-3 together per result, with a `run.sh` per stage and its captured output — start here to reproduce a specific result end-to-end.
