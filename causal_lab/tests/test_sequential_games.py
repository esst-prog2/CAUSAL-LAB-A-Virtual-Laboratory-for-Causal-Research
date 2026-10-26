"""Stackelberg leadership and bargaining, against closed forms."""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sympy as sp

from theory_engine.bargaining import nash_bargaining, rubinstein_finite, rubinstein_share
from theory_engine.catalogue import build
from theory_engine.sequential import solve_stackelberg
from utils.i18n import LocalizedError

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _raises_key(key, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except LocalizedError as exc:
        assert exc.msg.key == key, exc.msg.key
    else:
        raise AssertionError(key)


def test_cournot_duopoly_leadership_closed_form():
    # Linear demand a - b Q, costs c1, c2: q1 = (a - 2c1 + c2) / (2b), q2 = (a + 2c1 - 3c2) / (4b).
    a, b, c1, c2 = 100.0, 1.0, 10.0, 20.0
    result = solve_stackelberg(build("cournot", 2), {"c1": c1, "c2": c2}, leader=0)
    # Nested numerical solution: the follower is located to ~1e-8, the leader to ~1e-7 relative.
    assert abs(result.strategies["q1"] / ((a - 2 * c1 + c2) / (2 * b)) - 1) < 1e-7
    assert abs(result.strategies["q2"] / ((a + 2 * c1 - 3 * c2) / (4 * b)) - 1) < 1e-7
    assert result.leader_gain_check <= 1e-9


def test_one_leader_two_followers():
    # Followers' Nash given qL: qF = (a - c - b qL) / (3b); the leader then sets qL = (a - c) / (2b).
    result = solve_stackelberg(build("cournot", 3), None, leader=0)
    assert abs(result.strategies["q1"] - 45.0) < 1e-4
    assert abs(result.strategies["q2"] - 15.0) < 1e-4 and abs(result.strategies["q3"] - 15.0) < 1e-4


def test_bertrand_price_leadership_matches_backward_induction():
    game = build("bertrand")
    values = {"c1": 15.0}
    subs = game.substitutions(values)
    p1, p2 = game.strategies
    reply = sp.solve(sp.diff(game.agents[1].utility.subs(subs), p2), p2)[0]
    leader = sp.solve(sp.diff(game.agents[0].utility.subs(subs).subs(p2, reply), p1), p1)[0]
    result = solve_stackelberg(game, values, leader=0)
    assert abs(result.strategies["p1"] - float(leader)) < 1e-5
    assert abs(result.strategies["p2"] - float(reply.subs(p1, leader))) < 1e-5


def test_tullock_leader_matches_dixit():
    # Dixit (1987): the follower plays sqrt(V2 x1) - x1, so the leader chooses x1 = V1^2 / (4 V2).
    v1, v2 = 10.0, 6.0
    result = solve_stackelberg(build("tullock", 2), {"V1": v1, "V2": v2}, leader=0)
    x1 = v1 ** 2 / (4 * v2)
    # The leader's objective is flat at the optimum, and the follower's response is located to ~1e-8:
    # strategies to 1e-3 relative, utility to 1e-7.
    assert abs(result.strategies["x1"] - x1) < 1e-3 * x1
    assert abs(result.utilities[result.leader] - (v1 * math.sqrt(x1 / v2) - x1)) < 1e-7


def test_leading_never_hurts_the_leader():
    for key, n, values in (("cournot", 2, None), ("bertrand", None, None), ("tullock", 2, None)):
        result = solve_stackelberg(build(key, n), values, leader=0)
        assert result.utilities[result.leader] >= result.simultaneous.utilities[result.leader] - 1e-6, key


def test_nash_bargaining_closed_forms():
    linear = nash_bargaining(100.0, alpha=0.3, d1=10.0, d2=20.0)
    assert abs(linear.share_1 - (10 + 0.3 * 70) / 100) < 1e-7
    # sqrt utility for player 1: maximize sqrt(x S) (1 - x) S -> 1 / (2x) = 1 / (1 - x) -> x = 1/3.
    assert abs(nash_bargaining(100.0, utility_1="sqrt(m)").share_1 - 1 / 3) < 1e-7
    _raises_key("err.bargain_alpha", nash_bargaining, 100.0, alpha=1.0)
    _raises_key("err.bargain_surplus", nash_bargaining, 0.0)
    _raises_key("err.bargain_no_gain", nash_bargaining, 10.0, d1=8.0, d2=8.0)


def test_rubinstein_and_its_limits():
    assert abs(rubinstein_share(0.9, 0.8) - 0.2 / 0.28) < 1e-12
    path = rubinstein_finite(0.9, 0.8, 300)
    assert path[0] == 1.0 and abs(path[1] - 0.2) < 1e-12              # T = 2: offer the responder delta2
    assert abs(path[-1] - rubinstein_share(0.9, 0.8)) < 1e-10
    # Binmore, Rubinstein & Wolinsky: delta_i = exp(-r_i dt), dt -> 0: share -> r2 / (r1 + r2),
    # the Nash solution with bargaining power r2 / (r1 + r2).
    r1, r2 = 0.05, 0.10
    share = rubinstein_share(math.exp(-r1 * 1e-4), math.exp(-r2 * 1e-4))
    assert abs(share - r2 / (r1 + r2)) < 1e-4
    assert abs(nash_bargaining(1.0, alpha=r2 / (r1 + r2)).share_1 - r2 / (r1 + r2)) < 1e-7
    _raises_key("err.bargain_delta", rubinstein_share, 1.0, 0.5)


def test_sequential_kinds_on_the_theory_page():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=300)
    at.session_state["page"] = "theory"
    at.run()
    at.radio(key="th_kind").set_value("stackelberg").run()
    next(b for b in at.button if b.key == "seq_solve").click().run()
    assert not at.exception, [e.value for e in at.exception]
    stored = at.session_state["seq_result"][1]
    assert abs(stored.strategies["q1"] - 45.0) < 1e-4                  # symmetric costs 10: (100 - 10) / 2
    at.radio(key="th_kind").set_value("bargaining").run()
    assert not at.exception, [e.value for e in at.exception]
    assert any(m.label == "Player 1's share" for m in at.metric)


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("test_sequential_games: OK")
