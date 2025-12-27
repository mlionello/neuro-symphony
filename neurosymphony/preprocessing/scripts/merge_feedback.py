#!/usr/bin/env python3
import argparse
import pandas as pd
from pathlib import Path

ON = ["userid", "expid", "track_number"]


def main():
    ap = argparse.ArgumentParser(description="Merge processed OpenAI feedback back into the base dataset.")
    ap.add_argument("--base", required=True, help="Base CSV (e.g., merged_exp_data.csv)")
    ap.add_argument("--feedback", required=True, help="Feedback CSV (e.g., processed_feedback_results.csv)")
    ap.add_argument("--out", required=True, help="Output CSV (final merged dataset)")
    ap.add_argument("--on", nargs="+", default=None, help="Join key columns (override autodetect)")
    ap.add_argument("--how", default="left", choices=["left","inner","right","outer"], help="Merge type (default left)")
    args = ap.parse_args()

    base = pd.read_csv(args.base)
    fb = pd.read_csv(args.feedback)

    # Keep only new feedback columns + keys (avoid duplicating existing base columns)
    fb_cols_new = [c for c in fb.columns if c not in base.columns or c in ON]
    fb = fb[fb_cols_new]

    # Sanity checks: make sure feedback keys are unique (otherwise merge can explode rows)
    dup = fb.duplicated(subset=ON, keep=False)
    if dup.any():
        bad = fb.loc[dup, ON].drop_duplicates().head(20)
        raise SystemExit(
            f"Feedback file has duplicate rows for join keys {ON}. "
            f"Fix upstream or aggregate first. Example duplicate keys:\n{bad}"
        )

    out = base.merge(fb, on=ON, how=args.how, validate="m:1" if args.how in ("left","inner") else None)

    # Useful stats
    matched = out[ON].merge(fb[ON], on=ON, how="inner").shape[0]
    print(f"Join keys: {ON}")
    print(f"Base rows: {len(base):,}")
    print(f"Feedback rows: {len(fb):,}")
    print(f"Output rows: {len(out):,}")
    print(f"Matched base rows: {matched:,} (some keys may repeat in base; that’s ok)")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)


if __name__ == "__main__":
    main()
