"""
Two-player finite (matrix) games and their Nash equilibria in mixed strategies.

A bimatrix game gives the row player payoffs A[i, j] and the column player
payoffs B[i, j] when row plays i and column plays j. A mixed strategy is a
probability vector over a player's actions. A pair (x, y) is a Nash
equilibrium when every action x plays with positive probability earns the
row player's best expected payoff against y (and likewise for y).

`nash_equilibria` finds all of them by vertex enumeration of the
best-response polytopes (Gambit's enummixed); in a degenerate game an
equilibrium component is reported by its extreme points. Exact for the
small games this page handles (up to 6 x 6).

`logit_qre` computes the logit quantal response equilibrium (McKelvey &
Palfrey 1995): each player plays action k with probability proportional to
exp(lambda * expected payoff of k). lambda = 0 is uniform play; as lambda
grows the QRE approaches a Nash equilibrium. It is the model behind the
structural estimation of games from observed choice frequencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

import numpy as np

from utils.i18n import LocalizedError, Msg

MAX_ACTIONS = 6
TOLERANCE = 1e-9


@dataclass
class BimatrixGame:
    name: Msg | str
    row_actions: list[str]
    col_actions: list[str]
    row_payoffs: np.ndarray           # A, shape (m, n)
    col_payoffs: np.ndarray           # B, shape (m, n)
    row_player: Msg | str = "Row"
    col_player: Msg | str = "Column"
    description: Msg | str = ""
    references: tuple[str, ...] = ()      # keys of utils/references.py, optionally "key:pinpoint"
    parameters: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.row_payoffs = np.asarray(self.row_payoffs, dtype=float)
        self.col_payoffs = np.asarray(self.col_payoffs, dtype=float)
        m, n = len(self.row_actions), len(self.col_actions)
        if self.row_payoffs.shape != (m, n) or self.col_payoffs.shape != (m, n):
            raise LocalizedError("err.matrix_shape", rows=m, cols=n)
        if not (1 <= m <= MAX_ACTIONS and 1 <= n <= MAX_ACTIONS):
            raise LocalizedError("err.matrix_size", maximum=MAX_ACTIONS)
        if not (np.isfinite(self.row_payoffs).all() and np.isfinite(self.col_payoffs).all()):
            raise LocalizedError("err.matrix_finite")


@dataclass
class MixedEquilibrium:
    row: np.ndarray                   # probabilities over row actions
    col: np.ndarray
    row_payoff: float
    col_payoff: float
    pure: bool
    max_gain: float                   # largest gain from a pure deviation (~0 at a Nash equilibrium)


def _vertices(constraints: np.ndarray, n_vars: int) -> list[tuple[np.ndarray, frozenset]]:
    """Vertices of {z >= 0, constraints @ z <= 1} other than the origin, with their
    labels: label k < n_vars when z_k = 0, label n_vars + r when constraint r binds."""
    n_rows = constraints.shape[0]
    full = np.vstack([-np.eye(n_vars), constraints])           # full @ z <= [0, ..., 0, 1, ..., 1]
    bound = np.concatenate([np.zeros(n_vars), np.ones(n_rows)])
    out = []
    for tight in combinations(range(n_vars + n_rows), n_vars):
        sub = full[list(tight)]
        if abs(np.linalg.det(sub)) < 1e-12:
            continue
        z = np.linalg.solve(sub, bound[list(tight)])
        slack = bound - full @ z
        if slack.min() < -1e-9 or z.sum() < 1e-12:
            continue
        labels = frozenset(np.flatnonzero(np.abs(slack) <= 1e-9).tolist())
        if not any(np.allclose(z, v, atol=1e-10) for v, _ in out):
            out.append((z, labels))
    return out


def _gain(game: BimatrixGame, x: np.ndarray, y: np.ndarray) -> float:
    a, b = game.row_payoffs, game.col_payoffs
    row_value, col_value = x @ a @ y, x @ b @ y
    return float(max(np.max(a @ y) - row_value, np.max(x @ b) - col_value))


def nash_equilibria(game: BimatrixGame) -> list[MixedEquilibrium]:
    """All extreme Nash equilibria, by vertex enumeration of the best-response
    polytopes (Avis, Rosenberg, Savani & von Stengel 2010; Gambit's enummixed).
    With payoffs shifted to be positive, P = {x >= 0, B'x <= 1} and
    Q = {y >= 0, A y <= 1}; a pair of non-zero vertices whose labels together
    cover every action is an equilibrium once normalized. In a degenerate game
    an equilibrium component is reported by its extreme points."""
    a, b = game.row_payoffs, game.col_payoffs
    m, n = a.shape
    a_pos = a - a.min() + 1.0                          # equilibria do not change with a constant shift
    b_pos = b - b.min() + 1.0
    # Labels: row actions 0..m-1, column actions m..m+n-1, in both polytopes.
    p_vertices = _vertices(b_pos.T, m)                 # x_i = 0 -> label i; (B'x)_j = 1 -> label m+j (as returned)
    q_vertices = [(y, frozenset(l - n if l >= n else m + l for l in labels))
                  for y, labels in _vertices(a_pos, n)]       # y_j = 0 -> label m+j; (A'y)_i = 1 -> label i
    everything = frozenset(range(m + n))
    found: list[MixedEquilibrium] = []
    for x_raw, x_labels in p_vertices:
        for y_raw, y_labels in q_vertices:
            if x_labels | y_labels != everything:
                continue
            x = np.clip(x_raw / x_raw.sum(), 0.0, None) + 0.0       # no "-0.0" from rounding
            y = np.clip(y_raw / y_raw.sum(), 0.0, None) + 0.0
            if any(np.allclose(x, e.row, atol=1e-9) and np.allclose(y, e.col, atol=1e-9) for e in found):
                continue
            found.append(MixedEquilibrium(row=x, col=y, row_payoff=float(x @ a @ y), col_payoff=float(x @ b @ y),
                                          pure=bool(x.max() > 1 - 1e-12 and y.max() > 1 - 1e-12),
                                          max_gain=_gain(game, x, y)))
    found.sort(key=lambda e: (not e.pure, -e.row_payoff - e.col_payoff))
    return found


def _softmax(z: np.ndarray) -> np.ndarray:
    e = np.exp(z - z.max())
    return e / e.sum()


def logit_branch(game: BimatrixGame, lam: float, max_step: float = 0.05,
                 start: tuple[float, np.ndarray] | None = None):
    """Points of the logit QRE principal branch, from lambda = 0 (or from
    `start` = (lambda, z) on the branch) up to `lam`: yields (lambda, z) at
    every continuation step, the last one at `lam`.

    Unknowns are log-odds against each player's first action, z = (zx, zy),
    with x = softmax(0, zx) and y = softmax(0, zy); the QRE solves
    zx_i = lam * ((A y)_i - (A y)_0) and zy_j = lam * ((x'B)_j - (x'B)_0).
    The branch is followed by Newton's method at each step, with the step
    halved whenever Newton fails, as Gambit's logit_solve_lambda does by
    predictor-corrector path following. A damped fixed-point iteration was
    tried first and jumped to other branches (or cycled) at lambda >= 3 in
    Battle of the Sexes and the inspection game."""
    from scipy.optimize import root

    if lam < 0:
        raise LocalizedError("err.qre_lambda", value=lam)
    a, b = game.row_payoffs, game.col_payoffs
    m, n = a.shape
    scale = max(1.0, float(np.abs(a).max()), float(np.abs(b).max()))

    def residual(z, level):
        x, y = qre_profile(game, z)
        ux, uy = a @ y, x @ b
        return np.r_[z[:m - 1] - level * (ux[1:] - ux[0]), z[m - 1:] - level * (uy[1:] - uy[0])]

    level, z = (0.0, np.zeros(m + n - 2)) if start is None else (float(start[0]), np.asarray(start[1], float))
    step = max_step / scale
    while level < lam - 1e-15:
        target = min(lam, level + step)
        sol = root(residual, z, args=(target,), method="hybr", tol=1e-13)
        if sol.success and np.abs(residual(sol.x, target)).max() < 1e-10                 and np.abs(sol.x - z).max() < 1.0 + 10 * step * scale:
            z, level = sol.x, target
            step = min(step * 1.5, 1.0 / scale)
            yield level, z
        else:
            step /= 2
            if step < 1e-10:
                raise LocalizedError("err.qre_path", value=lam, reached=level)


def qre_profile(game: BimatrixGame, z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Mixed strategies (x, y) from the log-odds vector of logit_branch."""
    m = game.row_payoffs.shape[0]
    return _softmax(np.r_[0.0, z[:m - 1]]), _softmax(np.r_[0.0, z[m - 1:]])


def logit_qre(game: BimatrixGame, lam: float, max_step: float = 0.05) -> tuple[np.ndarray, np.ndarray]:
    """Logit QRE on the principal branch at precision `lam` >= 0 (see logit_branch)."""
    z = np.zeros(sum(game.row_payoffs.shape) - 2)
    for _, z in logit_branch(game, lam, max_step):
        pass
    return qre_profile(game, z)


# --------------------------------------------------------------------------
# Catalogue
# --------------------------------------------------------------------------
def _game(key: str, rows, cols, a, b, row_player, col_player, references: tuple[str, ...]) -> BimatrixGame:
    return BimatrixGame(name=Msg(f"matrix.{key}.name"),
                        row_actions=[Msg(f"matrix.{key}.row.{r}") for r in rows],
                        col_actions=[Msg(f"matrix.{key}.col.{c}") for c in cols],
                        row_payoffs=a, col_payoffs=b, row_player=Msg(row_player), col_player=Msg(col_player),
                        description=Msg(f"matrix.{key}.description"), references=references)


def matrix_catalogue() -> dict[str, BimatrixGame]:
    return {
        "prisoners_dilemma": _game("prisoners_dilemma", ("cooperate", "defect"), ("cooperate", "defect"),
                                   [[3, 0], [5, 1]], [[3, 5], [0, 1]], "player.player1", "player.player2",
                                   ("tucker_1950", "axelrod_1984")),
        "matching_pennies": _game("matching_pennies", ("heads", "tails"), ("heads", "tails"),
                                  [[1, -1], [-1, 1]], [[-1, 1], [1, -1]], "player.player1", "player.player2",
                                  ("von_neumann_morgenstern_1944",)),
        "battle_of_sexes": _game("battle_of_sexes", ("opera", "football"), ("opera", "football"),
                                 [[2, 0], [0, 1]], [[1, 0], [0, 2]], "player.player1", "player.player2",
                                 ("luce_raiffa_1957",)),
        "hawk_dove": _game("hawk_dove", ("hawk", "dove"), ("hawk", "dove"),
                           [[-1, 4], [0, 2]], [[-1, 0], [4, 2]], "player.player1", "player.player2",
                           ("maynard_smith_price_1973",)),
        "stag_hunt": _game("stag_hunt", ("stag", "hare"), ("stag", "hare"),
                           [[4, 0], [3, 3]], [[4, 3], [0, 3]], "player.player1", "player.player2",
                           ("rousseau_1755", "skyrms_2004")),
        "inspection": _game("inspection", ("comply", "evade"), ("inspect", "skip"),
                            # taxpayer: tax 1, fine 3 if caught evading; authority: inspection costs 0.5,
                            # catching an evader yields 3, an unnoticed evasion costs it 2
                            [[-1, -1], [-4, 0]], [[-0.5, 0], [3, -2]], "player.taxpayer", "player.authority",
                            ("tsebelis_1989", "andreozzi_2004")),
        "rock_paper_scissors": _game("rock_paper_scissors", ("rock", "paper", "scissors"),
                                     ("rock", "paper", "scissors"),
                                     [[0, -1, 1], [1, 0, -1], [-1, 1, 0]], [[0, 1, -1], [-1, 0, 1], [1, -1, 0]],
                                     "player.player1", "player.player2", ("fudenberg_tirole_1991:ch. 1",)),
    }
