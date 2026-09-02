# `analysis/synchrony_reanalysis/`: H4 between-listener synchrony

H4 ("shared affective framing shapes the temporal coordination of listeners'
continuous emotion reports") is tested two ways, both scored with Finn
Upham's Activity Analysis Toolbox 2.1 (`simpleActivityTest`, Coordination
Score C) on the exp1 (Brahms 3) / exp2 (Dvořák 8) button-press data:

1. **Within-condition synchrony, Fisher-combined across movements**: does either Affective-Coherence
   group show more internal synchrony than a same-sized random relabeling of
   the same participants?
   Reproduce via: `pca_composite_events.py` -> `run_h4_pca_composite_table.m`
   + `run_h4_pca_composite_permutation_test.m` ->
   `build_within_synchrony_table.py` + `build_between_synchrony_table.py`.

2. **Bi-Coordination Score, between-group**: a non-directional complement testing joint
   dependence between the Coherent and Opposite listener groups directly.
   Reproduce via: `run_h4_pca_composite_bicoord_permutation_test.m` ->
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
matlab -batch "run_h4_pca_composite_table"
matlab -batch "run_h4_pca_composite_permutation_test"
python3 build_within_synchrony_table.py
python3 build_between_synchrony_table.py

matlab -batch "run_h4_pca_composite_bicoord_permutation_test"
python3 build_bicoordination_table.py
python3 build_bicoordination_between_table.py
```

