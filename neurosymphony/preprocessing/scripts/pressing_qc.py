#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture

from core.qc import anomaly_detector_like_legacy, normalize_for_qc
from core.pressing import gmm_bimodal_threshold


READING_MIN_MS = 10_000


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Pressing-task QC + participant exclusion (legacy-compatible).\n\n"
            "This script keeps the original CLI used in the dissertation, but also reproduces the "
            "full participant exclusion logic from the legacy `anomaly_detector(final_df)` workflow: "
            "poor button activity, low engagement ratings, and skipping descriptions."
        )
    )
    ap.add_argument("--in", dest="inp", required=True, help="Input CSV (e.g., merged_exp_data_with_metrics.csv)")
    ap.add_argument("--column", required=True, help="Column to fit for the pressing GMM (typically total_events)")
    ap.add_argument("--upper-limit", type=float, default=80.0, help="Upper limit filter used to fit the GMM")
    ap.add_argument("--plot", action="store_true", help="Show the legacy-style histogram and Venn diagram")
    ap.add_argument(
        "--out-anomalies",
        default=None,
        help="Output CSV with excluded rows (default: <input>_excluded_rows.csv)",
    )
    ap.add_argument(
        "--out-filtered",
        default=None,
        help="Output CSV with excluded participants removed (default: <input>_filtered.csv)",
    )
    ap.add_argument(
        "--plot-dir",
        default=None,
        help="Optional directory to save plots as PNG in addition to showing them",
    )
    args = ap.parse_args()

    inp = Path(args.inp)
    df_raw = pd.read_csv(inp)

    # --- Run legacy-style participant exclusions ---
    ex = anomaly_detector_like_legacy(
        df_raw,
        pressing_column=args.column,
        pressing_upper_limit=float(args.upper_limit),
        reading_thr=READING_MIN_MS,
    )

    # Keep the legacy diagnostic printout for the GMM
    thr_diag = gmm_bimodal_threshold(df_raw, column=args.column, upper_limit=float(args.upper_limit))
    print(f"GMM means (sorted): {thr_diag.means}")

    print(f"Pressing threshold ({args.column}): {ex.pressing_threshold:.3f}")
    print(f"Excluded (poor button activity): {len(ex.excluded_pressing)}")
    print(f"Excluded (not engaged): {len(ex.excluded_not_engaged)}")
    print(f"Excluded (skipping description): {len(ex.excluded_skipping_desc)}")
    print(f"Excluded (union): {len(ex.excluded_union)}")

    # --- Outputs: excluded rows + filtered dataset ---
    out_anom = Path(args.out_anomalies) if args.out_anomalies else inp.with_name(inp.stem + "_excluded_rows.csv")
    out_filt = Path(args.out_filtered) if args.out_filtered else inp.with_name(inp.stem + "_filtered.csv")

    df = normalize_for_qc(df_raw)
    residual_row_reading_mask = df['track_reading_duration'].fillna(0) < READING_MIN_MS

    excluded_mask = df["userid"].astype(str).isin(ex.excluded_union) | residual_row_reading_mask
    excluded_rows = df[excluded_mask].copy()

    # Keep the same key columns as the dissertation export (plus reason flags)
    keep_cols = [
        c
        for c in [
            "userid",
            "expid",
            "track_number",
            "reading_dur",
            args.column,
            "track_q1_1",
            "track_q1_2",
            "track_q1_3",
        ]
        if c in excluded_rows.columns
    ]
    excluded_rows["flag_poor_button_activity"] = excluded_rows["userid"].astype(str).isin(ex.excluded_pressing)
    excluded_rows["flag_not_engaged"] = excluded_rows["userid"].astype(str).isin(ex.excluded_not_engaged)
    excluded_rows["flag_skipping_description"] = (excluded_rows["userid"].astype(str).isin(ex.excluded_skipping_desc) |
                                                  residual_row_reading_mask.loc[excluded_rows.index])

    out_anom.parent.mkdir(parents=True, exist_ok=True)
    excluded_rows[keep_cols + ["flag_poor_button_activity", "flag_not_engaged", "flag_skipping_description"]].to_csv(
        out_anom, index=False
    )
    print(f"Wrote excluded rows -> {out_anom}")

    user_excl_mask = df["userid"].astype(str).isin(ex.excluded_union)
    excluded_mask = user_excl_mask | residual_row_reading_mask
    filtered = df.loc[~excluded_mask].copy()

    out_filt.parent.mkdir(parents=True, exist_ok=True)
    filtered.to_csv(out_filt, index=False)
    print(f"Wrote filtered dataset -> {out_filt}")

    # Optional: write a simple per-user summary
    summary_path = out_anom.with_name(out_anom.stem.replace("_excluded_rows", "") + "_excluded_users.csv")
    summary = pd.DataFrame(
        {
            "userid": ex.excluded_union,
            "poor_button_activity": [u in set(ex.excluded_pressing) for u in ex.excluded_union],
            "not_engaged": [u in set(ex.excluded_not_engaged) for u in ex.excluded_union],
            "skipping_description": [u in set(ex.excluded_skipping_desc) for u in ex.excluded_union],
        }
    )
    summary.to_csv(summary_path, index=False)
    print(f"Wrote excluded users summary -> {summary_path}")

    # --- Plots: legacy histogram triptych + venn3 ---
    if args.plot:
        plot_dir = Path(args.plot_dir) if args.plot_dir else None
        if plot_dir:
            plot_dir.mkdir(parents=True, exist_ok=True)

        _plot_pressing_hist_triptych(
            df_raw=df_raw,
            column=args.column,
            upper_limit=float(args.upper_limit),
            threshold=ex.pressing_threshold,
            save_to=(plot_dir / f"pressing_qc_{args.column}.png") if plot_dir else None,
        )
        _plot_exclusion_venn(
            ex,
            save_to=(plot_dir / "excluded_participants_venn3.png") if plot_dir else None,
        )

        plt.show()

    return 0


