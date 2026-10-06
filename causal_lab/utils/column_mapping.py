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

from utils.i18n import Msg


@dataclass(frozen=True)
class Role:
    key: str
    label_key: str               # locale key of the role's display label
    multi: bool = False          # several columns (covariates, instruments)
    required: bool = True
    numeric: bool = True

    @property
    def label(self) -> Msg:
        return Msg(self.label_key)


METHOD_ROLES: dict[str, tuple[Role, ...]] = {
    "rct": (
        Role("outcome", "role.outcome"),
        Role("treatment", "role.treatment_binary"),
        Role("covariates", "role.covariates", multi=True, required=False),
    ),
    "matching": (
        Role("outcome", "role.outcome"),
        Role("treatment", "role.treatment_binary"),
        Role("covariates", "role.covariates", multi=True),
    ),
    "iv": (
        Role("outcome", "role.outcome"),
        Role("treatment", "role.treatment_endogenous"),
        Role("instruments", "role.instruments", multi=True),
        Role("controls", "role.controls", multi=True, required=False),
    ),
    "rdd": (
        Role("outcome", "role.outcome"),
        Role("running", "role.running"),
    ),
    "synthetic_control": (
        Role("unit", "role.unit", numeric=False),
        Role("period", "role.period"),
        Role("outcome", "role.outcome"),
    ),
    "dml": (
        Role("outcome", "role.outcome"),
        Role("treatment", "role.treatment"),
        Role("covariates", "role.covariates", multi=True),
    ),
}


def _as_list(value) -> list[str]:
    if value is None or value == "":
        return []
    return list(value) if isinstance(value, (list, tuple)) else [value]


def validate_mapping(df: pd.DataFrame, method: str, mapping: dict) -> list[Msg]:
    """Return human-readable problems with `mapping` (role key -> column
    name, or list of names for multi roles). Empty list = valid."""
    problems: list[Msg] = []
    used: dict[str, Msg] = {}
    for role in METHOD_ROLES[method]:
        columns = _as_list(mapping.get(role.key))
        if role.required and not columns:
            problems.append(Msg("mapping.no_column", role=role.label))
            continue
        for col in columns:
            if col not in df.columns:
                problems.append(Msg("mapping.not_in_file", role=role.label, column=col))
                continue
            if col in used:
                problems.append(Msg("mapping.already_used", role=role.label, column=col, other=used[col]))
            used.setdefault(col, role.label)
            if role.numeric and not pd.api.types.is_numeric_dtype(df[col]):
                problems.append(Msg("mapping.not_numeric", role=role.label, column=col))
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
