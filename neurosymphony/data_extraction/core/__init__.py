"""Neuro-Symphony / Music Context data-processing utilities.

This package contains small, dependency-light helpers used by the CLI scripts
in `code_cleaned/scripts/`.
"""

from .goldmsi import compute_goldmsi_scores
from .pressing import gmm_bimodal_threshold
from .metrics import compute_pressing_metrics
from .extract import extract_merged_experiment_table

__all__ = [
    "compute_goldmsi_scores",
    "gmm_bimodal_threshold",
    "compute_pressing_metrics",
    "extract_merged_experiment_table",
]
