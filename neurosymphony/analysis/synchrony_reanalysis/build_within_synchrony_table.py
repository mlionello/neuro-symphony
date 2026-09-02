#!/usr/bin/env python3
"""Builds the H4 per-movement WITHIN-synchrony table (Coordination Score C/p
per movement x button_subset (all6_pca/sad/joy) x affective-coherence
condition, press_onset only), flagging non-reliable (degenerate_2bin) rows.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
FIG_DIR = REPO / "analysis" / "figures"

CONDITIONS = ["Aff Coher", "Aff Opp"]
MOVEMENTS = [("exp1", t) for t in (1, 2, 3, 4)] + [("exp2", t) for t in (1, 2, 3, 4)]


def load_sad_joy() -> pd.DataFrame:
    df = pd.read_csv(FIG_DIR / "h4_within_aff_condition_toolbox_exp1-exp2.csv")
    df = df[(df["event_type"] == "press_onset") & (df["button"].isin(["Sadness", "Joy/Happiness"]))].copy()
    df["button_subset"] = df["button"].map({"Sadness": "sad", "Joy/Happiness": "joy"})
    df["reliable"] = df["feasible"].astype(bool) & ~df["degenerate_2bin"].astype(bool)
    return df[["expid", "track_number", "button_subset", "condition", "C", "p", "reliable"]]


def load_all6_pca() -> pd.DataFrame:
    df = pd.read_csv(FIG_DIR / "h4_pca_composite_toolbox_exp1-exp2.csv")
    df["button_subset"] = "all6_pca"
    df["reliable"] = df["feasible"].astype(bool) & ~df["degenerate_2bin"].astype(bool)
    return df[["expid", "track_number", "button_subset", "condition", "C", "p", "reliable"]]


def build_table() -> pd.DataFrame:
    long = pd.concat([load_sad_joy(), load_all6_pca()], ignore_index=True)
    rows = []
    for expid, track_number in MOVEMENTS:
        row = {"movement": f"{expid} trk{track_number}"}
        for subset in ("all6_pca", "sad", "joy"):
            for condition in CONDITIONS:
                sub = long[
                    (long["expid"] == expid) & (long["track_number"] == track_number)
                    & (long["button_subset"] == subset) & (long["condition"] == condition)
                ]
                key = f"{subset}_{condition.replace(' ', '_')}"
                if len(sub) == 0:
                    row[f"{key}_C"] = None
                    row[f"{key}_p"] = None
                    row[f"{key}_reliable"] = None
                else:
                    r = sub.iloc[0]
                    row[f"{key}_C"] = r["C"]
                    row[f"{key}_p"] = r["p"]
                    row[f"{key}_reliable"] = bool(r["reliable"])
        rows.append(row)
    return pd.DataFrame(rows)


def make_markdown(table: pd.DataFrame) -> str:
    def fmt(row, subset, condition):
        key = f"{subset}_{condition.replace(' ', '_')}"
        c, p, rel = row[f"{key}_C"], row[f"{key}_p"], row[f"{key}_reliable"]
        if c is None or pd.isna(c):
            return "--"
        flag = "" if rel else "$^{\\dagger}$"
        return f"C={c:.3f}, p={p:.3g}{flag}"

    out = ["| Movement | all6\\_pca (Aff Coher) | all6\\_pca (Aff Opp) | sad (Aff Coher) | sad (Aff Opp) | joy (Aff Coher) | joy (Aff Opp) |",
           "|---|---|---|---|---|---|---|"]
    for _, row in table.iterrows():
        cells = [row["movement"]]
        for subset in ("all6_pca", "sad", "joy"):
            for condition in CONDITIONS:
                cells.append(fmt(row, subset, condition))
        out.append("| " + " | ".join(cells) + " |")
    out.append("")
    out.append("$^{\\dagger}$degenerate\\_2bin: within-collection test fell back to 2 bins "
                "(toolbox dof=0 pins p at exactly 0) -- not treated as reliable evidence, per section 0g's convention.")
    return "\n".join(out)


if __name__ == "__main__":
    table = build_table()
    out_csv = FIG_DIR / "h4_within_synchrony_table_exp1-exp2.csv"
    table.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}")
    print()
    print(make_markdown(table))
