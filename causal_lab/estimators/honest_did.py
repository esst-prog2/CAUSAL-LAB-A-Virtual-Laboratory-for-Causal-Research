"""
Sensitivity of an event-study effect to violations of parallel trends
(Rambachan & Roth 2023), under their smoothness restriction Delta^SD(M).

Write the event-study coefficients as beta = delta + (0, tau): delta is the
difference in trends that is not caused by the treatment, tau the effect in
each post-treatment period. Parallel trends says delta = 0. Delta^SD(M) only
asks that delta bend little: its second differences stay within M,

    | (delta_{t+1} - delta_t) - (delta_t - delta_{t-1}) | <= M  for every t,

with delta = 0 in the reference period (k = -1). M = 0 allows exactly the
linear trends, extrapolated from the pre-periods; larger M allows the trend
to curve after treatment by up to M per period.

The target is theta = l' tau, by default the mean of the post-treatment
effects. The interval is the fixed-length confidence interval (FLCI) of
Rambachan & Roth (2023, Section 4.1), from Armstrong & Kolesar (2018):
among the estimators theta_hat = l' beta_post + w' beta_pre, take the one
whose interval

    theta_hat +/- sigma_w * cv(b_w / sigma_w)

is shortest, where sigma_w is its standard error, b_w its largest bias over
Delta^SD(M), and cv(t) the 1 - alpha quantile of |N(t, 1)|. Once w removes
linear trends, the deviation is a linear function of its second differences,
each in [-M, M], so b_w = M * ||B' c||_1 exactly (_max_bias). The bias is
finite only if w removes linear trends, so w is searched in that subspace.
The interval covers theta with probability at least 1 - alpha for every
delta in Delta^SD(M). Inference is normal, as in the paper.

One deviation from the paper, for small samples. The paper picks w with the
estimated covariance of beta. With 30 treated units and 19 coefficients that
estimate is noisy, and the w that minimises the *estimated* variance fits its
noise: on 200 study worlds the M = 0 interval then covered 88.5%. Here w is
picked with a working covariance that the outcomes do not shape (independent
errors: Cov(Y_t - Y_ref, Y_s - Y_ref) proportional to 1 + [t = s] in each
group, scaled once to the estimated variances), and the standard error of the
chosen estimator is then estimated from the units. The interval keeps its
guarantee; it may be a little longer than the paper's.

Scope: one treatment date and a balanced panel (problem_from_panel), where the
event-study coefficients are two-group differences and their covariance is
estimated from the units. Validated (tests/test_honest_did.py,
spike/honest_did_validation.py): the worst-case bias equals a linear program;
M = 0 gives the closed-form linear extrapolation; at the worst case of
Delta^SD(M) the interval covers 95.0%, 94.9% and 94.9% at M = 0, 0.02 and
0.05 (100,000 draws); and on the study's worlds with diverging pre-trends,
which are linear, the M = 0 interval covers the true effect 94.9% of the time
at the none, low and medium levels, where the plain DiD interval covers 94.9%,
31.3% and 0.0% (1,000 worlds per level).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import optimize, stats
from scipy.linalg import null_space

from utils.i18n import LocalizedError

ALPHA = 0.05


def critical_value(t: float, alpha: float = ALPHA) -> float:
    """1 - alpha quantile of |N(t, 1)|: the c solving Phi(c - t) - Phi(-c - t) = 1 - alpha."""
    t = abs(t)
    f = lambda c: stats.norm.cdf(c - t) - stats.norm.cdf(-c - t) - (1 - alpha)      # noqa: E731
    return float(optimize.brentq(f, 0.0, t + 10.0))


@dataclass
class _Problem:
    pre: np.ndarray               # relative periods before treatment, without the reference (sorted)
    post: np.ndarray              # relative periods from 0 on (sorted)
    beta: np.ndarray              # (pre, post) coefficients
    sigma: np.ndarray             # their covariance, estimated: gives the standard error
    l: np.ndarray                 # target weights on the post periods
    sigma_work: np.ndarray | None = None    # covariance used to choose w (default: sigma)


def _second_difference_basis(n_pre: int, n_post: int) -> np.ndarray:
    """B with delta = B d: the deviation path over (pre, reference, post) whose
    second differences are d, with delta = 0 at the reference and no slope
    there (delta_0 = delta_-1 = 0 when there is a post period). Linear trends
    are left out: the estimators considered do not see them."""
    n = n_pre + 1 + n_post
    ref = n_pre
    eq = np.zeros((n, n))
    eq[0, ref] = 1.0                                      # delta_ref = 0
    eq[1, ref + 1] = 1.0                                  # slope at the reference: delta_0 - delta_ref = 0
    eq[1, ref] = -1.0
    for i in range(1, n - 1):                             # second differences
        eq[i + 1, i - 1:i + 2] = (1.0, -2.0, 1.0)
    rhs = np.zeros((n, n - 2))
    rhs[2:, :] = np.eye(n - 2)
    return np.linalg.solve(eq, rhs)


def _max_bias(problem: _Problem, w: np.ndarray, m: float) -> float:
    """max over delta in Delta^SD(M) of |w' delta_pre + l' delta_post|, exactly: M * ||B' c||_1.
    Infinite unless w removes linear trends."""
    c = np.concatenate([w, [0.0], problem.l])
    periods = np.concatenate([problem.pre, [-1.0], problem.post])
    if abs(float(c @ (periods + 1.0))) > 1e-9 * (1.0 + np.abs(c).sum()):
        return np.inf
    b = _second_difference_basis(len(problem.pre), len(problem.post))
    return float(m * np.abs(b.T @ c).sum())


def _linear_trend_constraint(problem: _Problem) -> tuple[np.ndarray, np.ndarray]:
    """w must satisfy sum_k w_k (k + 1) + sum_t l_t (t + 1) = 0 (delta_t = c (t + 1) has zero bias).
    Returns a particular solution and a basis of the solutions' directions."""
    g = problem.pre + 1.0
    target = -float(problem.l @ (problem.post + 1.0))
    particular = g * target / float(g @ g)
    return particular, null_space(g[None, :])


