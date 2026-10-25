"""
Synthetic Control estimator (Abadie, Diamond & Hainmueller 2010).

The counterfactual for a single treated unit is a convex combination
of untreated donor units, with weights w (w_j >= 0, sum w_j = 1).

Without covariates, w reproduces the treated unit's pre-treatment outcome
path:

    min_w || y1_pre - Y0_pre w ||^2

With covariates, w matches predictors instead: the pre-treatment mean of
each covariate and of the outcome, each standardized by its standard
deviation across units (as R Synth). For a diagonal predictor-importance
matrix V,

    w(V) = argmin_w (x1 - X0 w)' V (x1 - X0 w),

and V is chosen to minimize the pre-treatment outcome MSPE of w(V) (ADH
2010). That outer problem is not convex: it is searched by Nelder-Mead on
the simplex of V from k + 1 starts (equal weights, then each predictor
dominant in turn), keeping the best.

The effect in each period is the gap y1_t - Y0_t w; the headline
estimate is the mean post-treatment gap.

Inference is by placebo-in-space permutation: every donor in turn is
treated as if it were the treated unit, and the p-value is the share
of units (treated included) whose post/pre RMSPE ratio is at least as
large as the treated unit's. No standard error is reported.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize, nnls

from estimators.common import MethodResult, format_summary
from utils.i18n import LocalizedError, Msg


def _fit_weights(y1_pre: np.ndarray, y0_pre: np.ndarray) -> tuple[np.ndarray, bool]:
    n_donors = y0_pre.shape[1]

    def loss(w):
        r = y1_pre - y0_pre @ w
        return r @ r

    def grad(w):
        return -2 * y0_pre.T @ (y1_pre - y0_pre @ w)

    res = minimize(loss, np.full(n_donors, 1 / n_donors), jac=grad, method="SLSQP",
                   bounds=[(0.0, 1.0)] * n_donors,
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1,
                                 "jac": lambda w: np.ones_like(w)}],
                   options={"maxiter": 500, "ftol": 1e-12})
    w = np.clip(res.x, 0, None)
    return w / w.sum(), bool(res.success)


# With fewer predictors than donors the predictor fit has many exact solutions,
# and different NNLS implementations pick different ones (scipy 1.15 and 1.17
# disagreed on 14 of 300 test problems). A tiny ridge term makes the solution
# unique, so every correct solver returns the same weights (identical across
# scipy 1.15-1.17 on those problems); its penalty, 1e-6 * |w|^2, is negligible.
RIDGE = 1e-3


def _simplex_weights(x1: np.ndarray, x0: np.ndarray, v: np.ndarray) -> np.ndarray:
    """argmin_w (x1 - x0 w)' diag(v) (x1 - x0 w) + RIDGE^2 |w|^2 on the simplex:
    non-negative least squares with the sum-to-one constraint as a heavily
    weighted row. Needs scipy >= 1.15, whose rewritten NNLS does not stall."""
    root_v = np.sqrt(v)
    n_donors = x0.shape[1]
    penalty = 1e4 * (1 + np.abs(x0).max())
    a = np.vstack([root_v[:, None] * x0, RIDGE * np.eye(n_donors), np.full((1, n_donors), penalty)])
    b = np.concatenate([root_v * x1, np.zeros(n_donors), [penalty]])
    w = nnls(a, b, maxiter=50 * n_donors)[0]
    return w / w.sum()


def _fit_weights_with_predictors(x1: np.ndarray, x0: np.ndarray, y1_pre: np.ndarray,
                                 y0_pre: np.ndarray) -> tuple[np.ndarray, np.ndarray, bool]:
    """(w, v, converged) for standardized predictors x1 (k,), x0 (k, J)."""
    k = len(x1)

    def v_of(theta):                     # softmax: positive, sums to one
        e = np.exp(theta - theta.max())
        return e / e.sum()

    def mspe(theta):
        r = y1_pre - y0_pre @ _simplex_weights(x1, x0, v_of(theta))
        return float(r @ r) / len(r)

    # Equal V, then each predictor dominant in turn (the outcome predictor is last).
    starts = [np.zeros(k)] + [3.0 * np.eye(k)[j] for j in range(k)]
    best = min((minimize(mspe, s, method="Nelder-Mead",
                         options={"maxiter": 400 * k, "xatol": 1e-6, "fatol": 1e-12}) for s in starts),
               key=lambda r: r.fun)
    v = v_of(best.x)
    return _simplex_weights(x1, x0, v), v, bool(best.success)


def _rmspe(gaps: np.ndarray) -> float:
    return float(np.sqrt(np.mean(gaps ** 2)))


def estimate_synthetic_control(df: pd.DataFrame, unit_col: str = "unit", period_col: str = "period",
                               outcome_col: str = "Y", treated_unit=None,
                               treatment_period=None, covariate_cols: list[str] | None = None) -> MethodResult:
    if treated_unit is None or treatment_period is None:
        raise LocalizedError("err.sc_needs_unit_period")
    covariate_cols = list(covariate_cols or [])
    data = df[[unit_col, period_col, outcome_col] + covariate_cols].dropna()
    if data.duplicated([unit_col, period_col]).any():
        raise LocalizedError("err.sc_duplicates")
    wide = data.pivot(index=period_col, columns=unit_col, values=outcome_col).sort_index()
    if treated_unit not in wide.columns:
        raise LocalizedError("err.sc_unknown_unit", unit=treated_unit, column=unit_col)
    if wide.isna().any().any():
        raise LocalizedError("err.sc_unbalanced")

    periods = wide.index.to_numpy()
    pre = periods < treatment_period
    if pre.sum() < 2 or (~pre).sum() < 1:
        raise LocalizedError("err.sc_periods", before=int(pre.sum()), after=int((~pre).sum()),
                             period=treatment_period)
    donors = [u for u in wide.columns if u != treated_unit]
    if len(donors) < 2:
        raise LocalizedError("err.sc_donors")

    # Predictors: pre-treatment means of the covariates and of the outcome, per unit.
    predictor_names = covariate_cols + ([outcome_col] if covariate_cols else [])
    if covariate_cols:
        pre_rows = data[data[period_col] < treatment_period]
        raw = pre_rows.groupby(unit_col)[predictor_names].mean().T[wide.columns]       # k x units
        scale = raw.std(axis=1, ddof=1).replace(0, 1.0)
        predictors = raw.div(scale, axis=0)

    def run(treated, pool):
        y1 = wide[treated].to_numpy(float)
        y0 = wide[pool].to_numpy(float)
        if covariate_cols:
            w, v, ok = _fit_weights_with_predictors(predictors[treated].to_numpy(float),
                                                    predictors[pool].to_numpy(float), y1[pre], y0[pre])
        else:
            (w, ok), v = _fit_weights(y1[pre], y0[pre]), None
        synthetic = y0 @ w
        gaps = y1 - synthetic
        pre_rmspe, post_rmspe = _rmspe(gaps[pre]), _rmspe(gaps[~pre])
        return dict(weights=w, v=v, synthetic=synthetic, gaps=gaps, ok=ok,
                    pre_rmspe=pre_rmspe, post_rmspe=post_rmspe,
                    ratio=post_rmspe / max(pre_rmspe, 1e-12))

    main = run(treated_unit, donors)
    estimate = float(main["gaps"][~pre].mean())

    placebo_gaps = {}
    ratios = [main["ratio"]]
    for donor in donors:
        placebo = run(donor, [u for u in donors if u != donor])
        placebo_gaps[donor] = placebo["gaps"]
        ratios.append(placebo["ratio"])
    p_value = float(np.mean(np.array(ratios) >= main["ratio"]))

    warnings: list[str] = []
    if not main["ok"]:
        warnings.append(Msg("warn.sc_convergence"))
    outcome_sd = float(np.std(wide[treated_unit].to_numpy()[pre]))
    if outcome_sd > 0 and main["pre_rmspe"] > 0.5 * outcome_sd:
        warnings.append(Msg("warn.sc_fit", rmspe=main["pre_rmspe"]))

    weights = pd.DataFrame({"donor": donors, "weight": main["weights"]}) \
        .sort_values("weight", ascending=False).reset_index(drop=True)
    paths = pd.DataFrame({"period": periods, "treated": wide[treated_unit].to_numpy(float),
                          "synthetic": main["synthetic"], "gap": main["gaps"]})
    predictor_table = None
    if covariate_cols:
        predictor_table = pd.DataFrame({
            "predictor": predictor_names,
            "treated": raw[treated_unit].to_numpy(float),
            "synthetic": raw[donors].to_numpy(float) @ main["weights"],
            "donor_mean": raw[donors].mean(axis=1).to_numpy(float),
            "v_weight": main["v"],
        })
    result = MethodResult(
        method="Synthetic Control", key="synthetic_control",
        estimand=Msg("estimand.sc"),
        estimate=estimate, se=None, ci_low=None, ci_high=None, p_value=p_value,
        n_obs=int(wide.size),
        details=dict(
            weights=weights, paths=paths,
            placebo_gaps=pd.DataFrame(placebo_gaps, index=periods),
            pre_rmspe=main["pre_rmspe"], post_rmspe=main["post_rmspe"], rmspe_ratio=main["ratio"],
            n_donors=len(donors), treatment_period=treatment_period, treated_unit=treated_unit,
            covariates=covariate_cols, predictors=predictor_table,
        ),
        warnings=warnings,
    )
    top = weights[weights["weight"] > 0.01]
    lines = [Msg("summary.sc.rmspe", pre=main["pre_rmspe"], ratio=main["ratio"]),
             Msg("summary.sc.placebo", units=len(donors) + 1),
             Msg("summary.sc.weights", weights=", ".join(f"{r.donor}={r.weight:.3f}" for r in top.itertuples()))]
    if covariate_cols:
        lines.append(Msg("summary.sc.predictors", predictors=", ".join(
            f"{name}={v:.3f}" for name, v in zip(predictor_names, main["v"]))))
    result.summary_text = format_summary(result, lines)
    return result
