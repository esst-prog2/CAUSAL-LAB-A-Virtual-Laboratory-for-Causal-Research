"""
Bargaining over a surplus of size S between two players.

Nash bargaining solution (Nash 1950; generalized with bargaining power alpha):
player 1 receives the share x of S that maximizes

    (u1(x S) - d1)^alpha * (u2((1 - x) S) - d2)^(1 - alpha),

where u1, u2 are the players' utilities of money (sympy expressions in m) and
d1, d2 their disagreement utilities. With linear utilities the solution is
x S = d1 + alpha (S - d1 - d2).

Rubinstein (1982) alternating offers: player 1 proposes first, a rejected
offer is followed by the other player's offer next period, and the players
discount with delta1, delta2. The unique subgame-perfect equilibrium is
immediate agreement with player 1 receiving (1 - delta2) / (1 - delta1 delta2)
of the surplus. The finite-horizon game (T rounds, nothing after) is solved by
backward induction and converges to that share as T grows. As both players
become patient at equal rates, the share tends to the symmetric Nash solution
(Binmore, Rubinstein & Wolinsky 1986).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import sympy as sp
from scipy.optimize import minimize_scalar

from theory_engine.game import parse_expression
from utils.i18n import LocalizedError

MONEY = sp.Symbol("m", real=True)


@dataclass
class NashBargaining:
    share_1: float          # share of the surplus to player 1
    payoff_1: float         # utilities at the solution
    payoff_2: float
    nash_product: float


def nash_bargaining(surplus: float, alpha: float = 0.5, d1: float = 0.0, d2: float = 0.0,
                    utility_1: str = "m", utility_2: str = "m") -> NashBargaining:
    if surplus <= 0:
        raise LocalizedError("err.bargain_surplus")
    if not 0 < alpha < 1:
        raise LocalizedError("err.bargain_alpha")
    u1 = sp.lambdify(MONEY, parse_expression(utility_1, {"m": MONEY}), modules="numpy")
    u2 = sp.lambdify(MONEY, parse_expression(utility_2, {"m": MONEY}), modules="numpy")

    def log_product(x):
        with np.errstate(all="ignore"):
            g1, g2 = float(u1(x * surplus)) - d1, float(u2((1 - x) * surplus)) - d2
        if not (np.isfinite(g1) and np.isfinite(g2)) or g1 <= 0 or g2 <= 0:
            return np.inf
        return -(alpha * np.log(g1) + (1 - alpha) * np.log(g2))

    grid = np.linspace(0, 1, 401)
    scores = np.array([log_product(x) for x in grid])
    if not np.isfinite(scores).any():
        raise LocalizedError("err.bargain_no_gain")
    k = int(np.argmin(scores))
    res = minimize_scalar(log_product, bounds=(grid[max(k - 1, 0)], grid[min(k + 1, 400)]), method="bounded",
                          options={"xatol": 1e-12})
    x = float(res.x) if res.fun <= scores[k] else float(grid[k])
    p1, p2 = float(u1(x * surplus)), float(u2((1 - x) * surplus))
    return NashBargaining(share_1=x, payoff_1=p1, payoff_2=p2, nash_product=float(np.exp(-log_product(x))))


def rubinstein_share(delta_1: float, delta_2: float) -> float:
    """Proposer's (player 1's) equilibrium share of the surplus, infinite horizon."""
    if not (0 <= delta_1 < 1 and 0 <= delta_2 < 1):
        raise LocalizedError("err.bargain_delta")
    return (1 - delta_2) / (1 - delta_1 * delta_2)


def rubinstein_finite(delta_1: float, delta_2: float, rounds: int) -> list[float]:
    """Backward induction: the first proposer's share when T = 1..rounds offers remain.
    With one round left the proposer takes everything; with t rounds the proposer
    offers the responder exactly the discounted value of proposing next round."""
    if rounds < 1:
        raise LocalizedError("err.bargain_rounds")
    # (v1, v2): the share a proposer gets with t rounds left, when player 1 / player 2 proposes.
    v1, v2 = 1.0, 1.0                    # one round left: the proposer takes everything
    shares = [v1]
    for _ in range(2, rounds + 1):
        v1, v2 = 1 - delta_2 * v2, 1 - delta_1 * v1    # the responder proposes next round
        shares.append(v1)
    return shares