@dataclass
class FLCI:
    m: float
    estimate: float              # l' beta_post + w' beta_pre at the optimal w
    se: float
    max_bias: float
    ci_low: float
    ci_high: float
    weights_pre: dict[int, float]


def flci(problem: _Problem, m: float, alpha: float = ALPHA) -> FLCI:
    particular, basis = _linear_trend_constraint(problem)
    work = problem.sigma if problem.sigma_work is None else problem.sigma_work

    def parts(z, cov=work):
        w = particular + basis @ z if basis.size else particular
        v = np.concatenate([w, problem.l])
        sd = float(np.sqrt(v @ cov @ v))
        return w, v, sd

    def half_length(z):
        w, _, sd = parts(z)
        bias = _max_bias(problem, w, m)
        if not np.isfinite(bias) or sd <= 0:
            return 1e300
        return sd * critical_value(bias / sd, alpha)

    z0 = np.zeros(basis.shape[1]) if basis.size else np.zeros(0)
    if z0.size:
        # The minimum-variance w that removes linear trends, in closed form: the M = 0
        # optimum (bias 0), and the start of the search when M > 0.
        n_pre = len(problem.pre)
        s_pp, s_pq = work[:n_pre, :n_pre], work[:n_pre, n_pre:]
        g = problem.pre + 1.0
        target = -float(problem.l @ (problem.post + 1.0))
        inv_g = np.linalg.solve(s_pp, g)
        inv_q = np.linalg.solve(s_pp, s_pq @ problem.l)
        w_star = inv_g * (target + g @ inv_q) / (g @ inv_g) - inv_q
        z0 = basis.T @ (w_star - particular)          # basis is orthonormal and w_star - particular lies in it
        if m > 0:
            z0 = optimize.minimize(half_length, z0, method="Nelder-Mead",
                                   options={"xatol": 1e-9, "fatol": 1e-12, "maxiter": 4000}).x
    w, v, sd = parts(z0, problem.sigma)                 # the standard error of the chosen estimator
    bias = _max_bias(problem, w, m)
    est = float(v @ problem.beta)
    half = sd * critical_value(bias / sd, alpha)
    return FLCI(m=float(m), estimate=est, se=sd, max_bias=bias, ci_low=est - half, ci_high=est + half,
                weights_pre={int(k): float(x) for k, x in zip(problem.pre, w)})


