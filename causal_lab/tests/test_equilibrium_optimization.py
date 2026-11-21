"""Nash equilibria found by optimisation (theory_engine/optimization.py) agree
with the existing exact or verified solvers: vertex enumeration for matrix
games, closed forms and best-response iteration for continuous games."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from theory_engine.catalogue import CATALOGUE, build
from theory_engine.finite_games import BimatrixGame, _gain, matrix_catalogue, nash_equilibria
from theory_engine.game import _NumericGame, solve_equilibrium
from theory_engine.optimization import (GAP_METHOD, mangasarian_stone, nikaido_isoda_gap, solve_by_gap_minimisation,
                                        zero_sum_solution)


def _same(a, b, tol=1e-5):
    return np.allclose(a, b, atol=tol)


def test_quadratic_program_finds_exactly_the_enumerated_equilibria_of_the_catalogue():
    for key, game in matrix_catalogue().items():
        enumerated = nash_equilibria(game)
        qp = mangasarian_stone(game)
        assert len(qp.equilibria) == len(enumerated), key
        for e in qp.equilibria:
            assert abs(e.objective) < 1e-6 and e.gain < 1e-7, key
            assert any(_same(e.row, f.row) and _same(e.col, f.col) for f in enumerated), key


def test_every_quadratic_program_solution_is_an_equilibrium_on_random_games():
    rng = np.random.default_rng(11)
    for _ in range(25):
        m, n = rng.integers(2, 5, size=2)
        game = BimatrixGame("random", [f"r{i}" for i in range(m)], [f"c{j}" for j in range(n)],
                            rng.integers(-5, 6, (m, n)), rng.integers(-5, 6, (m, n)))
        qp = mangasarian_stone(game)
        assert qp.equilibria                                        # every finite game has one (Nash 1950)
        for e in qp.equilibria:
            assert _gain(game, e.row, e.col) < 1e-6


def test_zero_sum_value_by_linear_programming():
    pennies = matrix_catalogue()["matching_pennies"]
    zs = zero_sum_solution(pennies)
    assert abs(zs.value) < 1e-9 and _same(zs.row, [0.5, 0.5]) and _same(zs.col, [0.5, 0.5])
    # A 2x2 game without a saddle point: value (ad - bc) / (a + d - b - c) = (2 - 1) / 5,
    # row mix ((d - c), (a - b)) / 5 = (0.4, 0.6), column mix ((d - b), (a - c)) / 5 = (0.4, 0.6).
    a = np.array([[2.0, -1.0], [-1.0, 1.0]])
    zs = zero_sum_solution(BimatrixGame("zero-sum", ["T", "B"], ["L", "R"], a, -a))
    assert abs(zs.value - 0.2) < 1e-9 and _same(zs.row, [0.4, 0.6]) and _same(zs.col, [0.4, 0.6])
    assert zero_sum_solution(matrix_catalogue()["prisoners_dilemma"]) is None


def test_the_gap_is_zero_at_an_equilibrium_and_positive_elsewhere():
    game = build("cournot")
    num = _NumericGame(game, None)
    eq = solve_equilibrium(game).equilibria[0]
    s = np.array(list(eq.strategies.values()))
    assert nikaido_isoda_gap(num, s) < 1e-9
    assert nikaido_isoda_gap(num, s * 0.5) > 1e-3


def test_gap_minimisation_agrees_with_best_response_iteration():
    for key in CATALOGUE:
        game = build(key)
        result = solve_by_gap_minimisation(game)
        if not game.smooth:
            assert not result.equilibria and result.message.key == "solve.gap_not_smooth", key
            continue
        reference = solve_equilibrium(game).equilibria
        assert len(result.equilibria) == len(reference) == 1, key
        got = np.array(list(result.equilibria[0].strategies.values()))
        want = np.array(list(reference[0].strategies.values()))
        assert np.max(np.abs(got - want)) < 1e-4 * (1 + np.max(np.abs(want))), key
        assert result.equilibria[0].verified and result.equilibria[0].method == GAP_METHOD
        assert min(r.gap for r in result.runs) < 1e-10, key


def test_the_theory_page_offers_both_solvers_and_shows_the_optimisation():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "app.py"), default_timeout=300).run()
    at.sidebar.radio(key="page").set_value("theory").run()
    at.selectbox(key="th_model").set_value("cournot").run()
    at.radio(key="th_cat_cournot_2_solver").set_value("gap").run()
    at.button(key="th_cat_cournot_2_solve").click().run()
    assert not at.exception
    assert any("Unique equilibrium" in s.value for s in at.success)
    assert any(e.label == "The optimisation problem and how it was solved" for e in at.expander)
    assert any("Nikaido" in m.value for m in at.markdown)

    at.radio(key="th_kind").set_value("matrix").run()
    at.selectbox(key="mx_model").set_value("matching_pennies").run()
    assert not at.exception
    assert "Equilibria by optimisation" in [h.value for h in at.subheader]
    assert any("Value of the game" in m.value for m in at.markdown)
