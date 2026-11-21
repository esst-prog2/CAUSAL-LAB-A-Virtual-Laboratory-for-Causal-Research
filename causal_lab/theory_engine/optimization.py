"""
Nash equilibria found by optimisation: each problem below has optimal value
zero exactly at the equilibria, so solving it is finding them.

Continuous games (theory_engine.game.Game). The Nikaido-Isoda gap

    V(s) = sum_i [ max_{y_i} u_i(y_i, s_-i) - u_i(s) ]

is the total gain the players could get by deviating one at a time. V >= 0
everywhere, and V(s) = 0 if and only if s is a Nash equilibrium (Nikaido &
Isoda 1955; von Heusinger & Kanzow 2009). V has kinks where a best response
jumps, so it is minimised over the strategy box by derivative-free methods:
Nelder-Mead from several starts, then Powell from where Nelder-Mead stopped
if V is not yet zero. On the five smooth catalogue games with two players
(25 starts, 800 evaluations each), Nelder-Mead alone stopped short of zero
from 1 start and Powell alone from 5; the combination reached zero from all 25. Each inner maximum uses the same grid-plus-bounded search as the
best-response solver. A minimiser counts as an equilibrium only if the
solver's own deviation check verifies it. Games with discontinuous payoffs
(smooth = False: Downs, Niskanen) are outside this method: V is then flat almost
everywhere, and their closed form is used instead.

Bimatrix games (theory_engine.finite_games.BimatrixGame). Mangasarian & Stone
(1964): (x, y) is a Nash equilibrium if and only if, with p and q,

    max  x'(A + B) y - p - q
    s.t. A y <= p 1,  B' x <= q 1,  x, y in the simplices,

has optimal value 0 at (x, y, p, q). The program is not concave, so it is
solved by SLSQP from many starts; every solution is checked by the payoff
gain of the best pure deviation. Starts are seeded, so the result is
reproducible. Unlike vertex enumeration it need not find every equilibrium:
the page shows both and says so.

Zero-sum games (A + B = 0). The value and the maximin strategies solve a
linear program (von Neumann & Morgenstern 1944), solved exactly by HiGHS.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import linprog, minimize

from theory_engine.finite_games import BimatrixGame, _gain
from theory_engine.game import PENALTY, Equilibrium, Game, SolveResult, _NumericGame
from utils.i18n import Msg

GAP_METHOD = "Nikaido-Isoda gap minimisation"
GAP_GRID = 24                    # grid points of each inner maximum while minimising
GAP_MAXFEV = 800                 # function evaluations per method and start
GAP_STARTS = 5
QP_STARTS = 40
QP_TOLERANCE = 1e-7              # largest pure-deviation gain accepted as an equilibrium
SAME_POINT = 1e-4


# --------------------------------------------------------------------------
# Continuous games: Nikaido-Isoda gap
# --------------------------------------------------------------------------
def nikaido_isoda_gap(num: _NumericGame, s: np.ndarray, n_grid: int = GAP_GRID) -> float:
    """V(s): the sum over players of the gain from their best unilateral deviation."""
    total = 0.0
    for i in range(len(s)):
        current = num.utility(i, s)
        if current <= PENALTY / 10:
            return np.inf
        _, best = num._maximize(i, s, n_grid)
        total += max(best - current, 0.0)
    return total


@dataclass
class GapRun:
    start: list[float]
    end: list[float]
    gap: float                   # V at the end point
    path: list[float]            # V after each Powell iteration
    evaluations: int


@dataclass
class GapResult(SolveResult):
    runs: list[GapRun] = field(default_factory=list)


def solve_by_gap_minimisation(game: Game, values: dict[str, float] | None = None, n_starts: int = GAP_STARTS,
                              seed: int = 0) -> GapResult:
    """Pure-strategy Nash equilibria of `game` as the zeros of the Nikaido-Isoda gap."""
    if not game.smooth:
        return GapResult([], Msg("solve.gap_not_smooth"))
    num = _NumericGame(game, values)
    lows = np.array([b[0] for b in num.bounds])
    highs = np.array([b[1] for b in num.bounds])
    rng = np.random.default_rng(seed)
    starts = [(lows + highs) / 2] + [lows + rng.random(len(lows)) * (highs - lows) for _ in range(n_starts - 1)]

    found: list[Equilibrium] = []
    runs: list[GapRun] = []
    for s0 in starts:
        path: list[float] = []

        def gap_at(s):
            return nikaido_isoda_gap(num, np.clip(s, lows, highs))

        def record(s, *_):
            path.append(gap_at(s))

        box = list(zip(lows, highs))
        res = minimize(gap_at, s0, method="Nelder-Mead", bounds=box, callback=record,
                       options={"xatol": 1e-10, "fatol": 1e-14, "maxfev": GAP_MAXFEV, "adaptive": True})
        evaluations = int(res.nfev)
        if gap_at(res.x) > 1e-12:
            res = minimize(gap_at, np.clip(res.x, lows, highs), method="Powell", bounds=box, callback=record,
                           options={"xtol": 1e-10, "ftol": 1e-14, "maxfev": GAP_MAXFEV})
            evaluations += int(res.nfev)
        s = np.clip(res.x, lows, highs)
        gap = gap_at(s)
        runs.append(GapRun(start=[float(v) for v in s0], end=[float(v) for v in s], gap=float(gap),
                           path=path or [float(gap)], evaluations=evaluations))
        eq = num.equilibrium(s, GAP_METHOD)
        if not eq.verified:
            continue
        vec = np.array(list(eq.strategies.values()))
        if all(np.max(np.abs(vec - np.array(list(f.strategies.values()))) / num.scale) > SAME_POINT for f in found):
            found.append(eq)
    if not found:
        return GapResult([], Msg("solve.gap_none"), runs)
    msg = Msg("solve.unique") if len(found) == 1 else Msg("solve.several", n=len(found))
    return GapResult(found, msg, runs)


# --------------------------------------------------------------------------
# Bimatrix games: Mangasarian-Stone quadratic program
# --------------------------------------------------------------------------
@dataclass
class QPEquilibrium:
    row: np.ndarray
    col: np.ndarray
    row_payoff: float
    col_payoff: float
    objective: float             # x'(A+B)y - p - q at the solution: 0 at an equilibrium
    gain: float                  # best pure-deviation gain, the check


@dataclass
class QPResult:
    equilibria: list[QPEquilibrium]
    starts: int
    converged: int               # starts whose solution passed the check


def _simplex_point(rng, k: int) -> np.ndarray:
    return rng.dirichlet(np.ones(k))


def mangasarian_stone(game: BimatrixGame, n_starts: int = QP_STARTS, seed: int = 0) -> QPResult:
    a, b = game.row_payoffs, game.col_payoffs
    m, n = a.shape
    c = a + b

    def unpack(z):
        return z[:m], z[m:m + n], z[m + n], z[m + n + 1]

    def objective(z):
        x, y, p, q = unpack(z)
        return -(x @ c @ y - p - q)

    def gradient(z):
        x, y, _, _ = unpack(z)
        return -np.concatenate([c @ y, c.T @ x, [-1.0, -1.0]])

    constraints = [
        {"type": "ineq", "fun": lambda z: unpack(z)[2] - a @ unpack(z)[1]},          # p - A y >= 0
        {"type": "ineq", "fun": lambda z: unpack(z)[3] - b.T @ unpack(z)[0]},        # q - B'x >= 0
        {"type": "eq", "fun": lambda z: np.array([unpack(z)[0].sum() - 1, unpack(z)[1].sum() - 1])},
    ]
    span = float(max(np.abs(a).max(), np.abs(b).max(), 1.0))
    bounds = [(0.0, 1.0)] * (m + n) + [(-2 * span, 2 * span)] * 2

    rng = np.random.default_rng(seed)
    starts = [np.full(m, 1 / m)] + [_simplex_point(rng, m) for _ in range(n_starts - 1)]
    found: list[QPEquilibrium] = []
    converged = 0
    for k, x0 in enumerate(starts):
        y0 = np.full(n, 1 / n) if k == 0 else _simplex_point(rng, n)
        z0 = np.concatenate([x0, y0, [float((a @ y0).max()), float((b.T @ x0).max())]])
        res = minimize(objective, z0, jac=gradient, method="SLSQP", bounds=bounds, constraints=constraints,
                       options={"ftol": 1e-12, "maxiter": 500})
        x, y, _, _ = unpack(res.x)
        x, y = np.clip(x, 0, None), np.clip(y, 0, None)
        x, y = x / x.sum(), y / y.sum()
        gain = _gain(game, x, y)
        if gain > QP_TOLERANCE * span:
            continue
        converged += 1
        # Clean the rounding of the solver: supports below 1e-9 are zero.
        x, y = np.where(x < 1e-9, 0, x), np.where(y < 1e-9, 0, y)
        x, y = x / x.sum(), y / y.sum()
        if any(np.max(np.abs(x - e.row)) < SAME_POINT and np.max(np.abs(y - e.col)) < SAME_POINT for e in found):
            continue
        p, q = float((a @ y).max()), float((b.T @ x).max())
        found.append(QPEquilibrium(row=x, col=y, row_payoff=float(x @ a @ y), col_payoff=float(x @ b @ y),
                                   objective=float(x @ c @ y - p - q), gain=float(gain)))
    found.sort(key=lambda e: (tuple(-e.row), tuple(-e.col)))
    return QPResult(found, len(starts), converged)


# --------------------------------------------------------------------------
# Zero-sum games: linear programming
# --------------------------------------------------------------------------
@dataclass
class ZeroSumSolution:
    value: float                 # what the row player guarantees, and the column player concedes
    row: np.ndarray
    col: np.ndarray


def is_zero_sum(game: BimatrixGame, tol: float = 1e-12) -> bool:
    return bool(np.all(np.abs(game.row_payoffs + game.col_payoffs) <= tol * (1 + np.abs(game.row_payoffs))))


def _maximin(a: np.ndarray) -> tuple[float, np.ndarray]:
    """max_x min_j (x'A)_j over the simplex: variables (x, v), minimise -v."""
    m, n = a.shape
    cost = np.concatenate([np.zeros(m), [-1.0]])
    a_ub = np.hstack([-a.T, np.ones((n, 1))])                       # v - (A'x)_j <= 0
    a_eq = np.concatenate([np.ones(m), [0.0]])[None, :]
    res = linprog(cost, A_ub=a_ub, b_ub=np.zeros(n), A_eq=a_eq, b_eq=[1.0],
                  bounds=[(0, None)] * m + [(None, None)], method="highs")
    return float(-res.fun), res.x[:m]


def zero_sum_solution(game: BimatrixGame) -> ZeroSumSolution | None:
    if not is_zero_sum(game):
        return None
    value, x = _maximin(game.row_payoffs)
    _, y = _maximin(-game.row_payoffs.T)          # the column player maximises -A' over its mixes
    return ZeroSumSolution(value=value, row=x, col=y)
