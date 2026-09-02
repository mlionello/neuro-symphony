from __future__ import annotations

from typing import List

import pandas as pd

MERGE_KEYS = ["userid", "expid", "track_number"]


def merge_feedback(base: pd.DataFrame, feedback: pd.DataFrame, on: List[str] = MERGE_KEYS) -> pd.DataFrame:
    fb_cols_new = [c for c in feedback.columns if c not in base.columns or c in on]
    fb = feedback[fb_cols_new]

    dup = fb.duplicated(subset=on, keep=False)
    if dup.any():
        bad = fb.loc[dup, on].drop_duplicates().head(20)
        raise ValueError(f"Feedback file has duplicate rows for join keys {on}:\n{bad}")

    return base.merge(fb, on=on, how="left", validate="m:1")