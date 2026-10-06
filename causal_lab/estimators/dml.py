"""
Double / Debiased Machine Learning estimator (Chernozhukov et al. 2018)
for the partially linear model

    Y = theta * D + g(X) + e,      D = m(X) + v.

With K-fold cross-fitting, l(X) = E[Y|X] and m(X) = E[D|X] are
predicted for each fold by random forests trained on the other folds.
theta is the coefficient from regressing the outcome residuals
Y - l(X) on the treatment residuals D - m(X). Its standard error comes
from the influence function psi = (u - theta * v) * v.

Unlike OLS with linear controls, this stays consistent when the
covariates affect treatment and outcome non-linearly.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold

from estimators.common import MethodResult, format_summary, normal_inference


def _r2(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(1 - np.sum((actual - predicted) ** 2) / np.sum((actual - actual.mean()) ** 2))


def estimate_dml(df: pd.DataFrame, outcome_col: str = "Y", treatment_col: str = "D",
                 covariate_cols: list[str] | None = None, n_folds: int = 5,
                 seed: int = 0) -> MethodResult:
    covariate_cols = list(covariate_cols or [])
    if not covariate_cols:
        raise ValueError("DML requires at least one covariate.")
    data = df[[outcome_col, treatment_col] + covariate_cols].dropna().astype(float)
    if len(data) < 10 * n_folds:
        raise ValueError(f"DML needs at least {10 * n_folds} complete observations for {n_folds}-fold "
                         f"cross-fitting (found {len(data)}).")
    if data[treatment_col].nunique() < 2:
        raise ValueError(f"Treatment column '{treatment_col}' has no variation.")
    y = data[outcome_col].to_numpy()
    d = data[treatment_col].to_numpy()
    x = data[covariate_cols].to_numpy()

    l_hat, m_hat = np.empty_like(y), np.empty_like(d)
    for train, test in KFold(n_splits=n_folds, shuffle=True, random_state=seed).split(x):
        for target, out in ((y, l_hat), (d, m_hat)):
            model = RandomForestRegressor(n_estimators=200, min_samples_leaf=5,
                                          random_state=seed, n_jobs=-1)
            model.fit(x[train], target[train])
            out[test] = model.predict(x[test])

    u, v = y - l_hat, d - m_hat
    theta = float(np.sum(v * u) / np.sum(v * v))
    psi = (u - theta * v) * v
    se = float(np.sqrt(np.mean(psi ** 2) / np.mean(v * v) ** 2 / len(y)))
    ci_low, ci_high, p_value = normal_inference(theta, se)

    ols = sm.OLS(y, sm.add_constant(data[[treatment_col] + covariate_cols], has_constant="add")) \
        .fit(cov_type="HC1")

    warnings: list[str] = []
    r2_d = _r2(d, m_hat)
    if r2_d > 0.95:
        warnings.append(f"The covariates predict the treatment almost perfectly (out-of-fold R2 = {r2_d:.3f}): "
                        f"little independent treatment variation is left, so theta is weakly identified.")

    result = MethodResult(
        method="Double Machine Learning",
        estimand="theta (partially linear model)",
        estimate=theta, se=se, ci_low=ci_low, ci_high=ci_high, p_value=p_value,
        n_obs=len(y),
        details=dict(
            n_folds=n_folds, learner="RandomForestRegressor(n_estimators=200, min_samples_leaf=5)",
            r2_outcome=_r2(y, l_hat), r2_treatment=r2_d,
            ols_estimate=float(ols.params[treatment_col]), ols_se=float(ols.bse[treatment_col]),
            covariates=covariate_cols,
        ),
        warnings=warnings,
    )
    result.summary_text = format_summary(result, [
        f"{n_folds}-fold cross-fitting, random-forest nuisance models "
        f"(out-of-fold R2: outcome {result.details['r2_outcome']:.3f}, treatment {r2_d:.3f})",
        f"Naive OLS with linear controls = {result.details['ols_estimate']:.4f} "
        f"(SE {result.details['ols_se']:.4f})",
    ])
    return result
