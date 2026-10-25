"""
"Break My Design" stress-test module (CAUSAL LAB spec, Section 19).

Runs a battery of diagnostic checks against a fitted DiD design on
actual (real or simulated) panel data, and produces a PASS / WARNING /
N/A verdict for each threat, plus an overall "Identification Strength"
score out of 100. This score is a diagnostic heuristic, not a
statistical proof — this is stated explicitly in every rendering.

A check that cannot be computed on the data (too few periods or units,
no neighbourhood structure) returns N/A. N/A is shown as such and is
excluded from the score: a lack of evidence is not evidence of failure
(user decision, hw6 review 3).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

from estimators.did import nested_fe_factor
from robustness_engine.neighbourhood import adjacent_control_ids
from utils.i18n import Msg

PASS, WARNING, NOT_APPLICABLE = "PASS", "WARNING", "N/A"

# Failures of the regression itself on degenerate data (singular design,
# no residual degrees of freedom). The check is then not computable: N/A,
# with the error shown. Any other exception is a bug and is not hidden.
NUMERICAL_ERRORS = (ValueError, np.linalg.LinAlgError, ZeroDivisionError)

# Locale key suffix of each check's display name (check.<slug>).
CHECK_SLUGS = {
    "Parallel Trends": "parallel_trends", "Anticipation": "anticipation", "Spillovers": "spillovers",
    "Serial Correlation": "serial_correlation", "Heterogeneous Effects": "heterogeneous_effects",
}


@dataclass
class CheckResult:
    name: str
    verdict: str          # PASS, WARNING or NOT_APPLICABLE ("N/A")
    message: Msg          # translatable explanation; str(message) is English
    statistic: float | None = None
    p_value: float | None = None
    assessment: str | None = None   # plain-language verdict, e.g. "plausible"

    @property
    def slug(self) -> str:
        return CHECK_SLUGS[self.name]


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
    identification_strength: float | None = None   # None when no check could be computed
    n_computable: int = 0


def _check_parallel_trends(df: pd.DataFrame, outcome_col, unit_col, time_col,
                            treated_unit_col, treatment_period) -> CheckResult:
    pre = df[df[time_col] < treatment_period].copy()
    if pre[time_col].nunique() < 2 or pre[treated_unit_col].nunique() < 2:
        return CheckResult("Parallel Trends", NOT_APPLICABLE, Msg("stress.pt.not_enough"))
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
        # Same small-sample correction as the DiD: unit dummies not counted in K.
        factor = nested_fe_factor(pre, fitted, unit_col, unit_col)
        wald = fitted.f_test([f"{t} = 0" for t in interaction_terms],
                             cov_p=fitted.cov_params() * factor ** 2)
        p_value = float(np.asarray(wald.pvalue))
        assessment = parallel_trends_assessment(p_value)
        if p_value < 0.10:
            return CheckResult("Parallel Trends", "WARNING", Msg(f"stress.pt.{assessment}", p=p_value),
                               p_value=p_value, assessment=assessment)
        return CheckResult("Parallel Trends", "PASS", Msg("stress.pt.plausible", p=p_value),
                           p_value=p_value, assessment=assessment)
    except NUMERICAL_ERRORS as exc:
        return CheckResult("Parallel Trends", NOT_APPLICABLE, Msg("stress.error", error=str(exc)))


def _check_serial_correlation(df: pd.DataFrame, outcome_col, unit_col, time_col,
                               treatment_col) -> CheckResult:
    # A first-order autocorrelation of fixed-effects residuals needs at
    # least three periods: with two, the within residuals of each unit are
    # exactly opposite, and the -1/(T-1) correction turns that into rho = 1.
    if df[time_col].nunique() < 3:
        return CheckResult("Serial Correlation", NOT_APPLICABLE, Msg("stress.serial.not_enough"))
    data = df.sort_values([unit_col, time_col]).reset_index(drop=True)
    units, periods = data[unit_col].copy(), data[time_col].copy()
    data[unit_col] = data[unit_col].astype("category")
    data[time_col] = data[time_col].astype("category")
    formula = f"{outcome_col} ~ {treatment_col} + C({unit_col}) + C({time_col})"
    try:
        resid = smf.ols(formula, data=data).fit().resid.values
    except NUMERICAL_ERRORS as exc:
        return CheckResult("Serial Correlation", NOT_APPLICABLE, Msg("stress.error", error=str(exc)))

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
        return CheckResult("Serial Correlation", "WARNING", Msg("stress.serial.warning", dw=dw, rho=rho),
                           statistic=dw)
    return CheckResult("Serial Correlation", "PASS", Msg("stress.serial.pass", dw=dw, rho=rho), statistic=dw)


def _check_anticipation(df: pd.DataFrame, outcome_col, unit_col, time_col,
                         treated_unit_col, treatment_period) -> CheckResult:
    lead_period, before_lead = treatment_period - 1, treatment_period - 2
    pre = df[df[time_col].isin([lead_period, before_lead])]
    if pre.empty or pre[time_col].nunique() < 2:
        return CheckResult("Anticipation", NOT_APPLICABLE, Msg("stress.anticipation.not_enough"))
    # First difference between the last two pre-treatment periods, per
    # unit: this removes unit fixed effects, so the test compares how
    # treated and control units *changed* just before treatment.
    wide = pre.pivot_table(index=unit_col, columns=time_col, values=outcome_col)
    groups = pre.groupby(unit_col)[treated_unit_col].max()
    fd = pd.DataFrame({"change": wide[lead_period] - wide[before_lead], "treated": groups}).dropna()
    if fd["treated"].nunique() < 2:
        return CheckResult("Anticipation", NOT_APPLICABLE, Msg("stress.anticipation.not_enough"))
    try:
        fitted = smf.ols("change ~ treated", data=fd).fit(cov_type="HC1")
        p_value = float(fitted.pvalues["treated"])
        if p_value < 0.10:
            return CheckResult("Anticipation", "WARNING", Msg("stress.anticipation.warning", p=p_value),
                               p_value=p_value)
        return CheckResult("Anticipation", "PASS", Msg("stress.anticipation.pass", p=p_value), p_value=p_value)
    except NUMERICAL_ERRORS as exc:
        return CheckResult("Anticipation", NOT_APPLICABLE, Msg("stress.error", error=str(exc)))


def _check_spillovers(df: pd.DataFrame, outcome_col, unit_col, time_col,
                      treated_unit_col, treatment_period, ids_encode_neighbourhood: bool) -> CheckResult:
    """Compare control units adjacent to a treated unit (unit id
    distance 1, the neighbourhood structure of the Virtual World) with
    the remaining controls, before vs. after treatment. Only meaningful
    when unit ids encode a neighbourhood; otherwise N/A."""
    if not ids_encode_neighbourhood:
        return CheckResult("Spillovers", NOT_APPLICABLE, Msg("stress.spillovers.no_neighbourhood"))
    if not pd.api.types.is_numeric_dtype(df[unit_col]):
        return CheckResult("Spillovers", NOT_APPLICABLE, Msg("stress.spillovers.non_numeric"))
    adjacent = adjacent_control_ids(df, unit_col, treated_unit_col)
    controls = df[df[treated_unit_col] == 0].copy()
    controls["adjacent"] = controls[unit_col].isin(adjacent).astype(int)
    n_adjacent = controls.loc[controls["adjacent"] == 1, unit_col].nunique()
    n_far = controls.loc[controls["adjacent"] == 0, unit_col].nunique()
    if n_adjacent < 2 or n_far < 2:
        return CheckResult("Spillovers", NOT_APPLICABLE, Msg("stress.spillovers.too_few"))

    controls["adj_post"] = controls["adjacent"] * (controls[time_col] >= treatment_period).astype(int)
    controls[unit_col] = controls[unit_col].astype("category")
    controls[time_col] = controls[time_col].astype("category")
    try:
        fitted = smf.ols(f"{outcome_col} ~ adj_post + C({unit_col}) + C({time_col})",
                         data=controls).fit(cov_type="cluster",
                                            cov_kwds={"groups": controls[unit_col]})
        effect = float(fitted.params["adj_post"])
        # Same small-sample correction as the DiD: unit dummies not counted in K.
        se = float(fitted.bse["adj_post"]) * nested_fe_factor(controls, fitted, unit_col, unit_col)
        p_value = float(2 * stats.norm.sf(abs(effect / se)))
    except NUMERICAL_ERRORS as exc:
        return CheckResult("Spillovers", NOT_APPLICABLE, Msg("stress.error", error=str(exc)))
    if p_value < 0.10:
        return CheckResult("Spillovers", "WARNING",
                           Msg("stress.spillovers.warning", n=n_adjacent, effect=effect, p=p_value),
                           statistic=effect, p_value=p_value)
    return CheckResult("Spillovers", "PASS", Msg("stress.spillovers.pass", effect=effect, p=p_value),
                       statistic=effect, p_value=p_value)


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
        return CheckResult("Heterogeneous Effects", NOT_APPLICABLE, Msg("stress.heterogeneity.too_few"))
    var_ratio = float(treated_changes.var() / control_changes.var())
    p_value = float(stats.f.sf(var_ratio, len(treated_changes) - 1, len(control_changes) - 1))
    if p_value < 0.10:
        return CheckResult("Heterogeneous Effects", "WARNING",
                           Msg("stress.heterogeneity.warning", ratio=var_ratio, p=p_value),
                           statistic=var_ratio, p_value=p_value)
    return CheckResult("Heterogeneous Effects", "PASS",
                       Msg("stress.heterogeneity.pass", ratio=var_ratio, p=p_value),
                       statistic=var_ratio, p_value=p_value)


def identification_strength(checks: list[CheckResult]) -> float | None:
    """Score = 100 * PASS / (checks that are not N/A); None when every check is N/A."""
    computable = [c for c in checks if c.verdict != NOT_APPLICABLE]
    if not computable:
        return None
    return 100 * sum(c.verdict == PASS for c in computable) / len(computable)


def run_stress_test(df: pd.DataFrame, treatment_period: int, *, ids_encode_neighbourhood: bool,
                     outcome_col: str = "Y", unit_col: str = "unit", time_col: str = "period",
                     treatment_col: str = "D", treated_unit_col: str = "treated_unit") -> StressTestReport:
    """Run the five checks. `ids_encode_neighbourhood` must be stated
    explicitly: True only when consecutive unit ids are neighbours (the
    Virtual World); on uploaded or real data the Spillovers check is N/A."""
    checks = [
        _check_parallel_trends(df, outcome_col, unit_col, time_col, treated_unit_col, treatment_period),
        _check_anticipation(df, outcome_col, unit_col, time_col, treated_unit_col, treatment_period),
        _check_spillovers(df, outcome_col, unit_col, time_col, treated_unit_col, treatment_period,
                          ids_encode_neighbourhood),
        _check_serial_correlation(df, outcome_col, unit_col, time_col, treatment_col),
        _check_heterogeneous_effects(df, outcome_col, unit_col, time_col, treated_unit_col, treatment_period),
    ]
    n_computable = sum(c.verdict != NOT_APPLICABLE for c in checks)
    return StressTestReport(checks=checks, identification_strength=identification_strength(checks),
                            n_computable=n_computable)
