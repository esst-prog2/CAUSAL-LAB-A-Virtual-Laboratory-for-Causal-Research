"""
Ready-made models with multidimensional strategies (see multidim.py).

- Two-dimensional probabilistic voting with logit vote probabilities.
- Multimarket Cournot oligopoly with a joint production cost.
- A contest over two prizes with a convex cost of total effort.

Each gives its equilibrium in closed form, derived from the first-order
conditions at the symmetric profile, so the numerical solver is checked
against it (tests/test_multidim.py).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import sympy as sp

from theory_engine.multidim import VectorAgent, VectorGame
from utils.i18n import LocalizedError, Msg


def _syms(*names: str) -> list[sp.Symbol]:
    return [sp.Symbol(n, real=True) for n in names]


def spatial_voting_2d(n: int | None = None) -> VectorGame:
    """Two parties choose platforms (x, y). A voter of group g weighs the
    second issue by s and votes for A with probability
    1 / (1 + exp(-phi_g (L_g(B) - L_g(A)))), L_g the quadratic loss from
    its ideal point. At a common platform every probability is 1/2, so
    the first-order conditions give the mean of the ideal points weighted
    by n_g phi_g, on each issue whatever s (Coughlin 1992; Lin, Enelow &
    Dorussen 1999)."""
    groups = [_syms(f"n{g}", f"bx{g}", f"by{g}", f"phi{g}") for g in (1, 2, 3)]
    s, = _syms("s")
    xa, ya, xb, yb = _syms("xA", "yA", "xB", "yB")

    def loss(x, y, bx, by):
        return (x - bx) ** 2 + s * (y - by) ** 2

    total = sum(ng for ng, *_ in groups)
    share_a = sum(ng / (1 + sp.exp(-fg * (loss(xb, yb, bx, by) - loss(xa, ya, bx, by))))
                  for ng, bx, by, fg in groups) / total
    weight = sum(ng * fg for ng, _, _, fg in groups)
    mean_x = sum(ng * fg * bx for ng, bx, _, fg in groups) / weight
    mean_y = sum(ng * fg * by for ng, _, by, fg in groups) / weight
    xs, ys = [bx for _, bx, _, _ in groups], [by for _, _, by, _ in groups]
    lower = [sp.Min(*xs) - 1, sp.Min(*ys) - 1]
    upper = [sp.Max(*xs) + 1, sp.Max(*ys) + 1]
    defaults = {"n1": 40, "bx1": 0.2, "by1": 0.8, "phi1": 1.0,
                "n2": 35, "bx2": 0.5, "by2": 0.2, "phi2": 1.0,
                "n3": 25, "bx3": 0.9, "by3": 0.6, "phi3": 2.0, "s": 1.0}
    info = {}
    for g in (1, 2, 3):
        info.update({f"n{g}": Msg("param.pv.size", g=g), f"bx{g}": Msg("param.md.ideal_x", g=g),
                     f"by{g}": Msg("param.md.ideal_y", g=g), f"phi{g}": Msg("param.pv.responsiveness", g=g)})
    info["s"] = Msg("param.md.salience")
    return VectorGame(
        name=Msg("model.md_voting.name"),
        agents=[VectorAgent(Msg("agent.party", label="A"), [xa, ya], share_a, lower, upper),
                VectorAgent(Msg("agent.party", label="B"), [xb, yb], 1 - share_a, lower, upper)],
        parameters=defaults, symbols={sym.name: sym for g in groups for sym in g} | {"s": s},
        parameter_info=info,
        outcomes={Msg("outcome.vote_share_a"): share_a,
                  Msg("outcome.platform_distance"): sp.sqrt((xa - xb) ** 2 + (ya - yb) ** 2)},
        closed_form={"xA": mean_x, "yA": mean_y, "xB": mean_x, "yB": mean_y},
        description=Msg("model.md_voting.description"),
        references="Coughlin (1992); Lin, Enelow & Dorussen (1999); Schofield (2007).",
    )


def multimarket_cournot(n: int = 2) -> VectorGame:
    """n firms sell in two markets with inverse demands a_k - b Q_k and
    marginal costs c_k, and pay a joint cost g/2 (q_1 + q_2)^2: selling
    more in one market raises the cost of the other (Bulow, Geanakoplos &
    Klemperer 1985). Symmetric first-order conditions:
    A_k - b (n + 1) q_k - g S = 0, A_k = a_k - c_k, S = q_1 + q_2; a firm
    leaves market k when A_k - g S <= 0 there."""
    a1, a2, c1, c2, b, g = _syms("a1", "a2", "c1", "c2", "b", "g")
    qs = [_syms(f"q{i}_1", f"q{i}_2") for i in range(1, n + 1)]
    big_q = [sum(q[k] for q in qs) for k in (0, 1)]
    agents = []
    for i, (q1, q2) in enumerate(qs):
        profit = (a1 - b * big_q[0] - c1) * q1 + (a2 - b * big_q[1] - c2) * q2 - g / 2 * (q1 + q2) ** 2
        agents.append(VectorAgent(Msg("agent.firm", i=i + 1), [q1, q2], profit,
                                  [sp.Integer(0), sp.Integer(0)], [a1 / b, a2 / b]))
    big_a1, big_a2, slope = a1 - c1, a2 - c2, b * (n + 1)
    both = (big_a1 + big_a2) / (slope + 2 * g)
    only_1, only_2 = big_a1 / (slope + g), big_a2 / (slope + g)
    q1_closed = sp.Piecewise(((big_a1 - g * both) / slope, (big_a1 - g * both > 0) & (big_a2 - g * both > 0)),
                             (only_1, (big_a1 > 0) & (big_a2 - g * only_1 <= 0)),
                             (0, True))
    q2_closed = sp.Piecewise(((big_a2 - g * both) / slope, (big_a1 - g * both > 0) & (big_a2 - g * both > 0)),
                             (only_2, (big_a2 > 0) & (big_a1 - g * only_2 <= 0)),
                             (0, True))
    closed = {}
    for q1, q2 in qs:
        closed[str(q1)], closed[str(q2)] = q1_closed, q2_closed
    return VectorGame(
        name=Msg("model.md_cournot.name", n=n),
        agents=agents,
        parameters={"a1": 100.0, "a2": 80.0, "c1": 10.0, "c2": 20.0, "b": 1.0, "g": 0.5},
        symbols={sym.name: sym for sym in (a1, a2, c1, c2, b, g)},
        parameter_info={"a1": Msg("param.md.demand", k=1), "a2": Msg("param.md.demand", k=2),
                        "c1": Msg("param.md.cost", k=1), "c2": Msg("param.md.cost", k=2),
                        "b": Msg("param.demand_slope"), "g": Msg("param.md.joint_cost")},
        outcomes={Msg("outcome.md_price", k=1): a1 - b * big_q[0], Msg("outcome.md_price", k=2): a2 - b * big_q[1],
                  Msg("outcome.md_quantity", k=1): big_q[0], Msg("outcome.md_quantity", k=2): big_q[1]},
        closed_form=closed,
        description=Msg("model.md_cournot.description"),
        references="Bulow, Geanakoplos & Klemperer (1985).",
    )


def two_prize_contest(n: int = 2) -> VectorGame:
    """n contestants split effort between two Tullock prizes V_1, V_2 and
    pay c/2 E^2 for total effort E. Symmetric first-order conditions:
    V_k (n - 1) / (n^2 x_k) = c E, so E = sqrt((n - 1)(V_1 + V_2) / c) / n
    and x_k = V_k (n - 1) / (n^2 c E): effort follows the prizes (Snyder
    1989; Konrad 2009)."""
    v1, v2, c = _syms("V1", "V2", "c")
    xs = [_syms(f"x{i}_1", f"x{i}_2") for i in range(1, n + 1)]
    totals = [sum(x[k] for x in xs) for k in (0, 1)]
    agents = [VectorAgent(Msg("agent.contestant", i=i + 1), [x1, x2],
                          v1 * x1 / totals[0] + v2 * x2 / totals[1] - c / 2 * (x1 + x2) ** 2,
                          [sp.Integer(0), sp.Integer(0)], [v1, v2])
              for i, (x1, x2) in enumerate(xs)]
    effort = sp.sqrt((n - 1) * (v1 + v2) / c) / n
    closed = {}
    for x1, x2 in xs:
        closed[str(x1)] = v1 * (n - 1) / (n ** 2 * c * effort)
        closed[str(x2)] = v2 * (n - 1) / (n ** 2 * c * effort)
    return VectorGame(
        name=Msg("model.md_contest.name", n=n),
        agents=agents,
        parameters={"V1": 10.0, "V2": 5.0, "c": 1.0},
        symbols={"V1": v1, "V2": v2, "c": c},
        parameter_info={"V1": Msg("param.md.prize", k=1), "V2": Msg("param.md.prize", k=2),
                        "c": Msg("param.md.effort_cost")},
        outcomes={Msg("outcome.md_effort", k=1): totals[0], Msg("outcome.md_effort", k=2): totals[1]},
        closed_form=closed,
        description=Msg("model.md_contest.description"),
        references="Snyder (1989); Konrad (2009).",
    )


@dataclass(frozen=True)
class VectorEntry:
    key: str
    label: Msg
    builder: Callable[[int | None], VectorGame]
    n_range: tuple[int, int] | None = None


VECTOR_CATALOGUE: dict[str, VectorEntry] = {e.key: e for e in (
    VectorEntry("md_voting", Msg("catalogue.md_voting"), spatial_voting_2d),
    VectorEntry("md_cournot", Msg("catalogue.md_cournot"), multimarket_cournot, (2, 4)),
    VectorEntry("md_contest", Msg("catalogue.md_contest"), two_prize_contest, (2, 4)),
)}


def build_vector(key: str, n_agents: int | None = None) -> VectorGame:
    entry = VECTOR_CATALOGUE[key]
    if entry.n_range is None:
        return entry.builder(None)
    lo, hi = entry.n_range
    n = n_agents or lo
    if not lo <= n <= hi:
        raise LocalizedError("err.catalogue_n", model=entry.label, lo=lo, hi=hi)
    return entry.builder(n)
