"""
Upload column validation (CAUSAL LAB spec: real-world-data-upload).

The app assumes a fixed set of column names throughout — estimators,
the stress test, and the robustness battery all default to them — and
offers no column-mapping UI. This module is the single place that
checks an uploaded CSV has them, run at upload time before the file
becomes the active dataset.
"""
from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = ("unit", "period", "Y", "D", "treated_unit")


def missing_required_columns(df: pd.DataFrame) -> list[str]:
    """Return the required columns absent from `df`, in canonical order."""
    return [c for c in REQUIRED_COLUMNS if c not in df.columns]