def _plot_pressing_hist_triptych(
    df_raw: pd.DataFrame,
    column: str,
    upper_limit: float,
    threshold: float,
    save_to: Optional[Path] = None,
) -> None:
    """Replicate the legacy histogram+GMM+scatter diagnostic (3 panels)."""

    x_full = pd.to_numeric(df_raw[column], errors="coerce").dropna()
    df_fit = df_raw.copy()
    df_fit[column] = pd.to_numeric(df_fit[column], errors="coerce")
    df_fit = df_fit.dropna(subset=[column])
    df_fit = df_fit[df_fit[column] < float(upper_limit)]

    if len(df_fit) < 5:
        fig = plt.figure(figsize=(12, 6))
        plt.title("Not enough data to fit a 2-component GMM")
        return

    data = df_fit[column].to_numpy().reshape(-1, 1)
    gmm = GaussianMixture(n_components=2, random_state=0)
    gmm.fit(data)
    labels = gmm.predict(data)

    fig = plt.figure(figsize=(12, 6))

    # Panel 1: full data histogram
    ax1 = plt.subplot(1, 3, 1)
    ax1.hist(x_full, bins=40, density=True)
    ax1.set_title("Full Data", fontsize=20)
    ax1.set_xlabel(column, fontsize=20)
    ax1.set_ylabel("Occurancies", fontsize=20)
    ax1.tick_params(axis="both", labelsize=16)

    # Panel 2: filtered histogram + fitted PDF
    ax2 = plt.subplot(1, 3, 2)
    ax2.hist(df_fit[column], bins=max(int(upper_limit / 2), 10), density=True)

    # Compute fitted pdf
    x = np.linspace(df_fit[column].min(), df_fit[column].max(), 1000).reshape(-1, 1)
    logprob = gmm.score_samples(x)
    pdf = np.exp(logprob)
    ax2.plot(x, pdf, linewidth=2)
    ax2.axvline(threshold, linestyle="--", linewidth=2)
    ax2.set_title("Data and Fitted GMM", fontsize=20)
    ax2.set_xlabel(column, fontsize=20)
    ax2.set_ylabel("Density", fontsize=20)
    ax2.tick_params(axis="both", labelsize=16)

    # Panel 3: clustered observations
    ax3 = plt.subplot(1, 3, 3)
    sc = ax3.scatter(range(len(df_fit[column])), df_fit[column], c=labels, cmap="viridis")
    ax3.set_xlabel("Observation Index", fontsize=20)
    ax3.set_ylabel(column, fontsize=20)
    ax3.set_title("Clustered Observations", fontsize=20)
    ax3.tick_params(axis="both", labelsize=16)
    cb = plt.colorbar(sc, ax=ax3)
    cb.ax.tick_params(labelsize=16)

    plt.tight_layout()
    if save_to is not None:
        fig.savefig(save_to, dpi=200, bbox_inches="tight")


def _plot_exclusion_venn(ex, save_to: Optional[Path] = None) -> None:
    """Replicate the legacy venn3 plot of excluded participants."""

    try:
        from matplotlib_venn import venn3
    except Exception as e:  # pragma: no cover
        print("matplotlib-venn is not installed; skipping venn plot.")
        print(f"Import error: {e}")
        return

    set_pressing = set(ex.excluded_pressing)
    set_engaged = set(ex.excluded_not_engaged)
    set_reading = set(ex.excluded_skipping_desc)

    fig = plt.figure(figsize=(8, 6))
    v = venn3(
        [set_pressing, set_engaged, set_reading],
        set_labels=("Poor Buttons Activity", "Not Engaged", "Skipping Description"),
    )

    # Hide "0" subset labels and enlarge text to match the legacy script
    if v.subset_labels:
        for text in v.subset_labels:
            if text and text.get_text() == "0":
                text.set_text("")
            if text:
                text.set_fontsize(24)

    if v.set_labels:
        for label in v.set_labels:
            if label:
                label.set_fontsize(24)

    plt.title("Overlap of Participant excluded by categories", fontsize=24, fontweight="bold")

    if save_to is not None:
        fig.savefig(save_to, dpi=200, bbox_inches="tight")


if __name__ == "__main__":
    raise SystemExit(main())

