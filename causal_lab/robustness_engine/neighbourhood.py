"""
The Virtual World's neighbourhood: units whose ids differ by exactly 1
(simulation_engine.dgp lets spillovers reach those units).

This is the single definition used by the Spillovers check and by the
robustness battery (hw6 review 4). It is meaningful only where unit ids
encode a neighbourhood, which callers state explicitly; on uploaded or
real data both features are N/A or left out (user decisions, hw6 reviews
3 and 4).
"""
from __future__ import annotations

import pandas as pd


def adjacent_control_ids(df: pd.DataFrame, unit_col: str, treated_unit_col: str) -> set:
    """Control units whose id is next to a treated unit's id; empty when ids are not numeric."""
    if not pd.api.types.is_numeric_dtype(df[unit_col]):
        return set()
    treated_ids = set(df.loc[df[treated_unit_col] == 1, unit_col].unique())
    return {c for c in df.loc[df[treated_unit_col] == 0, unit_col].unique()
            if (c - 1) in treated_ids or (c + 1) in treated_ids}
