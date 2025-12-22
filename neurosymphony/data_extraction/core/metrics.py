from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional

import json
from pathlib import Path

import numpy as np


def _to_int01(x: Any) -> int:
    try:
        v = int(float(x))
    except Exception:
        return 0
    return 1 if v != 0 else 0


def load_pressing_csv(path: str | Path) -> np.ndarray:
    """Load a per-track pressing log CSV.

    Expected format: first column timestamp (ms) then one column per button.
    Values are treated as binary.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)

    raw = np.genfromtxt(p, delimiter=",", dtype=str)
    if raw.ndim != 2 or raw.shape[1] < 2:
        raise ValueError(f"Unexpected pressing CSV shape: {raw.shape}")

    # Keep timestamp as float, rest as 0/1
    ts = raw[:, 0].astype(float)
    buttons = np.vectorize(_to_int01)(raw[:, 1:]).astype(int)
    return np.column_stack([ts, buttons])


def compute_pressing_metrics(matrix: np.ndarray) -> Dict[str, Any]:
    """Compute summary metrics for a pressing-task matrix.

    Parameters
    ----------
    matrix
        2D array with shape (T, 1 + K) where first column is time and
        remaining K columns are button states.

    Returns
    -------
    dict
        activation_rate, event_rate, total_events, feature_event_rate (list),
        avg_activation_duration (list), max_activation_duration (list),
        total_activation_duration (list)
    """
    if matrix.ndim != 2 or matrix.shape[1] < 2:
        raise ValueError("matrix must be (T, 1+K) with at least one feature")

    features = matrix[:, 1:].astype(int)
    if len(features) < 2:
        raise ValueError("Need at least 2 timepoints to compute events")

    activation_rate = float(np.mean(features))

    # Events: any change between adjacent samples for a given feature
    events_per_feature = features[1:, :] - features[:-1, :]
    events_overall = np.any(events_per_feature != 0, axis=1)

    event_rate = float(np.mean(events_overall))
    total_events = int(np.sum(events_overall))

    feature_event_rate = np.mean(events_per_feature != 0, axis=0).tolist()

    # Activation durations per feature (run-length of consecutive 1s)
    avg_durs: List[float] = []
    max_durs: List[float] = []
    tot_durs: List[float] = []

    for k in range(features.shape[1]):
        col = features[:, k]
        # Find runs of 1s
        durs: List[int] = []
        run = 0
        for v in col:
            if v == 1:
                run += 1
            else:
                if run:
                    durs.append(run)
                run = 0
        if run:
            durs.append(run)

        if durs:
            avg_durs.append(float(np.mean(durs)))
            max_durs.append(float(np.max(durs)))
            tot_durs.append(float(np.sum(durs)))
        else:
            avg_durs.append(0.0)
            max_durs.append(0.0)
            tot_durs.append(0.0)

    return {
        "activation_rate": activation_rate,
        "event_rate": event_rate,
        "total_events": total_events,
        "feature_event_rate": feature_event_rate,
        "avg_activation_duration": avg_durs,
        "max_activation_duration": max_durs,
        "total_activation_duration": tot_durs,
    }


def json_dumps_compact(obj: Any) -> str:
    """Compact JSON dump used for embedding arrays into CSV."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
