"""
Catalogue of ready-made theoretical models (CAUSAL LAB spec:
theoretical-model).

Public choice:
    Downsian median voter, probabilistic voting (Lindbeck-Weibull),
    Tullock rent-seeking contest, Niskanen bureaucracy, voluntary
    public-good provision.
Market interaction:
    Cournot oligopoly, differentiated-products Bertrand duopoly.

Each builder returns a `Game`. Closed forms are given wherever the
literature has one; for smooth models they are used for display and
tests while the solver works numerically (see design.md).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import sympy as sp

from theory_engine.game import Agent, Game


def _syms(*names: str) -> list[sp.Symbol]:
    return [sp.Symbol(n, real=True) for n in names]


# --------------------------------------------------------------------------
# Public choice
# --------------------------------------------------------------------------
def downs_median_voter(n: int | None = None) -> Game:
    m, = _syms("m")
    xa, xb = _syms("xA", "xB")
    share_a = (1 + sp.sign(sp.Abs(xb - m) - sp.Abs(xa - m))) / 2
    return Game(
        name="Downsian median voter",
        agents=[Agent("Party A", xa, share_a, m - 1, m + 1),
                Agent("Party B", xb, 1 - share_a, m - 1, m + 1)],
        parameters={"m": 0.5}, symbols={"m": m},
        parameter_info={"m": "Median voter's ideal point (one-dimensional policy space)"},
        outcomes={"Policy distance between parties": sp.Abs(xa - xb)},
        closed_form={"xA": m, "xB": m}, smooth=False,
        description="Two office-seeking parties choose platforms on a line; voters with single-peaked "
                    "preferences vote for the closer platform. Both parties converge to the median "
                    "voter's ideal point.",
        references="Downs (1957); Black (1948).",
    )


def probabilistic_voting(n: int | None = None) -> Game:
    n1, n2, n3, b1, b2, b3, f1, f2, f3 = _syms("n1", "n2", "n3", "b1", "b2", "b3", "phi1", "phi2", "phi3")
    xa, xb = _syms("xA", "xB")
    groups = [(n1, b1, f1), (n2, b2, f2), (n3, b3, f3)]
    total = n1 + n2 + n3
    share_a = sp.Rational(1, 2) + sum(ng * fg * ((xb - bg) ** 2 - (xa - bg) ** 2) for ng, bg, fg in groups) / total
    weighted = sum(ng * fg * bg for ng, bg, fg in groups) / sum(ng * fg for ng, _, fg in groups)
    lo, hi = sp.Min(b1, b2, b3) - 1, sp.Max(b1, b2, b3) + 1
    return Game(
        name="Probabilistic voting",
        agents=[Agent("Party A", xa, share_a, lo, hi), Agent("Party B", xb, 1 - share_a, lo, hi)],
        parameters={"n1": 40, "n2": 35, "n3": 25, "b1": 0.2, "b2": 0.5, "b3": 0.9,
                    "phi1": 1.0, "phi2": 1.0, "phi3": 2.0},
        symbols={s.name: s for s in (n1, n2, n3, b1, b2, b3, f1, f2, f3)},
        parameter_info={"n1": "Size of group 1", "n2": "Size of group 2", "n3": "Size of group 3",
                        "b1": "Ideal policy of group 1", "b2": "Ideal policy of group 2",
                        "b3": "Ideal policy of group 3",
                        "phi1": "Electoral responsiveness (swing-voter density) of group 1",
                        "phi2": "Electoral responsiveness of group 2", "phi3": "Electoral responsiveness of group 3"},
        outcomes={"Equilibrium policy": xa, "Vote share of A": share_a},
        closed_form={"xA": weighted, "xB": weighted},
        description="Parties maximize expected vote share when voters' choices are subject to random "
                    "ideological shocks. Policy converges to an average of group ideal points weighted by "
                    "group size and responsiveness: responsive (swing) groups get more weight.",
        references="Lindbeck & Weibull (1987); Persson & Tabellini (2000), ch. 3.",
    )


def tullock_contest(n: int = 2) -> Game:
    xs = _syms(*[f"x{i}" for i in range(1, n + 1)])
    vs = _syms(*[f"V{i}" for i in range(1, n + 1)])
    total = sum(xs)
    agents = [Agent(f"Contestant {i + 1}", xs[i], vs[i] * xs[i] / total - xs[i], sp.Integer(0), vs[i])
              for i in range(n)]
    closed = None
    if n == 2:
        v1, v2 = vs
        closed = {"x1": v1 ** 2 * v2 / (v1 + v2) ** 2, "x2": v1 * v2 ** 2 / (v1 + v2) ** 2}
    return Game(
        name=f"Tullock rent-seeking contest ({n} contestants)",
        agents=agents,
        parameters={v.name: 10.0 for v in vs}, symbols={v.name: v for v in vs},
        parameter_info={v.name: f"Value of the rent (prize) for contestant {i + 1}" for i, v in enumerate(vs)},
        outcomes={"Total rent-seeking effort": total,
                  "Rent dissipation (total effort / largest prize)": total / sp.Max(*vs)},
        closed_form=closed,
        description="Interest groups spend resources to win a politically allocated rent; each wins with "
                    "probability proportional to its effort. With identical prizes each spends (n-1)V/n^2 "
                    "and a share (n-1)/n of the rent is dissipated.",
        references="Tullock (1980); Hillman & Riley (1989).",
    )


def niskanen_bureaucracy(n: int | None = None) -> Game:
    a, b, c, d = _syms("a", "b", "c", "d")
    q, = _syms("Q")
    budget = a * q - b * q ** 2 / 2
    cost = c * q + d * q ** 2 / 2
    utility = sp.Piecewise((budget, budget - cost >= -1e-9 * (1 + sp.Abs(budget))), (-1e9, True))
    q_social = (a - c) / (b + d)
    q_bureau = sp.Min(a / b, 2 * (a - c) / (b + d))
    return Game(
        name="Niskanen budget-maximizing bureau",
        agents=[Agent("Bureau", q, utility, sp.Integer(0), 2 * a / b)],
        parameters={"a": 10.0, "b": 1.0, "c": 2.0, "d": 1.0}, symbols={"a": a, "b": b, "c": c, "d": d},
        parameter_info={"a": "Sponsor's marginal valuation at zero output", "b": "Decline of marginal valuation",
                        "c": "Constant marginal cost", "d": "Increase of marginal cost"},
        outcomes={"Socially optimal output Q*": q_social, "Oversupply ratio Q/Q*": q / q_social,
                  "Budget B(Q)": budget},
        closed_form={"Q": q_bureau}, smooth=False,
        description="A bureau with a monopoly on supply maximizes its budget subject to covering its costs. "
                    "When budget-constrained it produces twice the socially optimal output.",
        references="Niskanen (1971); Mueller, Public Choice III (2003), ch. 16.",
    )


def public_good(n: int = 3) -> Game:
    gs = _syms(*[f"g{i}" for i in range(1, n + 1)])
    ws = _syms(*[f"w{i}" for i in range(1, n + 1)])
    alpha, = _syms("alpha")
    total = sum(gs)
    agents = [Agent(f"Citizen {i + 1}", gs[i],
                    alpha * sp.log(ws[i] - gs[i]) + (1 - alpha) * sp.log(total), sp.Integer(0), ws[i])
              for i in range(n)]
    return Game(
        name=f"Voluntary public-good provision ({n} contributors)",
        agents=agents,
        parameters={"alpha": 0.5, **{w.name: 10.0 for w in ws}},
        symbols={"alpha": alpha, **{w.name: w for w in ws}},
        parameter_info={"alpha": "Weight on private consumption (1 - alpha on the public good)",
                        **{w.name: f"Endowment (income) of citizen {i + 1}" for i, w in enumerate(ws)}},
        outcomes={"Total public good G": total},
        closed_form=None,
        description="Citizens split their income between private consumption and contributions to a public "
                    "good. Free riding leads to under-provision; poorer citizens may not contribute at all.",
        references="Bergstrom, Blume & Varian (1986); Samuelson (1954).",
    )


# --------------------------------------------------------------------------
# Market interaction
# --------------------------------------------------------------------------
def cournot(n: int = 2) -> Game:
    a, b = _syms("a", "b")
    qs = _syms(*[f"q{i}" for i in range(1, n + 1)])
    cs = _syms(*[f"c{i}" for i in range(1, n + 1)])
    total = sum(qs)
    price = a - b * total
    agents = [Agent(f"Firm {i + 1}", qs[i], (price - cs[i]) * qs[i], sp.Integer(0), a / b) for i in range(n)]
    closed = {q.name: (a - (n + 1) * cs[i] + sum(cs)) / ((n + 1) * b) for i, q in enumerate(qs)}
    return Game(
        name=f"Cournot oligopoly ({n} firms)",
        agents=agents,
        parameters={"a": 100.0, "b": 1.0, **{c.name: 10.0 for c in cs}},
        symbols={"a": a, "b": b, **{c.name: c for c in cs}},
        parameter_info={"a": "Demand intercept", "b": "Demand slope",
                        **{c.name: f"Marginal cost of firm {i + 1}" for i, c in enumerate(cs)}},
        outcomes={"Total quantity Q": total, "Market price P": price},
        closed_form=closed,
        description="Firms choose quantities simultaneously facing linear inverse demand P = a - bQ.",
        references="Cournot (1838); Tirole (1988), ch. 5.",
    )


def bertrand_differentiated(n: int | None = None) -> Game:
    a, b, d, c1, c2 = _syms("a", "b", "d", "c1", "c2")
    p1, p2 = _syms("p1", "p2")
    q1, q2 = a - b * p1 + d * p2, a - b * p2 + d * p1
    upper = 3 * a / (b - d) + c1 + c2
    den = 4 * b ** 2 - d ** 2
    return Game(
        name="Bertrand duopoly with differentiated products",
        agents=[Agent("Firm 1", p1, (p1 - c1) * q1, sp.Integer(0), upper),
                Agent("Firm 2", p2, (p2 - c2) * q2, sp.Integer(0), upper)],
        parameters={"a": 100.0, "b": 2.0, "d": 1.0, "c1": 10.0, "c2": 10.0},
        symbols={"a": a, "b": b, "d": d, "c1": c1, "c2": c2},
        parameter_info={"a": "Demand intercept", "b": "Own-price sensitivity",
                        "d": "Cross-price sensitivity (substitutability, d < b)",
                        "c1": "Marginal cost of firm 1", "c2": "Marginal cost of firm 2"},
        outcomes={"Quantity of firm 1": q1, "Quantity of firm 2": q2, "Average price": (p1 + p2) / 2},
        closed_form={"p1": (2 * b * (a + b * c1) + d * (a + b * c2)) / den,
                     "p2": (2 * b * (a + b * c2) + d * (a + b * c1)) / den},
        description="Two firms set prices for imperfect substitutes with linear demands q_i = a - b p_i + d p_j.",
        references="Singh & Vives (1984); Vives (1999).",
    )


@dataclass(frozen=True)
class CatalogueEntry:
    key: str
    label: str
    category: str
    builder: Callable[[int], Game]
    n_range: tuple[int, int] | None = None     # adjustable number of agents


CATALOGUE: dict[str, CatalogueEntry] = {e.key: e for e in (
    CatalogueEntry("downs", "Downsian median voter", "Public choice", downs_median_voter),
    CatalogueEntry("probabilistic_voting", "Probabilistic voting (3 groups)", "Public choice", probabilistic_voting),
    CatalogueEntry("tullock", "Tullock rent-seeking contest", "Public choice", tullock_contest, (2, 6)),
    CatalogueEntry("niskanen", "Niskanen bureaucracy", "Public choice", niskanen_bureaucracy),
    CatalogueEntry("public_good", "Voluntary public-good provision", "Public choice", public_good, (2, 6)),
    CatalogueEntry("cournot", "Cournot oligopoly", "Market interaction", cournot, (2, 6)),
    CatalogueEntry("bertrand", "Differentiated Bertrand duopoly", "Market interaction", bertrand_differentiated),
)}


def build(key: str, n_agents: int | None = None) -> Game:
    entry = CATALOGUE[key]
    if entry.n_range is None:
        return entry.builder(None)
    lo, hi = entry.n_range
    n = n_agents or lo
    if not lo <= n <= hi:
        raise ValueError(f"{entry.label} supports between {lo} and {hi} agents.")
    return entry.builder(n)
