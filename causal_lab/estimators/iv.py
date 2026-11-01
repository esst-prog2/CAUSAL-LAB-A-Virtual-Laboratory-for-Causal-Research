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

The Wald interval of 2SLS is unreliable when the instrument is weak, and with
one instrument 2SLS has no finite mean. The Anderson-Rubin (1949) confidence
set does not depend on instrument strength: it collects every beta0 for which
the excluded instruments do not predict Y - beta0 D (heteroskedasticity-robust
Wald test, as recommended by Andrews, Stock & Sun 2019). With one instrument
it is solved exactly from a quadratic inequality; it can be an interval, two
unbounded rays, or the whole line when the instrument carries no information.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import optimize, stats
from linearmodels.iv import IV2SLS

from estimators.common import MethodResult, format_summary
from utils.i18n import LocalizedError, Msg

WEAK_INSTRUMENT_F = 10.0
AR_LEVEL = 0.95


def _ar_pieces(y: np.ndarray, d: np.ndarray, x: np.ndarray, k: int):
    """Coefficients of the k excluded instruments (the last k columns of x) in
    the regressions of y and of d on x, and the HC0 sandwich pieces such that
    Var(gamma_y - b gamma_d) = S_yy - b (S_yd + S_yd') + b^2 S_dd."""
    bread = np.linalg.pinv(x.T @ x)
    a = (bread @ x.T)[-k:]                       # k x n: the instruments' rows of (X'X)^-1 X'
    g_y, g_d = a @ y, a @ d
    u_y = y - x @ (bread @ x.T @ y)
    u_d = d - x @ (bread @ x.T @ d)
    s_yy = (a * u_y ** 2) @ a.T
    s_yd = (a * (u_y * u_d)) @ a.T
    s_dd = (a * u_d ** 2) @ a.T
    return g_y, g_d, s_yy, s_yd, s_dd


def anderson_rubin_stat(pieces, b0: float) -> float:
    g_y, g_d, s_yy, s_yd, s_dd = pieces
    g = g_y - b0 * g_d
    v = s_yy - b0 * (s_yd + s_yd.T) + b0 ** 2 * s_dd
    return float(g @ np.linalg.solve(v, g))


def anderson_rubin_set(y, d, x, k: int, level: float = AR_LEVEL, center: float = 0.0, scale: float = 1.0) -> dict:
    """Anderson-Rubin confidence set for the coefficient of d, and the AR p-value of b = 0.

    kind: "interval" (lo, hi), "rays" (-inf, lo] and [hi, +inf), "line" (every value),
    or "empty" (no value: the instruments reject every b, a sign of misspecification)."""
    pieces = _ar_pieces(np.asarray(y, float), np.asarray(d, float), np.asarray(x, float), k)
    crit = float(stats.chi2.ppf(level, k))
    p0 = float(stats.chi2.sf(anderson_rubin_stat(pieces, 0.0), k))
    if k == 1:
        g_y, g_d, s_yy, s_yd, s_dd = (float(np.ravel(v)[0]) for v in pieces)
        a2 = g_d ** 2 - crit * s_dd
        a1 = -2 * g_y * g_d + 2 * crit * s_yd
        a0 = g_y ** 2 - crit * s_yy
        disc = a1 ** 2 - 4 * a2 * a0
        if abs(a2) < 1e-14 * max(1.0, abs(a1), abs(a0)):
            return {"kind": "rays", "low": -np.inf, "high": np.inf, "p_zero": p0}
        if disc < 0:
            return {"kind": "empty" if a2 > 0 else "line", "low": np.nan, "high": np.nan, "p_zero": p0}
        r1, r2 = sorted(((-a1 - np.sqrt(disc)) / (2 * a2), (-a1 + np.sqrt(disc)) / (2 * a2)))
        return {"kind": "interval" if a2 > 0 else "rays", "low": float(r1), "high": float(r2), "p_zero": p0}
    # Several instruments: invert the test on a grid around the 2SLS estimate, refine the bounds.
    grid = center + scale * np.linspace(-200, 200, 8001)
    accept = np.array([anderson_rubin_stat(pieces, b) <= crit for b in grid])
    if not accept.any():
        return {"kind": "empty", "low": np.nan, "high": np.nan, "p_zero": p0}
    if accept[0] or accept[-1]:
        return {"kind": "line" if accept.all() else "rays", "low": np.nan, "high": np.nan, "p_zero": p0}
    f = lambda b: anderson_rubin_stat(pieces, b) - crit                     # noqa: E731
    i, j = int(np.argmax(accept)), len(accept) - 1 - int(np.argmax(accept[::-1]))
    lo = optimize.brentq(f, grid[i - 1], grid[i]) if i > 0 else grid[i]
    hi = optimize.brentq(f, grid[j], grid[j + 1]) if j < len(grid) - 1 else grid[j]
    kind = "interval" if accept[i:j + 1].all() else "union"
    return {"kind": kind, "low": float(lo), "high": float(hi), "p_zero": p0}


