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

Inference is analytic. Each aggregate is a linear combination of cohort and
comparison-group means, so it is a sum of one contribution per unit; units are
independent, and within an adoption cohort (or the never-treated group) their
contributions are identically distributed. The variance is the sum over these
strata of n_s times the unbiased (n_s - 1) variance of the contributions, and
the interval uses a Student t with Welch-Satterthwaite degrees of freedom
(Welch 1947), the small-sample analogue of the influence-function variance of
the R package `did`. A cohort of one unit borrows the variance of the same
combination of outcome changes among the never-treated (else not-yet-treated)
units. In the validation study (spike/estimator_validation.py, cohorts of
about 3 units) this interval covered 95.0% and the test's size was 5.0%,
where the unit bootstrap gave 91.4% and 8.6%. The bootstrap remains only as a
fallback when no variance can be borrowed.

Units not observed in every period are dropped and counted in `n_dropped`,
as the reference R package `did` does by default
(allow_unbalanced_panel = FALSE; user decision, hw6 review 3).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from estimators.common import Z_95
from utils.i18n import LocalizedError

N_BOOTSTRAP = 199                   # fallback only
# Cohorts this small rest on few units: the result reports the smallest cohort and the
# pages say so, although the analytic interval keeps its coverage (95.0% with ~3-unit cohorts).
SMALL_COHORT = 5
COMPARISONS = ("never_treated", "not_yet_treated")


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
    n_dropped: int = 0              # units dropped because not observed in every period
    min_cohort_size: int = 0        # units in the smallest adoption cohort
    df: float = float("inf")        # Welch-Satterthwaite degrees of freedom of the overall ATT
    p_value: float = float("nan")
    inference: str = "analytic"     # "analytic" | "bootstrap" (fallback)


def _wide(df: pd.DataFrame, outcome_col, unit_col, time_col, treatment_col):
    """Unit x period outcome matrix of the units observed in every period,
    their first treated period, and the number of units dropped."""
    y = df.pivot_table(index=unit_col, columns=time_col, values=outcome_col)
    complete = y.notna().all(axis=1)
    if not complete.any():
        raise LocalizedError("err.cs_unbalanced")
    y = y[complete]
    d = df.pivot_table(index=unit_col, columns=time_col, values=treatment_col).reindex_like(y)
    periods = np.array(y.columns)
    treated_any = (d.to_numpy() == 1)
    first = np.where(treated_any.any(axis=1), periods[np.argmax(treated_any, axis=1)], np.inf)
    return y.to_numpy(float), periods, first, int((~complete).sum())


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


def _cells(gt: pd.DataFrame, rel: int | None = None) -> list[tuple[float, float, float]]:
    """(cohort, period, weight) of the cells of the overall ATT (rel None) or of ATT(rel)."""
    if rel is None:
        part = gt[gt["period"] >= gt["cohort"]]
    else:
        part = gt[gt["period"] - gt["cohort"] == rel]
    total = part["n_cohort"].sum()
    return [(g, t, n / total) for g, t, n in zip(part["cohort"], part["period"], part["n_cohort"], strict=True)]


def _controls(first: np.ndarray, comparison: str, g: float, t: float) -> np.ndarray:
    controls = ~np.isfinite(first) if comparison == "never_treated" else first > max(t, g - 1)
    return controls & (first != g)


def _contributions(y, index, first, comparison, cells) -> np.ndarray:
    """u with sum(u) = the aggregate: each unit's share of the weighted mean differences."""
    u = np.zeros(len(first))
    for g, t, w in cells:
        members, controls = first == g, _controls(first, comparison, g, t)
        change = y[:, index[t]] - y[:, index[g - 1]]
        u[members] += w * change[members] / members.sum()
        u[controls] -= w * change[controls] / controls.sum()
    return u


