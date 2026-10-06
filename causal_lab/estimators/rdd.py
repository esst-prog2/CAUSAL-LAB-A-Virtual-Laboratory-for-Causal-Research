"""
Sharp Regression Discontinuity estimator.

Treatment is assigned by whether a running variable X crosses a known
cutoff c (D = 1[X >= c]). The effect at the cutoff is the jump in
E[Y | X] at c, estimated by local linear regression on each side,

    Y_i = a + tau * D_i + b * (X_i - c) + g * D_i * (X_i - c) + e_i,

using only observations with |X_i - c| < h, weighted by the triangular
kernel 1 - |X_i - c| / h, with HC1 robust standard errors.

The default bandwidth h is the MSE-optimal bandwidth of Imbens &
Kalyanaraman (2012). Conventional (not bias-corrected) inference is
reported; estimates at h/2 and 2h are always shown for sensitivity.
The manipulation check compares observation counts just below and just
above the cutoff (a simple binomial stand-in for the McCrary test).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from estimators.common import MethodResult, format_summary, normal_inference
from utils.i18n import LocalizedError, Msg

MIN_OBS_PER_SIDE = 10
C_TRIANGULAR = 3.4375


def _poly_fit(x: np.ndarray, y: np.ndarray, degree: int) -> np.ndarray:
    return np.polyfit(x, y, degree)[::-1]          # ascending coefficients


def ik_bandwidth(x: np.ndarray, y: np.ndarray, cutoff: float) -> float:
    """Imbens & Kalyanaraman (2012) bandwidth for the triangular kernel."""
    xc = x - cutoff
    n = len(x)
    left, right = xc < 0, xc >= 0

    # Step 1: density and conditional variances at the cutoff.
    h1 = 1.84 * np.std(x, ddof=1) * n ** (-1 / 5)
    in_l, in_r = left & (xc > -h1), right & (xc < h1)
    if in_l.sum() < 2 or in_r.sum() < 2:
        raise LocalizedError("err.rdd_bandwidth_data")
    f_c = (in_l.sum() + in_r.sum()) / (2 * n * h1)
    var_l, var_r = np.var(y[in_l], ddof=1), np.var(y[in_r], ddof=1)

    # Step 2: third derivative from a global cubic with a jump, fit
    # between the medians of X on each side.
    med_l, med_r = np.median(xc[left]), np.median(xc[right])
    window = (xc >= med_l) & (xc <= med_r)
    design = np.column_stack([np.ones(window.sum()), right[window], xc[window],
                              xc[window] ** 2, xc[window] ** 3])
    gamma = np.linalg.lstsq(design, y[window], rcond=None)[0]
    m3 = 6 * gamma[4]
    m3_sq = max(m3 ** 2, 1e-4)

    h2_l = 3.56 * (var_l / (f_c * m3_sq)) ** (1 / 7) * left.sum() ** (-1 / 7)
    h2_r = 3.56 * (var_r / (f_c * m3_sq)) ** (1 / 7) * right.sum() ** (-1 / 7)
    sel_l, sel_r = left & (xc > -h2_l), right & (xc < h2_r)
    if sel_l.sum() < 3 or sel_r.sum() < 3:
        sel_l, sel_r = left, right
    m2_l = 2 * _poly_fit(xc[sel_l], y[sel_l], 2)[2]
    m2_r = 2 * _poly_fit(xc[sel_r], y[sel_r], 2)[2]

    # Step 3: regularized optimal bandwidth.
    r_l = 2160 * var_l / (sel_l.sum() * h2_l ** 4)
    r_r = 2160 * var_r / (sel_r.sum() * h2_r ** 4)
    h = C_TRIANGULAR * ((var_l + var_r) / (f_c * ((m2_r - m2_l) ** 2 + r_l + r_r))) ** (1 / 5) * n ** (-1 / 5)
    max_h = max(-xc.min(), xc.max())
    return float(min(h, max_h))


def _local_linear(x: np.ndarray, y: np.ndarray, cutoff: float, h: float):
    xc = x - cutoff
    keep = np.abs(xc) < h
    n_left, n_right = int((keep & (xc < 0)).sum()), int((keep & (xc >= 0)).sum())
    if n_left < MIN_OBS_PER_SIDE or n_right < MIN_OBS_PER_SIDE:
        raise LocalizedError("err.rdd_bandwidth_sides", h=h, cutoff=cutoff, left=n_left, right=n_right,
                             minimum=MIN_OBS_PER_SIDE)
    d = (xc[keep] >= 0).astype(float)
    design = np.column_stack([np.ones(keep.sum()), d, xc[keep], d * xc[keep]])
    weights = 1 - np.abs(xc[keep]) / h
    fitted = sm.WLS(y[keep], design, weights=weights).fit(cov_type="HC1")
    return fitted, n_left, n_right


def estimate_rdd(df: pd.DataFrame, outcome_col: str = "Y", running_col: str = "X",
                 cutoff: float = 0.0, bandwidth: float | None = None) -> MethodResult:
    data = df[[outcome_col, running_col]].dropna().astype(float)
    x, y = data[running_col].to_numpy(), data[outcome_col].to_numpy()
    n_below, n_above = int((x < cutoff).sum()), int((x >= cutoff).sum())
    if n_below < MIN_OBS_PER_SIDE or n_above < MIN_OBS_PER_SIDE:
        raise LocalizedError("err.rdd_cutoff", cutoff=cutoff, below=n_below, above=n_above,
                             minimum=MIN_OBS_PER_SIDE)

    if bandwidth is not None and bandwidth <= 0:
        raise LocalizedError("err.rdd_bandwidth_positive")
    h = float(bandwidth) if bandwidth is not None else ik_bandwidth(x, y, cutoff)

    fitted, n_left, n_right = _local_linear(x, y, cutoff, h)
    estimate, se = float(fitted.params[1]), float(fitted.bse[1])
    ci_low, ci_high, p_value = normal_inference(estimate, se)

    sensitivity = []
    for factor in (0.5, 1.0, 2.0):
        try:
            f, _, _ = _local_linear(x, y, cutoff, h * factor)
            sensitivity.append(dict(bandwidth=h * factor, factor=factor,
                                    estimate=float(f.params[1]), se=float(f.bse[1])))
        except ValueError:
            sensitivity.append(dict(bandwidth=h * factor, factor=factor,
                                    estimate=float("nan"), se=float("nan")))

    warnings: list[str] = []
    w = h / 2
    count_below = int(((x >= cutoff - w) & (x < cutoff)).sum())
    count_above = int(((x >= cutoff) & (x < cutoff + w)).sum())
    manipulation_p = float(stats.binomtest(count_above, count_below + count_above, 0.5).pvalue) \
        if count_below + count_above > 0 else float("nan")
    if manipulation_p < 0.05:
        warnings.append(Msg("warn.rdd_manipulation", below=count_below, above=count_above, p=manipulation_p))

    a, tau, b, g = (float(v) for v in fitted.params)
    result = MethodResult(
        method="Regression Discontinuity (sharp)", key="rdd",
        estimand=Msg("estimand.rdd"),
        estimate=estimate, se=se, ci_low=ci_low, ci_high=ci_high, p_value=p_value,
        n_obs=n_left + n_right,
        details=dict(
            cutoff=cutoff, bandwidth=h, bandwidth_rule="user" if bandwidth is not None else "Imbens-Kalyanaraman",
            n_left=n_left, n_right=n_right,
            fit_left=dict(intercept=a, slope=b), fit_right=dict(intercept=a + tau, slope=b + g),
            sensitivity=pd.DataFrame(sensitivity),
            manipulation=dict(count_below=count_below, count_above=count_above, p_value=manipulation_p),
            plot_data=pd.DataFrame({"x": x, "y": y}),
            notes=Msg("note.rdd_inference"),
        ),
        warnings=warnings,
    )
    result.summary_text = format_summary(result, [
        Msg("summary.rdd.bandwidth", h=h, rule=result.details["bandwidth_rule"], left=n_left, right=n_right),
        Msg("summary.rdd.sensitivity",
            values=", ".join(f"{r['factor']:g}h -> {r['estimate']:.3f}" for r in sensitivity)),
    ])
    return result
