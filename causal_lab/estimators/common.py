"""
Shared result type for the Causal Methods estimators (RCT, Matching,
IV, RDD, Synthetic Control, DML).

Every estimator returns a `MethodResult` so the Causal Methods page can
render any of them with the same metric row and warning list; anything
method-specific (balance tables, effect paths, sensitivity tables)
lives in `details`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import stats

from utils.i18n import LocalizedError, Msg

Z_95 = float(stats.norm.ppf(0.975))


@dataclass
class MethodResult:
    method: str
    estimand: Msg | str
    estimate: float
    se: float | None
    ci_low: float | None
    ci_high: float | None
    p_value: float | None
    n_obs: int
    details: dict = field(default_factory=dict)
    warnings: list[Msg] = field(default_factory=list)
    summary_text: str = ""
    key: str = ""                     # locale key suffix: method.<key>


def normal_inference(estimate: float, se: float) -> tuple[float, float, float]:
    """95% normal-approximation CI and two-sided p-value."""
    if not np.isfinite(se) or se <= 0:
        return float("nan"), float("nan"), float("nan")
    z = estimate / se
    p_value = float(2 * stats.norm.sf(abs(z)))
    return estimate - Z_95 * se, estimate + Z_95 * se, p_value


def format_summary(result: MethodResult, extra_lines: list[str] | None = None) -> str:
    lines = [f"{result.method} — {result.estimand} = {result.estimate:.4f}"]
    if result.se is not None:
        lines.append(f"SE = {result.se:.4f}, 95% CI = [{result.ci_low:.4f}, {result.ci_high:.4f}], "
                     f"p = {result.p_value:.4f}")
    if result.p_value is not None and result.se is None:
        lines.append(f"Permutation p-value = {result.p_value:.4f}")
    lines.append(f"N = {result.n_obs}")
    lines.extend(extra_lines or [])
    return "\n".join(lines)


def require_binary(series, name: str) -> None:
    """Raise ValueError unless `series` is coded 0/1 with both values present."""
    values = set(np.unique(series.dropna()))
    if not values <= {0, 1} or len(values) < 2:
        raise LocalizedError("err.treatment_not_binary", column=name, values=sorted(values)[:10])


def standardized_difference(x_treated, x_control) -> float:
    """Standardized mean difference using the pooled standard deviation."""
    pooled_sd = np.sqrt((np.var(x_treated, ddof=1) + np.var(x_control, ddof=1)) / 2)
    if pooled_sd == 0:
        return 0.0
    return float((np.mean(x_treated) - np.mean(x_control)) / pooled_sd)