def _analytic(y, index, first, comparison, cells) -> tuple[float, float]:
    """Welch-Satterthwaite variance and degrees of freedom of sum(u), or (nan, nan)."""
    u = _contributions(y, index, first, comparison, cells)
    strata = np.where(np.isfinite(first), first, -1.0)
    parts, dfs = [], []
    for s in np.unique(strata):
        us = u[strata == s]
        if not np.any(us):
            continue                                    # stratum not used by these cells
        if len(us) >= 2:
            parts.append(len(us) * us.var(ddof=1))
            dfs.append(len(us) - 1)
            continue
        # One unit: the same combination of outcome changes among comparison units.
        donors = ~np.isfinite(first)
        if donors.sum() < 2:
            donors = first > max(t for g, t, _ in cells if g == s)
        if donors.sum() < 2:
            return float("nan"), float("nan")
        q = sum(w * (y[donors, index[t]] - y[donors, index[g - 1]]) for g, t, w in cells if g == s)
        parts.append(float(np.var(q, ddof=1)))
        dfs.append(int(donors.sum()) - 1)
    v = float(sum(parts))
    den = sum(p ** 2 / d for p, d in zip(parts, dfs, strict=True))
    return v, (v ** 2 / den if den > 0 else float("inf"))


def _bootstrap(y, periods, first, comparison, event_index, n_bootstrap, seed):
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
    event_se = pd.concat(boot_event, axis=1).std(axis=1, ddof=1).reindex(event_index) if boot_event \
        else pd.Series(np.nan, index=event_index)
    return se, event_se


def estimate_staggered_did(df: pd.DataFrame, outcome_col: str = "Y", treatment_col: str = "D",
                           unit_col: str = "unit", time_col: str = "period",
                           comparison: str = "never_treated", seed: int = 0,
                           n_bootstrap: int = N_BOOTSTRAP) -> StaggeredDiDResult:
    if comparison not in COMPARISONS:
        raise LocalizedError("err.cs_comparison", value=comparison, allowed=", ".join(COMPARISONS))
    if n_bootstrap < 2:
        raise LocalizedError("err.cs_bootstrap", value=n_bootstrap)
    data = df[[unit_col, time_col, outcome_col, treatment_col]].dropna()
    y, periods, first, n_dropped = _wide(data, outcome_col, unit_col, time_col, treatment_col)
    if not np.isfinite(first).any():
        raise LocalizedError("err.no_variation", column=treatment_col)
    if comparison == "never_treated" and np.isfinite(first).all():
        comparison = "not_yet_treated"      # no never-treated units: use not-yet-treated ones
    gt = _group_time(y, periods, first, comparison)
    if gt.empty or not (gt["period"] >= gt["cohort"]).any():
        raise LocalizedError("err.cs_no_cells")
    att, event = _aggregate(gt)

    index = {p: i for i, p in enumerate(periods)}
    v, dof = _analytic(y, index, first, comparison, _cells(gt))
    event_v = {int(e): _analytic(y, index, first, comparison, _cells(gt, int(e))) for e in event.index}
    inference = "analytic"
    if not np.isfinite(v) or any(not np.isfinite(ev) for ev, _ in event_v.values()):
        inference = "bootstrap"
        se, event_se = _bootstrap(y, periods, first, comparison, event.index, n_bootstrap, seed)
        dof, crit, p_value = float("inf"), Z_95, float(2 * stats.norm.sf(abs(att / se)))
        es = pd.DataFrame({"rel_period": event.index.astype(int), "estimate": event.values, "se": event_se.values})
        es["ci_low"] = es["estimate"] - Z_95 * es["se"]
        es["ci_high"] = es["estimate"] + Z_95 * es["se"]
    else:
        se = float(np.sqrt(v))
        crit = float(stats.t.ppf(0.975, dof))
        p_value = float(2 * stats.t.sf(abs(att / se), dof)) if se > 0 else float("nan")
        rows = []
        for e, est in event.items():
            ev, edf = event_v[int(e)]
            ese = float(np.sqrt(ev))
            ecrit = float(stats.t.ppf(0.975, edf))
            rows.append((int(e), float(est), ese, est - ecrit * ese, est + ecrit * ese))
        es = pd.DataFrame(rows, columns=["rel_period", "estimate", "se", "ci_low", "ci_high"])
    return StaggeredDiDResult(
        att=att, se=se, ci_low=att - crit * se, ci_high=att + crit * se,
        group_time=gt, event_study=es.reset_index(drop=True),
        n_cohorts=int(gt["cohort"].nunique()), n_units=y.shape[0], comparison=comparison,
        n_dropped=n_dropped, min_cohort_size=int(gt.groupby("cohort")["n_cohort"].first().min()),
        df=float(dof), p_value=p_value, inference=inference,
    )