def estimate_iv(df: pd.DataFrame, outcome_col: str = "Y", treatment_col: str = "D",
                instrument_cols: list[str] | None = None,
                control_cols: list[str] | None = None) -> MethodResult:
    instrument_cols = list(instrument_cols or [])
    control_cols = list(control_cols or [])
    if not instrument_cols:
        raise LocalizedError("err.iv_needs_instrument")
    data = df[[outcome_col, treatment_col] + instrument_cols + control_cols].dropna().astype(float)
    if data[treatment_col].nunique() < 2:
        raise LocalizedError("err.no_variation", column=treatment_col)
    # Constant, treatment and controls are estimated; with no residual degree
    # of freedom the robust covariance divides by zero.
    minimum = len(control_cols) + max(len(instrument_cols), 1) + 2
    if len(data) <= minimum:
        raise LocalizedError("err.iv_too_few", n=len(data), minimum=minimum + 1)

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
    x_ar = np.column_stack([exog.to_numpy(float), data[instrument_cols].to_numpy(float)])
    ar = anderson_rubin_set(data[outcome_col].to_numpy(float), data[treatment_col].to_numpy(float), x_ar,
                            len(instrument_cols), center=estimate, scale=max(se, 1e-8))

    warnings: list[str] = []
    if first_stage_f < WEAK_INSTRUMENT_F:
        warnings.append(Msg("warn.weak_instrument", f=first_stage_f, threshold=WEAK_INSTRUMENT_F))

    result = MethodResult(
        method="Instrumental Variables (2SLS)", key="iv",
        estimand=Msg("estimand.iv"),
        estimate=estimate, se=se, ci_low=float(ci["lower"]), ci_high=float(ci["upper"]),
        p_value=float(fitted.pvalues[treatment_col]),
        n_obs=int(fitted.nobs),
        details=dict(
            first_stage_f=first_stage_f, first_stage_coefs=first_stage_coefs,
            partial_r2=float(diag["partial.rsquared"]),
            ols_estimate=float(ols.params[treatment_col]), ols_se=float(ols.bse[treatment_col]),
            instruments=instrument_cols, controls=control_cols,
            ar_kind=ar["kind"], ar_low=ar["low"], ar_high=ar["high"], ar_p_zero=ar["p_zero"],
        ),
        warnings=warnings,
    )
    result.summary_text = format_summary(result, [
        Msg("summary.iv.first_stage", f=first_stage_f, r2=result.details["partial_r2"]),
        Msg("summary.iv.ols", value=result.details["ols_estimate"], se=result.details["ols_se"]),
        _ar_line(ar),
    ])
    return result


def _ar_line(ar: dict) -> Msg:
    if ar["kind"] == "interval":
        return Msg("summary.iv.ar_interval", lo=ar["low"], hi=ar["high"], p=ar["p_zero"])
    if ar["kind"] == "rays" and np.isfinite(ar["low"]):
        return Msg("summary.iv.ar_rays", lo=ar["low"], hi=ar["high"], p=ar["p_zero"])
    return Msg(f"summary.iv.ar_{'rays_unknown' if ar['kind'] == 'rays' else ar['kind']}", p=ar["p_zero"])
