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

Small-sample correction: CR1, G/(G-1) * (N-1)/(N-K). When the unit fixed
effects are nested in the clusters (always true when clustering by unit),
their dummies are not counted in K, as in Stata's xtreg, fe and reghdfe.
Counting them inflates the SE badly on short panels: with two periods,
N/K is close to 2 (hw6 review 3; on Card & Krueger, 1.91 instead of ~1.36).

Inference uses a Student t with G - 1 degrees of freedom, G being the number
of clusters, as Stata's xtreg, fe and R fixest do. With few clusters the normal
interval under-covers: on 500 worlds it covered 87.8% with 10 units, against
91.2% for this one. With few treated clusters neither is reliable (about 85%
with 4 treated units of 40), so the result then carries a warning.

Note: this canonical two-way fixed-effects specification can be biased under
staggered treatment timing combined with treatment effect heterogeneity (see
the diagnosis engine's warning). The heterogeneity-robust alternative is
estimators.staggered_did (Callaway & Sant'Anna 2021).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

from utils.i18n import LocalizedError, Msg

# Below these, clustered inference is unreliable; the result says so.
FEW_CLUSTERS = 30
FEW_CLUSTERS_PER_ARM = 10


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
    n_clusters: int = 0
    warnings: list[Msg] = field(default_factory=list)


def estimate_did(df: pd.DataFrame, outcome_col: str = "Y", treatment_col: str = "D",
                  unit_col: str = "unit", time_col: str = "period",
                  cluster_col: str | None = None) -> DiDResult:
    """Estimate a two-way fixed-effects DiD model via OLS with unit and
    period dummies, using cluster-robust standard errors at the unit
    level (or `cluster_col` if provided)."""
    # Only complete rows: statsmodels would drop them from the model but not from the clusters.
    used = list(dict.fromkeys([outcome_col, treatment_col, unit_col, time_col, cluster_col or unit_col]))
    df = df[used].dropna()
    if df[treatment_col].nunique() < 2:
        raise LocalizedError("err.did_no_variation", column=treatment_col)
    # A text or boolean treatment would enter the formula as a category and
    # the coefficient named `treatment_col` would not exist (hw6 review 5:
    # the estimate used to come back as NaN without any error).
    if df[treatment_col].dtype == bool:
        df = df.assign(**{treatment_col: df[treatment_col].astype(int)})
    if not pd.api.types.is_numeric_dtype(df[treatment_col]):
        raise LocalizedError("err.did_non_numeric", column=treatment_col)

    data = df.copy()
    data[unit_col] = data[unit_col].astype("category")
    data[time_col] = data[time_col].astype("category")

    formula = f"{outcome_col} ~ {treatment_col} + C({unit_col}) + C({time_col})"
    model = smf.ols(formula, data=data)

    cluster_var = cluster_col or unit_col
    fitted = model.fit(cov_type="cluster", cov_kwds={"groups": data[cluster_var]})

    beta = fitted.params[treatment_col]
    se = fitted.bse[treatment_col] * nested_fe_factor(data, fitted, unit_col, cluster_var)
    n_clusters = int(data[cluster_var].nunique())
    dof = max(n_clusters - 1, 1)
    t_stat = beta / se
    p_value = 2 * stats.t.sf(abs(t_stat), dof)
    half_width = stats.t.ppf(0.975, dof) * se
    ci = (beta - half_width, beta + half_width)

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
        n_clusters=n_clusters,
        warnings=_warnings(data, treatment_col, unit_col, time_col, cluster_var, n_clusters),
    )


def _warnings(data: pd.DataFrame, treatment_col, unit_col, time_col, cluster_var, n_clusters: int) -> list[Msg]:
    """What the coefficient and its interval cannot be trusted for on these data."""
    out = []
    treated_clusters = int((data.groupby(cluster_var, observed=True)[treatment_col].max() > 0).sum())
    if n_clusters < FEW_CLUSTERS or min(treated_clusters, n_clusters - treated_clusters) < FEW_CLUSTERS_PER_ARM:
        out.append(Msg("warn.did_few_clusters", clusters=n_clusters, treated=treated_clusters))
    d = data[treatment_col].astype(float)
    if not set(d.unique()) <= {0.0, 1.0}:
        out.append(Msg("warn.did_not_binary"))
        return out
    ordered = data.assign(_d=d).sort_values(time_col, kind="stable")
    switched_off = (ordered.groupby(unit_col, observed=True)["_d"].diff() < 0).groupby(
        ordered[unit_col], observed=True).any()
    if switched_off.any():
        out.append(Msg("warn.did_reversal", n=int(switched_off.sum())))
    return out


def nested_fe_factor(data: pd.DataFrame, fitted, unit_col: str, cluster_var: str) -> float:
    """Rescale statsmodels' CR1 SE so the unit dummies are not counted in K
    when every unit lies in a single cluster: sqrt((N - K) / (N - K + U - 1)).
    Also used by the stress-test regressions, so every unit-clustered fit in
    the app follows the same convention."""
    if data.groupby(unit_col, observed=True)[cluster_var].nunique().max() != 1:
        return 1.0
    n, k = fitted.nobs, len(fitted.params)
    n_unit_dummies = data[unit_col].nunique() - 1
    return float(np.sqrt((n - k) / (n - k + n_unit_dummies)))
