#!/usr/bin/env python3
import argparse
import pandas as pd
from pathlib import Path

PREFERRED_KEYS = [
    # strongest single key (if present)
    ["response_id"],
    ["feedback_id"],
    # common combinations
    ["user_id", "experiment_id", "movement_id", "question_id"],
    ["user_id", "experiment", "movement", "question"],
    ["participant_id", "experiment_id", "movement_id", "question_id"],
    ["participant_id", "experiment", "movement", "question"],
    ["user_id", "experiment_id", "movement_id"],
    ["user_id", "experiment", "movement"],
    ["participant_id", "experiment_id", "movement_id"],
    ["participant_id", "experiment", "movement"],
]

def pick_join_keys(base: pd.DataFrame, fb: pd.DataFrame):
    base_cols = set(base.columns)
    fb_cols = set(fb.columns)

    # Try preferred patterns first
    for keys in PREFERRED_KEYS:
        if all(k in base_cols for k in keys) and all(k in fb_cols for k in keys):
            return keys

    # Fall back: use intersection of likely identifier columns
    candidates = [c for c in base.columns if c in fb.columns and any(tok in c.lower() for tok in
                   ["user", "participant", "subject", "id", "experiment", "movement", "track", "question", "item"])]
    if candidates:
        return candidates

    raise SystemExit(
        "Could not infer join keys. Pass --on col1 col2 ... explicitly."
    )

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

    on = args.on if args.on else pick_join_keys(base, fb)

    # Keep only new feedback columns + keys (avoid duplicating existing base columns)
    fb_cols_new = [c for c in fb.columns if c not in base.columns or c in on]
    fb = fb[fb_cols_new]

    # Sanity checks: make sure feedback keys are unique (otherwise merge can explode rows)
    dup = fb.duplicated(subset=on, keep=False)
    if dup.any():
        bad = fb.loc[dup, on].drop_duplicates().head(20)
        raise SystemExit(
            f"Feedback file has duplicate rows for join keys {on}. "
            f"Fix upstream or aggregate first. Example duplicate keys:\n{bad}"
        )

    out = base.merge(fb, on=on, how=args.how, validate="m:1" if args.how in ("left","inner") else None)

    # Useful stats
    matched = out[on].merge(fb[on], on=on, how="inner").shape[0]
    print(f"Join keys: {on}")
    print(f"Base rows: {len(base):,}")
    print(f"Feedback rows: {len(fb):,}")
    print(f"Output rows: {len(out):,}")
    print(f"Matched base rows: {matched:,} (some keys may repeat in base; that’s ok)")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)

if __name__ == "__main__":
    main()
