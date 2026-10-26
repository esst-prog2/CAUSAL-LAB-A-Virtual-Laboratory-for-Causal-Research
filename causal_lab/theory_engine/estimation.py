"""
Structural estimation of the theoretical models (README section 3, "Not
this term": structural estimation (MLE/GMM); built on 2026-10-26).

Calibration (calibration.py) sets each parameter from one explicit moment
of the data. Here parameters are estimated with standard errors:

- `fit_logit_qre`: maximum likelihood estimate of the logit QRE precision
  lambda of a matrix game from counts of observed choices (McKelvey &
  Palfrey 1995). The likelihood is evaluated along the principal branch
  at every continuation step, its maximum refined by a bounded search, as
  Gambit's logit_estimate takes the global maximizer along that branch.
  Standard error from the curvature of the log-likelihood; 95% interval
  by inverting the likelihood-ratio test, which stays valid when lambda
  is near 0 or the likelihood is flat towards a Nash equilibrium.
- `gmm_first_order_conditions`: generalized method of moments on the
  equilibrium conditions of a continuous game (Hansen 1982; Hansen &
  Singleton 1982). Each row of the data is one observed equilibrium, for
  instance one market. At the true parameters an agent's first-order
  condition equals an unobserved shock with mean zero given the
  instruments, so E[FOC_a(s, x; theta) z] = 0 for every agent a used and
  instrument z (a constant and the chosen columns). The equilibrium is
  never re-solved: only the observed strategies enter. Two-step efficient
  GMM (first step weight (Z'Z/n)^-1 per agent, second step the inverse of
  the moments' covariance, uncentered), heteroskedasticity-robust sandwich
  standard errors, and Hansen's J test when there are more moments than
  parameters.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import sympy as sp
from scipy.optimize import brentq, least_squares, minimize_scalar
from scipy.special import xlogy
from scipy.stats import chi2, norm

from theory_engine.finite_games import BimatrixGame, logit_branch, qre_profile
from theory_engine.game import Game, first_order_conditions
from utils.i18n import LocalizedError

LAMBDA_MAX = 200.0               # largest lambda traced, times 1 / (largest absolute payoff)
LEVEL = 0.95


# --------------------------------------------------------------------------
# Logit QRE by maximum likelihood
# --------------------------------------------------------------------------
@dataclass
class QREFit:
    lam: float
    log_likelihood: float
    row: np.ndarray                      # fitted mixed strategies
    col: np.ndarray
    se: float | None                     # None at a bound (lambda = 0 or the end of the traced branch)
    ci_low: float
    ci_high: float                       # inf when the likelihood never drops enough
    at_bound: bool                       # maximum at the end of the traced branch: play looks like Nash
    n_obs: int
    random_log_likelihood: float         # lambda = 0: uniform play
    lr_random: float                     # 2 (logL - logL at lambda = 0)
    p_random: float
    curve: list[tuple[float, float]]     # (lambda, log-likelihood) along the branch


def fit_logit_qre(game: BimatrixGame, row_counts, col_counts, lam_max: float | None = None) -> QREFit:
    a = game.row_payoffs
    rc, cc = np.asarray(row_counts, dtype=float), np.asarray(col_counts, dtype=float)
    if rc.shape != (a.shape[0],) or cc.shape != (a.shape[1],):
        raise LocalizedError("err.qre_counts_shape", rows=a.shape[0], cols=a.shape[1])
    if not (np.isfinite(rc).all() and np.isfinite(cc).all()) or rc.min() < 0 or cc.min() < 0:
        raise LocalizedError("err.qre_counts")
    if rc.sum() + cc.sum() <= 0:
        raise LocalizedError("err.qre_no_data")
    scale = max(1.0, float(np.abs(a).max()), float(np.abs(game.col_payoffs).max()))
    lam_max = LAMBDA_MAX / scale if lam_max is None else float(lam_max)

    def loglik(z) -> float:
        x, y = qre_profile(game, z)
        return float(xlogy(rc, x).sum() + xlogy(cc, y).sum())

    points = [(0.0, np.zeros(sum(a.shape) - 2))] + list(logit_branch(game, lam_max))
    levels = np.array([p[0] for p in points])
    values = np.array([loglik(z) for _, z in points])

    def z_at(lam: float) -> np.ndarray:
        k = int(np.searchsorted(levels, lam, side="right")) - 1      # last traced point at or below lam
        z = points[k][1]
        if lam > levels[k]:
            for _, z in logit_branch(game, lam, start=points[k]):
                pass
        return z

    def ll_at(lam: float) -> float:
        return loglik(z_at(lam))

    k = int(np.argmax(values))
    last = len(points) - 1
    lo, hi = levels[max(k - 1, 0)], levels[min(k + 1, last)]
    lam_hat, ll_hat = levels[k], values[k]
    if hi > lo:
        res = minimize_scalar(lambda t: -ll_at(t), bounds=(lo, hi), method="bounded",
                              options={"xatol": 1e-10 * max(1.0, hi)})
        if -res.fun > ll_hat:
            lam_hat, ll_hat = float(res.x), float(-res.fun)
    # The likelihood still rising, or flat to rounding, at the end of the traced branch:
    # play is consistent with the Nash limit and lambda has no finite estimate (data all on
    # a pure equilibrium give log-likelihood 0 from some lambda on).
    at_bound = bool(values[last] >= ll_hat - 1e-9 * max(1.0, abs(ll_hat)))

    se = None
    if not at_bound and lam_hat > 0:
        h = 1e-3 * max(lam_hat, 1.0 / scale)
        if lam_hat - h > 0:
            curvature = (ll_at(lam_hat + h) - 2 * ll_hat + ll_at(lam_hat - h)) / h ** 2
            if curvature < 0:
                se = float(1 / np.sqrt(-curvature))

    threshold = ll_hat - chi2.ppf(LEVEL, 1) / 2

    def crossing(direction: int) -> float:
        idx = range(k, -1, -1) if direction < 0 else range(k, last + 1)
        prev = lam_hat
        for j in idx:
            if (direction < 0 and levels[j] >= lam_hat) or (direction > 0 and levels[j] <= lam_hat):
                continue
            if values[j] < threshold:
                return float(brentq(lambda t: ll_at(t) - threshold, *sorted((prev, levels[j])), xtol=1e-12))
            prev = levels[j]
        return 0.0 if direction < 0 else float("inf")

    row, col = qre_profile(game, z_at(lam_hat))
    lr = max(0.0, 2 * (ll_hat - values[0]))
    return QREFit(lam=float(lam_hat), log_likelihood=float(ll_hat), row=row, col=col, se=se,
                  ci_low=crossing(-1), ci_high=crossing(+1), at_bound=bool(at_bound),
                  n_obs=int(round(rc.sum() + cc.sum())), random_log_likelihood=float(values[0]),
                  lr_random=float(lr), p_random=float(chi2.sf(lr, 1)),
                  curve=[(float(l), float(v)) for l, v in zip(levels, values)])


# --------------------------------------------------------------------------
# GMM on the equilibrium first-order conditions
# --------------------------------------------------------------------------
@dataclass
class GMMFit:
    names: list[str]
    estimates: np.ndarray
    se: np.ndarray
    ci_low: np.ndarray
    ci_high: np.ndarray
    n: int
    n_dropped: int
    n_moments: int
    j_stat: float | None                 # None when exactly identified
    j_df: int
    j_p: float | None
    first_step: np.ndarray
    converged: bool


def _column(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        raise LocalizedError("err.gmm_column", column=column)
    values = pd.to_numeric(df[column], errors="coerce")
    if values.notna().sum() == 0:
        raise LocalizedError("err.gmm_not_numeric", column=column)
    return values


def gmm_first_order_conditions(game: Game, df: pd.DataFrame, strategy_columns: dict[str, str],
                               estimate: dict[str, float], instruments: list[str],
                               observed: dict[str, str] | None = None, fixed: dict[str, float] | None = None,
                               agents: list[int] | None = None) -> GMMFit:
    """Two-step GMM estimate of the parameters in `estimate` (name -> start
    value). `strategy_columns` maps every strategy to a column, `observed`
    maps parameters that vary by row to columns, `fixed` overrides the
    defaults of the remaining parameters; `agents` selects whose
    first-order conditions are used (all by default)."""
    focs = first_order_conditions(game)
    if focs is None:
        raise LocalizedError("err.gmm_not_smooth")
    observed, fixed = dict(observed or {}), dict(fixed or {})
    agents = list(range(len(game.agents))) if agents is None else list(agents)
    if not agents:
        raise LocalizedError("err.gmm_no_agent")
    if not estimate:
        raise LocalizedError("err.gmm_nothing")
    for name in (*estimate, *observed, *fixed):
        if name not in game.symbols:
            raise LocalizedError("err.game_unknown_params", names=name)
    clash = (set(estimate) & set(observed)) | (set(estimate) & set(fixed)) | (set(observed) & set(fixed))
    if clash:
        raise LocalizedError("err.gmm_role_twice", names=", ".join(sorted(clash)))
    missing = [str(s) for s in game.strategies if str(s) not in strategy_columns]
    if missing:
        raise LocalizedError("err.gmm_strategy_column", names=", ".join(missing))

    # Data: rows with every needed value present.
    needed = {**{f"s:{k}": v for k, v in strategy_columns.items()}, **{f"p:{k}": v for k, v in observed.items()},
              **{f"z:{c}": c for c in instruments}}
    table = pd.DataFrame({key: _column(df, col) for key, col in needed.items()})
    complete = table.dropna()
    n, n_dropped = len(complete), len(table) - len(complete)
    names = list(estimate)
    q = 1 + len(instruments)
    n_moments = len(agents) * q
    if n_moments < len(names):
        raise LocalizedError("err.gmm_underidentified", moments=n_moments, parameters=len(names))
    if n <= n_moments:
        raise LocalizedError("err.gmm_too_few_rows", n=n, moments=n_moments)

    # Moment functions: FOC_a(s, x; theta) for the agents used, and their theta-derivatives.
    defaults = {k: v for k, v in {**game.parameters, **fixed}.items() if k not in estimate and k not in observed}
    subs = {game.symbols[k]: float(v) for k, v in defaults.items()}
    theta = [game.symbols[k] for k in names]
    obs_syms = [game.symbols[k] for k in observed]
    args = [*game.strategies, *obs_syms, *theta]
    used = [focs[game.agents[a].name].subs(subs) for a in agents]
    foc_fn = sp.lambdify(args, used, modules="numpy")
    jac_fn = sp.lambdify(args, [[sp.diff(f, t) for t in theta] for f in used], modules="numpy")
    data_cols = [complete[f"s:{s}"].to_numpy(float) for s in map(str, game.strategies)] + \
                [complete[f"p:{k}"].to_numpy(float) for k in observed]
    z = np.column_stack([np.ones(n)] + [complete[f"z:{c}"].to_numpy(float) for c in instruments])

    def broadcast(values) -> np.ndarray:
        return np.array([np.broadcast_to(np.asarray(v, float), (n,)) for v in values])

    def moments(t: np.ndarray) -> np.ndarray:                          # n x (A q)
        with np.errstate(all="ignore"):
            f = broadcast(foc_fn(*data_cols, *t))                      # A x n
        return (f.T[:, :, None] * z[:, None, :]).reshape(n, -1)

    def moment_jacobian(t: np.ndarray) -> np.ndarray:                  # (A q) x K, averaged over rows
        with np.errstate(all="ignore"):
            raw = jac_fn(*data_cols, *t)
        d = np.array([[np.broadcast_to(np.asarray(v, float), (n,)) for v in row] for row in raw])   # A x K x n
        return np.einsum("akn,nq->aqk", d, z).reshape(-1, len(names)) / n

    def solve(weight: np.ndarray, start: np.ndarray) -> tuple[np.ndarray, bool]:
        c = np.linalg.cholesky(weight)                                  # weight = c c'
        res = least_squares(lambda t: c.T @ moments(t).mean(axis=0), start,
                            jac=lambda t: c.T @ moment_jacobian(t), method="lm",
                            xtol=1e-15, ftol=1e-15, gtol=1e-15, max_nfev=2000)
        return res.x, bool(res.success and np.all(np.isfinite(res.x)))

    start = np.array([float(estimate[k]) for k in names])
    if not np.all(np.isfinite(moments(start))):
        raise LocalizedError("err.gmm_start")
    zz = z.T @ z / n
    if np.linalg.matrix_rank(zz) < q:
        raise LocalizedError("err.gmm_collinear_instruments")
    w1 = np.kron(np.eye(len(agents)), np.linalg.inv(zz))
    theta1, ok1 = solve(w1, start)
    g1 = moments(theta1)
    s1 = g1.T @ g1 / n
    if np.linalg.matrix_rank(s1) < n_moments:
        raise LocalizedError("err.gmm_singular_moments")
    w2 = np.linalg.inv(s1)
    theta2, ok2 = solve(w2, theta1)

    g = moments(theta2)
    gbar = g.mean(axis=0)
    jac = moment_jacobian(theta2)
    if np.linalg.matrix_rank(jac) < len(names):
        raise LocalizedError("err.gmm_not_identified")
    s2 = g.T @ g / n
    bread = np.linalg.inv(jac.T @ w2 @ jac)
    cov = bread @ jac.T @ w2 @ s2 @ w2 @ jac @ bread / n
    se = np.sqrt(np.clip(np.diag(cov), 0, None))
    zc = norm.ppf(0.5 + LEVEL / 2)
    j_df = n_moments - len(names)
    # Hansen J: n times the minimized objective, i.e. with the weight used in the second step.
    j_stat = float(n * gbar @ w2 @ gbar) if j_df > 0 else None
    return GMMFit(names=names, estimates=theta2, se=se, ci_low=theta2 - zc * se, ci_high=theta2 + zc * se,
                  n=n, n_dropped=n_dropped, n_moments=n_moments, j_stat=j_stat, j_df=j_df,
                  j_p=float(chi2.sf(j_stat, j_df)) if j_stat is not None else None,
                  first_step=theta1, converged=ok1 and ok2)
