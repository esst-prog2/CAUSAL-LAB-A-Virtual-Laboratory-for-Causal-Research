"""
Which dataset a session works on, and its treatment timing.

Shared by the app pages and the report, so both describe the same data.
`state` is the Streamlit session state or any mapping with the same keys.
"""
from __future__ import annotations

import pandas as pd


def active_data(state) -> pd.DataFrame | None:
    """The uploaded real-world dataset if there is one, else the Virtual World."""
    if state.get("uploaded_df") is not None:
        return state.get("uploaded_df")
    return state.get("virtual_df")


def treatment_setup(state, df: pd.DataFrame) -> tuple[int, bool]:
    """(treatment period, staggered?) for the active dataset: taken from the
    configuration that generated the Virtual World, or inferred from the first
    period in which each unit has D == 1 for uploaded data."""
    if state.get("uploaded_df") is None and state.get("virtual_cfg") is not None:
        cfg = state.get("virtual_cfg")
        return cfg.treatment_period, cfg.staggered_adoption
    first_treated = df.loc[df["D"] == 1].groupby("unit")["period"].min()
    return int(first_treated.min()), first_treated.nunique() > 1


def ids_encode_neighbourhood(state) -> bool:
    """Unit ids encode a neighbourhood only in a generated Virtual World."""
    return state.get("uploaded_df") is None and state.get("virtual_cfg") is not None


def virtual_truth(state) -> dict | None:
    """The ground truth of the active data, which only a Virtual World has."""
    return state.get("virtual_truth") if state.get("uploaded_df") is None else None