def problem_from_panel(df: pd.DataFrame, treatment_period: int, outcome_col: str = "Y", unit_col: str = "unit",
                       period_col: str = "period", treated_col: str = "treated_unit",
                       target: str = "average") -> _Problem:
    """Event-study coefficients and their covariance, from the units themselves.

    With one treatment date and a balanced panel, the event-study coefficient of
    period t (reference t0 - 1) is exactly a difference between two groups,

        beta_t = mean_treated(Y_t - Y_ref) - mean_control(Y_t - Y_ref)

    (it equals estimators.event_study's coefficient to rounding), so the
    covariance of the coefficients is that of two independent samples:
    Cov_treated / n_treated + Cov_control / n_control, with n - 1 divisors.
    The clustered covariance of the event-study regression was tried first:
    on 300 study worlds the M = 0 interval built on it covered 89.3%, its
    standard error averaging 0.240 against an empirical 0.284; built on the
    two-sample covariance it covered 94.9% (1,000 worlds, empirical 0.288,
    mean SE 0.284)."""
    data = df[[unit_col, period_col, outcome_col, treated_col]].dropna()
    wide = data.pivot_table(index=unit_col, columns=period_col, values=outcome_col)
    if wide.isna().any().any():
        raise LocalizedError("err.honest_balanced")
    treated = data.groupby(unit_col)[treated_col].first().reindex(wide.index).to_numpy() == 1
    periods = np.array(sorted(wide.columns))
    ref = treatment_period - 1
    rel = periods - treatment_period
    if ref not in wide.columns or treated.sum() < 2 or (~treated).sum() < 2:
        raise LocalizedError("err.honest_periods", pre=int((rel < -1).sum()), post=int((rel >= 0).sum()))
    pre, post = rel[rel < -1], rel[rel >= 0]
    if len(pre) < 2 or len(post) < 1 or np.any(np.diff(np.concatenate([pre, [-1], post])) != 1):
        raise LocalizedError("err.honest_periods", pre=len(pre), post=len(post))
    keep = [p for p in periods if p != ref]
    d = wide[keep].sub(wide[ref], axis=0).to_numpy(float)         # Y_t - Y_ref per unit
    a, b = d[treated], d[~treated]
    beta = a.mean(axis=0) - b.mean(axis=0)
    sigma = np.atleast_2d(np.cov(a, rowvar=False)) / len(a) + np.atleast_2d(np.cov(b, rowvar=False)) / len(b)
    l = np.full(len(post), 1.0 / len(post)) if target == "average" else np.eye(len(post))[0]
    k = len(keep)
    pattern = np.eye(k) + np.ones((k, k))                          # iid errors: 1 + [t = s]
    work = pattern * float(np.trace(sigma) / np.trace(pattern))    # one scale, from the data
    return _Problem(pre=pre.astype(float), post=post.astype(float), beta=beta, sigma=sigma, l=l, sigma_work=work)


def sensitivity(df: pd.DataFrame, treatment_period: int, m_grid=None, target: str = "average",
                alpha: float = ALPHA, **columns) -> pd.DataFrame:
    """FLCI for each M; M in units of the outcome per period squared. By default
    the grid runs from 0 to twice the largest second difference seen among the
    pre-period coefficients."""
    problem = problem_from_panel(df, treatment_period, target=target, **columns)
    if m_grid is None:
        pre_path = np.concatenate([problem.beta[:len(problem.pre)], [0.0]])
        seen = float(np.max(np.abs(np.diff(pre_path, 2)))) if len(pre_path) >= 3 else 0.0
        top = 2 * seen if seen > 0 else float(np.sqrt(np.diag(problem.sigma)).mean())
        m_grid = np.linspace(0.0, top, 6)
    rows = [flci(problem, float(m), alpha) for m in m_grid]
    return pd.DataFrame([dict(M=r.m, estimate=r.estimate, se=r.se, max_bias=r.max_bias, ci_low=r.ci_low,
                              ci_high=r.ci_high) for r in rows])


def breakdown_m(table: pd.DataFrame) -> float | None:
    """The smallest M on the grid at which the interval includes 0 (None if it never does;
    0.0 if it already does under linear trends)."""
    hits = table[(table["ci_low"] <= 0) & (table["ci_high"] >= 0)]
    return float(hits["M"].min()) if len(hits) else None
