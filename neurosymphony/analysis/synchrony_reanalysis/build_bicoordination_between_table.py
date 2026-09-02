#!/usr/bin/env python3
"""Builds the H4 BETWEEN-groups Bi-Coordination table (Fisher-combined,
two-sided permutation-calibrated Bi-Coordination Score per button_subset).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
FIG_DIR = REPO / "analysis" / "figures"
sys.path.insert(0, str(REPO / "analysis" / "synchrony_reanalysis"))

from summarize_h4_fisher_permutation_test import fisher_stat

BUTTON_SUBSETS = {
    "sad": (FIG_DIR / "h4_bicoord_permutation_test_exp1-exp2.csv", "Sadness"),
    "joy": (FIG_DIR / "h4_bicoord_permutation_test_exp1-exp2.csv", "Joy/Happiness"),
    "all6_pca": (FIG_DIR / "h4_pca_composite_bicoord_permutation_test_exp1-exp2.csv", "PC1_composite"),
}


def load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["reliable"] = df["reliable"].astype(bool)
    return df


def per_draw_fisher_stat(df: pd.DataFrame, button: str) -> pd.Series:
    sub = df[(df["reliable"]) & (df["event_type"] == "press_onset") & (df["button"] == button)]
    return sub.groupby("perm_idx")["p"].apply(lambda p: fisher_stat(p.values))


def per_draw_k(df: pd.DataFrame, button: str) -> pd.Series:
    sub = df[(df["reliable"]) & (df["event_type"] == "press_onset") & (df["button"] == button)]
    return sub.groupby("perm_idx").size()


def _two_sided_empirical_p(observed: float, null: np.ndarray) -> float:
    n = len(null)
    p_upper = (int(np.sum(null >= observed)) + 1) / (n + 1)
    p_lower = (int(np.sum(null <= observed)) + 1) / (n + 1)
    return float(min(1.0, 2.0 * min(p_upper, p_lower)))


def run_cell(button_subset: str) -> dict:
    path, button = BUTTON_SUBSETS[button_subset]
    df = load(path)
    stat = per_draw_fisher_stat(df, button)
    k = per_draw_k(df, button)

    if 0 not in stat.index:
        return {
            "button_subset": button_subset, "k_movements": np.nan, "fisher_observed": np.nan,
            "null_5th_percentile": np.nan, "null_95th_percentile": np.nan, "null_mean": np.nan,
            "permutation_p_two_sided": np.nan, "significant_two_sided": None,
        }

    obs = stat.loc[0]
    null = stat.drop(index=0).values
    perm_p = _two_sided_empirical_p(obs, null)
    p5 = float(np.percentile(null, 5))
    p95 = float(np.percentile(null, 95))

    return {
        "button_subset": button_subset, "k_movements": int(k.loc[0]), "fisher_observed": float(obs),
        "null_5th_percentile": p5, "null_95th_percentile": p95, "null_mean": float(null.mean()),
        "permutation_p_two_sided": perm_p, "significant_two_sided": bool(obs > p95 or obs < p5),
    }


def build_table() -> pd.DataFrame:
    return pd.DataFrame([run_cell(subset) for subset in BUTTON_SUBSETS])


def make_markdown(table: pd.DataFrame) -> str:
    out = ["| button_subset | k (movements) | Fisher observed | null 5th-95th pct band | two-sided permutation p |",
           "|---|---|---|---|---|"]
    for _, row in table.iterrows():
        sig = "*" if row["significant_two_sided"] else ""
        out.append(
            f"| {row['button_subset']} | {int(row['k_movements'])} | {row['fisher_observed']:.1f} | "
            f"[{row['null_5th_percentile']:.1f}, {row['null_95th_percentile']:.1f}] | "
            f"{row['permutation_p_two_sided']:.4f}{sig} |"
        )
    out.append("")
    out.append("*observed Fisher statistic falls outside the null's 5th-95th percentile band.")
    return "\n".join(out)


if __name__ == "__main__":
    table = build_table()
    out_csv = FIG_DIR / "h4_bicoordination_between_table_exp1-exp2.csv"
    table.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}")
    print()
    print(make_markdown(table))
