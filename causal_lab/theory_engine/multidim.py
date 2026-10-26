"""
Games with multidimensional strategies (README section 3, "Not this term":
multidimensional strategies; built on 2026-10-26).

Each agent chooses a point in a box of R^d, d <= MAX_DIMENSIONS: a party's
platform on two issues, a firm's quantities in two markets, a contestant's
effort on two prizes. The scalar `Game` of game.py is left untouched (the
Stackelberg solver and calibration rely on it); this module mirrors its
method in vector form.

- Best response: the agent's utility is evaluated on a grid over its box
  (GRID_BR points per axis), then maximized by L-BFGS-B with the analytic
  gradient from the best grid points and from the current strategy.
- Equilibrium: multi-start Gauss-Seidel best-response iteration (damped
  Jacobi as fallback), then the Karush-Kuhn-Tucker conditions are polished
  by Newton's method on the coordinates that are not at a bound, with the
  analytic Jacobian. A bounded maximizer alone locates an optimum to about
  1e-8; the polish brings an interior equilibrium to about 1e-12.
- A profile is reported only if no agent gains more than GAIN_TOLERANCE
  (relative) by deviating anywhere in its box: finer grid plus local
  searches from its best points, as in game.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import sympy as sp
from scipy.optimize import minimize, root

from theory_engine.game import (ALLOWED_FUNCTIONS, GAIN_TOLERANCE, PENALTY, Equilibrium, SolveResult, _safe,
                                parse_expression)
from utils.i18n import LocalizedError, Msg

MAX_DIMENSIONS = 4
MAX_AGENTS = 6
# Grid points per axis. The products (64, 289, 343, 625 for a best response)
# keep one best response around a millisecond-scale budget per dimension count.
GRID_BR = {1: 64, 2: 17, 3: 7, 4: 5}
GRID_VERIFY = {1: 400, 2: 41, 3: 13, 4: 7}
N_LOCAL_BR = 3                   # local searches started from the best grid points
N_LOCAL_VERIFY = 6
_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


@dataclass
class VectorAgent:
    name: str
    strategies: list[sp.Symbol]
    utility: sp.Expr
    lower: list[sp.Expr]
    upper: list[sp.Expr]


@dataclass
class VectorGame:
    name: str
    agents: list[VectorAgent]
    parameters: dict[str, float]
    symbols: dict[str, sp.Symbol]
    parameter_info: dict[str, str] = field(default_factory=dict)
    outcomes: dict[str, sp.Expr] = field(default_factory=dict)
    closed_form: dict[str, sp.Expr] | None = None
    description: str = ""
    references: str = ""

    def __post_init__(self):
        if not 1 <= len(self.agents) <= MAX_AGENTS:
            raise LocalizedError("err.vector_agents", max=MAX_AGENTS)
        for a in self.agents:
            if not 1 <= len(a.strategies) <= MAX_DIMENSIONS:
                raise LocalizedError("err.vector_dimensions", agent=a.name, max=MAX_DIMENSIONS)
            if len(a.lower) != len(a.strategies) or len(a.upper) != len(a.strategies):
                raise LocalizedError("err.vector_bounds_count", agent=a.name, n=len(a.strategies))

    @property
    def strategies(self) -> list[sp.Symbol]:
        return [s for a in self.agents for s in a.strategies]

    def substitutions(self, values: dict[str, float] | None) -> dict:
        merged = {**self.parameters, **(values or {})}
        unknown = set(merged) - set(self.symbols)
        if unknown:
            raise LocalizedError("err.game_unknown_params", names=", ".join(sorted(unknown)))
        return {self.symbols[k]: float(v) for k, v in merged.items()}


def _safe_vector(fn):
    def wrapped(s: np.ndarray) -> np.ndarray | None:
        with np.errstate(all="ignore"):
            try:
                value = np.asarray(fn(*s), dtype=float)
            except (ZeroDivisionError, ValueError, OverflowError, TypeError, FloatingPointError):
                return None
        return value if np.all(np.isfinite(value)) else None
    return wrapped


class _NumericVectorGame:
    def __init__(self, game: VectorGame, values: dict[str, float] | None):
        self.game = game
        subs = game.substitutions(values)
        syms = game.strategies
        self.slices, pos = [], 0
        lows, highs = [], []
        for a in game.agents:
            self.slices.append(slice(pos, pos + len(a.strategies)))
            pos += len(a.strategies)
            for s, lo_e, hi_e in zip(a.strategies, a.lower, a.upper):
                lo, hi = float(lo_e.subs(subs)), float(hi_e.subs(subs))
                if not (np.isfinite(lo) and np.isfinite(hi)) or lo >= hi:
                    raise LocalizedError("err.game_bounds", agent=a.name, lo=lo, hi=hi)
                lows.append(lo)
                highs.append(hi)
        self.lows, self.highs = np.array(lows), np.array(highs)
        self.scale = self.highs - self.lows
        utilities = [a.utility.subs(subs) for a in game.agents]
        self.raw_utils = [sp.lambdify(syms, u, modules="numpy") for u in utilities]
        self.utils = [_safe(f) for f in self.raw_utils]
        gradients = [[sp.diff(u, s) for s in a.strategies] for a, u in zip(game.agents, utilities)]
        self.grads = [_safe_vector(sp.lambdify(syms, g, modules="numpy")) for g in gradients]
        stacked = sp.Matrix([g for gs in gradients for g in gs])
        self.kkt = _safe_vector(sp.lambdify(syms, list(stacked), modules="numpy"))
        self.kkt_jac = _safe_vector(sp.lambdify(syms, stacked.jacobian(syms), modules="numpy"))
        self.outcome_fns = {k: _safe(sp.lambdify(syms, e.subs(subs), modules="numpy"))
                            for k, e in game.outcomes.items()}

    def utility(self, i: int, s: np.ndarray) -> float:
        return self.utils[i](*s)

    def _grid_values(self, i: int, s: np.ndarray, points: np.ndarray) -> np.ndarray:
        """Agent i's utility at each grid point, the others fixed at s: one
        array call of the lambdified utility, or point by point when the
        expression does not broadcast (Min / Max of mixed shapes)."""
        sl = self.slices[i]
        args = [np.full(len(points), v) for v in s]
        for k, col in enumerate(range(sl.start, sl.stop)):
            args[col] = points[:, k]
        with np.errstate(all="ignore"):
            try:
                values = np.asarray(self.raw_utils[i](*args), dtype=complex)
                if values.shape == (len(points),):
                    real = values.real.copy()
                    real[~np.isfinite(values) | (np.abs(values.imag) > 1e-12)] = PENALTY
                    return real
            except (ZeroDivisionError, ValueError, OverflowError, TypeError, FloatingPointError):
                pass
        trial = s.copy()
        values = np.empty(len(points))
        for k, p in enumerate(points):
            trial[sl] = p
            values[k] = self.utility(i, trial)
        return values

    def _maximize(self, i: int, s: np.ndarray, grid: dict[int, int], n_local: int) -> tuple[np.ndarray, float]:
        sl = self.slices[i]
        lo, hi = self.lows[sl], self.highs[sl]
        d = len(lo)
        axes = [np.linspace(lo[k], hi[k], grid[d]) for k in range(d)]
        points = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1).reshape(-1, d)
        trial = s.copy()
        values = self._grid_values(i, s, points)
        order = np.argsort(values)[::-1]
        best_x, best_v = points[order[0]].copy(), float(values[order[0]])

        def neg(x):
            trial[sl] = x
            return -self.utility(i, trial)

        def neg_grad(x):
            trial[sl] = x
            g = self.grads[i](trial)
            return -g if g is not None else np.zeros(d)

        for x0 in [points[k] for k in order[:n_local]] + [s[sl].copy()]:
            trial[sl] = x0
            if self.utility(i, trial) <= PENALTY / 10:
                continue
            jac = neg_grad if self.grads[i](trial) is not None else None
            res = minimize(neg, x0, jac=jac, method="L-BFGS-B", bounds=list(zip(lo, hi)),
                           options={"ftol": 1e-15, "gtol": 1e-12, "maxiter": 500})
            x = np.clip(res.x, lo, hi)
            trial[sl] = x
            v = self.utility(i, trial)
            if v > best_v:
                best_x, best_v = x, v
        return best_x, best_v

    def best_response(self, i: int, s: np.ndarray) -> np.ndarray:
        return self._maximize(i, s, GRID_BR, N_LOCAL_BR)[0]

    def max_gain(self, s: np.ndarray) -> float:
        worst = 0.0
        for i in range(len(self.utils)):
            current = self.utility(i, s)
            if current <= PENALTY / 10:
                return np.inf
            _, best = self._maximize(i, s, GRID_VERIFY, N_LOCAL_VERIFY)
            worst = max(worst, (best - current) / (1 + abs(current)))
        return worst

    def iterate(self, s0: np.ndarray, known: list[np.ndarray]) -> np.ndarray:
        s = s0.copy()

        def done(a, b):
            return np.max(np.abs(a - b) / self.scale) < 1e-8

        def duplicate(a):
            return any(np.max(np.abs(a - k) / self.scale) < 1e-6 for k in known)

        for _ in range(200):                       # Gauss-Seidel
            prev = s.copy()
            for i, sl in enumerate(self.slices):
                s[sl] = self.best_response(i, s)
            if done(s, prev) or duplicate(s):
                return s
        for _ in range(300):                       # damped Jacobi fallback
            new = s.copy()
            for i, sl in enumerate(self.slices):
                new[sl] = self.best_response(i, s)
            nxt = 0.5 * s + 0.5 * new
            if done(nxt, s) or duplicate(nxt):
                return nxt
            s = nxt
        return s

    def polish(self, s: np.ndarray) -> np.ndarray:
        """Newton on the first-order conditions of the coordinates that are
        not at a bound; returns s unchanged if that fails or leaves the box."""
        free = (s - self.lows > 1e-9 * self.scale) & (self.highs - s > 1e-9 * self.scale)
        if not free.any() or self.kkt(s) is None or self.kkt_jac(s) is None:
            return s

        def eqs(z):
            x = s.copy()
            x[free] = z
            g = self.kkt(x)
            return g[free] if g is not None else np.full(free.sum(), 1e10)

        def jac(z):
            x = s.copy()
            x[free] = z
            j = self.kkt_jac(x)
            return j[np.ix_(free, free)] if j is not None else np.eye(free.sum())

        res = root(eqs, s[free], jac=jac, method="hybr", options={"xtol": 1e-14})
        polished = s.copy()
        polished[free] = res.x
        inside = np.all(polished >= self.lows) and np.all(polished <= self.highs)
        close = np.max(np.abs(polished - s) / self.scale) < 1e-4       # same equilibrium, not another root
        return polished if res.success and inside and close else s

    def equilibrium(self, s: np.ndarray, method: str) -> Equilibrium:
        gain = self.max_gain(s)
        return Equilibrium(
            strategies={str(sym): float(v) for sym, v in zip(self.game.strategies, s)},
            utilities={a.name: self.utility(i, s) for i, a in enumerate(self.game.agents)},
            outcomes={k: f(*s) for k, f in self.outcome_fns.items()},
            verified=gain <= GAIN_TOLERANCE, max_gain=float(gain), method=method,
        )


def solve_vector_equilibrium(game: VectorGame, values: dict[str, float] | None = None, n_starts: int = 8,
                             seed: int = 0, start: dict[str, float] | None = None) -> SolveResult:
    """Pure-strategy Nash equilibria of a game with vector strategies."""
    num = _NumericVectorGame(game, values)
    rng = np.random.default_rng(seed)
    if start is not None:
        starts = [np.array([start[str(s)] for s in game.strategies], dtype=float)]
    else:
        starts = [(num.lows + num.highs) / 2]
        starts.extend(num.lows + rng.random(len(num.lows)) * num.scale for _ in range(max(0, n_starts - 1)))

    found: list[Equilibrium] = []
    for s0 in starts:
        known = [np.array(list(f.strategies.values())) for f in found]
        s = num.polish(num.iterate(np.clip(s0, num.lows, num.highs), known))
        eq = num.equilibrium(s, "vector best-response iteration + KKT polish")
        if not eq.verified:
            continue
        vec = np.array(list(eq.strategies.values()))
        if all(np.max(np.abs(vec - np.array(list(f.strategies.values()))) / num.scale) > 1e-4 for f in found):
            found.append(eq)
    if not found:
        return SolveResult([], Msg("solve.none"))
    return SolveResult(found, Msg("solve.unique") if len(found) == 1 else Msg("solve.several", n=len(found)))


def closed_form_values(game: VectorGame, values: dict[str, float] | None) -> dict[str, float] | None:
    if game.closed_form is None:
        return None
    subs = game.substitutions(values)
    return {k: float(e.subs(subs)) for k, e in game.closed_form.items()}


# --------------------------------------------------------------------------
# Free editor
# --------------------------------------------------------------------------
def _split(text: str) -> list[str]:
    return [p.strip() for p in str(text).split(",") if p.strip()]


def build_vector_game(name: str, parameters: dict[str, float], agents: list[dict],
                      outcomes: dict[str, str] | None = None) -> VectorGame:
    """Build a VectorGame from user text. `agents` items have keys name,
    strategies ("x, y"), lower and upper (one value per strategy, or one
    value for all), utility."""
    if not 1 <= len(agents) <= MAX_AGENTS:
        raise LocalizedError("err.vector_agents", max=MAX_AGENTS)
    strategy_names = [_split(a["strategies"]) for a in agents]
    names = list(parameters) + [s for names in strategy_names for s in names]
    for n in names:
        if not _NAME.match(n) or "__" in n or n in ALLOWED_FUNCTIONS:
            raise LocalizedError("err.game_bad_name", name=n)
    if len(set(names)) != len(names):
        raise LocalizedError("err.game_duplicate_names")

    param_syms = {k: sp.Symbol(k, real=True) for k in parameters}
    strat_syms = {s: sp.Symbol(s, real=True) for names in strategy_names for s in names}
    all_syms = {**param_syms, **strat_syms}
    built = []
    for a, own in zip(agents, strategy_names):
        label = a.get("name") or ", ".join(own)
        if not 1 <= len(own) <= MAX_DIMENSIONS:
            raise LocalizedError("err.vector_dimensions", agent=label, max=MAX_DIMENSIONS)
        bounds = []
        for key, where in (("lower", "where.lower"), ("upper", "where.upper")):
            parts = _split(a[key])
            if len(parts) == 1:
                parts = parts * len(own)
            if len(parts) != len(own):
                raise LocalizedError("err.vector_bounds_count", agent=label, n=len(own))
            bounds.append([parse_expression(p, param_syms, Msg(where, agent=label)) for p in parts])
        built.append(VectorAgent(
            name=label, strategies=[strat_syms[s] for s in own],
            utility=parse_expression(a["utility"], all_syms, Msg("where.utility", agent=label)),
            lower=bounds[0], upper=bounds[1]))
    parsed_outcomes = {k: parse_expression(v, all_syms, Msg("where.outcome", name=k))
                       for k, v in (outcomes or {}).items()}
    return VectorGame(name=name, agents=built, parameters={k: float(v) for k, v in parameters.items()},
                      symbols=param_syms, outcomes=parsed_outcomes, description=Msg("model.custom.description"))
