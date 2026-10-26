"""Games with multidimensional strategies, against closed forms and sympy."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sympy as sp

from theory_engine.multidim import build_vector_game, closed_form_values, solve_vector_equilibrium
from theory_engine.vector_catalogue import build_vector
from utils.i18n import LocalizedError

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _raises_key(key, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except LocalizedError as exc:
        assert exc.msg.key == key, exc.msg.key
    else:
        raise AssertionError(key)


def _matches_closed_form(key, n, values, tol=1e-7):
    game = build_vector(key, n)
    result = solve_vector_equilibrium(game, values)
    closed = closed_form_values(game, values)
    assert len(result.equilibria) == 1, (key, values, len(result.equilibria))
    eq = result.equilibria[0]
    for name, value in closed.items():
        assert abs(eq.strategies[name] - value) <= tol * max(1.0, abs(value)), (key, name, eq.strategies[name], value)
    assert eq.verified
    return eq


def test_two_issue_voting_converges_to_the_weighted_mean():
    # n*phi weights 40, 35, 50: x = (8 + 17.5 + 45) / 125 = 0.564, y = (32 + 7 + 30) / 125 = 0.552.
    eq = _matches_closed_form("md_voting", None, None)
    assert abs(eq.strategies["xA"] - 0.564) < 1e-7 and abs(eq.strategies["yA"] - 0.552) < 1e-7
    # The weight of issue 2 changes how voters trade the issues off, not where the parties meet.
    _matches_closed_form("md_voting", None, {"s": 3.0})
    _matches_closed_form("md_voting", None, {"phi1": 0.5, "bx2": 0.1, "by3": 0.9})


def test_multimarket_cournot_interior_and_corner():
    eq = _matches_closed_form("md_cournot", 2, None)
    assert abs(eq.strategies["q1_1"] - 23.75) < 1e-7 and abs(eq.strategies["q1_2"] - 13.75) < 1e-7
    _matches_closed_form("md_cournot", 3, {"g": 2.0})
    # Market 2 barely profitable: firms leave it, q_1 = (a1 - c1) / (3b + g) = 90 / 3.5.
    eq = _matches_closed_form("md_cournot", 2, {"a2": 25.0})
    assert eq.strategies["q1_2"] == 0.0 and abs(eq.strategies["q1_1"] - 90 / 3.5) < 1e-7


def test_two_prize_contest():
    eq = _matches_closed_form("md_contest", 2, None)
    effort = 15 ** 0.5 / 2                                   # sqrt((n - 1)(V1 + V2) / c) / n
    assert abs(eq.strategies["x1_1"] - 10 / (4 * effort)) < 1e-7
    _matches_closed_form("md_contest", 3, {"V2": 2.0, "c": 0.5})


def test_asymmetric_game_matches_sympy():
    # Firm-specific costs and a cross term: no symmetric closed form, but the
    # first-order conditions are linear and every profit is concave.
    agents = [dict(name="F1", strategies="u1, u2", lower="0", upper="100, 80",
                   utility="(100 - (u1+v1))*u1 + (80 - (u2+v2))*u2 - 10*u1 - 25*u2 - g1/2*(u1+u2)^2"),
              dict(name="F2", strategies="v1, v2", lower="0", upper="100, 80",
                   utility="(100 - (u1+v1))*v1 + (80 - (u2+v2))*v2 - 15*v1 - 18*v2 - g2/2*(v1+v2)^2 - 0.5*v1*v2")]
    game = build_vector_game("asym", {"g1": 0.4, "g2": 1.2}, agents)
    eq = solve_vector_equilibrium(game).equilibria[0]
    subs = game.substitutions(None)
    focs = [sp.diff(a.utility.subs(subs), s) for a in game.agents for s in a.strategies]
    exact = sp.solve(focs, game.strategies, dict=True)[0]
    for s in game.strategies:
        assert abs(eq.strategies[str(s)] / float(exact[s]) - 1) < 1e-9, s


def test_non_concave_agent_ends_at_a_kkt_corner():
    # With -3 v1 v2, F2's profit is not concave: the interior solution of the
    # first-order conditions is a saddle. The equilibrium has v2 = 0, and there
    # dU2/dv2 < 0 (Karush-Kuhn-Tucker).
    agents = [dict(name="F1", strategies="u1, u2", lower="0", upper="100, 80",
                   utility="(100 - (u1+v1))*u1 + (80 - (u2+v2))*u2 - 10*u1 - 25*u2 - 0.2*(u1+u2)^2"),
              dict(name="F2", strategies="v1, v2", lower="0", upper="100, 80",
                   utility="(100 - (u1+v1))*v1 + (80 - (u2+v2))*v2 - 15*v1 - 18*v2 - 0.6*(v1+v2)^2 - 3*v1*v2")]
    game = build_vector_game("corner", {}, agents)
    eq = solve_vector_equilibrium(game).equilibria[0]
    u1, u2, v1, v2 = game.strategies
    focs = {s: sp.diff(a.utility, s) for a in game.agents for s in a.strategies}
    exact = sp.solve([focs[s].subs(v2, 0) for s in (u1, u2, v1)], [u1, u2, v1], dict=True)[0] | {v2: 0}
    assert eq.strategies["v2"] == 0.0
    for s in (u1, u2, v1):
        assert abs(eq.strategies[str(s)] / float(exact[s]) - 1) < 1e-9, s
    assert float(focs[v2].subs(exact)) < 0


def test_one_dimensional_case_is_the_scalar_tullock_contest():
    game = build_vector_game("t", {"V1": 10.0, "V2": 6.0},
                             [dict(name="1", strategies="x", lower="0", upper="V1", utility="V1*x/(x+y) - x"),
                              dict(name="2", strategies="y", lower="0", upper="V2", utility="V2*y/(x+y) - y")])
    eq = solve_vector_equilibrium(game).equilibria[0]
    assert abs(eq.strategies["x"] - 100 * 6 / 256) < 1e-9 and abs(eq.strategies["y"] - 10 * 36 / 256) < 1e-9


def test_global_best_response_with_two_peaks():
    # One agent, two peaks: a broad local one at (0.6, 0.6) and a narrow, higher one at
    # (0.1, 0.9). Local search from the centre climbs the broad peak; only the grid over
    # the whole box finds the global one.
    game = build_vector_game("peaks", {}, [dict(
        name="A", strategies="x, y", lower="0", upper="1",
        utility="exp(-5*((x-0.6)^2 + (y-0.6)^2)) + 1.5*exp(-40*((x-0.1)^2 + (y-0.9)^2))")])
    result = solve_vector_equilibrium(game)
    assert len(result.equilibria) == 1
    eq = result.equilibria[0]
    # The broad peak shifts the maximum slightly away from (0.1, 0.9); the gradient is zero there.
    assert abs(eq.strategies["x"] - 0.1) < 0.01 and abs(eq.strategies["y"] - 0.9) < 0.01
    x, y = game.strategies
    u = game.agents[0].utility
    point = {x: eq.strategies["x"], y: eq.strategies["y"]}
    assert max(abs(float(sp.diff(u, v).subs(point))) for v in (x, y)) < 1e-8


def test_no_pure_equilibrium_is_reported_as_none():
    # Pursuit-evasion on the unit square: the pursuer wants to match, the evader to be far.
    game = build_vector_game("pe", {}, [
        dict(name="P", strategies="a1, a2", lower="0", upper="1", utility="-((a1-b1)^2 + (a2-b2)^2)"),
        dict(name="E", strategies="b1, b2", lower="0", upper="1", utility="(a1-b1)^2 + (a2-b2)^2")])
    assert not solve_vector_equilibrium(game, n_starts=2).found


def test_editor_errors():
    ok = dict(name="A", strategies="x, y", lower="0", upper="1", utility="-x^2 - y^2")
    _raises_key("err.vector_bounds_count", build_vector_game, "g", {}, [{**ok, "upper": "1, 2, 3"}])
    _raises_key("err.vector_dimensions", build_vector_game, "g", {}, [{**ok, "strategies": "a, b, c, d, e"}])
    _raises_key("err.game_duplicate_names", build_vector_game, "g", {}, [ok, {**ok, "name": "B"}])
    _raises_key("err.game_bad_name", build_vector_game, "g", {}, [{**ok, "strategies": "x, __y"}])
    _raises_key("err.vector_agents", build_vector_game, "g", {}, [])
    _raises_key("err.game_bounds", solve_vector_equilibrium,
                build_vector_game("g", {}, [{**ok, "lower": "0, 2", "upper": "1"}]))


def test_multidim_kind_on_the_theory_page():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=300)
    at.session_state["page"] = "theory"
    at.run()
    at.radio(key="th_kind").set_value("multidim").run()
    next(b for b in at.button if b.key == "md_solve").click().run()
    assert not at.exception, [e.value for e in at.exception]
    eq = at.session_state["md_result"][1].equilibria[0]
    assert abs(eq.strategies["xA"] - 0.564) < 1e-7
    at.radio(key="md_mode").set_value("editor").run()
    next(b for b in at.button if b.key == "md_ed_build").click().run()
    next(b for b in at.button if b.key == "md_solve").click().run()
    assert not at.exception, [e.value for e in at.exception]
    eq = at.session_state["md_result"][1].equilibria[0]
    # Default editor game: quadratic, concave; first-order conditions are linear in the four variables.
    assert eq.verified and 0.3 < eq.strategies["xA"] < eq.strategies["xB"] < 0.8


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("test_multidim: OK")
