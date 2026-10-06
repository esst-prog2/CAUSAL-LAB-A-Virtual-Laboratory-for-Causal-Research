"""
Heterogeneity-robust Difference-in-Differences for staggered adoption
(Callaway & Sant'Anna 2021), without covariates.

Two-way fixed effects can be badly biased when units adopt treatment at
different dates and effects change over time, because already-treated
units end up serving as controls (Goodman-Bacon 2021). Callaway &
Sant'Anna avoid this by estimating one effect per adoption cohort g and
period t, each comparing cohort g only with a clean comparison group:

    ATT(g, t) = E[Y_t - Y_{g-1} | G = g] - E[Y_t - Y_{g-1} | comparison]

where the comparison group is the never-treated units (default) or,
for each t, the units not yet treated by max(t, g-1)+1 ("not yet
treated"). The ATT(g, t) are then aggregated:

    overall ATT  — average over post-treatment cells (t >= g), weighted by
                   cohort size, i.e. the mean effect over treated
                   unit-periods;
    event study  — ATT(e) = cohort-size-weighted average of ATT(g, g+e).

Inference is by a unit-level (cluster) bootstrap with a fixed seed.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from estimators.common import Z_95
from utils.i18n import LocalizedError

N_BOOTSTRAP = 199


@dataclass
class StaggeredDiDResult:
    att: float
    se: float
    ci_low: float
    ci_high: float
    group_time: pd.DataFrame        # cohort, period, att, n_cohort
    event_study: pd.DataFrame       # rel_period, estimate, se, ci_low, ci_high
    n_cohorts: int
    n_units: int
    comparison: str                 # "never_treated" | "not_yet_treated"


def _wide(df: pd.DataFrame, outcome_col, unit_col, time_col, treatment_col):
    y = df.pivot_table(index=unit_col, columns=time_col, values=outcome_col)
    if y.isna().any().any():
        raise LocalizedError("err.cs_unbalanced")
    d = df.pivot_table(index=unit_col, columns=time_col, values=treatment_col).reindex_like(y)
    periods = np.array(y.columns)
    treated_any = (d.to_numpy() == 1)
    first = np.where(treated_any.any(axis=1), periods[np.argmax(treated_any, axis=1)], np.inf)
    return y.to_numpy(float), periods, first


def _group_time(y: np.ndarray, periods: np.ndarray, first: np.ndarray, comparison: str):
    """ATT(g, t) for every cohort g and every period t != g - 1."""
    index = {p: i for i, p in enumerate(periods)}
    cohorts = sorted(g for g in set(first[np.isfinite(first)]) if g - 1 in index)
    rows = []
    for g in cohorts:
        members = first == g
        base = index[g - 1]
        for t in periods:
            if t == g - 1:
                continue
            if comparison == "never_treated":
                controls = ~np.isfinite(first)
            else:   # not yet treated at either t or the base period
                controls = first > max(t, g - 1)
            controls &= ~members
            if controls.sum() == 0:
                continue
            ti = index[t]
            change_g = y[members, ti] - y[members, base]
            change_c = y[controls, ti] - y[controls, base]
            rows.append((g, t, change_g.mean() - change_c.mean(), int(members.sum())))
    return pd.DataFrame(rows, columns=["cohort", "period", "att", "n_cohort"])


def _aggregate(gt: pd.DataFrame) -> tuple[float, pd.Series]:
    post = gt[gt["period"] >= gt["cohort"]]
    overall = float(np.average(post["att"], weights=post["n_cohort"])) if len(post) else float("nan")
    gt = gt.assign(rel=gt["period"] - gt["cohort"])
    event = gt.groupby("rel").apply(lambda s: np.average(s["att"], weights=s["n_cohort"]), include_groups=False)
    return overall, event


def estimate_staggered_did(df: pd.DataFrame, outcome_col: str = "Y", treatment_col: str = "D",
                           unit_col: str = "unit", time_col: str = "period",
                           comparison: str = "never_treated", seed: int = 0,
                           n_bootstrap: int = N_BOOTSTRAP) -> StaggeredDiDResult:
    data = df[[unit_col, time_col, outcome_col, treatment_col]].dropna()
    y, periods, first = _wide(data, outcome_col, unit_col, time_col, treatment_col)
    if not np.isfinite(first).any():
        raise LocalizedError("err.no_variation", column=treatment_col)
    if comparison == "never_treated" and np.isfinite(first).all():
        comparison = "not_yet_treated"      # no never-treated units: use not-yet-treated ones
    gt = _group_time(y, periods, first, comparison)
    if gt.empty or not (gt["period"] >= gt["cohort"]).any():
        raise LocalizedError("err.cs_no_cells")
    att, event = _aggregate(gt)

    rng = np.random.default_rng(seed)
    n_units = y.shape[0]
    boot_att, boot_event = [], []
    for _ in range(n_bootstrap):
        idx = rng.integers(0, n_units, n_units)
        gt_b = _group_time(y[idx], periods, first[idx], comparison)
        if gt_b.empty or not (gt_b["period"] >= gt_b["cohort"]).any():
            continue
        a_b, e_b = _aggregate(gt_b)
        boot_att.append(a_b)
        boot_event.append(e_b)
    se = float(np.std(boot_att, ddof=1)) if len(boot_att) > 1 else float("nan")
    event_se = pd.concat(boot_event, axis=1).std(axis=1, ddof=1).reindex(event.index) if boot_event \
        else pd.Series(np.nan, index=event.index)
    es = pd.DataFrame({"rel_period": event.index.astype(int), "estimate": event.values,
                       "se": event_se.values})
    es["ci_low"] = es["estimate"] - Z_95 * es["se"]
    es["ci_high"] = es["estimate"] + Z_95 * es["se"]
    return StaggeredDiDResult(
        att=att, se=se, ci_low=att - Z_95 * se, ci_high=att + Z_95 * se,
        group_time=gt, event_study=es.reset_index(drop=True),
        n_cohorts=int(gt["cohort"].nunique()), n_units=n_units, comparison=comparison,
    )
