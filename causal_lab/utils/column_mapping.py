"""
Column mapping for the Causal Methods page (CAUSAL LAB spec:
causal-methods-lab).

Unlike the panel/DiD upload (fixed column names, see validation.py),
each additional method maps the uploaded CSV's columns to its own
roles. This module declares those roles and checks a mapping before
any estimator runs, returning problems by role name instead of
raising, in the same spirit as `missing_required_columns`.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Role:
    key: str
    label: str
    multi: bool = False          # several columns (covariates, instruments)
    required: bool = True
    numeric: bool = True


METHOD_ROLES: dict[str, tuple[Role, ...]] = {
    "rct": (
        Role("outcome", "Outcome"),
        Role("treatment", "Treatment (0/1)"),
        Role("covariates", "Covariates", multi=True, required=False),
    ),
    "matching": (
        Role("outcome", "Outcome"),
        Role("treatment", "Treatment (0/1)"),
        Role("covariates", "Covariates", multi=True),
    ),
    "iv": (
        Role("outcome", "Outcome"),
        Role("treatment", "Treatment (endogenous)"),
        Role("instruments", "Instrument(s)", multi=True),
        Role("controls", "Exogenous controls", multi=True, required=False),
    ),
    "rdd": (
        Role("outcome", "Outcome"),
        Role("running", "Running variable"),
    ),
    "synthetic_control": (
        Role("unit", "Unit", numeric=False),
        Role("period", "Period"),
        Role("outcome", "Outcome"),
    ),
    "dml": (
        Role("outcome", "Outcome"),
        Role("treatment", "Treatment"),
        Role("covariates", "Covariates", multi=True),
    ),
}


def _as_list(value) -> list[str]:
    if value is None or value == "":
        return []
    return list(value) if isinstance(value, (list, tuple)) else [value]


def validate_mapping(df: pd.DataFrame, method: str, mapping: dict) -> list[str]:
    """Return human-readable problems with `mapping` (role key -> column
    name, or list of names for multi roles). Empty list = valid."""
    problems: list[str] = []
    used: dict[str, str] = {}
    for role in METHOD_ROLES[method]:
        columns = _as_list(mapping.get(role.key))
        if role.required and not columns:
            problems.append(f"{role.label}: no column selected.")
            continue
        for col in columns:
            if col not in df.columns:
                problems.append(f"{role.label}: column '{col}' is not in the file.")
                continue
            if col in used:
                problems.append(f"{role.label}: column '{col}' is already used as {used[col]}.")
            used.setdefault(col, role.label)
            if role.numeric and not pd.api.types.is_numeric_dtype(df[col]):
                problems.append(f"{role.label}: column '{col}' must be numeric.")
    return problems


def prepare_mapped_frame(df: pd.DataFrame, method: str, mapping: dict) -> tuple[pd.DataFrame, int]:
    """Keep only the mapped columns and drop rows with a missing value
    in any of them. Returns (clean frame, number of rows dropped)."""
    columns: list[str] = []
    for role in METHOD_ROLES[method]:
        columns.extend(c for c in _as_list(mapping.get(role.key)) if c not in columns)
    subset = df[columns]
    clean = subset.dropna().reset_index(drop=True)
    return clean, len(subset) - len(clean)
