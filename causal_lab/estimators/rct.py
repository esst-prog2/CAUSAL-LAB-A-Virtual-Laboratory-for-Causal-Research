"""
Randomized Controlled Trial estimator.

Under random assignment the average treatment effect (ATE) is
identified by the difference in mean outcomes between treated and
control units. When baseline covariates are available, the
regression-adjusted estimator of Lin (2013),

    Y_i = a + tau * D_i + (X_i - mean(X))' b + D_i * (X_i - mean(X))' c + e_i,

keeps the same estimand and is never less precise asymptotically.
Both use HC2 heteroskedasticity-robust standard errors.

A balance table (standardized mean differences) checks whether the
randomization actually produced comparable groups.
"""
from __future__ import annotations

import pandas as pd
import statsmodels.api as sm

from estimators.common import (MethodResult, format_summary, normal_inference,
                               require_binary, standardized_difference)
from utils.i18n import LocalizedError, Msg

IMBALANCE_THRESHOLD = 0.1


def _ols_effect(y, design: pd.DataFrame) -> tuple[float, float]:
    fitted = sm.OLS(y, sm.add_constant(design, has_constant="add")).fit(cov_type="HC2")
    return float(fitted.params["D"]), float(fitted.bse["D"])


def estimate_rct(df: pd.DataFrame, outcome_col: str = "Y", treatment_col: str = "D",
                 covariate_cols: list[str] | None = None) -> MethodResult:
    covariate_cols = list(covariate_cols or [])
    require_binary(df[treatment_col], treatment_col)
    data = df[[outcome_col, treatment_col] + covariate_cols].dropna()
    y = data[outcome_col].astype(float)
    d = data[treatment_col].astype(int).rename("D")
    treated, control = data[d == 1], data[d == 0]

    diff_means, diff_se = _ols_effect(y, d.to_frame())

    balance_rows = []
    for c in covariate_cols:
        smd = standardized_difference(treated[c], control[c])
        balance_rows.append(dict(covariate=c, mean_treated=float(treated[c].mean()),
                                 mean_control=float(control[c].mean()), std_diff=smd,
                                 imbalanced=abs(smd) > IMBALANCE_THRESHOLD))
    balance = pd.DataFrame(balance_rows)

    warnings: list[str] = []
    if covariate_cols:
        xc = data[covariate_cols] - data[covariate_cols].mean()
        design = pd.concat([d, xc, xc.mul(d, axis=0).add_prefix("D_x_")], axis=1)
        estimate, se = _ols_effect(y, design)
        imbalanced = balance.loc[balance["imbalanced"], "covariate"].tolist()
        if imbalanced:
            warnings.append(Msg("warn.rct_imbalance", covariates=", ".join(imbalanced),
                                threshold=IMBALANCE_THRESHOLD))
    else:
        estimate, se = diff_means, diff_se

    ci_low, ci_high, p_value = normal_inference(estimate, se)
    result = MethodResult(
        method="Randomized Controlled Trial", key="rct",
        estimand=Msg("estimand.ate"),
        estimate=estimate, se=se, ci_low=ci_low, ci_high=ci_high, p_value=p_value,
        n_obs=len(data),
        details=dict(
            difference_in_means=diff_means, difference_in_means_se=diff_se,
            covariate_adjusted=bool(covariate_cols),
            n_treated=int((d == 1).sum()), n_control=int((d == 0).sum()),
            balance=balance,
        ),
        warnings=warnings,
    )
    extra = [f"Difference in means = {diff_means:.4f} (SE {diff_se:.4f})"]
    if covariate_cols:
        extra.append(f"Lin (2013) covariate-adjusted using {covariate_cols}")
    result.summary_text = format_summary(result, extra)
    return result
