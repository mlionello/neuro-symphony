from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .pressing import gmm_bimodal_threshold


@dataclass(frozen=True)
class ExclusionResult:
    """Participant exclusion results replicating the dissertation pipeline.

    The original dissertation scripts excluded participants based on three
    categories (computed at the *movement* level):

    - Poor button activity (pressing task)
    - Not engaged (low post-movement engagement ratings)
    - Skipping the description (reading time < 10s)

    This dataclass keeps both the *per-user* sets and the GMM threshold used
    for the pressing criterion.
    """

    pressing_threshold: float
    excluded_pressing: Sequence[str]
    excluded_not_engaged: Sequence[str]
    excluded_skipping_desc: Sequence[str]
    excluded_union: Sequence[str]

    # Additional “anomaly” lists computed in the original function but not
    # used for exclusion (kept for parity / diagnostics).
    anomaly_users_std: Sequence[str]
    anomaly_users_iqr: Sequence[str]


def _coalesce_track_value(df: pd.DataFrame, base: str) -> pd.Series:
    """Return a unified per-row series for the current track.

    The cleaned extraction keeps track-specific columns (e.g.
    `track_1_reading_duration`) while the legacy scripts created unified
    columns (e.g. `reading_dur`) per movement. This helper recreates the
    legacy behavior.
    """

    if base in df.columns:
        return df[base]

    if "track_number" not in df.columns:
        # Best effort: return NA.
        return pd.Series([pd.NA] * len(df), index=df.index)

    out = pd.Series([pd.NA] * len(df), index=df.index)
    for tn in [1, 2, 3, 4]:
        col = f"track_{tn}_{base}"
        if col in df.columns:
            out = out.where(df["track_number"] != tn, df[col])
    return out


def normalize_for_qc(df: pd.DataFrame) -> pd.DataFrame:
    """Add legacy-compatible QC columns.

    Adds/overwrites:
    - `reading_dur`
    - `track_q1_1`, `track_q1_2`, `track_q1_3`
    """

    work = df.copy()

    # Durations
    if "reading_dur" not in work.columns:
        # In the web app this is stored as `reading_duration` (ms)
        work["reading_dur"] = _coalesce_track_value(work, "reading_duration")

    # Engagement ratings
    for i in (1, 2, 3):
        legacy = f"track_q1_{i}"
        if legacy not in work.columns:
            work[legacy] = _coalesce_track_value(work, f"q1_{i}")

    return work


def _apply_multi_session_grace_rule(
    df: pd.DataFrame,
    flagged_userids: List[str],
    max_ratio: float,
    min_rows_for_grace: int = 8,
) -> List[str]:
    """Replicate the original “grace rule” for multi-symphony participants."""

    flagged_copy = list(flagged_userids)
    out = list(flagged_userids)

    for u in np.unique(flagged_copy):
        m = flagged_copy.count(u)
        n = int((df["userid"] == u).sum()) if "userid" in df.columns else 0
        if n >= min_rows_for_grace and n > 0 and (m / n) <= max_ratio:
            out = [x for x in out if x != u]
    return out


def anomaly_detector_like_legacy(
    df_raw: pd.DataFrame,
    pressing_column: str = "total_events",
    pressing_upper_limit: float = 80,
    reading_thr: int = 10000,
) -> ExclusionResult:
    """Compute exclusions using the same logic as the legacy `anomaly_detector`.

    Parameters
    ----------
    df_raw
        Movement-level dataframe, typically the output of
        `add_pressing_metrics.py`.
    pressing_column
        Column used for pressing QC (default `total_events`).
    pressing_upper_limit
        Upper limit filter used while fitting the bimodal GMM.
    """

    df = normalize_for_qc(df_raw)

    # --- Extra anomaly heuristics (computed, but not used for exclusion) ---
    # The legacy function computed IQR- and mean/std-based anomalies on
    # multiple pressing metrics. It parsed JSON arrays, then took their max.
    anomaly_users_iqr: List[str] = []
    anomaly_users_std: List[str] = []

    json_array_fields = [
        "feature_event_rate",
        "avg_activation_duration",
        "max_activation_duration",
        "total_activation_duration",
    ]

    work = df.copy()
    for k in json_array_fields:
        if k in work.columns:
            def _parse(v):
                if v is None or (isinstance(v, float) and np.isnan(v)):
                    return None
                if isinstance(v, (list, tuple, np.ndarray)):
                    return list(v)
                if isinstance(v, str):
                    try:
                        return json.loads(v)
                    except Exception:
                        return None
                return None

            parsed = work[k].apply(_parse)
            # max over list-like values
            work[k] = parsed.apply(lambda x: max(x) if isinstance(x, list) and len(x) else np.nan)

    features = [
        "activation_rate",
        "event_rate",
        "feature_event_rate",
        "avg_activation_duration",
        "max_activation_duration",
        "total_activation_duration",
    ]
    for feat in features:
        if feat not in work.columns:
            continue
        series = pd.to_numeric(work[feat], errors="coerce")
        series = series.dropna()
        if len(series) < 10:
            continue

        # IQR rule
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_iqr = q1 - 1.5 * iqr
        anomaly_users_iqr.extend(work.loc[series.index[series < lower_iqr], "userid"].astype(str).tolist())

        # mean/std rule (legacy used mean - 2*std)
        mean = float(series.mean())
        std = float(series.std())
        lower_std = mean - 2.0 * std
        anomaly_users_std.extend(work.loc[series.index[series < lower_std], "userid"].astype(str).tolist())

    # --- Exclusion categories ---
    # 1) Skipping description: reading_dur < 10 seconds (10,000 ms)
    reading = pd.to_numeric(df["track_reading_duration"], errors="coerce")
    users_skip = df.loc[reading < reading_thr, "userid"].astype(str).tolist()
    users_skip = _apply_multi_session_grace_rule(df, users_skip, max_ratio=(1 / 8))

    # 2) Not engaged: any of track_q1_1..3 < 2
    targets = ["track_q1_1", "track_q1_2", "track_q1_3"]
    present_targets = [t for t in targets if t in df.columns]
    if present_targets:
        tdf = df[present_targets].apply(pd.to_numeric, errors="coerce")
        not_engaged_mask = tdf.lt(2).any(axis=1)
        users_not_engaged = df.loc[not_engaged_mask, "userid"].astype(str).tolist()
    else:
        users_not_engaged = []
    users_not_engaged = _apply_multi_session_grace_rule(df, users_not_engaged, max_ratio=0.25)

    # 3) Poor button activity: threshold via bimodal GMM on total_events
    thr_res = gmm_bimodal_threshold(df, column=pressing_column, upper_limit=pressing_upper_limit)
    threshold = float(thr_res.threshold)

    total_events = pd.to_numeric(df.get(pressing_column), errors="coerce")
    users_not_pressing = df.loc[(~total_events.notna()) | (total_events < threshold), "userid"].astype(str).tolist()
    users_not_pressing = _apply_multi_session_grace_rule(df, users_not_pressing, max_ratio=(1 / 8))

    # Unique sets + union
    set_pressing = sorted(set(users_not_pressing))
    set_engaged = sorted(set(users_not_engaged))
    set_reading = sorted(set(users_skip))
    union = sorted(set(set_pressing) | set(set_engaged) | set(set_reading))

    return ExclusionResult(
        pressing_threshold=threshold,
        excluded_pressing=set_pressing,
        excluded_not_engaged=set_engaged,
        excluded_skipping_desc=set_reading,
        excluded_union=union,
        anomaly_users_std=sorted(set(anomaly_users_std)),
        anomaly_users_iqr=sorted(set(anomaly_users_iqr)),
    )
