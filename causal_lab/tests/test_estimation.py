"""Structural estimation: logit QRE by maximum likelihood (against Gambit) and
GMM on first-order conditions (against linearmodels, and by simulation)."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "external_reference"))

import numpy as np
import pandas as pd
from scipy.special import xlogy

from make_reference import load
from theory_engine.catalogue import build
from theory_engine.estimation import fit_logit_qre, gmm_first_order_conditions
from theory_engine.finite_games import BimatrixGame, logit_qre, matrix_catalogue
from theory_engine.game import build_custom_game
from utils.i18n import LocalizedError

APP = str(Path(__file__).resolve().parent.parent / "app.py")
EXPECTED = json.loads((Path(__file__).resolve().parent / "external_reference" / "expected.json")
                      .read_text(encoding="utf-8"))


def _raises_key(key, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except LocalizedError as exc:
        assert exc.msg.key == key, exc.msg.key
    else:
        raise AssertionError(key)


def _matrix(a, b) -> BimatrixGame:
    a, b = np.array(a), np.array(b)
    return BimatrixGame("g", [str(k) for k in range(a.shape[0])], [str(k) for k in range(a.shape[1])], a, b)


# --------------------------------------------------------------------------
# Logit QRE by maximum likelihood
# --------------------------------------------------------------------------
def test_qre_estimates_match_gambit():
    at_bound = 0
    for ref in EXPECTED["qre_estimates"]:
        game = _matrix(ref["a"], ref["b"])
        fit = fit_logit_qre(game, ref["row_counts"], ref["col_counts"])
        if fit.at_bound:
            # Choices all on a pure equilibrium: the likelihood rises to 0 as lambda grows, and
            # Gambit stops somewhere on that plateau. Only a lower bound is meaningful.
            at_bound += 1
            assert fit.log_likelihood > -1e-6 and fit.ci_high == np.inf and fit.se is None
            assert ref["lam"] >= fit.ci_low
            continue
        assert abs(fit.lam - ref["lam"]) <= 1e-4 * max(1.0, ref["lam"]), (fit.lam, ref["lam"])
        assert abs(fit.log_likelihood - ref["log_like"]) <= 2e-6
        # The gap is Gambit's path tolerance: at its lambda the likelihood is not higher than ours.
        x, y = logit_qre(game, ref["lam"])
        assert fit.log_likelihood >= xlogy(ref["row_counts"], x).sum() + xlogy(ref["col_counts"], y).sum() - 1e-10
    assert at_bound <= 2


def test_qre_recovers_lambda_from_expected_counts():
    # Counts proportional to the QRE at lambda = 2: the likelihood peaks exactly there.
    game = matrix_catalogue()["inspection"]
    x, y = logit_qre(game, 2.0)
    fit = fit_logit_qre(game, 1000 * x, 1000 * y)
    assert abs(fit.lam - 2.0) < 1e-6 and not fit.at_bound
    assert fit.ci_low < 2.0 < fit.ci_high and fit.se > 0
    assert np.allclose(fit.row, x, atol=1e-8) and np.allclose(fit.col, y, atol=1e-8)
    assert fit.p_random < 1e-6
    # The interval inverts the likelihood-ratio test: at each end, 2 (logL_max - logL) = chi2_1(0.95).
    for end in (fit.ci_low, fit.ci_high):
        xe, ye = logit_qre(game, end)
        drop = fit.log_likelihood - (xlogy(1000 * x, xe).sum() + xlogy(1000 * y, ye).sum())
        assert abs(2 * drop - 3.841458820694124) < 1e-6, (end, drop)


def test_qre_on_nash_play_has_only_a_lower_bound():
    game = matrix_catalogue()["prisoners_dilemma"]
    defect = [k for k, a in enumerate(game.row_actions) if "defect" in str(a.key)][0]
    counts = np.zeros(2)
    counts[defect] = 50
    fit = fit_logit_qre(game, counts, counts)
    assert fit.at_bound and fit.se is None and fit.ci_high == np.inf and fit.ci_low > 0


def test_qre_input_errors():
    game = matrix_catalogue()["matching_pennies"]
    _raises_key("err.qre_counts_shape", fit_logit_qre, game, [1, 2, 3], [1, 2])
    _raises_key("err.qre_counts", fit_logit_qre, game, [1, -2], [1, 2])
    _raises_key("err.qre_no_data", fit_logit_qre, game, [0, 0], [0, 0])


# --------------------------------------------------------------------------
# GMM on first-order conditions
# --------------------------------------------------------------------------
def _cournot_game():
    # Firm i's profit (A0 + A1 w - B (x1 + x2)) x_i - 5 r_i x_i: the cost intercept is
    # absorbed in A0, the cost slope 5 on r_i is known.
    return build_custom_game("cournot", {"A0": 50, "A1": 1, "B": 0.5, "w": 0, "r1": 0, "r2": 0}, [
        dict(name="F1", strategy="x1", lower="0", upper="1000", utility="(A0 + A1*w - B*(x1 + x2))*x1 - 5*r1*x1"),
        dict(name="F2", strategy="x2", lower="0", upper="1000", utility="(A0 + A1*w - B*(x1 + x2))*x2 - 5*r2*x2")])


def _fit_cournot(df, agents=None, instruments=("w", "r1", "r2")):
    return gmm_first_order_conditions(_cournot_game(), df, {"x1": "q1", "x2": "q2"}, {"A0": 50, "A1": 1, "B": 0.5},
                                      list(instruments), observed={"w": "w", "r1": "r1", "r2": "r2"}, agents=agents)


def test_gmm_matches_linearmodels_ivgmm():
    # Firm 1's condition is linear in (A0, A1, B): the same moments as linearmodels' IVGMM.
    fit = _fit_cournot(load("cournot_markets"), agents=[0])
    for got, want in zip(fit.estimates, EXPECTED["gmm.estimates"]):
        assert abs(got / want - 1) < 1e-8, (got, want)
    for got, want in zip(fit.se, EXPECTED["gmm.se"]):
        assert abs(got / want - 1) < 1e-8, (got, want)
    assert abs(fit.j_stat / EXPECTED["gmm.j"] - 1) < 1e-8 and fit.j_df == 1
    # True values: A0 = 100 - 10 = 90, A1 = 10, B = 1.
    assert np.all(np.abs(fit.estimates - [90, 10, 1]) < 3 * fit.se)


def test_gmm_both_firms_overidentified():
    fit = _fit_cournot(load("cournot_markets"))
    assert fit.n_moments == 8 and fit.j_df == 5 and fit.j_p > 0.01
    assert np.all(np.abs(fit.estimates - [90, 10, 1]) < 3 * fit.se)
    # Two firms' conditions are more informative than one.
    assert np.all(fit.se < _fit_cournot(load("cournot_markets"), agents=[0]).se)


def test_gmm_nonlinear_model_recovers_parameters():
    # Constant-elasticity demand A exp(A1 w) Q^(-1/eta), costs 10 + 2 r_i + u_i: the conditions
    # are nonlinear in (A, A1, eta). Equilibrium in closed form: P = eta (c1 + c2) / (2 eta - 1).
    rng = np.random.default_rng(3)
    n, big_a, a1, eta = 2000, 100.0, 0.3, 2.0
    w = rng.normal(size=n)
    r = rng.uniform(-1, 1, size=(2, n))
    c = 10 + 2 * r + rng.normal(scale=0.5, size=(2, n))
    price = eta * c.sum(axis=0) / (2 * eta - 1)
    q = eta * (1 - c / price) * (big_a * np.exp(a1 * w) / price) ** eta
    df = pd.DataFrame(dict(w=w, r1=r[0], r2=r[1], q1=q[0], q2=q[1]))
    game = build_custom_game("ce", {"A": 80, "A1": 0.1, "eta": 1.5, "w": 0, "r1": 0, "r2": 0}, [
        dict(name="F1", strategy="x1", lower="0.001", upper="1e4",
             utility="A*exp(A1*w)*(x1+x2)^(-1/eta)*x1 - (10 + 2*r1)*x1"),
        dict(name="F2", strategy="x2", lower="0.001", upper="1e4",
             utility="A*exp(A1*w)*(x1+x2)^(-1/eta)*x2 - (10 + 2*r2)*x2")])
    fit = gmm_first_order_conditions(game, df, {"x1": "q1", "x2": "q2"}, {"A": 80, "A1": 0.1, "eta": 1.5},
                                     ["w", "r1", "r2"], observed={"w": "w", "r1": "r1", "r2": "r2"})
    assert fit.converged
    assert np.all(np.abs(fit.estimates - [big_a, a1, eta]) < 3 * fit.se), (fit.estimates, fit.se)
    assert np.all(fit.se / np.array([big_a, a1, eta]) < 0.05)


def test_gmm_errors():
    df = load("cournot_markets")
    game = _cournot_game()
    strategies = {"x1": "q1", "x2": "q2"}
    observed = {"w": "w", "r1": "r1", "r2": "r2"}
    _raises_key("err.gmm_underidentified", gmm_first_order_conditions, game, df, strategies,
                {"A0": 50, "A1": 1, "B": 0.5}, [], observed=observed, agents=[0])
    _raises_key("err.gmm_role_twice", gmm_first_order_conditions, game, df, strategies,
                {"A0": 50, "w": 0}, ["r1"], observed=observed)
    _raises_key("err.gmm_strategy_column", gmm_first_order_conditions, game, df, {"x1": "q1"},
                {"A0": 50}, ["r1"], observed=observed)
    _raises_key("err.gmm_column", gmm_first_order_conditions, game, df, strategies, {"A0": 50}, ["nope"],
                observed=observed)
    _raises_key("err.gmm_collinear_instruments", gmm_first_order_conditions, game, df.assign(w2=2 * df["w"]),
                strategies, {"A0": 50}, ["w", "w2"], observed=observed)
    _raises_key("err.gmm_not_smooth", gmm_first_order_conditions, build("downs"), df, {"xA": "q1", "xB": "q2"},
                {"m": 0.5}, ["w"])
    # A cost intercept next to the demand intercept: only their difference enters the conditions.
    two_intercepts = build_custom_game("c", {"A0": 50, "C0": 0, "B": 0.5, "r1": 0}, [
        dict(name="F1", strategy="x1", lower="0", upper="1000", utility="(A0 - B*(x1 + x2))*x1 - (C0 + 5*r1)*x1"),
        dict(name="F2", strategy="x2", lower="0", upper="1000", utility="(A0 - B*(x1 + x2))*x2 - (C0 + 5*r1)*x2")])
    _raises_key("err.gmm_not_identified", gmm_first_order_conditions, two_intercepts, df, strategies,
                {"A0": 50, "C0": 0, "B": 0.5}, ["w", "r2"], observed={"r1": "r1"})


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
def test_estimation_on_the_pages():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=300)
    at.session_state["page"] = "theory"
    # Catalogue Cournot duopoly: demand 100 + v (v unobserved) - Q, observed costs c1, c2.
    rng = np.random.default_rng(1)
    n = 300
    c = 10 + 5 * rng.uniform(size=(2, n))
    a = 100 + rng.normal(scale=3, size=n)
    at.session_state["uploaded_df"] = pd.DataFrame(dict(q1=(a - 2 * c[0] + c[1]) / 3, q2=(a - 2 * c[1] + c[0]) / 3,
                                                        c1=c[0], c2=c[1]))
    at.run()
    at.selectbox(key="th_model").set_value("cournot").run()
    sig = "cat_cournot_2_est"
    at.selectbox(key=f"th_{sig}_data").set_value("Virtual Lab dataset").run()
    for name in ("c1", "c2"):
        at.selectbox(key=f"th_{sig}_role_{name}").set_value("observed").run()
        at.selectbox(key=f"th_{sig}_col_{name}").set_value(name).run()
    at.multiselect(key=f"th_{sig}_iv").set_value(["c1", "c2"]).run()
    at.button(key=f"th_{sig}_run").click().run()
    assert not at.exception, [e.value for e in at.exception]
    fit = at.session_state["theory"]["gmm"][1]
    assert fit.names == ["a", "b"] and np.all(np.abs(fit.estimates - [100, 1]) < 3 * fit.se)

    at.radio(key="th_kind").set_value("matrix").run()
    at.selectbox(key="mx_model").set_value("inspection").run()
    for key, value in (("mx_est_r0_2x2", 30), ("mx_est_r1_2x2", 70), ("mx_est_c0_2x2", 55), ("mx_est_c1_2x2", 45)):
        at.number_input(key=key).set_value(value).run()
    at.button(key="mx_est_run").click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.session_state["mx_est"][1].n_obs == 200


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("test_estimation: OK")
