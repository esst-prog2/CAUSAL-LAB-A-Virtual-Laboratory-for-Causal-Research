"""
Synthetic Control estimator (Abadie, Diamond & Hainmueller 2010).

The counterfactual for a single treated unit is a convex combination
of untreated donor units, with weights w (w_j >= 0, sum w_j = 1)
chosen to reproduce the treated unit's pre-treatment outcome path:

    min_w || y1_pre - Y0_pre w ||^2

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
from scipy.optimize import minimize

from estimators.common import MethodResult, format_summary


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


def _rmspe(gaps: np.ndarray) -> float:
    return float(np.sqrt(np.mean(gaps ** 2)))


def estimate_synthetic_control(df: pd.DataFrame, unit_col: str = "unit", period_col: str = "period",
                               outcome_col: str = "Y", treated_unit=None,
                               treatment_period=None) -> MethodResult:
    if treated_unit is None or treatment_period is None:
        raise ValueError("Synthetic control requires a treated unit and a first treated period.")
    data = df[[unit_col, period_col, outcome_col]].dropna()
    if data.duplicated([unit_col, period_col]).any():
        raise ValueError("Each (unit, period) pair must appear once: the panel has duplicate rows.")
    wide = data.pivot(index=period_col, columns=unit_col, values=outcome_col).sort_index()
    if treated_unit not in wide.columns:
        raise ValueError(f"Treated unit '{treated_unit}' is not in the '{unit_col}' column.")
    if wide.isna().any().any():
        raise ValueError("The panel must be balanced: every unit needs an outcome in every period.")

    periods = wide.index.to_numpy()
    pre = periods < treatment_period
    if pre.sum() < 2 or (~pre).sum() < 1:
        raise ValueError(f"Need at least 2 pre-treatment periods and 1 post-treatment period "
                         f"(found {int(pre.sum())} before and {int((~pre).sum())} from {treatment_period}).")
    donors = [u for u in wide.columns if u != treated_unit]
    if len(donors) < 2:
        raise ValueError("Synthetic control needs at least two donor units.")

    def run(treated, pool):
        y1 = wide[treated].to_numpy(float)
        y0 = wide[pool].to_numpy(float)
        w, ok = _fit_weights(y1[pre], y0[pre])
        synthetic = y0 @ w
        gaps = y1 - synthetic
        pre_rmspe, post_rmspe = _rmspe(gaps[pre]), _rmspe(gaps[~pre])
        return dict(weights=w, synthetic=synthetic, gaps=gaps, ok=ok,
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
        warnings.append("The weight optimizer did not report convergence; weights may be slightly suboptimal.")
    outcome_sd = float(np.std(wide[treated_unit].to_numpy()[pre]))
    if outcome_sd > 0 and main["pre_rmspe"] > 0.5 * outcome_sd:
        warnings.append(f"Poor pre-treatment fit: RMSPE = {main['pre_rmspe']:.3f}, more than half the "
                        f"treated unit's pre-treatment outcome SD. The treated unit may lie outside "
                        f"the donors' convex hull.")

    weights = pd.DataFrame({"donor": donors, "weight": main["weights"]}) \
        .sort_values("weight", ascending=False).reset_index(drop=True)
    paths = pd.DataFrame({"period": periods, "treated": wide[treated_unit].to_numpy(float),
                          "synthetic": main["synthetic"], "gap": main["gaps"]})
    result = MethodResult(
        method="Synthetic Control",
        estimand="Mean post-treatment effect on the treated unit",
        estimate=estimate, se=None, ci_low=None, ci_high=None, p_value=p_value,
        n_obs=int(wide.size),
        details=dict(
            weights=weights, paths=paths,
            placebo_gaps=pd.DataFrame(placebo_gaps, index=periods),
            pre_rmspe=main["pre_rmspe"], post_rmspe=main["post_rmspe"], rmspe_ratio=main["ratio"],
            n_donors=len(donors), treatment_period=treatment_period, treated_unit=treated_unit,
        ),
        warnings=warnings,
    )
    top = weights[weights["weight"] > 0.01]
    result.summary_text = format_summary(result, [
        f"Pre-treatment RMSPE = {main['pre_rmspe']:.4f}, post/pre RMSPE ratio = {main['ratio']:.2f}",
        f"Placebo p-value over {len(donors) + 1} units",
        "Donor weights > 0.01: " + ", ".join(f"{r.donor}={r.weight:.3f}" for r in top.itertuples()),
    ])
    return result
