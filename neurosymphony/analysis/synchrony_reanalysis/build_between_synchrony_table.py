#!/usr/bin/env python3
"""Builds the H4 BETWEEN-synchrony table (Fisher-combined, permutation-
calibrated Coordination Score per button_subset x affective-coherence
condition).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
FIG_DIR = REPO / "analysis" / "figures"
sys.path.insert(0, str(REPO / "analysis" / "synchrony_reanalysis"))

from summarize_h4_fisher_permutation_test import (  # noqa: E402
    fisher_stat, per_draw_stats, _empirical_p,
)

CONDITIONS = ["Aff Coher", "Aff Opp"]
CONDITION_TO_ROLE = {"Aff Coher": "Coher_role", "Aff Opp": "Opp_role"}
BUTTON_SUBSETS = {
    "sad": (FIG_DIR / "h4_permutation_test_exp1-exp2.csv", ["Sadness"]),
    "joy": (FIG_DIR / "h4_permutation_test_exp1-exp2.csv", ["Joy/Happiness"]),
    "all6_pca": (FIG_DIR / "h4_pca_composite_permutation_test_exp1-exp2.csv", ["PC1_composite"]),
}


def load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["reliable"] = df["reliable"].astype(bool)
    return df


def run_cell(button_subset: str, condition: str) -> dict:
    path, buttons = BUTTON_SUBSETS[button_subset]
    df = load(path)
    role = CONDITION_TO_ROLE[condition]
    stats = per_draw_stats(df, role, "press_onset", buttons)

    if 0 not in stats.index:
        return {
            "button_subset": button_subset, "condition": condition,
            "k_movements": np.nan, "fisher_observed": np.nan,
            "null_95th_percentile": np.nan, "null_mean": np.nan,
            "permutation_p": np.nan, "significant_at_95pct": None,
        }

    obs = stats.loc[0]
    null = stats.drop(index=0)["fisher_stat"].values

    perm_p, pct_rank = _empirical_p(obs["fisher_stat"], null)
    p95 = float(np.percentile(null, 95))

    return {
        "button_subset": button_subset, "condition": condition,
        "k_movements": int(obs["k"]), "fisher_observed": float(obs["fisher_stat"]),
        "null_95th_percentile": p95, "null_mean": float(null.mean()),
        "permutation_p": perm_p, "significant_at_95pct": bool(obs["fisher_stat"] > p95),
    }


def build_table() -> pd.DataFrame:
    rows = [run_cell(subset, condition) for subset in BUTTON_SUBSETS for condition in CONDITIONS]
    return pd.DataFrame(rows)


def make_markdown(table: pd.DataFrame) -> str:
    wide = table.pivot(index="button_subset", columns="condition")
    out = ["| button_subset | Aff Coher (k, Fisher obs, null 95th pct, perm p) | Aff Opp (k, Fisher obs, null 95th pct, perm p) |",
           "|---|---|---|"]
    for subset in ["all6_pca", "sad", "joy"]:
        cells = []
        for condition in CONDITIONS:
            row = table[(table.button_subset == subset) & (table.condition == condition)].iloc[0]
            sig = "*" if row["significant_at_95pct"] else ""
            cells.append(
                f"k={row['k_movements']}, obs={row['fisher_observed']:.1f}, "
                f"95th={row['null_95th_percentile']:.1f}, perm_p={row['permutation_p']:.4f}{sig}"
            )
        out.append(f"| {subset} | {cells[0]} | {cells[1]} |")
    out.append("")
    out.append("*observed Fisher statistic exceeds the null's 95th percentile.")
    return "\n".join(out)


if __name__ == "__main__":
    table = build_table()
    out_csv = FIG_DIR / "h4_between_synchrony_table_exp1-exp2.csv"
    table.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}")
    print()
    print(make_markdown(table))
