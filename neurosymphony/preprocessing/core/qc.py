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
    pressing_threshold: float
    excluded_pressing: Sequence[str]
    excluded_not_engaged: Sequence[str]
    excluded_skipping_desc: Sequence[str]
    excluded_union: Sequence[str]

    anomaly_users_std: Sequence[str]
    anomaly_users_iqr: Sequence[str]


def _coalesce_track_value(df: pd.DataFrame, base: str) -> pd.Series:

    if base in df.columns:
        return df[base]

    if "track_number" not in df.columns:
        return pd.Series([pd.NA] * len(df), index=df.index)

    out = pd.Series([pd.NA] * len(df), index=df.index)
    for tn in [1, 2, 3, 4]:
        col = f"track_{tn}_{base}"
        if col in df.columns:
            out = out.where(df["track_number"] != tn, df[col])
    return out


def normalize_for_qc(df: pd.DataFrame) -> pd.DataFrame:

    work = df.copy()

    if "reading_dur" not in work.columns:
        work["reading_dur"] = _coalesce_track_value(work, "reading_duration")

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

    flagged_copy = list(flagged_userids)
    out = list(flagged_userids)

    for u in np.unique(flagged_copy):
        m = flagged_copy.count(u)
        n = int((df["userid"] == u).sum()) if "userid" in df.columns else 0
        if n >= min_rows_for_grace and n > 0 and (m / n) <= max_ratio:
            out = [x for x in out if x != u]
    return out


def detect_pressing_anomalies(
    df_raw: pd.DataFrame,
    pressing_column: str = "total_events",
    pressing_upper_limit: float = 80,
    reading_thr: int = 10000,
) -> ExclusionResult:

    df = normalize_for_qc(df_raw)

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

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_iqr = q1 - 1.5 * iqr
        anomaly_users_iqr.extend(work.loc[series.index[series < lower_iqr], "userid"].astype(str).tolist())

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
