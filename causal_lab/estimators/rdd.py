"""
Regression Discontinuity estimator: sharp or fuzzy, conventional or robust
bias-corrected inference.

Treatment is assigned, or in a fuzzy design encouraged, by whether a running
variable X crosses a known cutoff c. On each side a local linear regression
of Y on (X - c) is fitted with the triangular kernel (1 - |X - c| / h) / h:

    sharp  tau = jump in E[Y | X] at c
    fuzzy  tau = jump in E[Y | X] / jump in E[D | X]   (local Wald estimate)

Standard errors are HC1 on each side, as rdrobust's vce = "hc1"
(Calonico, Cattaneo & Titiunik 2014); the fuzzy variance is the delta
method on the two jumps. The point estimate is always the conventional one.
With inference = "robust", the CI and p-value are robust bias-corrected
(CCT 2014): the leading bias is estimated by a local quadratic with
bandwidth b (b = h by default, as rdrobust when h is given), the CI is
centred on the bias-corrected estimate, and its variance accounts for the
bias estimate. Both inferences are always in `details`.

The default bandwidth h is the MSE-optimal bandwidth of Imbens &
Kalyanaraman (2012), computed on the outcome. Estimates at h/2 and 2h are
shown for sensitivity. The manipulation check compares observation counts
just below and just above the cutoff (a simple binomial stand-in for the
McCrary test).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from estimators.common import Z_95, MethodResult, format_summary, normal_inference
from utils.i18n import LocalizedError, Msg

MIN_OBS_PER_SIDE = 10
C_TRIANGULAR = 3.4375
INFERENCES = ("conventional", "robust")
# What the app reports by default. A validation study (spike/estimator_validation.py,
# 1,000 worlds) found the conventional CI under-covers in small samples (91.6% at
# n = 400) and the robust bias-corrected CI does not (93.8%), as Calonico, Cattaneo
# & Titiunik (2014) predict. The function default stays "conventional", the
# rdrobust "Conventional" row that the reference tests compare.
APP_INFERENCE = "robust"
WEAK_FIRST_STAGE_F = 10.0


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


# --------------------------------------------------------------------------
# Local polynomial core (one side at a time, as rdrobust)
# --------------------------------------------------------------------------
def _triangular(u: np.ndarray, bandwidth: float) -> np.ndarray:
    return np.where(np.abs(u) <= 1, (1 - np.abs(u)) / bandwidth, 0.0)


def _side(x: np.ndarray, d: np.ndarray, cutoff: float, h: float, b: float, p: int = 1) -> dict:
    """Fits for one side. `d` holds the outcome (and the treatment, fuzzy) as columns."""
    q = p + 1
    u = (x - cutoff) / h
    w_h, w_b = _triangular(u, h), _triangular((x - cutoff) / b, b)
    keep = (w_h > 0) if h > b else (w_b > 0)
    x, d, u, w_h, w_b = x[keep], d[keep], u[keep], w_h[keep], w_b[keep]
    n = len(x)
    r_q = np.vander(x - cutoff, q + 1, increasing=True)
    r_p = r_q[:, :p + 1]
    rw_p = r_p * w_h[:, None]
    inv_g_p = np.linalg.inv(r_p.T @ rw_p)
    inv_g_q = np.linalg.inv(r_q.T @ (r_q * w_b[:, None]))
    beta_p = inv_g_p @ rw_p.T @ d
    beta_q = inv_g_q @ (r_q * w_b[:, None]).T @ d
    # Bias-corrected weights: the p-th order fit minus h^(p+1) times the
    # estimated (p+1)-th derivative term (CCT 2014, rdrobust's Q_q).
    m = (r_q @ inv_g_q[p + 1, :]) * w_b
    big_l = rw_p.T @ u ** (p + 1)
    q_q = rw_p - h ** (p + 1) * np.outer(m, big_l)
    beta_bc = inv_g_p @ q_q.T @ d
    res_h = np.sqrt(n / (n - (p + 1))) * (d - r_p @ beta_p)       # HC1, per side
    res_b = np.sqrt(n / (n - (q + 1))) * (d - r_q @ beta_q)
    return dict(beta_p=beta_p, beta_bc=beta_bc, inv_g_p=inv_g_p, rw_p=rw_p, q_q=q_q, res_h=res_h, res_b=res_b,
                n_h=int((w_h > 0).sum()))


def _variance(side: dict, s: np.ndarray, robust: bool) -> float:
    design, res = (side["q_q"], side["res_b"]) if robust else (side["rw_p"], side["res_h"])
    score = design * (res @ s)[:, None]
    v = side["inv_g_p"] @ score.T @ score @ side["inv_g_p"]
    return float(v[0, 0])


def rd_fit(x: np.ndarray, y: np.ndarray, cutoff: float, h: float, treatment: np.ndarray | None = None,
           b: float | None = None) -> dict:
    """Conventional and robust bias-corrected RD estimates at bandwidth h
    (bias bandwidth b, default h), sharp or fuzzy."""
    b = h if b is None else b
    d = np.column_stack([y] if treatment is None else [y, treatment]).astype(float)
    below, above = x < cutoff, x >= cutoff
    sides = [_side(x[below], d[below], cutoff, h, b), _side(x[above], d[above], cutoff, h, b)]
    left, right = sides
    n_left, n_right = left["n_h"], right["n_h"]
    if n_left < MIN_OBS_PER_SIDE or n_right < MIN_OBS_PER_SIDE:
        raise LocalizedError("err.rdd_bandwidth_sides", h=h, cutoff=cutoff, left=n_left, right=n_right,
                             minimum=MIN_OBS_PER_SIDE)
    jump = right["beta_p"][0] - left["beta_p"][0]          # per column: Y, and D if fuzzy
    jump_bc = right["beta_bc"][0] - left["beta_bc"][0]
    if treatment is None:
        s = np.array([1.0])
        tau, tau_bc = float(jump[0]), float(jump_bc[0])
        first_stage = None
    else:
        if abs(jump[1]) < 1e-12:
            raise LocalizedError("err.rdd_no_first_stage")
        s = np.array([1 / jump[1], -jump[0] / jump[1] ** 2])          # delta method
        tau = float(jump[0] / jump[1])
        tau_bc = float(tau - s @ (jump - jump_bc))
        t_se = np.sqrt(sum(_variance(side, np.array([0.0, 1.0]), robust=False) for side in sides))
        first_stage = dict(jump=float(jump[1]), se=float(t_se), f=float((jump[1] / t_se) ** 2))
    se = np.sqrt(sum(_variance(side, s, robust=False) for side in sides))
    se_rb = np.sqrt(sum(_variance(side, s, robust=True) for side in sides))
    p_rb = float(2 * stats.norm.sf(abs(tau_bc / se_rb)))
    return dict(estimate=tau, se=float(se), estimate_bc=tau_bc, se_robust=float(se_rb),
                ci_robust=(tau_bc - Z_95 * se_rb, tau_bc + Z_95 * se_rb), p_robust=p_rb,
                n_left=n_left, n_right=n_right, bias_bandwidth=float(b), first_stage=first_stage,
                fit_left=dict(intercept=float(left["beta_p"][0, 0]), slope=float(left["beta_p"][1, 0])),
                fit_right=dict(intercept=float(right["beta_p"][0, 0]), slope=float(right["beta_p"][1, 0])))


def estimate_rdd(df: pd.DataFrame, outcome_col: str = "Y", running_col: str = "X",
                 cutoff: float = 0.0, bandwidth: float | None = None, treatment_col: str | None = None,
                 inference: str = "conventional", bias_bandwidth: float | None = None) -> MethodResult:
    if inference not in INFERENCES:
        raise LocalizedError("err.rdd_inference", value=inference, allowed=", ".join(INFERENCES))
    columns = [outcome_col, running_col] + ([treatment_col] if treatment_col else [])
    data = df[columns].dropna().astype(float)
    x, y = data[running_col].to_numpy(), data[outcome_col].to_numpy()
    t = data[treatment_col].to_numpy() if treatment_col else None
    n_below, n_above = int((x < cutoff).sum()), int((x >= cutoff).sum())
    if n_below < MIN_OBS_PER_SIDE or n_above < MIN_OBS_PER_SIDE:
        raise LocalizedError("err.rdd_cutoff", cutoff=cutoff, below=n_below, above=n_above,
                             minimum=MIN_OBS_PER_SIDE)

    if bandwidth is not None and bandwidth <= 0:
        raise LocalizedError("err.rdd_bandwidth_positive")
    h = float(bandwidth) if bandwidth is not None else ik_bandwidth(x, y, cutoff)

    fit = rd_fit(x, y, cutoff, h, t, bias_bandwidth)
    estimate = fit["estimate"]
    if inference == "robust":
        se = fit["se_robust"]
        (ci_low, ci_high), p_value = fit["ci_robust"], fit["p_robust"]
    else:
        se = fit["se"]
        ci_low, ci_high, p_value = normal_inference(estimate, se)

    sensitivity = []
    for factor in (0.5, 1.0, 2.0):
        try:
            f = fit if factor == 1.0 else rd_fit(x, y, cutoff, h * factor, t)
            sensitivity.append(dict(bandwidth=h * factor, factor=factor, estimate=f["estimate"], se=f["se"]))
        except (LocalizedError, np.linalg.LinAlgError):
            sensitivity.append(dict(bandwidth=h * factor, factor=factor,
                                    estimate=float("nan"), se=float("nan")))

    warnings: list[Msg] = []
    w = h / 2
    count_below = int(((x >= cutoff - w) & (x < cutoff)).sum())
    count_above = int(((x >= cutoff) & (x < cutoff + w)).sum())
    manipulation_p = float(stats.binomtest(count_above, count_below + count_above, 0.5).pvalue) \
        if count_below + count_above > 0 else float("nan")
    if manipulation_p < 0.05:
        warnings.append(Msg("warn.rdd_manipulation", below=count_below, above=count_above, p=manipulation_p))
    if fit["first_stage"] is not None and fit["first_stage"]["f"] < WEAK_FIRST_STAGE_F:
        warnings.append(Msg("warn.rdd_weak_first_stage", f=fit["first_stage"]["f"],
                            threshold=WEAK_FIRST_STAGE_F))

    design = "fuzzy" if treatment_col else "sharp"
    result = MethodResult(
        method=f"Regression Discontinuity ({design})", key="rdd",
        estimand=Msg("estimand.rdd_fuzzy" if treatment_col else "estimand.rdd"),
        estimate=estimate, se=se, ci_low=ci_low, ci_high=ci_high, p_value=p_value,
        n_obs=fit["n_left"] + fit["n_right"],
        details=dict(
            cutoff=cutoff, bandwidth=h, bandwidth_rule="user" if bandwidth is not None else "Imbens-Kalyanaraman",
            n_left=fit["n_left"], n_right=fit["n_right"], design=design, inference=inference,
            fit_left=fit["fit_left"], fit_right=fit["fit_right"],
            conventional=dict(estimate=estimate, se=fit["se"]),
            robust=dict(estimate_bc=fit["estimate_bc"], se=fit["se_robust"], ci_low=fit["ci_robust"][0],
                        ci_high=fit["ci_robust"][1], p_value=fit["p_robust"], bias_bandwidth=fit["bias_bandwidth"]),
            first_stage=fit["first_stage"],
            sensitivity=pd.DataFrame(sensitivity),
            manipulation=dict(count_below=count_below, count_above=count_above, p_value=manipulation_p),
            plot_data=pd.DataFrame({"x": x, "y": y}),
            notes=Msg("note.rdd_inference_robust" if inference == "robust" else "note.rdd_inference"),
        ),
        warnings=warnings,
    )
    lines = [Msg("summary.rdd.bandwidth", h=h, rule=result.details["bandwidth_rule"], left=fit["n_left"],
                 right=fit["n_right"]),
             Msg("summary.rdd.robust", estimate=fit["estimate_bc"], se=fit["se_robust"],
                 lo=fit["ci_robust"][0], hi=fit["ci_robust"][1], b=fit["bias_bandwidth"]),
             Msg("summary.rdd.sensitivity",
                 values=", ".join(f"{r['factor']:g}h -> {r['estimate']:.3f}" for r in sensitivity))]
    if fit["first_stage"] is not None:
        lines.insert(1, Msg("summary.rdd.first_stage", jump=fit["first_stage"]["jump"], se=fit["first_stage"]["se"],
                            f=fit["first_stage"]["f"]))
    result.summary_text = format_summary(result, lines)
    return result
