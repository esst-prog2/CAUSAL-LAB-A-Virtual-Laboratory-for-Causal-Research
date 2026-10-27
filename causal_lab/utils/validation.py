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


INDICATOR_COLUMNS = ("D", "treated_unit")     # 0/1 indicators
NUMERIC_COLUMNS = ("period", "Y")


def invalid_required_columns(df: pd.DataFrame) -> list[str]:
    """Required columns whose values the estimators cannot use: indicators
    that are not all 0/1 (booleans count as 0/1), and a non-numeric period
    or outcome. Assumes no required column is missing (hw6 review 5)."""
    bad = [c for c in INDICATOR_COLUMNS
           if df[c].isna().any() or not df[c].isin([0, 1]).all()]
    bad += [c for c in NUMERIC_COLUMNS if not pd.api.types.is_numeric_dtype(df[c])]
    return bad


def missing_required_columns(df: pd.DataFrame) -> list[str]:
    """Return the required columns absent from `df`, in canonical order."""
    return [c for c in REQUIRED_COLUMNS if c not in df.columns]


def drop_incomplete_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Leave out rows with a missing unit, period or outcome, as the other
    estimators do (listwise deletion), and say how many. Missing values in
    the 0/1 indicators are refused instead (invalid_required_columns): a
    missing treatment status is not something to guess."""
    keep = df[["unit", "period", "Y"]].notna().all(axis=1)
    return df[keep].reset_index(drop=True), int((~keep).sum())
