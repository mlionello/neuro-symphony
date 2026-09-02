#!/usr/bin/env python3
"""Raw logs -> a final.csv-equivalent table.

Walks web/userdata/user_*/ JSON logs and button-press CSVs, joins in
symphony metadata and description ratings, computes pressing metrics,
runs participant-exclusion QC (poor button activity / not engaged /
skipped description reading, with a grace rule for multi-symphony
participants), and, given a precomputed feedback CSV via --feedback,
merges it in. All the logic lives in core/; this script just calls it
in order.

--out-final (final.csv by default) is the intended input to
scripts/build_dataset.py --in.

Usage:
    python -m scripts.extract_final \\
        --userdata web/userdata \\
        --framework web/data/framework.json \\
        --ratings data/programnotes/ratings \\
        --feedback feedbacks_metrics.csv \\
        --out merged_exp_data_with_metrics.csv \\
        --out-final final.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from core.extract import extract_merged_experiment_table
from core.merge import merge_feedback
from core.metrics import compute_pressing_metrics, json_dumps_compact, load_pressing_csv
from core.qc import detect_pressing_anomalies, normalize_for_qc

READING_MIN_MS = 10_000
PRESSING_METRIC_FIELDS = [
    "activation_rate", "event_rate", "total_events", "feature_event_rate",
    "avg_activation_duration", "max_activation_duration", "total_activation_duration",
]
JSON_ARRAY_FIELDS = [
    "feature_event_rate", "avg_activation_duration", "max_activation_duration", "total_activation_duration",
]


def add_pressing_metrics(df: pd.DataFrame, pressing_col: str = "pressing_csv") -> pd.DataFrame:
    metrics_rows = []
    for _, row in df.iterrows():
        p = row.get(pressing_col)
        metrics = None
        if isinstance(p, str) and p.strip():
            try:
                metrics = compute_pressing_metrics(load_pressing_csv(p))
            except Exception:
                metrics = None
        if metrics is None:
            metrics = {k: None for k in PRESSING_METRIC_FIELDS}

        out_metrics = dict(metrics)
        for k in JSON_ARRAY_FIELDS:
            if out_metrics.get(k) is not None:
                out_metrics[k] = json_dumps_compact(out_metrics[k])
        metrics_rows.append(out_metrics)

    mdf = pd.DataFrame(metrics_rows)
    return pd.concat([df.reset_index(drop=True), mdf.reset_index(drop=True)], axis=1)


def apply_qc(df: pd.DataFrame, pressing_column: str = "total_events", pressing_upper_limit: float = 80.0):
    ex = detect_pressing_anomalies(
        df, pressing_column=pressing_column, pressing_upper_limit=pressing_upper_limit, reading_thr=READING_MIN_MS,
    )
    normalized = normalize_for_qc(df)
    residual_row_reading_mask = (
        pd.to_numeric(normalized["track_reading_duration"], errors="coerce").fillna(0) < READING_MIN_MS
    )
    excluded_mask = normalized["userid"].astype(str).isin(ex.excluded_union) | residual_row_reading_mask
    return normalized.loc[~excluded_mask].copy(), ex


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--userdata", required=True, help="Path to web/userdata")
    ap.add_argument("--framework", required=True, help="Path to web/data/framework.json")
    ap.add_argument("--ratings", required=True, help="Path to the description-ratings folder (data/programnotes/ratings)")
    ap.add_argument("--out", default="merged_exp_data_with_metrics.csv", help="Extraction+metrics output (pre-QC)")
    ap.add_argument("--skip-qc", action="store_true", help="Skip participant exclusion / QC")
    ap.add_argument("--pressing-column", default="total_events", help="Column used for the pressing-activity GMM")
    ap.add_argument("--upper-limit", type=float, default=80.0, help="Upper limit filter used to fit the GMM")
    ap.add_argument("--out-filtered", default=None, help="QC'd output (default: <out>_filtered.csv)")
    ap.add_argument("--out-excluded-users", default=None, help="Excluded-users summary (default: <out>_excluded_users.csv)")
    ap.add_argument("--feedback", default=None, help="Optional pre-computed feedback CSV to merge in (e.g. feedbacks_metrics.csv)")
    ap.add_argument("--out-final", default=None, help="Final merged output when --feedback is given (default: final.csv)")
    args = ap.parse_args()

    df = extract_merged_experiment_table(args.userdata, args.framework, args.ratings)
    df = add_pressing_metrics(df)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Wrote {len(df):,} rows -> {out}")

    current = df
    if not args.skip_qc:
        filtered, ex = apply_qc(df, args.pressing_column, args.upper_limit)
        print(f"Pressing threshold ({args.pressing_column}): {ex.pressing_threshold:.3f}")
        print(f"Excluded (poor button activity): {len(ex.excluded_pressing)}")
        print(f"Excluded (not engaged): {len(ex.excluded_not_engaged)}")
        print(f"Excluded (skipping description): {len(ex.excluded_skipping_desc)}")
        print(f"Excluded (union): {len(ex.excluded_union)}")

        out_filt = Path(args.out_filtered) if args.out_filtered else out.with_name(out.stem + "_filtered.csv")
        filtered.to_csv(out_filt, index=False)
        print(f"Wrote {len(filtered):,} rows -> {out_filt}")

        out_excl = Path(args.out_excluded_users) if args.out_excluded_users else out.with_name(out.stem + "_excluded_users.csv")
        pd.DataFrame(
            {
                "userid": ex.excluded_union,
                "poor_button_activity": [u in set(ex.excluded_pressing) for u in ex.excluded_union],
                "not_engaged": [u in set(ex.excluded_not_engaged) for u in ex.excluded_union],
                "skipping_description": [u in set(ex.excluded_skipping_desc) for u in ex.excluded_union],
            }
        ).to_csv(out_excl, index=False)
        print(f"Wrote excluded-users summary -> {out_excl}")

        current = filtered

    if args.feedback:
        feedback = pd.read_csv(args.feedback)
        merged = merge_feedback(current, feedback)
        out_final = Path(args.out_final) if args.out_final else Path("final.csv")
        merged.to_csv(out_final, index=False)
        print(f"Wrote {len(merged):,} rows -> {out_final}")
    elif not args.skip_qc:
        print("No --feedback given; stopping after QC. Pass --feedback <csv> to also produce a final.csv-equivalent.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())