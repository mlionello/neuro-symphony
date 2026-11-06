#!/usr/bin/env python3
"""Builds the H4 BETWEEN-synchrony table (Fisher-combined, two-sided
permutation-calibrated Coordination Score per button_subset x affective-coherence
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
    per_draw_stats, two_sided_matched_k,
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
            "null_2.5th": np.nan, "null_97.5th": np.nan, "n_matched_draws": 0,
            "permutation_p_two_sided": np.nan, "significant_two_sided": None,
        }

    obs = stats.loc[0]
    null = stats.drop(index=0)
    test = two_sided_matched_k(obs["fisher_stat"], obs["k"], null["fisher_stat"], null["k"])

    return {
        "button_subset": button_subset, "condition": condition,
        "k_movements": int(obs["k"]), "fisher_observed": float(obs["fisher_stat"]),
        "null_2.5th": test["null_2.5th"], "null_97.5th": test["null_97.5th"],
        "n_matched_draws": test["n_matched_draws"],
        "permutation_p_two_sided": test["p_two_sided"],
        "significant_two_sided": bool(test["p_two_sided"] < 0.05),
    }


def build_table() -> pd.DataFrame:
    rows = [run_cell(subset, condition) for subset in BUTTON_SUBSETS for condition in CONDITIONS]
    return pd.DataFrame(rows)


def make_markdown(table: pd.DataFrame) -> str:
    wide = table.pivot(index="button_subset", columns="condition")
    out = ["| button_subset | Aff Coher (k, Fisher obs, null 2.5-97.5 pct, two-sided p) | Aff Opp (k, Fisher obs, null 2.5-97.5 pct, two-sided p) |",
           "|---|---|---|"]
    for subset in ["all6_pca", "sad", "joy"]:
        cells = []
        for condition in CONDITIONS:
            row = table[(table.button_subset == subset) & (table.condition == condition)].iloc[0]
            sig = "*" if row["significant_two_sided"] else ""
            cells.append(
                f"k={row['k_movements']}, obs={row['fisher_observed']:.1f}, "
                f"[{row['null_2.5th']:.1f}, {row['null_97.5th']:.1f}] (n={row['n_matched_draws']}), "
                f"p={row['permutation_p_two_sided']:.4f}{sig}"
            )
        out.append(f"| {subset} | {cells[0]} | {cells[1]} |")
    out.append("")
    out.append("*two-sided permutation p < .05 (null draws matched on the number of movements combined).")
    return "\n".join(out)


if __name__ == "__main__":
    table = build_table()
    out_csv = FIG_DIR / "h4_between_synchrony_table_exp1-exp2.csv"
    table.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}")
    print()
    print(make_markdown(table))
