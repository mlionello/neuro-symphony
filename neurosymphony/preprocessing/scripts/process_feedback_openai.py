#!/usr/bin/env python3
from __future__ import annotations
import argparse
import pandas as pd

from core.openai_feedback import OpenAIChat, is_narrative, rate_valence_arousal


def main() -> int:
    ap = argparse.ArgumentParser(description="Rate open-ended feedback valence/arousal via OpenAI (optional pipeline step).")
    ap.add_argument("--in", dest="inp", required=True, help="Input merged CSV (from extract_data.py)")
    ap.add_argument("--out", required=True, help="Output CSV")
    ap.add_argument("--model", default="gpt-4o-mini", help="Model name")
    ap.add_argument("--repeats", type=int, default=5, help="How many times to sample ratings and average")
    ap.add_argument("--max-rows", type=int, default=None, help="Optional cap for testing")
    args = ap.parse_args()

    df = pd.read_csv(args.inp)
    chat = OpenAIChat(model=args.model)

    out_rows = []
    n = len(df) if args.max_rows is None else min(len(df), args.max_rows)

    for i in range(n):
        print(f"Processing row {i+1} of {n}")
        row = df.iloc[i]
        track_n = int(row.get("track_number", 0) or 0)
        if track_n not in (1, 2, 3, 4):
            continue

        feedback = row.get(f"track_feedback")
        if not isinstance(feedback, str) or len(feedback.strip()) < 10:
            continue

        # reference text shown to the participant (if available)
        ref_text = row.get("description_text") if isinstance(row.get("description_text"), str) else ""

        if not is_narrative(chat, feedback):
            continue

        fb_ar, fb_val = rate_valence_arousal(chat, feedback, repeats=args.repeats)

        out_rows.append(
            {
                "userid": row.get("userid"),
                "expid": row.get("expid"),
                "track_number": track_n,
                "cond_track": row.get("cond_track"),
                "description_line": row.get("description_line"),
                "feedback": feedback,
                "description_text": ref_text,
                "rating_feedback_arousal": fb_ar,
                "rating_feedback_valence": fb_val,
                "track_q2_1": row.get(f"track_q2_1"),
                "track_q2_2": row.get(f"track_q2_2"),
                "track_q2_3": row.get(f"track_q2_3"),
                "track_q2_4": row.get(f"track_q2_4"),
            }
        )

        if (len(out_rows) % 25) == 0:
            print(f"Rated {len(out_rows)} narrative feedback items (scanned {i+1}/{n} rows)")

    out_df = pd.DataFrame(out_rows)
    out_df.to_csv(args.out, index=False)
    print(f"Wrote {len(out_df):,} rows -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
