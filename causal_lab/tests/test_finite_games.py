"""Matrix games: every Nash equilibrium and the logit QRE.

Closed forms for the catalogue, and Gambit's results (enummixed, logit_solve_lambda)
stored in tests/external_reference/expected.json for 60 random games."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from theory_engine.finite_games import BimatrixGame, logit_qre, matrix_catalogue, nash_equilibria
from utils.i18n import LocalizedError

EXPECTED = json.loads((Path(__file__).resolve().parent / "external_reference" / "expected.json").read_text())
APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _game(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return BimatrixGame("g", [str(i) for i in range(a.shape[0])], [str(j) for j in range(a.shape[1])], a, b)


def _profiles(equilibria):
    return sorted(tuple(np.round(np.concatenate([e.row, e.col]), 7)) for e in equilibria)


def test_catalogue_equilibria_match_their_closed_forms():
    cat = matrix_catalogue()
    expected = {
        "prisoners_dilemma": [(0, 1, 0, 1)],
        "matching_pennies": [(0.5, 0.5, 0.5, 0.5)],
        "battle_of_sexes": [(0, 1, 0, 1), (1, 0, 1, 0), (2 / 3, 1 / 3, 1 / 3, 2 / 3)],
        "hawk_dove": [(0, 1, 1, 0), (1, 0, 0, 1), (2 / 3, 1 / 3, 2 / 3, 1 / 3)],
        "stag_hunt": [(0, 1, 0, 1), (1, 0, 1, 0), (0.75, 0.25, 0.75, 0.25)],
        # Taxpayer evades with p making the authority indifferent: -0.5 + 3.5p = -2p -> p = 1/11;
        # authority inspects with q making the taxpayer indifferent: -1 = -4q -> q = 1/4.
        "inspection": [(10 / 11, 1 / 11, 0.25, 0.75)],
        "rock_paper_scissors": [(1 / 3,) * 6],
    }
    for key, profiles in expected.items():
        assert _profiles(nash_equilibria(cat[key])) == sorted(tuple(np.round(p, 7)) for p in profiles), key


def test_equilibria_equal_gambit_on_random_games():
    for index, case in enumerate(EXPECTED["matrix_games"]):
        ours = _profiles(nash_equilibria(_game(case["a"], case["b"])))
        theirs = sorted(tuple(np.round(e, 7)) for e in case["equilibria"])
        assert ours == theirs, (index, ours, theirs)


def test_every_reported_equilibrium_has_no_profitable_deviation():
    rng = np.random.default_rng(3)
    for _ in range(100):
        m, n = rng.integers(2, 6, size=2)
        a, b = rng.integers(-2, 3, size=(m, n)), rng.integers(-2, 3, size=(m, n))
        for e in nash_equilibria(_game(a, b)):
            assert e.max_gain < 1e-9 and abs(e.row.sum() - 1) < 1e-12 and e.row.min() >= 0


def test_generic_games_have_an_odd_number_of_equilibria():
    rng = np.random.default_rng(4)
    for _ in range(100):
        m, n = rng.integers(2, 6, size=2)
        assert len(nash_equilibria(_game(rng.normal(size=(m, n)), rng.normal(size=(m, n))))) % 2 == 1


def test_qre_equals_gambit_and_solves_its_equations():
    for case in EXPECTED["matrix_games"]:
        game = _game(case["a"], case["b"])
        m = game.row_payoffs.shape[0]
        for lam, reference in case["qre"].items():
            x, y = logit_qre(game, float(lam))
            assert np.abs(np.r_[x, y] - np.array(reference)).max() < 1e-6, (lam, x, y, reference)
            ux, uy = game.row_payoffs @ y, x @ game.col_payoffs
            assert np.allclose(np.log(x / x[0]), float(lam) * (ux - ux[0]), atol=1e-8)
            assert np.allclose(np.log(y / y[0]), float(lam) * (uy - uy[0]), atol=1e-8)
            assert len(x) == m


def test_qre_starts_from_random_play_and_reaches_nash_in_a_dominance_solvable_game():
    pd = matrix_catalogue()["prisoners_dilemma"]
    x0, y0 = logit_qre(pd, 0.0)
    assert np.allclose(x0, 0.5) and np.allclose(y0, 0.5)
    x, y = logit_qre(pd, 50.0)
    assert x[1] > 0.999 and y[1] > 0.999                        # defect, the unique equilibrium
    rps = matrix_catalogue()["rock_paper_scissors"]
    assert np.allclose(logit_qre(rps, 20.0)[0], 1 / 3)


def test_invalid_games_are_refused():
    for args, key in ((([[1, 2]], [[1]]), "err.matrix_shape"), (([[np.inf]], [[0]]), "err.matrix_finite")):
        try:
            _game(*args)
        except LocalizedError as exc:
            assert exc.msg.key == key
        else:
            raise AssertionError(key)
    try:
        _game(np.zeros((7, 2)), np.zeros((7, 2)))
    except LocalizedError as exc:
        assert exc.msg.key == "err.matrix_size"
    try:
        logit_qre(matrix_catalogue()["stag_hunt"], -1)
    except LocalizedError as exc:
        assert exc.msg.key == "err.qre_lambda"


def test_matrix_games_on_the_theory_page():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=300)
    at.session_state["page"] = "theory"
    at.run()
    at.radio(key="th_kind").set_value("matrix").run()
    for key in matrix_catalogue():
        at.selectbox(key="mx_model").set_value(key).run()
        assert not at.exception, (key, [e.value for e in at.exception])
    tables = [d.value for d in at.dataframe]
    assert any("Kind" in t.columns for t in tables)
    at.session_state["page"] = "dashboard"
    at.run()
    at.session_state["page"] = "theory"
    at.run()
    assert at.radio(key="th_kind").value == "matrix"                 # kept when coming back
    at.radio(key="mx_source").set_value("editor").run()
    assert not at.exception, [e.value for e in at.exception]


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("test_finite_games: OK")
