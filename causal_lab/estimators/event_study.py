"""
Event-study (leads-and-lags) estimator (CAUSAL LAB spec, Section 14 —
"Dynamic analysis").

Estimates a separate treatment-effect coefficient for each period
relative to the treatment date:

    Y_it = alpha_i + gamma_t + sum_k (beta_k * 1[t - T0_i = k]) + eps_it

with one leave-out period (k = -1, the period right before
treatment) as the reference category. The pre-treatment coefficients
(k < -1) provide an informal, visual test of the parallel-trends
assumption: they should be statistically indistinguishable from zero
if the design is valid.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.tools.sm_exceptions import SingularMatrixWarning


@dataclass
class EventStudyResult:
    coefficients: pd.DataFrame   # columns: rel_period, estimate, se, ci_low, ci_high
    reference_period: int
    n_obs: int


def estimate_event_study(df: pd.DataFrame, outcome_col: str = "Y",
                          unit_col: str = "unit", time_col: str = "period",
                          treated_unit_col: str = "treated_unit",
                          adoption_period_col: str | None = None,
                          fixed_treatment_period: int | None = None,
                          reference_period: int = -1,
                          window: int = 6) -> EventStudyResult:
    """Estimate dynamic (leads/lags) treatment effects.

    Units not in the treated group act as the comparison group for
    all relative-period coefficients (i.e., a stacked, non-staggered
    event study). For staggered adoption designs, `adoption_period_col`
    can supply a per-unit adoption period; otherwise
    `fixed_treatment_period` applies to every treated unit.
    """
    data = df.copy()

    if adoption_period_col and adoption_period_col in data.columns:
        adoption = data[adoption_period_col]
    elif fixed_treatment_period is not None:
        adoption = fixed_treatment_period
    else:
        # Infer adoption period as the first period where treated_now/D == 1
        treat_col = "treated_now" if "treated_now" in data.columns else "D"
        adoption_map = (
            data.loc[data[treat_col] == 1]
            .groupby(unit_col)[time_col].min()
        )
        adoption = data[unit_col].map(adoption_map)

    data["rel_period"] = np.where(
        data[treated_unit_col] == 1,
        data[time_col] - adoption,
        np.nan,
    )
    data["rel_period"] = data["rel_period"].clip(lower=-window, upper=window)

    data["rel_bucket"] = data["rel_period"].apply(
        lambda x: "control" if pd.isna(x) else f"k{int(x):+d}"
    )
    data.loc[data["rel_bucket"] == f"k{reference_period:+d}", "rel_bucket"] = "ref"

    data[unit_col] = data[unit_col].astype("category")
    data[time_col] = data[time_col].astype("category")

    formula = f"{outcome_col} ~ C(rel_bucket, Treatment('ref')) + C({unit_col}) + C({time_col})"
    model = smf.ols(formula, data=data)
    # In a non-staggered design (a single adoption date shared by all
    # treated units), the treated units' relative-period dummies are
    # collinear with the calendar-period fixed effects for the control
    # units that never receive any rel_period bucket. statsmodels
    # already falls back to a pseudo-inverse in this case, which gives
    # correct estimates for the identified coefficients; we just
    # silence the resulting (expected, non-fatal) warning.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=SingularMatrixWarning)
        fitted = model.fit(cov_type="cluster", cov_kwds={"groups": data[unit_col]})

    rows = []
    for name, coef in fitted.params.items():
        if "rel_bucket" not in name:
            continue
        bucket = name.split("[T.")[-1].rstrip("]")
        if bucket in ("control",):
            continue
        try:
            k = int(bucket.replace("k", ""))
        except ValueError:
            continue
        se = fitted.bse[name]
        ci = fitted.conf_int().loc[name]
        rows.append(dict(rel_period=k, estimate=coef, se=se, ci_low=ci[0], ci_high=ci[1]))

    rows.append(dict(rel_period=reference_period, estimate=0.0, se=0.0,
                      ci_low=0.0, ci_high=0.0))
    coef_df = pd.DataFrame(rows).sort_values("rel_period").reset_index(drop=True)

    return EventStudyResult(
        coefficients=coef_df,
        reference_period=reference_period,
        n_obs=int(fitted.nobs),
    )
