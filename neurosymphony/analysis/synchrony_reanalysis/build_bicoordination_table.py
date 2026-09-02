#!/usr/bin/env python3
"""Builds the H4 per-movement Bi-Coordination Score table (sad/joy/all6_pca,
no per-condition split -- a single joint-dependence test between the two
groups per movement).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
FIG_DIR = REPO / "analysis" / "figures"

MOVEMENTS = [("exp1", t) for t in (1, 2, 3, 4)] + [("exp2", t) for t in (1, 2, 3, 4)]


def load_sad_joy_draw0() -> pd.DataFrame:
    df = pd.read_csv(FIG_DIR / "h4_bicoord_permutation_test_exp1-exp2.csv")
    df = df[(df["perm_idx"] == 0) & (df["event_type"] == "press_onset")
            & (df["button"].isin(["Sadness", "Joy/Happiness"]))].copy()
    df["button_subset"] = df["button"].map({"Sadness": "sad", "Joy/Happiness": "joy"})
    df["reliable"] = df["reliable"].astype(bool)
    return df[["expid", "track_number", "button_subset", "C", "p", "reliable"]]


def load_all6_pca_draw0() -> pd.DataFrame:
    df = pd.read_csv(FIG_DIR / "h4_pca_composite_bicoord_permutation_test_exp1-exp2.csv")
    df = df[df["perm_idx"] == 0].copy()
    df["button_subset"] = "all6_pca"
    df["reliable"] = df["reliable"].astype(bool)
    return df[["expid", "track_number", "button_subset", "C", "p", "reliable"]]


def build_table() -> pd.DataFrame:
    long = pd.concat([load_sad_joy_draw0(), load_all6_pca_draw0()], ignore_index=True)
    rows = []
    for expid, track_number in MOVEMENTS:
        row = {"movement": f"{expid} trk{track_number}"}
        for subset in ("all6_pca", "sad", "joy"):
            sub = long[(long["expid"] == expid) & (long["track_number"] == track_number)
                       & (long["button_subset"] == subset)]
            if len(sub) == 0:
                row[f"{subset}_C"] = None
                row[f"{subset}_p"] = None
                row[f"{subset}_reliable"] = None
            else:
                r = sub.iloc[0]
                row[f"{subset}_C"] = r["C"]
                row[f"{subset}_p"] = r["p"]
                row[f"{subset}_reliable"] = bool(r["reliable"])
        rows.append(row)
    return pd.DataFrame(rows)


def make_markdown(table: pd.DataFrame) -> str:
    def fmt(row, subset):
        c, p, rel = row[f"{subset}_C"], row[f"{subset}_p"], row[f"{subset}_reliable"]
        if c is None or pd.isna(c):
            return "--"
        flag = "" if rel else "$^{\\dagger}$"
        return f"C={c:.3f}, p={p:.3g}{flag}"

    out = ["| Movement | all6\\_pca | sad | joy |", "|---|---|---|---|"]
    for _, row in table.iterrows():
        cells = [row["movement"]] + [fmt(row, subset) for subset in ("all6_pca", "sad", "joy")]
        out.append("| " + " | ".join(cells) + " |")
    out.append("")
    out.append("$^{\\dagger}$degenerate/infeasible bin split -- not reliable evidence, excluded "
                "from the Fisher combination in build_bicoordination_between_table.py.")
    return "\n".join(out)


if __name__ == "__main__":
    table = build_table()
    out_csv = FIG_DIR / "h4_bicoordination_table_exp1-exp2.csv"
    table.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}")
    print()
    print(make_markdown(table))
