#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from core.metrics import compute_pressing_metrics, json_dumps_compact, load_pressing_csv


def main() -> int:
    ap = argparse.ArgumentParser(description="Add pressing-task summary metrics to a merged table.")
    ap.add_argument("--in", dest="inp", required=True, help="Input CSV (e.g., merged_exp_data.csv)")
    ap.add_argument("--out", required=True, help="Output CSV")
    ap.add_argument("--pressing-col", default="pressing_csv", help="Column containing the pressing-log path")
    ap.add_argument("--keep-raw", action="store_true", help="Keep JSON arrays as expanded columns (default stores arrays as JSON strings)")
    args = ap.parse_args()

    df = pd.read_csv(args.inp)
    if args.pressing_col not in df.columns:
        raise SystemExit(f"Missing column: {args.pressing_col}. Did you run extract_data.py?")

    metrics_rows = []
    for i, row in df.iterrows():
        p = row.get(args.pressing_col)
        if isinstance(p, str) and p.strip():
            try:
                mtx = load_pressing_csv(p)
                metrics = compute_pressing_metrics(mtx)
            except Exception:
                metrics = {
                    "activation_rate": None,
                    "event_rate": None,
                    "total_events": None,
                    "feature_event_rate": None,
                    "avg_activation_duration": None,
                    "max_activation_duration": None,
                    "total_activation_duration": None,
                }
        else:
            metrics = {
                "activation_rate": None,
                "event_rate": None,
                "total_events": None,
                "feature_event_rate": None,
                "avg_activation_duration": None,
                "max_activation_duration": None,
                "total_activation_duration": None,
            }

        # Store array-like fields as compact JSON strings for CSV friendliness
        out_metrics = dict(metrics)
        if not args.keep_raw:
            for k in [
                "feature_event_rate",
                "avg_activation_duration",
                "max_activation_duration",
                "total_activation_duration",
            ]:
                if out_metrics.get(k) is not None:
                    out_metrics[k] = json_dumps_compact(out_metrics[k])
        metrics_rows.append(out_metrics)

        if (i + 1) % 250 == 0:
            print(f"Processed {i + 1}/{len(df)} rows")

    mdf = pd.DataFrame(metrics_rows)
    out_df = pd.concat([df.reset_index(drop=True), mdf.reset_index(drop=True)], axis=1)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out, index=False)
    print(f"Wrote {len(out_df):,} rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
