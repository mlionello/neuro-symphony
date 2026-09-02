#!/usr/bin/env python3
"""Builds the PCA-composite "7th button" signal (1st principal component
across the 6 real emotion buttons' held-state per movement, binarized by
sign).

Writes one per-participant composite pressing CSV per movement to
`analysis/figures/pca_composite/`, plus
`analysis/figures/pca_composite_manifest_exp1-exp2.csv`
and `pca_composite_variance_explained.csv`.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

SCRIPT_DIR = Path(__file__).resolve().parent
REPO = SCRIPT_DIR.parent.parent
DATA_DIR = REPO / "preprocessing" if (REPO / "preprocessing" / "dataset.csv").exists() else REPO
sys.path.insert(0, str(DATA_DIR))
os.chdir(DATA_DIR)

from core.metrics import load_pressing_csv

FRAME_SIZE = 2
MIN_PARTICIPANTS_PER_GROUP = 3 
BUTTON_LABELS = [
    "Power/Energy", "Joy/Happiness", "Sadness",
    "Wonder/Surprise", "Tension", "Calm/Tranquillity",
]
SYMPHONIES = ["exp1", "exp2"]
OUT_DIR = REPO / "analysis" / "figures"
COMPOSITE_CSV_DIR = OUT_DIR / "pca_composite"


def load_track_group(rows: pd.DataFrame):
    mats, ts = {}, {}
    for _, row in rows.iterrows():
        p = row["pressing_csv"]
        if not isinstance(p, str) or not Path(p).exists():
            continue
        m = load_pressing_csv(p)
        mats[row["userid"]] = m[:, 1:]
        ts[row["userid"]] = m[:, 0]
    if len(mats) < 2 * MIN_PARTICIPANTS_PER_GROUP:
        return None, None, None
    min_len = min(m.shape[0] for m in mats.values())
    if min_len < FRAME_SIZE * 10:
        return None, None, None
    mats = {u: m[:min_len] for u, m in mats.items()}
    ts = {u: t[:min_len] for u, t in ts.items()}
    return mats, ts, min_len


def build_composite_for_movement(expid: str, track_number: int, mats: dict, min_len: int):
    userids = sorted(mats.keys())
    pooled = np.concatenate([mats[u] for u in userids], axis=0)
    pca = PCA(n_components=1)
    pca.fit(pooled)

    composite = {}
    for u in userids:
        scores = pca.transform(mats[u]).ravel()
        composite[u] = (scores > 0).astype(int)
    return composite, float(pca.explained_variance_ratio_[0])


def main():
    df = pd.read_csv(DATA_DIR / "dataset.csv")
    df = df[df["expid"].isin(SYMPHONIES)]
    df = df.dropna(subset=["pressing_csv", "aggregated_condition_affective"])

    COMPOSITE_CSV_DIR.mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    variance_rows = []

    for (expid, track_number), rows in df.groupby(["expid", "track_number"]):
        mats, ts, min_len = load_track_group(rows)
        if mats is None:
            print(f"{expid} trk{track_number}: skipped (insufficient participants/frames)")
            continue

        composite, var_ratio = build_composite_for_movement(expid, track_number, mats, min_len)
        cond_by_user = dict(zip(rows["userid"], rows["aggregated_condition_affective"]))

        for u, binary in composite.items():
            out_path = COMPOSITE_CSV_DIR / f"{expid}_trk{track_number}_{u}.csv"
            out = np.column_stack([ts[u], binary])
            np.savetxt(out_path, out, delimiter=",", fmt=["%.3f", "%d"])
            manifest_rows.append({
                "userid": u, "expid": expid, "track_number": track_number,
                "pressing_csv": str(out_path),
                "aggregated_condition_affective": cond_by_user.get(u),
            })

        variance_rows.append({
            "expid": expid, "track_number": track_number,
            "n_participants": len(composite), "min_len": min_len,
            "pc1_variance_ratio": var_ratio,
        })
        print(f"{expid} trk{track_number}: n={len(composite)}, min_len={min_len}, "
              f"PC1 variance ratio={var_ratio:.3f}")

    manifest = pd.DataFrame(manifest_rows)
    manifest_path = OUT_DIR / "pca_composite_manifest_exp1-exp2.csv"
    manifest.to_csv(manifest_path, index=False)
    print(f"\nWrote {manifest_path} ({len(manifest)} rows)")

    variance_df = pd.DataFrame(variance_rows)
    variance_path = OUT_DIR / "pca_composite_variance_explained.csv"
    variance_df.to_csv(variance_path, index=False)
    print(f"Wrote {variance_path}")
    print(variance_df.to_string(index=False))


if __name__ == "__main__":
    main()
