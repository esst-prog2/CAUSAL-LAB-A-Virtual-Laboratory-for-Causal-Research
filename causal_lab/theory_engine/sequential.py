"""
Sequential play: Stackelberg leadership in any continuous game.

One agent, the leader, chooses first; the followers observe that choice and
play a Nash equilibrium among themselves (a single follower simply best
responds). The leader picks the strategy that maximizes its utility given
the followers' equilibrium response: the subgame-perfect equilibrium.

The followers' response is computed by re-solving the followers' game for
each leader strategy (the leader's strategy becomes a parameter of it),
warm-started from the previous response so it stays on one equilibrium
branch. The leader's problem is then one-dimensional: a grid over its
strategy interval refined by a bounded scalar search, as for best responses
in theory_engine.game. Both solutions are checked: the followers' profile is
verified Nash in their subgame, and no leader strategy on a fine grid does
better.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import sympy as sp
from scipy.optimize import minimize_scalar

from theory_engine.game import Agent, Equilibrium, Game, solve_equilibrium
from utils.i18n import LocalizedError

GRID_LEADER = 41
GRID_VERIFY = 201


@dataclass
class StackelbergResult:
    leader: str
    strategies: dict[str, float]
    utilities: dict[str, float]
    outcomes: dict[str, float]
    simultaneous: Equilibrium | None         # the Nash equilibrium of the same game, for comparison
    leader_gain_check: float                 # best grid improvement for the leader (<= ~0 when optimal)


def _follower_game(game: Game, leader: int) -> Game:
    """The followers' game, with the leader's strategy as an extra parameter."""
    lead = game.agents[leader]
    followers = [a for i, a in enumerate(game.agents) if i != leader]
    symbols = {**game.symbols, str(lead.strategy): lead.strategy}
    return Game(name=game.name, agents=[Agent(a.name, a.strategy, a.utility, a.lower, a.upper) for a in followers],
                parameters={**game.parameters, str(lead.strategy): 0.0}, symbols=symbols,
                outcomes={}, closed_form=None, smooth=game.smooth)


def solve_stackelberg(game: Game, values: dict[str, float] | None = None, leader: int = 0) -> StackelbergResult:
    if len(game.agents) < 2:
        raise LocalizedError("err.stackelberg_agents")
    if not 0 <= leader < len(game.agents):
        raise LocalizedError("err.stackelberg_leader", index=leader)
    subs = game.substitutions(values)
    lead = game.agents[leader]
    lo, hi = float(lead.lower.subs(subs)), float(lead.upper.subs(subs))
    sub_game = _follower_game(game, leader)
    lead_name = str(lead.strategy)
    utility = sp.lambdify([a.strategy for a in game.agents], lead.utility.subs(subs), modules="numpy")
    order = [str(a.strategy) for a in game.agents]
    cache: dict[float, dict[str, float]] = {}
    last = {"start": None}

    def response(s_lead: float) -> dict[str, float] | None:
        key = round(float(s_lead), 14)
        if key in cache:
            return cache[key]
        params = {**(values or {}), lead_name: float(s_lead)}
        result = solve_equilibrium(sub_game, params, start=last["start"]) if last["start"] else None
        if result is None or not result.found:
            result = solve_equilibrium(sub_game, params)
        if not result.found:
            cache[key] = None
            return None
        cache[key] = result.equilibria[0].strategies
        last["start"] = cache[key]
        return cache[key]

    def leader_value(s_lead: float) -> float:
        reply = response(s_lead)
        if reply is None:
            return -np.inf
        profile = {**reply, lead_name: s_lead}
        with np.errstate(all="ignore"):
            value = float(np.real(utility(*[profile[n] for n in order])))
        return value if np.isfinite(value) else -np.inf

    grid = np.linspace(lo, hi, GRID_LEADER)
    values_grid = np.array([leader_value(g) for g in grid])
    if not np.isfinite(values_grid).any():
        raise LocalizedError("err.stackelberg_no_response")
    k = int(np.argmax(values_grid))
    a, b = grid[max(k - 1, 0)], grid[min(k + 1, GRID_LEADER - 1)]
    best_x, best_v = grid[k], values_grid[k]
    if b > a:
        res = minimize_scalar(lambda x: -leader_value(x), bounds=(a, b), method="bounded",
                              options={"xatol": 1e-10 * (1 + abs(b))})
        if -res.fun > best_v:
            best_x, best_v = float(res.x), float(-res.fun)

    # Check: no leader strategy on a fine grid does better than the optimum found.
    check = max(leader_value(g) for g in np.linspace(lo, hi, GRID_VERIFY)) - best_v
    reply = response(best_x)
    strategies = {**reply, lead_name: float(best_x)}
    profile = [strategies[n] for n in order]
    utils = {}
    for agent in game.agents:
        f = sp.lambdify([a.strategy for a in game.agents], agent.utility.subs(subs), modules="numpy")
        utils[agent.name] = float(np.real(f(*profile)))
    outcomes = {name: float(np.real(sp.lambdify([a.strategy for a in game.agents], e.subs(subs), modules="numpy")(*profile)))
                for name, e in game.outcomes.items()}
    simultaneous = solve_equilibrium(game, values)
    return StackelbergResult(leader=lead.name, strategies={n: strategies[n] for n in order}, utilities=utils,
                             outcomes=outcomes,
                             simultaneous=simultaneous.equilibria[0] if simultaneous.found else None,
                             leader_gain_check=float(check / (1 + abs(best_v))))
