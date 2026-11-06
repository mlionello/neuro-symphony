# `analysis/synchrony_reanalysis/`: H4 between-listener synchrony

H4 is non-directional: does sharing an affective framing change how closely
listeners' continuous emotion reports line up in time? It is tested two ways,
both with Finn Upham's Activity Analysis Toolbox 2.1 (`simpleActivityTest`
for the Coordination Score, `relatedActivitiesTest` for the Bi-Coordination
Score) on the exp1 (Brahms 3) / exp2 (Dvořák 8) button-press data, for three
scopes: Joy/Happiness, Sadness, and a secondary PC1 composite of all six
buttons.

1. **Within-condition synchrony, Fisher-combined across movements**
   (manuscript Table 4): are listeners who read the same affective framing
   (Coherent, or Opposite) more or less coordinated than random groups of the
   same size drawn from the same listeners?
   Reproduce via: `run_h4_within_condition_table_toolbox.m` +
   `run_h4_permutation_test.m` (Joy/Happiness, Sadness) and
   `pca_composite_events.py` -> `run_h4_pca_composite_table.m` +
   `run_h4_pca_composite_permutation_test.m` (composite) ->
   `build_within_synchrony_table.py` + `build_between_synchrony_table.py`.

2. **Bi-Coordination Score, between-group** (manuscript Table 5): do the
   Coherent and Opposite groups line up with each other less, or more, closely
   than random splits of the same listeners into groups of the same sizes?
   Reproduce via: `run_h4_bicoord_permutation_test.m` (Joy/Happiness, Sadness)
   and `run_h4_pca_composite_bicoord_permutation_test.m` (composite) ->
   `build_bicoordination_table.py` -> `build_bicoordination_between_table.py`.

## External prerequisite: the toolbox itself

The `.m` scripts above require **Finn Upham's Activity Analysis Toolbox
2.1** (Upham & McAdams, 2018), Artistic
License 2.0. It is **not bundled in this repository** (it's a third-party
dependency, not code from this study) -- obtain it separately and place it
at:

```
<repo root>/ActivityAnalysisToolbox_2.1-master/
```

## Running

All scripts (both `.py` and `.m`) resolve `dataset.csv` and the raw
per-participant pressing CSVs it points to relative to their own file
location (`repo_root/preprocessing/` in this layout), and write their
outputs to `analysis/figures/` -- no path editing needed, only supplying
the toolbox above. Run each numbered chain in order, e.g. from a shell with
MATLAB on `PATH`:

```bash
python3 pca_composite_events.py
matlab -batch "run_h4_within_condition_table_toolbox"   # Joy/Sadness observed (Table 4)
matlab -batch "run_h4_pca_composite_table"              # composite observed
matlab -batch "run_h4_permutation_test"                 # Joy/Sadness null
matlab -batch "run_h4_pca_composite_permutation_test"   # composite null
python3 build_within_synchrony_table.py
python3 build_between_synchrony_table.py

matlab -batch "run_h4_bicoord_permutation_test"               # Joy/Sadness (Table 5)
matlab -batch "run_h4_pca_composite_bicoord_permutation_test" # composite
python3 build_bicoordination_table.py
python3 build_bicoordination_between_table.py
```
