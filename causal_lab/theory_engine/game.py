"""
Game engine for the Theoretical Model page (CAUSAL LAB specs:
theoretical-model, equilibrium-solver).

A `Game` is a set of agents. Each agent chooses one scalar strategy in
a bounded interval to maximize a utility that depends on everyone's
strategies and on named parameters. Utilities are sympy expressions,
so the same object serves three purposes:

- display: utilities, first-order conditions and best responses as
  LaTeX;
- closed-form solutions, where a model provides one;
- numerical Nash equilibria, solved by multi-start best-response
  iteration. A profile counts as an equilibrium only if no agent can
  gain by deviating unilaterally anywhere in its strategy space.

`build_custom_game` parses user-written expressions behind a token
whitelist, so free-text model input can never reach Python's eval with
anything but arithmetic on declared names.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import sympy as sp
from scipy.optimize import minimize_scalar
from sympy.parsing.sympy_parser import convert_xor, parse_expr, standard_transformations

PENALTY = -1e300                 # stands in for -inf / undefined utility values
GRID_BR = 64                     # grid points for a best response
GRID_VERIFY = 400                # grid points for the deviation check
GAIN_TOLERANCE = 1e-6            # relative tolerance for a profitable deviation


@dataclass
class Agent:
    name: str
    strategy: sp.Symbol
    utility: sp.Expr
    lower: sp.Expr
    upper: sp.Expr


@dataclass
class Game:
    name: str
    agents: list[Agent]
    parameters: dict[str, float]                                # name -> default value
    symbols: dict[str, sp.Symbol]                               # parameter name -> symbol
    parameter_info: dict[str, str] = field(default_factory=dict)
    outcomes: dict[str, sp.Expr] = field(default_factory=dict)
    closed_form: dict[str, sp.Expr] | None = None              # strategy name -> expression
    smooth: bool = True
    description: str = ""
    references: str = ""

    @property
    def strategies(self) -> list[sp.Symbol]:
        return [a.strategy for a in self.agents]

    def substitutions(self, values: dict[str, float] | None) -> dict:
        merged = {**self.parameters, **(values or {})}
        unknown = set(merged) - set(self.symbols)
        if unknown:
            raise ValueError(f"Unknown parameter(s): {sorted(unknown)}")
        return {self.symbols[k]: float(v) for k, v in merged.items()}


@dataclass
class Equilibrium:
    strategies: dict[str, float]
    utilities: dict[str, float]
    outcomes: dict[str, float]
    verified: bool
    max_gain: float
    method: str


@dataclass
class SolveResult:
    equilibria: list[Equilibrium]
    message: str = ""

    @property
    def found(self) -> bool:
        return bool(self.equilibria)


# --------------------------------------------------------------------------
# Symbolic derivations
# --------------------------------------------------------------------------
def first_order_conditions(game: Game) -> dict[str, sp.Expr] | None:
    """dU_i/ds_i for each agent (None for non-smooth models)."""
    if not game.smooth:
        return None
    return {a.name: sp.simplify(sp.diff(a.utility, a.strategy)) for a in game.agents}


def best_responses(game: Game, max_degree: int = 2) -> dict[str, list[sp.Expr] | None]:
    """Solve each FOC for the agent's own strategy when its numerator is
    a polynomial of low degree in that strategy; None otherwise (the
    best response is then only computed numerically)."""
    focs = first_order_conditions(game) or {}
    out: dict[str, list[sp.Expr] | None] = {}
    for agent in game.agents:
        foc = focs.get(agent.name)
        if foc is None:
            out[agent.name] = None
            continue
        numerator = sp.together(foc).as_numer_denom()[0]
        try:
            poly = sp.Poly(numerator, agent.strategy)
        except sp.PolynomialError:
            out[agent.name] = None
            continue
        if poly.degree() < 1 or poly.degree() > max_degree:
            out[agent.name] = None
            continue
        out[agent.name] = [sp.simplify(s) for s in sp.solve(numerator, agent.strategy)]
    return out


# --------------------------------------------------------------------------
# Numerical machinery
# --------------------------------------------------------------------------
def _safe(fn):
    def wrapped(*args) -> float:
        with np.errstate(all="ignore"):
            try:
                value = complex(fn(*args))
            except (ZeroDivisionError, ValueError, OverflowError, TypeError, FloatingPointError):
                return PENALTY
        if abs(value.imag) > 1e-12 or not np.isfinite(value.real):
            return PENALTY
        return float(value.real)
    return wrapped


class _NumericGame:
    def __init__(self, game: Game, values: dict[str, float] | None):
        self.game = game
        subs = game.substitutions(values)
        syms = game.strategies
        self.utils = [_safe(sp.lambdify(syms, a.utility.subs(subs), modules="numpy")) for a in game.agents]
        self.bounds = []
        for a in game.agents:
            lo, hi = float(a.lower.subs(subs)), float(a.upper.subs(subs))
            if not (np.isfinite(lo) and np.isfinite(hi)) or lo >= hi:
                raise ValueError(f"Strategy bounds of agent '{a.name}' are invalid for these parameter "
                                 f"values: [{lo:g}, {hi:g}].")
            self.bounds.append((lo, hi))
        self.outcome_fns = {k: _safe(sp.lambdify(syms, e.subs(subs), modules="numpy"))
                            for k, e in game.outcomes.items()}
        self.scale = np.array([hi - lo for lo, hi in self.bounds])

    def utility(self, i: int, s: np.ndarray) -> float:
        return self.utils[i](*s)

    def _maximize(self, i: int, s: np.ndarray, n_grid: int) -> tuple[float, float]:
        lo, hi = self.bounds[i]
        grid = np.linspace(lo, hi, n_grid)
        trial = s.copy()
        values = np.empty(n_grid)
        for k, g in enumerate(grid):
            trial[i] = g
            values[k] = self.utility(i, trial)
        k = int(np.argmax(values))
        best_x, best_v = grid[k], values[k]
        a, b = grid[max(k - 1, 0)], grid[min(k + 1, n_grid - 1)]
        if b > a:
            def neg(x):
                trial[i] = x
                return -self.utility(i, trial)
            res = minimize_scalar(neg, bounds=(a, b), method="bounded", options={"xatol": 1e-12 * (1 + abs(b))})
            if -res.fun > best_v:
                best_x, best_v = float(res.x), float(-res.fun)
        return best_x, best_v

    def best_response(self, i: int, s: np.ndarray) -> float:
        return self._maximize(i, s, GRID_BR)[0]

    def max_gain(self, s: np.ndarray) -> float:
        """Largest relative unilateral gain over all agents (<= tolerance means Nash)."""
        worst = 0.0
        for i in range(len(self.utils)):
            current = self.utility(i, s)
            _, best = self._maximize(i, s, GRID_VERIFY)
            if current <= PENALTY / 10:
                return np.inf
            worst = max(worst, (best - current) / (1 + abs(current)))
        return worst

    def iterate(self, s0: np.ndarray, known: list[np.ndarray] | None = None) -> np.ndarray:
        """Best-response iteration from s0. A bounded 1-D maximizer only
        locates an optimum to ~sqrt(machine eps) relative precision, so
        convergence is declared at 1e-8 of the strategy range. The run
        stops early once it is within 1e-6 of an equilibrium already
        found from another start."""
        s = s0.copy()
        tol = 1e-8

        def done(a, b):
            return np.max(np.abs(a - b) / self.scale) < tol

        def duplicate(a):
            return any(np.max(np.abs(a - k) / self.scale) < 1e-6 for k in (known or []))

        for _ in range(200):                       # Gauss-Seidel
            prev = s.copy()
            for i in range(len(s)):
                s[i] = self.best_response(i, s)
            if done(s, prev) or duplicate(s):
                return s
        for _ in range(300):                       # damped Jacobi fallback
            new = np.array([self.best_response(i, s) for i in range(len(s))])
            nxt = 0.5 * s + 0.5 * new
            if done(nxt, s) or duplicate(nxt):
                return nxt
            s = nxt
        return s

    def equilibrium(self, s: np.ndarray, method: str) -> Equilibrium:
        gain = self.max_gain(s)
        names = [a.name for a in self.game.agents]
        return Equilibrium(
            strategies={str(a.strategy): float(v) for a, v in zip(self.game.agents, s)},
            utilities={n: self.utility(i, s) for i, n in enumerate(names)},
            outcomes={k: f(*s) for k, f in self.outcome_fns.items()},
            verified=gain <= GAIN_TOLERANCE, max_gain=float(gain), method=method,
        )


def solve_equilibrium(game: Game, values: dict[str, float] | None = None, n_starts: int = 8,
                      seed: int = 0, start: dict[str, float] | None = None) -> SolveResult:
    """Pure-strategy Nash equilibria of `game` at the given parameter values."""
    num = _NumericGame(game, values)

    if game.closed_form is not None and not game.smooth:
        subs = game.substitutions(values)
        s = np.array([float(game.closed_form[str(a.strategy)].subs(subs)) for a in game.agents])
        eq = num.equilibrium(s, "closed form")
        if eq.verified:
            return SolveResult([eq], "Closed-form equilibrium (verified against unilateral deviations).")
        return SolveResult([], "The closed-form profile failed the deviation check at these parameter values.")

    rng = np.random.default_rng(seed)
    lows = np.array([b[0] for b in num.bounds])
    highs = np.array([b[1] for b in num.bounds])
    starts = []
    if start is not None:
        starts.append(np.array([start[str(a.strategy)] for a in game.agents], dtype=float))
    else:
        starts.append((lows + highs) / 2)
        starts.extend(lows + rng.random(len(lows)) * (highs - lows) for _ in range(max(0, n_starts - 1)))

    found: list[Equilibrium] = []
    for s0 in starts:
        known = [np.array(list(f.strategies.values())) for f in found]
        s = num.iterate(np.clip(s0, lows, highs), known)
        eq = num.equilibrium(s, "numerical best-response iteration")
        if not eq.verified:
            continue
        vec = np.array(list(eq.strategies.values()))
        if all(np.max(np.abs(vec - np.array(list(f.strategies.values()))) / num.scale) > 1e-4 for f in found):
            found.append(eq)
    if not found:
        return SolveResult([], "No pure-strategy Nash equilibrium was found: best-response iteration did not "
                               "reach a profile without profitable unilateral deviations.")
    msg = "Unique equilibrium found." if len(found) == 1 else f"{len(found)} distinct equilibria found."
    return SolveResult(found, msg)


def comparative_statics(game: Game, values: dict[str, float] | None, parameter: str,
                        equilibrium: Equilibrium) -> dict[str, float]:
    """d(strategy or outcome)/d(parameter) by central differences,
    re-solving from `equilibrium` to stay on the same branch."""
    base = {**game.parameters, **(values or {})}
    theta = float(base[parameter])
    # Equilibria are located to ~1e-8 relative precision, so h must stay
    # well above that; central differences keep the O(h^2) error small.
    h = 1e-3 * max(1.0, abs(theta))
    points = []
    for sign in (1, -1):
        shifted = {**base, parameter: theta + sign * h}
        res = solve_equilibrium(game, shifted, start=equilibrium.strategies)
        if not res.found:
            return {k: float("nan") for k in (*equilibrium.strategies, *equilibrium.outcomes)}
        points.append(res.equilibria[0])
    up, down = points
    out = {k: (up.strategies[k] - down.strategies[k]) / (2 * h) for k in equilibrium.strategies}
    out.update({k: (up.outcomes[k] - down.outcomes[k]) / (2 * h) for k in equilibrium.outcomes})
    return out


# --------------------------------------------------------------------------
# Safe parsing for the free editor
# --------------------------------------------------------------------------
ALLOWED_FUNCTIONS = {"log": sp.log, "exp": sp.exp, "sqrt": sp.sqrt, "Abs": sp.Abs, "Min": sp.Min, "Max": sp.Max}
_TOKEN = re.compile(r"\s*(?:(?P<num>(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)|(?P<name>[A-Za-z][A-Za-z0-9_]*)"
                    r"|(?P<op>\*\*|[-+*/^(),]))")
_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_GLOBALS = {"Integer": sp.Integer, "Float": sp.Float, "Rational": sp.Rational, "Symbol": sp.Symbol}


def _check_tokens(text: str, allowed_names: set[str], where: str) -> None:
    if not text.strip():
        raise ValueError(f"{where}: the expression is empty.")
    for bad in ("__", "[", "]", "'", '"', "lambda", ";", ":", "\\"):
        if bad in text:
            raise ValueError(f"{where}: '{bad}' is not allowed in an expression.")
    pos = 0
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            if text[pos:].strip() == "":
                break
            raise ValueError(f"{where}: unexpected character '{text[pos:].strip()[0]}'.")
        name = m.group("name")
        if name is not None and name not in allowed_names and name not in ALLOWED_FUNCTIONS:
            raise ValueError(f"{where}: unknown name '{name}' (declare it as a parameter or strategy).")
        pos = m.end()


def parse_expression(text: str, symbols: dict[str, sp.Symbol], where: str = "Expression") -> sp.Expr:
    _check_tokens(text, set(symbols), where)
    try:
        expr = parse_expr(text, local_dict={**symbols, **ALLOWED_FUNCTIONS}, global_dict=dict(_GLOBALS),
                          transformations=standard_transformations + (convert_xor,))
    except Exception as exc:          # syntax errors from the tokenizer-approved text
        raise ValueError(f"{where}: could not parse the expression ({exc}).") from None
    return sp.sympify(expr)


def build_custom_game(name: str, parameters: dict[str, float], agents: list[dict],
                      outcomes: dict[str, str] | None = None) -> Game:
    """Build a Game from user text. `agents` items have keys
    name, strategy, lower, upper, utility (strings)."""
    if len(agents) < 1:
        raise ValueError("Declare at least one agent.")
    names = list(parameters) + [a["strategy"].strip() for a in agents]
    for n in names:
        if not _NAME.match(n) or "__" in n or n in ALLOWED_FUNCTIONS:
            raise ValueError(f"'{n}' is not a valid parameter or strategy name.")
    if len(set(names)) != len(names):
        raise ValueError("Parameter and strategy names must all be distinct.")

    param_syms = {k: sp.Symbol(k, real=True) for k in parameters}
    strat_syms = {a["strategy"].strip(): sp.Symbol(a["strategy"].strip(), real=True) for a in agents}
    all_syms = {**param_syms, **strat_syms}
    built = []
    for a in agents:
        label = a.get("name") or a["strategy"]
        built.append(Agent(
            name=label, strategy=strat_syms[a["strategy"].strip()],
            utility=parse_expression(a["utility"], all_syms, f"Utility of {label}"),
            lower=parse_expression(str(a["lower"]), param_syms, f"Lower bound of {label}"),
            upper=parse_expression(str(a["upper"]), param_syms, f"Upper bound of {label}"),
        ))
    parsed_outcomes = {k: parse_expression(v, all_syms, f"Outcome '{k}'") for k, v in (outcomes or {}).items()}
    return Game(name=name, agents=built, parameters={k: float(v) for k, v in parameters.items()},
                symbols=param_syms, outcomes=parsed_outcomes, description="Custom model")
