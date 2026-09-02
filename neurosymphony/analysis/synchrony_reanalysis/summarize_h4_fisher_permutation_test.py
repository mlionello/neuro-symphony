#!/usr/bin/env python3
"""Permutation-calibrated Fisher-combination and sign tests for H4.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
FIG_DIR = REPO / "analysis" / "figures"

BUTTON_SUBSETS = {
    "all_6": ["Power/Energy", "Joy/Happiness", "Sadness", "Wonder/Surprise", "Tension", "Calm/Tranquillity"],
    "joy": ["Joy/Happiness"],
    "sad": ["Sadness"],
}
CONDITION_TO_ROLE = {"Aff Coher": "Coher_role", "Aff Opp": "Opp_role"}
EVENT_TYPES = ["press_onset", "release_onset", "any_transition"]


def load(suffix: str) -> pd.DataFrame:
    path = FIG_DIR / f"h4_permutation_test{suffix}.csv"
    df = pd.read_csv(path)
    df["reliable"] = df["reliable"].astype(bool)
    return df


def fisher_stat(pvals: np.ndarray) -> float:
    pvals = np.clip(np.asarray(pvals, dtype=float), 1e-300, 1.0)
    return float(-2.0 * np.sum(np.log(pvals)))


def sign_stat(pvals: np.ndarray) -> float:
    pvals = np.asarray(pvals, dtype=float)
    return float(np.mean(pvals < 0.5))


def per_draw_stats(df: pd.DataFrame, role: str, event_type: str, buttons: list[str]) -> pd.DataFrame:
    sub = df[
        (df["reliable"])
        & (df["pseudo_condition"] == role)
        & (df["event_type"] == event_type)
        & (df["button"].isin(buttons))
    ]
    grouped = sub.groupby("perm_idx")["p"]
    fisher = grouped.apply(lambda p: fisher_stat(p.values), include_groups=False)
    sign = grouped.apply(lambda p: sign_stat(p.values), include_groups=False)
    k = grouped.size()
    return pd.DataFrame({"fisher_stat": fisher, "sign_prop": sign, "k": k})


def _empirical_p(observed: float, null: np.ndarray) -> tuple[float, float]:
    n_ge = int(np.sum(null >= observed))
    p_value = (n_ge + 1) / (len(null) + 1)
    pct_rank = float(np.mean(null <= observed) * 100)
    return p_value, pct_rank


def run_and_report(df: pd.DataFrame, event_type: str, subset_name: str, condition: str):
    role = CONDITION_TO_ROLE[condition]
    buttons = BUTTON_SUBSETS[subset_name]
    stats = per_draw_stats(df, role, event_type, buttons)

    label = f"{event_type} / {subset_name} / {condition}"
    if 0 not in stats.index:
        print(f"{label}: no reliable rows for observed draw -- skipped.")
        return None

    obs = stats.loc[0]
    null = stats.drop(index=0)

    fisher_p, fisher_pct = _empirical_p(obs["fisher_stat"], null["fisher_stat"].values)
    sign_p, sign_pct = _empirical_p(obs["sign_prop"], null["sign_prop"].values)

    print(f"{label}: k={int(obs['k'])} | "
          f"Fisher: obs={obs['fisher_stat']:.1f}, null_mean={null['fisher_stat'].mean():.1f}, "
          f"pct={fisher_pct:.1f}%, perm_p={fisher_p:.4f} | "
          f"Sign: obs_prop={obs['sign_prop']:.3f}, null_mean_prop={null['sign_prop'].mean():.3f}, "
          f"pct={sign_pct:.1f}%, perm_p={sign_p:.4f}")

    return {
        "event_type": event_type, "button_subset": subset_name, "condition": condition, "k": int(obs["k"]),
        "fisher_obs": obs["fisher_stat"], "fisher_null_mean": null["fisher_stat"].mean(),
        "fisher_pct_rank": fisher_pct, "fisher_perm_p": fisher_p,
        "sign_obs_prop": obs["sign_prop"], "sign_null_mean_prop": null["sign_prop"].mean(),
        "sign_pct_rank": sign_pct, "sign_perm_p": sign_p,
    }


if __name__ == "__main__":
    df = load("_exp1-exp2")

    print("=== Permutation-calibrated Fisher + sign test: press_onset, all_6, per condition (0g's headline cells) ===")
    rows = []
    for condition in ["Aff Coher", "Aff Opp"]:
        r = run_and_report(df, "press_onset", "all_6", condition)
        if r:
            rows.append(r)

    print("\n=== Full grid (all event types x button subsets x conditions) ===")
    for event_type in EVENT_TYPES:
        for subset_name in BUTTON_SUBSETS:
            for condition in ["Aff Coher", "Aff Opp"]:
                r = run_and_report(df, event_type, subset_name, condition)
                if r:
                    rows.append(r)

    out_csv = FIG_DIR / "h4_fisher_permutation_test_exp1_exp2.csv"
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"\nWrote {out_csv}")
