from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture


@dataclass(frozen=True)
class GMMThresholdResult:
    """Result of a 2-component GMM fit on a 1D feature.

    Attributes
    ----------
    threshold
        Midpoint between the maximum value of the left cluster and the minimum
        value of the right cluster.
    labels
        Per-row cluster labels (0/1) for the subset used to fit the model.
    means
        Component means (sorted).
    """

    threshold: float
    labels: pd.Series
    means: Tuple[float, float]


def gmm_bimodal_threshold(
    df: pd.DataFrame,
    column: str,
    upper_limit: Optional[float] = None,
    random_state: int = 0,
) -> GMMThresholdResult:
    """Fit a 2-component GMM and compute a separation threshold.

    Parameters
    ----------
    df
        Input dataframe.
    column
        Column containing the feature (numeric).
    upper_limit
        If provided, only rows with values < upper_limit are used to fit.
        This matches the original exploratory workflow.

    Returns
    -------
    GMMThresholdResult
    """
    if column not in df.columns:
        raise KeyError(f"Column not found: {column}")

    work = df[[column]].copy()
    work[column] = pd.to_numeric(work[column], errors="coerce")
    work = work.dropna()

    if upper_limit is not None:
        work = work[work[column] < float(upper_limit)]

    if len(work) < 5:
        raise ValueError("Not enough data points to fit GMM.")

    data = work[column].to_numpy().reshape(-1, 1)
    gmm = GaussianMixture(n_components=2, random_state=random_state)
    gmm.fit(data)

    labels = pd.Series(gmm.predict(data), index=work.index)
    means = gmm.means_.reshape(-1)
    right = int(np.argmax(means))
    left = int(np.argmin(means))

    min_right = float(work.loc[labels[labels == right].index, column].min())
    max_left = float(work.loc[labels[labels == left].index, column].max())

    threshold = (max_left + min_right) / 2.0
    means_sorted = tuple(sorted([float(means[left]), float(means[right])]))

    return GMMThresholdResult(threshold=threshold, labels=labels, means=means_sorted)
