"""
"Break My Design" stress-test module (CAUSAL LAB spec, Section 19).

Runs a battery of diagnostic checks against a fitted DiD design on
actual (real or simulated) panel data, and produces a PASS / WARNING
verdict for each threat, plus an overall "Identification Strength"
score out of 100. This score is a diagnostic heuristic, not a
statistical proof — this is stated explicitly in every rendering.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats


@dataclass
class CheckResult:
    name: str
    verdict: str          # "PASS" or "WARNING"
    detail: str
    statistic: float | None = None
    p_value: float | None = None
    assessment: str | None = None   # plain-language verdict, e.g. "plausible"


def parallel_trends_assessment(p_value: float) -> str:
    """Plain-language parallel-trends verdict from the pre-trend p-value."""
    if p_value >= 0.10:
        return "plausible"
    if p_value >= 0.01:
        return "questionable"
    return "violated"


@dataclass
class StressTestReport:
    checks: list[CheckResult] = field(default_factory=list)
    identification_strength: float = 0.0

    def summary_table(self):
        return [(c.name, c.verdict, c.detail) for c in self.checks]


def _check_parallel_trends(df: pd.DataFrame, outcome_col, unit_col, time_col,
                            treated_unit_col, treatment_period) -> CheckResult:
    pre = df[df[time_col] < treatment_period].copy()
    if pre[time_col].nunique() < 2 or pre[treated_unit_col].nunique() < 2:
        return CheckResult("Parallel Trends", "WARNING",
                            "Not enough pre-treatment periods or groups to test pre-trends.")
    # Treated-group x pre-period interactions, omitting the last
    # pre-treatment period as the reference (including every period
    # would be collinear with the unit fixed effects).
    pre_periods = sorted(pre[time_col].unique())
    interaction_terms = []
    for i, p in enumerate(pre_periods[:-1]):
        name = f"pt_lead_{i}"
        pre[name] = ((pre[treated_unit_col] == 1) & (pre[time_col] == p)).astype(int)
        interaction_terms.append(name)
    pre[unit_col] = pre[unit_col].astype("category")
    pre[time_col] = pre[time_col].astype("category")
    formula = f"{outcome_col} ~ {' + '.join(interaction_terms)} + C({unit_col}) + C({time_col})"
    try:
        fitted = smf.ols(formula, data=pre).fit(
            cov_type="cluster", cov_kwds={"groups": pre[unit_col]})
        wald = fitted.f_test([f"{t} = 0" for t in interaction_terms])
        p_value = float(np.asarray(wald.pvalue))
        assessment = parallel_trends_assessment(p_value)
        if p_value < 0.10:
            return CheckResult(
                "Parallel Trends", "WARNING",
                f"Parallel trends: {assessment}. The joint test of pre-treatment "
                f"group-specific trends rejects equal trends (p = {p_value:.3f}); "
                f"differential pre-trends threaten the parallel-trends assumption.",
                p_value=p_value, assessment=assessment)
        return CheckResult(
            "Parallel Trends", "PASS",
            f"Parallel trends: {assessment}. No evidence of differential "
            f"pre-treatment trends (p = {p_value:.3f}).", p_value=p_value, assessment=assessment)
    except Exception as exc:  # pragma: no cover - defensive
        return CheckResult("Parallel Trends", "WARNING", f"Test could not be computed ({exc}).")


def _check_serial_correlation(df: pd.DataFrame, outcome_col, unit_col, time_col,
                               treatment_col) -> CheckResult:
    data = df.sort_values([unit_col, time_col]).reset_index(drop=True)
    units, periods = data[unit_col].copy(), data[time_col].copy()
    data[unit_col] = data[unit_col].astype("category")
    data[time_col] = data[time_col].astype("category")
    formula = f"{outcome_col} ~ {treatment_col} + C({unit_col}) + C({time_col})"
    resid = smf.ols(formula, data=data).fit().resid.values

    # Durbin-Watson computed *within* units only: consecutive rows
    # belonging to different units must not be differenced.
    same_unit = units.values[1:] == units.values[:-1]
    diffs = np.diff(resid)[same_unit]
    dw = float(np.sum(diffs ** 2) / np.sum(resid ** 2))

    # Unit fixed effects mechanically induce a negative residual
    # autocorrelation of about -1/(T-1) (Nickell bias); correct for it
    # before judging the first-order autocorrelation.
    n_periods = periods.nunique()
    rho = (1 - dw / 2) + 1 / max(1, n_periods - 1)
    if rho > 0.2:
        return CheckResult(
            "Serial Correlation", "WARNING",
            f"Within-unit Durbin-Watson statistic = {dw:.2f}; implied "
            f"residual autocorrelation (corrected for fixed-effects bias) "
            f"= {rho:.2f}. Serially correlated errors make non-clustered "
            f"standard errors too small (Bertrand, Duflo & Mullainathan "
            f"2004): keep clustering by unit, and consider a wild-cluster "
            f"bootstrap when clusters are few.", statistic=dw)
    return CheckResult("Serial Correlation", "PASS",
                        f"Within-unit Durbin-Watson statistic = {dw:.2f}; implied "
                        f"residual autocorrelation (corrected for fixed-effects "
                        f"bias) = {rho:.2f}, no strong evidence of serial correlation.",
                        statistic=dw)


def _check_anticipation(df: pd.DataFrame, outcome_col, unit_col, time_col,
                         treated_unit_col, treatment_period) -> CheckResult:
    lead_period, before_lead = treatment_period - 1, treatment_period - 2
    pre = df[df[time_col].isin([lead_period, before_lead])]
    if pre.empty or pre[time_col].nunique() < 2:
        return CheckResult("Anticipation", "WARNING", "Not enough data to test for anticipation effects.")
    # First difference between the last two pre-treatment periods, per
    # unit: this removes unit fixed effects, so the test compares how
    # treated and control units *changed* just before treatment.
    wide = pre.pivot_table(index=unit_col, columns=time_col, values=outcome_col)
    groups = pre.groupby(unit_col)[treated_unit_col].max()
    fd = pd.DataFrame({"change": wide[lead_period] - wide[before_lead], "treated": groups}).dropna()
    if fd["treated"].nunique() < 2:
        return CheckResult("Anticipation", "WARNING", "Not enough data to test for anticipation effects.")
    try:
        fitted = smf.ols("change ~ treated", data=fd).fit(cov_type="HC1")
        p_value = float(fitted.pvalues["treated"])
        if p_value < 0.10:
            return CheckResult("Anticipation", "WARNING",
                                f"Outcome jumps for treated units in the period right before "
                                f"treatment (p = {p_value:.3f}), suggesting possible anticipation.",
                                p_value=p_value)
        return CheckResult("Anticipation", "PASS",
                            f"No evidence of anticipatory behavior just before treatment "
                            f"(p = {p_value:.3f}).", p_value=p_value)
    except Exception as exc:  # pragma: no cover
        return CheckResult("Anticipation", "WARNING", f"Test could not be computed ({exc}).")


def _check_spillovers(df: pd.DataFrame, outcome_col, unit_col, time_col,
                      treated_unit_col, treatment_period) -> CheckResult:
    """Compare control units adjacent to a treated unit (unit id
    distance 1, the neighbourhood structure of the Virtual World) with
    the remaining controls, before vs. after treatment."""
    if not pd.api.types.is_numeric_dtype(df[unit_col]):
        return CheckResult("Spillovers", "WARNING",
                            "Unit identifiers are not numeric, so no neighbourhood "
                            "structure is available to test for spillovers.")
    treated_ids = set(df.loc[df[treated_unit_col] == 1, unit_col].unique())
    controls = df[df[treated_unit_col] == 0].copy()
    controls["adjacent"] = controls[unit_col].apply(
        lambda c: int((c - 1) in treated_ids or (c + 1) in treated_ids))
    n_adjacent = controls.loc[controls["adjacent"] == 1, unit_col].nunique()
    n_far = controls.loc[controls["adjacent"] == 0, unit_col].nunique()
    if n_adjacent < 2 or n_far < 2:
        return CheckResult("Spillovers", "PASS",
                            "Too few adjacent / non-adjacent control units to test for "
                            "spillovers; default pass.")

    controls["adj_post"] = controls["adjacent"] * (controls[time_col] >= treatment_period).astype(int)
    controls[unit_col] = controls[unit_col].astype("category")
    controls[time_col] = controls[time_col].astype("category")
    try:
        fitted = smf.ols(f"{outcome_col} ~ adj_post + C({unit_col}) + C({time_col})",
                         data=controls).fit(cov_type="cluster",
                                            cov_kwds={"groups": controls[unit_col]})
        p_value = float(fitted.pvalues["adj_post"])
        effect = float(fitted.params["adj_post"])
    except Exception as exc:  # pragma: no cover - defensive
        return CheckResult("Spillovers", "WARNING", f"Test could not be computed ({exc}).")
    if p_value < 0.10:
        return CheckResult(
            "Spillovers", "WARNING",
            f"The {n_adjacent} control unit(s) adjacent to a treated unit "
            f"shift by {effect:+.3f} after treatment relative to other "
            f"controls (p = {p_value:.3f}). Spillovers contaminate the "
            f"comparison group.", statistic=effect, p_value=p_value)
    return CheckResult(
        "Spillovers", "PASS",
        f"Control units adjacent to a treated unit do not change "
        f"differently after treatment (difference = {effect:+.3f}, "
        f"p = {p_value:.3f}).", statistic=effect, p_value=p_value)


def _check_heterogeneous_effects(df: pd.DataFrame, outcome_col, unit_col, time_col,
                                  treated_unit_col, treatment_period) -> CheckResult:
    """Compare the dispersion of unit-level pre/post changes among
    treated units with that among control units. Under a homogeneous
    effect both only reflect noise, so a significantly larger variance
    for treated units signals effect heterogeneity."""
    post = df[time_col] >= treatment_period
    pre_means = df[~post].groupby(unit_col)[outcome_col].mean()
    post_means = df[post].groupby(unit_col)[outcome_col].mean()
    changes = (post_means - pre_means).dropna()
    group = df.groupby(unit_col)[treated_unit_col].max().reindex(changes.index)
    treated_changes = changes[group == 1]
    control_changes = changes[group == 0]
    if len(treated_changes) < 3 or len(control_changes) < 3:
        return CheckResult("Heterogeneous Effects", "PASS",
                            "Too few treated or control units to assess effect "
                            "heterogeneity; default pass.")
    var_ratio = float(treated_changes.var() / control_changes.var())
    p_value = float(stats.f.sf(var_ratio, len(treated_changes) - 1, len(control_changes) - 1))
    if p_value < 0.10:
        return CheckResult(
            "Heterogeneous Effects", "WARNING",
            f"Pre/post changes vary more across treated units than across "
            f"controls (variance ratio = {var_ratio:.2f}, p = {p_value:.3f}). "
            f"A single average treatment effect may mask important "
            f"heterogeneity.", statistic=var_ratio, p_value=p_value)
    return CheckResult(
        "Heterogeneous Effects", "PASS",
        f"Pre/post changes are no more dispersed across treated units than "
        f"across controls (variance ratio = {var_ratio:.2f}, p = {p_value:.3f}).",
        statistic=var_ratio, p_value=p_value)


def run_stress_test(df: pd.DataFrame, treatment_period: int, outcome_col: str = "Y",
                     unit_col: str = "unit", time_col: str = "period",
                     treatment_col: str = "D", treated_unit_col: str = "treated_unit") -> StressTestReport:
    checks = [
        _check_parallel_trends(df, outcome_col, unit_col, time_col, treated_unit_col, treatment_period),
        _check_anticipation(df, outcome_col, unit_col, time_col, treated_unit_col, treatment_period),
        _check_spillovers(df, outcome_col, unit_col, time_col, treated_unit_col, treatment_period),
        _check_serial_correlation(df, outcome_col, unit_col, time_col, treatment_col),
        _check_heterogeneous_effects(df, outcome_col, unit_col, time_col, treated_unit_col, treatment_period),
    ]
    n_pass = sum(1 for c in checks if c.verdict == "PASS")
    identification_strength = 100 * n_pass / len(checks)
    return StressTestReport(checks=checks, identification_strength=identification_strength)
