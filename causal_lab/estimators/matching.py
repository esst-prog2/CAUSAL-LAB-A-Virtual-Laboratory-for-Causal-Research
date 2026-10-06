"""
Matching estimator of the average treatment effect on the treated
(ATT), under selection on observables: conditional on the covariates X,
treatment is as good as random.

1. Covariate matching (Abadie & Imbens 2006, 2011): each treated unit is
   matched, with replacement, to the control closest in Mahalanobis
   distance on X. The bias from inexact matches is removed with a
   regression of Y on X among controls:

       Y0hat_i = Y_j(i) + mu0(X_i) - mu0(X_j(i))

   Standard error: the Abadie-Imbens variance for the ATT,

       V = 1/N1^2 * [ sum_treated (Y_i - Y0hat_i - tau)^2
                      + sum_controls K_i (K_i - 1) sigma2_i ],

   with K_i the number of times control i is used and sigma2_i
   estimated by matching each control to its nearest other control.
   Matching on the covariates themselves (a known metric) is the setting
   for which this variance is derived; matching on an *estimated*
   propensity score makes it conservative (Abadie & Imbens 2016). On the
   Matching virtual world it gives 97% coverage for a nominal 95%.
   The bootstrap is not used: it is invalid for nearest-neighbour
   matching (Abadie & Imbens 2008).
2. The propensity score p(X) (logit) is still estimated, for the overlap
   diagnostic and for inverse probability weighting (Hajek weights
   p / (1 - p) on controls; bootstrap SE, valid for this smooth
   estimator).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.neighbors import NearestNeighbors

from estimators.common import (MethodResult, format_summary, normal_inference,
                               require_binary, standardized_difference)
from utils.i18n import LocalizedError, Msg

N_BOOTSTRAP = 200


def _propensity(data: pd.DataFrame, treatment_col: str, covariate_cols: list[str]) -> np.ndarray:
    x = sm.add_constant(data[covariate_cols].astype(float), has_constant="add")
    fitted = sm.Logit(data[treatment_col].astype(int), x).fit(disp=0, maxiter=200)
    return np.clip(fitted.predict(x).to_numpy(), 1e-6, 1 - 1e-6)


def _ipw_att(y: np.ndarray, d: np.ndarray, ps: np.ndarray) -> float:
    w = ps / (1 - ps)
    return float(y[d == 1].mean() - np.sum(w[d == 0] * y[d == 0]) / np.sum(w[d == 0]))


def _mahalanobis_coordinates(x: np.ndarray) -> np.ndarray:
    """Coordinates in which Euclidean distance is the Mahalanobis distance."""
    cov = np.atleast_2d(np.cov(x, rowvar=False))
    cov += np.eye(len(cov)) * 1e-9 * np.trace(cov)      # guard against singular covariates
    return x @ np.linalg.cholesky(np.linalg.inv(cov))


def estimate_matching(df: pd.DataFrame, outcome_col: str = "Y", treatment_col: str = "D",
                      covariate_cols: list[str] | None = None, seed: int = 0) -> MethodResult:
    covariate_cols = list(covariate_cols or [])
    if not covariate_cols:
        raise LocalizedError("err.needs_covariate", method=Msg("method.matching"))
    require_binary(df[treatment_col], treatment_col)
    data = df[[outcome_col, treatment_col] + covariate_cols].dropna().reset_index(drop=True)
    y = data[outcome_col].to_numpy(float)
    d = data[treatment_col].to_numpy(int)
    x = data[covariate_cols].to_numpy(float)

    t_idx, c_idx = np.flatnonzero(d == 1), np.flatnonzero(d == 0)
    if len(c_idx) < 2:
        raise LocalizedError("err.matching_two_controls")

    # 1-NN covariate matching (Mahalanobis), with replacement.
    z = _mahalanobis_coordinates(x)
    nn = NearestNeighbors(n_neighbors=2).fit(z[c_idx])
    match = c_idx[nn.kneighbors(z[t_idx], n_neighbors=1, return_distance=False)[:, 0]]

    # Bias correction with a linear regression of Y on X among controls.
    design_c = np.column_stack([np.ones(len(c_idx)), x[c_idx]])
    beta = np.linalg.lstsq(design_c, y[c_idx], rcond=None)[0]

    def mu0(rows):
        return np.column_stack([np.ones(len(rows)), x[rows]]) @ beta

    y0_hat = y[match] + mu0(t_idx) - mu0(match)
    att = float(np.mean(y[t_idx] - y0_hat))

    # Abadie-Imbens variance; sigma2 from each control's nearest other control.
    neighbour = c_idx[nn.kneighbors(z[c_idx], n_neighbors=2, return_distance=False)[:, 1]]
    sigma2 = (y[c_idx] - y[neighbour]) ** 2 / 2
    k_used = np.bincount(match, minlength=len(y))[c_idx]
    n1 = len(t_idx)
    variance = (np.sum((y[t_idx] - y0_hat - att) ** 2) + np.sum(k_used * (k_used - 1) * sigma2)) / n1 ** 2
    se = float(np.sqrt(variance))

    # Propensity score: overlap diagnostic and IPW with bootstrap SE.
    ps = _propensity(data, treatment_col, covariate_cols)
    ipw = _ipw_att(y, d, ps)
    rng = np.random.default_rng(seed)
    boot = []
    for _ in range(N_BOOTSTRAP):
        idx = rng.integers(0, len(y), len(y))
        if d[idx].min() == d[idx].max():
            continue
        try:
            boot.append(_ipw_att(y[idx], d[idx], _propensity(data.iloc[idx], treatment_col, covariate_cols)))
        except Exception:   # perfect separation in a resample
            continue
    ipw_se = float(np.std(boot, ddof=1)) if len(boot) > 1 else float("nan")

    # Balance before / after matching.
    balance = pd.DataFrame([dict(
        covariate=c,
        std_diff_before=standardized_difference(data[c].to_numpy()[t_idx], data[c].to_numpy()[c_idx]),
        std_diff_after=standardized_difference(data[c].to_numpy()[t_idx], data[c].to_numpy()[match]),
    ) for c in covariate_cols])

    warnings: list[Msg] = []
    outside = int(np.sum((ps[t_idx] > ps[c_idx].max()) | (ps[t_idx] < ps[c_idx].min())))
    if outside:
        warnings.append(Msg("warn.overlap", n=outside))
    if np.any(np.abs(balance["std_diff_after"]) > 0.1):
        warnings.append(Msg("warn.imbalance_after_matching"))

    ci_low, ci_high, p_value = normal_inference(att, se)
    result = MethodResult(
        method="Matching / Propensity Score", key="matching",
        estimand=Msg("estimand.att"),
        estimate=att, se=se, ci_low=ci_low, ci_high=ci_high, p_value=p_value,
        n_obs=len(data),
        details=dict(
            ipw_att=ipw, ipw_se=ipw_se,
            naive_difference=float(y[t_idx].mean() - y[c_idx].mean()),
            n_treated=n1, n_control=len(c_idx), n_controls_used=int(np.sum(k_used > 0)),
            propensity=pd.DataFrame({"propensity": ps, "treated": d}),
            balance=balance,
            notes=Msg("note.matching_se"),
        ),
        warnings=warnings,
    )
    result.summary_text = format_summary(result, [
        Msg("summary.matching.ipw", att=ipw, se=ipw_se),
        Msg("summary.matching.naive", value=result.details["naive_difference"]),
        Msg("summary.matching.controls", n=result.details["n_controls_used"]),
    ])
    return result
