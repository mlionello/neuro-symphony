# Program notes: stimulus ratings and reference tables

This folder holds two archives:

| archive | contents |
|---|---|
| `ratings.tar.xz` | `ratings/sorted_<symphony>_rating.csv` — one file per symphony (8), the LLM valence/arousal scores for each program-note text |
| `preprocessing.tar.xz` | `preprocessing/dataset.csv` and `preprocessing/dataset_categoricalonly.csv` — the processed tables the mixed-effects models were run against |

Extract both from the `neurosymphony/` folder:

```bash
tar -xJf data/programnotes/ratings.tar.xz -C data/programnotes/  # -> data/programnotes/ratings/
tar -xJf data/programnotes/preprocessing.tar.xz                  # -> preprocessing/dataset*.csv
```

## Text stimuli: see `web/data/`

The program-note text corpus itself (the `<symphony>_processed.csv` stimulus
files) lives in `neurosymphony/web/data/` (distributed as
`neurosymphony/web/data.tar.xz`). That folder's `README.md` documents the row layout.

Each `ratings/sorted_<symphony>_rating.csv` has 72 rows, row-aligned with
`web/data/<symphony>_processed.csv`: row *i* of the ratings file scores row
*i* of the corpus file, so the same 4 × 18-row movement/condition layout
applies to both.
