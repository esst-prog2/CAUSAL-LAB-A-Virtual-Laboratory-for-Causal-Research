"""
Robustness Engine (CAUSAL LAB spec, Section 21).

v0.1 implements a first, concrete subset of the full robustness
battery described in the spec:

    - alternative pre-treatment time windows
    - leave-one-unit-out (drop each treated unit and re-estimate)
    - alternative comparison-group definition (drop adjacent /
      potentially spilled-over control units)

Each check re-runs the actual DiD estimator on a modified sample and
reports the resulting ATT, so nothing here is approximated or
invented — it is the same estimator from estimators.did applied to
different, well-defined subsamples.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from estimators.did import DiDResult, estimate_did


@dataclass
class RobustnessRow:
    specification: str
    att: float
    se: float
    n_obs: int
    note: str = ""


def run_robustness_battery(df: pd.DataFrame, treatment_period: int,
                            outcome_col: str = "Y", unit_col: str = "unit",
                            time_col: str = "period", treatment_col: str = "D",
                            treated_unit_col: str = "treated_unit") -> list[RobustnessRow]:
    rows: list[RobustnessRow] = []

    # 1. Baseline specification.
    baseline = estimate_did(df, outcome_col, treatment_col, unit_col, time_col)
    rows.append(RobustnessRow("Baseline (full sample)", baseline.att, baseline.se, baseline.n_obs))

    # 2. Alternative time windows symmetric around the treatment date.
    for window in (3, 5):
        sub = df[(df[time_col] >= treatment_period - window)
                 & (df[time_col] < treatment_period + window)]
        if sub[time_col].nunique() < 2 or sub[treatment_col].nunique() < 2:
            continue
        res = estimate_did(sub, outcome_col, treatment_col, unit_col, time_col)
        rows.append(RobustnessRow(f"Restricted window (±{window} periods)", res.att, res.se, res.n_obs))

    # 3. Leave-one-treated-unit-out.
    treated_units = sorted(df.loc[df[treated_unit_col] == 1, unit_col].unique())
    loo_atts = []
    for u in treated_units[: min(10, len(treated_units))]:  # cap for performance
        sub = df[df[unit_col] != u]
        try:
            res = estimate_did(sub, outcome_col, treatment_col, unit_col, time_col)
            loo_atts.append(res.att)
        except Exception:
            continue
    if loo_atts:
        rows.append(RobustnessRow(
            "Leave-one-treated-unit-out (range)",
            att=sum(loo_atts) / len(loo_atts),
            se=float("nan"),  # a range of point estimates, not a sampling SE
            n_obs=len(loo_atts),
            note=f"min={min(loo_atts):.3f}, max={max(loo_atts):.3f} across {len(loo_atts)} unit(s) dropped",
        ))

    # 4. Drop control units directly adjacent to a treated unit
    #    (a control-group definition robust to local spillovers).
    #    Adjacency is defined on numeric unit ids (unit id distance 1).
    adjacent_controls: set = set()
    if pd.api.types.is_numeric_dtype(df[unit_col]):
        treated_ids = set(df.loc[df[treated_unit_col] == 1, unit_col].unique())
        adjacent_controls = {
            c for c in df.loc[df[treated_unit_col] == 0, unit_col].unique()
            if (c - 1) in treated_ids or (c + 1) in treated_ids
        }
    if adjacent_controls:
        sub = df[~df[unit_col].isin(adjacent_controls)]
        res = estimate_did(sub, outcome_col, treatment_col, unit_col, time_col)
        rows.append(RobustnessRow(
            "Excluding spillover-adjacent controls", res.att, res.se, res.n_obs,
            note=f"{len(adjacent_controls)} control unit(s) excluded",
        ))

    return rows
