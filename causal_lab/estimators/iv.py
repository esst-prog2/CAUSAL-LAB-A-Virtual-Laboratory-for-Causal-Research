"""
Instrumental Variables estimator: two-stage least squares (2SLS).

    First stage:   D_i = pi * Z_i + X_i' g + v_i
    Second stage:  Y_i = beta * D_i + X_i' h + e_i,  D instrumented by Z

Valid when the instrument Z is relevant (moves D) and excludable
(affects Y only through D). Relevance is checked with the first-stage
F statistic of the excluded instruments (rule of thumb: F >= 10;
Staiger & Stock 1997). Exclusion cannot be tested and must be argued.

Estimated with linearmodels' IV2SLS and heteroskedasticity-robust
standard errors; the naive OLS coefficient is reported for comparison.
"""
from __future__ import annotations

import pandas as pd
import statsmodels.api as sm
from linearmodels.iv import IV2SLS

from estimators.common import MethodResult, format_summary

WEAK_INSTRUMENT_F = 10.0


def estimate_iv(df: pd.DataFrame, outcome_col: str = "Y", treatment_col: str = "D",
                instrument_cols: list[str] | None = None,
                control_cols: list[str] | None = None) -> MethodResult:
    instrument_cols = list(instrument_cols or [])
    control_cols = list(control_cols or [])
    if not instrument_cols:
        raise ValueError("IV requires at least one instrument.")
    data = df[[outcome_col, treatment_col] + instrument_cols + control_cols].dropna().astype(float)
    if data[treatment_col].nunique() < 2:
        raise ValueError(f"Treatment column '{treatment_col}' has no variation.")

    exog = sm.add_constant(data[control_cols], has_constant="add")
    fitted = IV2SLS(data[outcome_col], exog, data[[treatment_col]], data[instrument_cols]).fit(cov_type="robust")
    estimate = float(fitted.params[treatment_col])
    se = float(fitted.std_errors[treatment_col])
    ci = fitted.conf_int().loc[treatment_col]

    # linearmodels reports a robust Wald chi2 for the excluded
    # instruments; dividing by their number gives the F statistic.
    diag = fitted.first_stage.diagnostics.loc[treatment_col]
    first_stage_f = float(diag["f.stat"]) / len(instrument_cols)
    first_stage = fitted.first_stage.individual[treatment_col]
    first_stage_coefs = {z: float(first_stage.params[z]) for z in instrument_cols}

    ols = sm.OLS(data[outcome_col], sm.add_constant(data[[treatment_col] + control_cols],
                                                    has_constant="add")).fit(cov_type="HC1")

    warnings: list[str] = []
    if first_stage_f < WEAK_INSTRUMENT_F:
        warnings.append(f"Weak instrument: first-stage F = {first_stage_f:.1f} < {WEAK_INSTRUMENT_F:.0f}. "
                        f"2SLS is biased toward OLS and its confidence interval is unreliable.")

    result = MethodResult(
        method="Instrumental Variables (2SLS)",
        estimand="LATE / effect of D",
        estimate=estimate, se=se, ci_low=float(ci["lower"]), ci_high=float(ci["upper"]),
        p_value=float(fitted.pvalues[treatment_col]),
        n_obs=int(fitted.nobs),
        details=dict(
            first_stage_f=first_stage_f, first_stage_coefs=first_stage_coefs,
            partial_r2=float(diag["partial.rsquared"]),
            ols_estimate=float(ols.params[treatment_col]), ols_se=float(ols.bse[treatment_col]),
            instruments=instrument_cols, controls=control_cols,
        ),
        warnings=warnings,
    )
    result.summary_text = format_summary(result, [
        f"First-stage F = {first_stage_f:.2f} (partial R2 = {result.details['partial_r2']:.3f})",
        f"Naive OLS = {result.details['ols_estimate']:.4f} (SE {result.details['ols_se']:.4f})",
    ])
    return result
