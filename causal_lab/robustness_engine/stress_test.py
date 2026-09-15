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
from statsmodels.stats.stattools import durbin_watson


@dataclass
class CheckResult:
    name: str
    verdict: str          # "PASS" or "WARNING"
    detail: str
    statistic: float | None = None
    p_value: float | None = None


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
    pre[unit_col] = pre[unit_col].astype("category")
    pre[time_col] = pre[time_col].astype("category")
    formula = f"{outcome_col} ~ {treated_unit_col} * {time_col} + C({unit_col})"
    try:
        fitted = smf.ols(formula, data=pre).fit(
            cov_type="cluster", cov_kwds={"groups": pre[unit_col]})
        interaction_terms = [p for p in fitted.params.index if f"{treated_unit_col}:" in p]
        if not interaction_terms:
            return CheckResult("Parallel Trends", "WARNING", "Could not estimate interaction terms.")
        wald = fitted.f_test([f"{t} = 0" for t in interaction_terms])
        p_value = float(np.asarray(wald.pvalue))
        if p_value < 0.10:
            return CheckResult(
                "Parallel Trends", "WARNING",
                f"Joint test of pre-treatment group-specific trends rejects "
                f"the null of equal trends (p = {p_value:.3f}). Differential "
                f"pre-trends are a threat to the parallel-trends assumption.",
                p_value=p_value)
        return CheckResult(
            "Parallel Trends", "PASS",
            f"No evidence of differential pre-treatment trends "
            f"(p = {p_value:.3f}).", p_value=p_value)
    except Exception as exc:  # pragma: no cover - defensive
        return CheckResult("Parallel Trends", "WARNING", f"Test could not be computed ({exc}).")


def _check_serial_correlation(df: pd.DataFrame, outcome_col, unit_col, time_col,
                               treatment_col) -> CheckResult:
    data = df.copy()
    data[unit_col] = data[unit_col].astype("category")
    data[time_col] = data[time_col].astype("category")
    formula = f"{outcome_col} ~ {treatment_col} + C({unit_col}) + C({time_col})"
    fitted = smf.ols(formula, data=data).fit()
    dw = durbin_watson(fitted.resid)
    if dw < 1.5 or dw > 2.5:
        return CheckResult(
            "Serial Correlation", "WARNING",
            f"Durbin-Watson statistic = {dw:.2f} (far from 2), suggesting "
            f"residual autocorrelation. Conventional standard errors may "
            f"understate true uncertainty; cluster by unit or use a "
            f"wild-cluster bootstrap.", statistic=dw)
    return CheckResult("Serial Correlation", "PASS",
                        f"Durbin-Watson statistic = {dw:.2f}, close to 2 "
                        f"(no strong evidence of residual autocorrelation).",
                        statistic=dw)


def _check_anticipation(df: pd.DataFrame, outcome_col, unit_col, time_col,
                         treated_unit_col, treatment_period) -> CheckResult:
    lead_period = treatment_period - 1
    pre = df[df[time_col].isin([lead_period, treatment_period - 2])].copy()
    if pre.empty or pre[time_col].nunique() < 2:
        return CheckResult("Anticipation", "WARNING", "Not enough data to test for anticipation effects.")
    pre["is_lead"] = (pre[time_col] == lead_period).astype(int)
    try:
        fitted = smf.ols(f"{outcome_col} ~ {treated_unit_col} * is_lead", data=pre).fit(
            cov_type="HC1")
        term = f"{treated_unit_col}:is_lead"
        if term not in fitted.params:
            return CheckResult("Anticipation", "PASS", "No anticipation interaction term available; default pass.")
        p_value = float(fitted.pvalues[term])
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


def _check_spillovers(df: pd.DataFrame, unit_col, treated_unit_col) -> CheckResult:
    treated_ids = set(df.loc[df[treated_unit_col] == 1, unit_col].unique())
    control_ids = set(df.loc[df[treated_unit_col] == 0, unit_col].unique())
    adjacent_controls = sum(
        1 for c in control_ids
        if any(abs(c - t) == 1 for t in treated_ids)
    )
    if adjacent_controls > 0:
        share = adjacent_controls / max(1, len(control_ids))
        return CheckResult(
            "Spillovers", "WARNING",
            f"{adjacent_controls} control unit(s) ({share:.0%} of controls) "
            f"are directly adjacent to a treated unit and may be exposed "
            f"to spillovers, biasing the comparison-group outcome.",
        )
    return CheckResult("Spillovers", "PASS",
                        "No control units directly adjacent to a treated unit were detected.")


def _check_heterogeneous_effects(df: pd.DataFrame, outcome_col, unit_col, time_col,
                                  treatment_col, treated_unit_col) -> CheckResult:
    post_treated = df[(df[treated_unit_col] == 1) & (df[treatment_col] == 1)]
    if post_treated[unit_col].nunique() < 3:
        return CheckResult("Heterogeneous Effects", "PASS",
                            "Too few treated units to assess effect heterogeneity; default pass.")
    unit_means = post_treated.groupby(unit_col)[outcome_col].mean()
    cv = float(unit_means.std() / (abs(unit_means.mean()) + 1e-8))
    if cv > 1.0:
        return CheckResult(
            "Heterogeneous Effects", "WARNING",
            f"Post-treatment outcomes vary substantially across treated "
            f"units (coefficient of variation = {cv:.2f}). A single average "
            f"treatment effect may mask important heterogeneity.",
            statistic=cv)
    return CheckResult("Heterogeneous Effects", "PASS",
                        f"Post-treatment outcomes are relatively homogeneous across "
                        f"treated units (coefficient of variation = {cv:.2f}).",
                        statistic=cv)


def run_stress_test(df: pd.DataFrame, treatment_period: int, outcome_col: str = "Y",
                     unit_col: str = "unit", time_col: str = "period",
                     treatment_col: str = "D", treated_unit_col: str = "treated_unit") -> StressTestReport:
    checks = [
        _check_parallel_trends(df, outcome_col, unit_col, time_col, treated_unit_col, treatment_period),
        _check_anticipation(df, outcome_col, unit_col, time_col, treated_unit_col, treatment_period),
        _check_spillovers(df, unit_col, treated_unit_col),
        _check_serial_correlation(df, outcome_col, unit_col, time_col, treatment_col),
        _check_heterogeneous_effects(df, outcome_col, unit_col, time_col, treatment_col, treated_unit_col),
    ]
    n_pass = sum(1 for c in checks if c.verdict == "PASS")
    identification_strength = 100 * n_pass / len(checks)
    return StressTestReport(checks=checks, identification_strength=identification_strength)
