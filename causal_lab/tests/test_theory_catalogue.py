import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from theory_engine.catalogue import CATALOGUE, build
from theory_engine.game import solve_equilibrium


def _closed(game, values=None):
    subs = game.substitutions(values)
    return {k: float(v.subs(subs)) for k, v in game.closed_form.items()}


def test_every_model_has_a_verified_equilibrium_matching_its_closed_form():
    for key, entry in CATALOGUE.items():
        sizes = [None] if entry.n_range is None else [entry.n_range[0], 3]
        for n in sizes:
            game = build(key, n)
            result = solve_equilibrium(game)
            assert result.found, (key, n, result.message)
            eq = result.equilibria[0]
            assert eq.verified, (key, n)
            if game.closed_form is not None:
                for k, v in _closed(game).items():
                    assert abs(eq.strategies[k] - v) / max(1.0, abs(v)) < 1e-3, (key, n, k, eq.strategies[k], v)


def test_asymmetric_tullock_matches_closed_form():
    game = build("tullock", 2)
    values = {"V1": 20.0, "V2": 5.0}
    eq = solve_equilibrium(game, values).equilibria[0]
    for k, v in _closed(game, values).items():
        assert abs(eq.strategies[k] - v) / v < 1e-3


def test_symmetric_tullock_dissipation():
    for n in (2, 3, 4):
        eq = solve_equilibrium(build("tullock", n)).equilibria[0]
        expected = (n - 1) / n
        assert abs(eq.outcomes["Rent dissipation (total effort / largest prize)"] - expected) < 1e-3


def test_niskanen_oversupply_ratio_is_two_when_budget_constrained():
    eq = solve_equilibrium(build("niskanen")).equilibria[0]
    assert abs(eq.outcomes["Oversupply ratio Q/Q*"] - 2.0) < 1e-9


def test_downs_converges_to_median():
    eq = solve_equilibrium(build("downs"), {"m": 0.37}).equilibria[0]
    assert eq.strategies == {"xA": 0.37, "xB": 0.37}


def test_n_agent_range_enforced():
    try:
        build("cournot", 9)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for 9 firms")


if __name__ == "__main__":
    test_every_model_has_a_verified_equilibrium_matching_its_closed_form()
    test_asymmetric_tullock_matches_closed_form()
    test_symmetric_tullock_dissipation()
    test_niskanen_oversupply_ratio_is_two_when_budget_constrained()
    test_downs_converges_to_median()
    test_n_agent_range_enforced()
    print("test_theory_catalogue: OK")
