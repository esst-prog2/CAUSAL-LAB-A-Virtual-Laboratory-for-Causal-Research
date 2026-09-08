"""
Two-way fixed effects Difference-in-Differences estimator (CAUSAL LAB
spec, Section 32):

    Y_it = alpha_i + gamma_t + beta * D_it + epsilon_it

`alpha_i` are unit fixed effects, `gamma_t` are period fixed effects,
`D_it` is the treatment indicator, and `beta` is the DiD estimate of
the average treatment effect on the treated (ATT).

Standard errors are clustered at the unit level by default, which is
the standard recommendation for panel DiD designs (Bertrand,
Duflo & Mullainathan, 2004).

Note: this canonical two-way fixed-effects specification can be
biased under staggered treatment timing combined with treatment
effect heterogeneity (see the diagnosis engine's warning). v0.1 ships
the canonical estimator only; heterogeneity-robust estimators
(Callaway & Sant'Anna, de Chaisemartin & D'Haultfoeuille) are planned
for a later version.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


@dataclass
class DiDResult:
    att: float
    se: float
    t_stat: float
    p_value: float
    ci_low: float
    ci_high: float
    n_obs: int
    n_units: int
    n_periods: int
    formula: str
    summary_text: str


def estimate_did(df: pd.DataFrame, outcome_col: str = "Y", treatment_col: str = "D",
                  unit_col: str = "unit", time_col: str = "period",
                  cluster_col: str | None = None) -> DiDResult:
    """Estimate a two-way fixed-effects DiD model via OLS with unit and
    period dummies, using cluster-robust standard errors at the unit
    level (or `cluster_col` if provided)."""
    data = df.copy()
    data[unit_col] = data[unit_col].astype("category")
    data[time_col] = data[time_col].astype("category")

    formula = f"{outcome_col} ~ {treatment_col} + C({unit_col}) + C({time_col})"
    model = smf.ols(formula, data=data)

    cluster_var = cluster_col or unit_col
    fitted = model.fit(cov_type="cluster", cov_kwds={"groups": data[cluster_var]})

    beta = fitted.params.get(treatment_col, np.nan)
    se = fitted.bse.get(treatment_col, np.nan)
    t_stat = fitted.tvalues.get(treatment_col, np.nan)
    p_value = fitted.pvalues.get(treatment_col, np.nan)
    ci = fitted.conf_int().loc[treatment_col]

    summary_text = (
        f"DiD estimate (ATT) = {beta:.4f}\n"
        f"Cluster-robust SE (by {cluster_var}) = {se:.4f}\n"
        f"t = {t_stat:.3f}, p = {p_value:.4f}\n"
        f"95% CI = [{ci[0]:.4f}, {ci[1]:.4f}]"
    )

    return DiDResult(
        att=float(beta),
        se=float(se),
        t_stat=float(t_stat),
        p_value=float(p_value),
        ci_low=float(ci[0]),
        ci_high=float(ci[1]),
        n_obs=int(fitted.nobs),
        n_units=data[unit_col].nunique(),
        n_periods=data[time_col].nunique(),
        formula=formula,
        summary_text=summary_text,
    )
