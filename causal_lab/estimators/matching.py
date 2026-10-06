"""
Matching / Propensity Score estimator of the average treatment effect
on the treated (ATT), under selection on observables: conditional on
the covariates X, treatment is as good as random.

1. Propensity score p(X) = P(D = 1 | X) by logistic regression.
2. Nearest-neighbour matching: each treated unit is matched (with
   replacement) to the control with the closest propensity score.
   Standard error: Abadie & Imbens (2006) variance for the ATT,

       V = 1/N1^2 * [ sum_treated (Y_i - Y0hat_i - tau)^2
                      + sum_controls K_i (K_i - 1) sigma2_i ],

   where K_i is the number of times control i is used as a match and
   sigma2_i is estimated by matching each control to its nearest other
   control. The bootstrap is NOT used: it is invalid for nearest-
   neighbour matching (Abadie & Imbens 2008). This variance ignores
   the estimation error of the propensity score itself.
3. Inverse probability weighting (Hajek): controls weighted by
   p / (1 - p); bootstrap SE (valid for this smooth estimator).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from estimators.common import (MethodResult, format_summary, normal_inference,
                               require_binary, standardized_difference)

N_BOOTSTRAP = 200


def _propensity(data: pd.DataFrame, treatment_col: str, covariate_cols: list[str]) -> np.ndarray:
    x = sm.add_constant(data[covariate_cols].astype(float), has_constant="add")
    fitted = sm.Logit(data[treatment_col].astype(int), x).fit(disp=0, maxiter=200)
    return np.clip(fitted.predict(x).to_numpy(), 1e-6, 1 - 1e-6)


def _nearest(sorted_values: np.ndarray, queries: np.ndarray) -> np.ndarray:
    """Index (into sorted_values) of the nearest element for each query."""
    pos = np.searchsorted(sorted_values, queries)
    left = np.clip(pos - 1, 0, len(sorted_values) - 1)
    right = np.clip(pos, 0, len(sorted_values) - 1)
    use_right = np.abs(sorted_values[right] - queries) < np.abs(sorted_values[left] - queries)
    return np.where(use_right, right, left)


def _ipw_att(y: np.ndarray, d: np.ndarray, ps: np.ndarray) -> float:
    w = ps / (1 - ps)
    return float(y[d == 1].mean() - np.sum(w[d == 0] * y[d == 0]) / np.sum(w[d == 0]))


def estimate_matching(df: pd.DataFrame, outcome_col: str = "Y", treatment_col: str = "D",
                      covariate_cols: list[str] | None = None, seed: int = 0) -> MethodResult:
    covariate_cols = list(covariate_cols or [])
    if not covariate_cols:
        raise ValueError("Matching requires at least one covariate.")
    require_binary(df[treatment_col], treatment_col)
    data = df[[outcome_col, treatment_col] + covariate_cols].dropna().reset_index(drop=True)
    y = data[outcome_col].to_numpy(float)
    d = data[treatment_col].to_numpy(int)
    ps = _propensity(data, treatment_col, covariate_cols)

    t_idx, c_idx = np.flatnonzero(d == 1), np.flatnonzero(d == 0)
    if len(c_idx) < 2:
        raise ValueError("Matching requires at least two control observations.")
    order = np.argsort(ps[c_idx])
    c_sorted, ps_c_sorted = c_idx[order], ps[c_idx][order]

    # 1-NN match of each treated unit on the propensity score.
    match = c_sorted[_nearest(ps_c_sorted, ps[t_idx])]
    y0_hat = y[match]
    att = float(np.mean(y[t_idx] - y0_hat))

    # Abadie-Imbens variance.
    k_used = np.bincount(match, minlength=len(y))[c_idx]
    pos_in_sorted = np.argsort(order)            # position of each control in c_sorted
    lower = np.clip(pos_in_sorted - 1, 0, len(c_sorted) - 1)
    upper = np.clip(pos_in_sorted + 1, 0, len(c_sorted) - 1)
    # Nearest *other* control: never the control itself at either end.
    pick_upper = (upper != pos_in_sorted) & (
        (lower == pos_in_sorted)
        | (np.abs(ps_c_sorted[upper] - ps[c_idx]) < np.abs(ps_c_sorted[lower] - ps[c_idx])))
    neighbour = c_sorted[np.where(pick_upper, upper, lower)]
    sigma2 = (y[c_idx] - y[neighbour]) ** 2 / 2
    n1 = len(t_idx)
    variance = (np.sum((y[t_idx] - y0_hat - att) ** 2) + np.sum(k_used * (k_used - 1) * sigma2)) / n1 ** 2
    se = float(np.sqrt(variance))

    # IPW with bootstrap SE.
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

    warnings: list[str] = []
    outside = int(np.sum((ps[t_idx] > ps[c_idx].max()) | (ps[t_idx] < ps[c_idx].min())))
    if outside:
        warnings.append(f"Overlap: {outside} treated observation(s) have a propensity score outside "
                        f"the range of control propensity scores; their matches are poor.")
    if np.any(np.abs(balance["std_diff_after"]) > 0.1):
        warnings.append("Some covariates remain imbalanced after matching (|standardized difference| > 0.1).")

    ci_low, ci_high, p_value = normal_inference(att, se)
    result = MethodResult(
        method="Matching / Propensity Score",
        estimand="ATT",
        estimate=att, se=se, ci_low=ci_low, ci_high=ci_high, p_value=p_value,
        n_obs=len(data),
        details=dict(
            ipw_att=ipw, ipw_se=ipw_se,
            naive_difference=float(y[t_idx].mean() - y[c_idx].mean()),
            n_treated=n1, n_control=len(c_idx), n_controls_used=int(np.sum(k_used > 0)),
            propensity=pd.DataFrame({"propensity": ps, "treated": d}),
            balance=balance,
            notes="Abadie-Imbens SE ignores propensity-score estimation error; on the Matching virtual "
                  "world it is conservative (about 30% too large, 100% CI coverage over 200 "
                  "replications).",
        ),
        warnings=warnings,
    )
    result.summary_text = format_summary(result, [
        f"IPW ATT = {ipw:.4f} (bootstrap SE {ipw_se:.4f})",
        f"Naive difference in means = {result.details['naive_difference']:.4f}",
        f"{result.details['n_controls_used']} distinct controls used as matches",
    ])
    return result
