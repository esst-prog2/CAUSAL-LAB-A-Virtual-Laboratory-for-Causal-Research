import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sympy as sp

from theory_engine.catalogue import build
from theory_engine.game import best_responses, build_custom_game, comparative_statics, solve_equilibrium

TULLOCK_AGENTS = [
    dict(name="A", strategy="x1", lower="0", upper="V", utility="V*x1/(x1+x2) - x1"),
    dict(name="B", strategy="x2", lower="0", upper="V", utility="V*x2/(x1+x2) - x2"),
]


def test_cournot_best_response_is_textbook():
    br = best_responses(build("cournot", 2))
    a, b, c1, q2 = sp.symbols("a b c1 q2", real=True)
    assert len(br["Firm 1"]) == 1
    assert sp.simplify(br["Firm 1"][0] - (a - c1 - b * q2) / (2 * b)) == 0


def test_custom_tullock_solves_to_v_over_4():
    game = build_custom_game("Tullock", {"V": 12}, TULLOCK_AGENTS, {"total": "x1 + x2"})
    result = solve_equilibrium(game)
    assert len(result.equilibria) == 1
    eq = result.equilibria[0]
    assert eq.verified
    for x in eq.strategies.values():
        assert abs(x - 3.0) / 3.0 < 1e-4


def test_editor_rejects_unsafe_or_unknown_input():
    for bad in ("__import__('os')", "x1.real", "a[0]", "foo * x1", "lambda: 1", "x1; x2"):
        agents = [dict(TULLOCK_AGENTS[0], utility=bad), TULLOCK_AGENTS[1]]
        try:
            build_custom_game("bad", {"V": 1}, agents)
        except ValueError:
            continue
        raise AssertionError(f"accepted unsafe expression {bad!r}")


def test_editor_rejects_duplicate_names():
    agents = [dict(TULLOCK_AGENTS[0], strategy="V"), TULLOCK_AGENTS[1]]
    try:
        build_custom_game("dup", {"V": 1}, agents)
    except ValueError as exc:
        assert "distinct" in str(exc)
    else:
        raise AssertionError("duplicate names accepted")


def test_corner_solution_is_verified():
    game = build("public_good", 3)
    result = solve_equilibrium(game, {"w1": 30, "w2": 10, "w3": 2})
    eq = result.equilibria[0]
    assert eq.verified
    assert abs(eq.strategies["g1"] - 15.0) < 1e-3          # (1 - alpha) * w1
    assert eq.strategies["g2"] < 1e-6 and eq.strategies["g3"] < 1e-6


def test_no_pure_equilibrium_reported():
    pursuit = build_custom_game("pursuit", {}, [
        dict(name="Hunter", strategy="x1", lower="0", upper="1", utility="-(x1 - x2)^2"),
        dict(name="Prey", strategy="x2", lower="0", upper="1", utility="(x1 - x2)^2"),
    ])
    result = solve_equilibrium(pursuit)
    assert not result.found
    assert "No pure-strategy" in result.message


def test_cournot_comparative_statics_signs():
    game = build("cournot", 2)
    eq = solve_equilibrium(game).equilibria[0]
    d = comparative_statics(game, None, "c1", eq)
    assert d["q1"] < 0 < d["q2"]
    assert abs(d["q1"] - (-2 / 3)) < 1e-3                   # dq1/dc1 = -2/(3b)


if __name__ == "__main__":
    test_cournot_best_response_is_textbook()
    test_custom_tullock_solves_to_v_over_4()
    test_editor_rejects_unsafe_or_unknown_input()
    test_editor_rejects_duplicate_names()
    test_corner_solution_is_verified()
    test_no_pure_equilibrium_reported()
    test_cournot_comparative_statics_signs()
    print("test_theory_game: OK")
