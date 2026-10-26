"""Parallel Trends, Anticipation and Spillovers checked against values worked out by hand.

Companion to test_stress_hand_computed.py, which covers heterogeneity, serial
correlation and the score. These three checks run regressions, so every
expected number below is derived on paper from a tiny two-period design.

Facts used, with their source:

(a) Two periods with unit and period fixed effects: the estimate equals the
    first-difference regression, and the unit-clustered sandwich equals HC0
    on the first differences. Proof: within-transformed regressor and
    residual are x_i1 = -x_i0 = dx_i / 2 and e_i1 = -e_i0 = u_i / 2, so
    V = sum(dx^2 u^2) / (sum dx^2)^2.
(b) For a 0/1 regressor with an intercept, the coefficient is the difference
    of group means, and its HC0 variance is sum(e_T^2)/n_T^2 + sum(e_C^2)/n_C^2.
(c) Conventions of statsmodels 0.15, read in its source (not assumed):
    cluster covariance times G/(G-1) * (N-1)/(N-K), with K counting every
    dummy (stats/sandwich_covariance.py, cov_cluster); a clustered fit sets
    df_resid_inference = G - 1 (base/covtype.py), which f_test uses as the
    F denominator; HC1 = HC0 * N/(N-K); coefficient p-values use the normal
    distribution (use_t is False).
    Since 2026-10-25 Spillovers rescales that covariance as the DiD does
    (estimators.did.nested_fe_factor): the unit dummies, nested in the unit
    clusters, are not counted in K (Stata xtreg/reghdfe). Parallel Trends
    uses a bootstrap instead, in which the factor cancels (see its section).
(d) Two-sided normal: p = erfc(|z| / sqrt(2)).

In the Anticipation and Spillovers designs each group has 2 units whose
changes are m - 1 and m + 1, so every first-difference residual is +-1 and
(b) gives HC0 = 2/4 + 2/4 = 1. With 4 units and 2 periods, N = 8 and K = 3
(intercept, regressor, 1 period dummy; the 3 unit dummies are not counted),
so the cluster factor in (c) is 4/3 * 7/5 = 28/15.
"""
import itertools
import sys
from math import erfc, sqrt
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from robustness_engine.stress_test import (NOT_APPLICABLE, PASS, WARNING, _check_anticipation,
                                           _check_parallel_trends, _check_spillovers)

CLUSTER_VAR = 28 / 15         # HC0 of 1, times the cluster factor in (c)


def _two_period(changes: dict, treated: set, periods=(0, 1), extra_period=None):
    """Y = 0 in the first period and the unit's change in the second."""
    rows = []
    for unit, change in changes.items():
        flag = int(unit in treated)
        rows += [(unit, periods[0], flag, 0.0), (unit, periods[1], flag, float(change))]
        if extra_period is not None:            # a post-treatment period the pre-period checks must ignore
            rows.append((unit, extra_period, flag, 100.0 * flag))
    df = pd.DataFrame(rows, columns=["unit", "period", "treated_unit", "Y"])
    df["D"] = 0
    return df


# ---------------------------------------------------------------- Parallel Trends
# Treatment in period 2, so the pre-treatment periods are 0 and 1. The single
# interaction is treated x period 0, and with (a) its coefficient is
# -(mean change treated - mean change control) between periods 0 and 1.
#
# Since 2026-10-25 the p-value comes from the wild cluster restricted bootstrap
# with Rademacher signs, not from F(q, G - 1). By (a) and (b), in first
# differences: under H0 the restricted residual of unit i is r_i = change_i -
# mean change, each sign pattern v gives the changes v_i * r_i, and
# W(v) = b(v)^2 / HC0(v). The CR1 factor of (c) multiplies every W(v) alike
# and cancels. With G units and G <= 9, all 2^G patterns are used, so
# p = #{v : W(v) >= W(1)} / 2^G, and p >= 2 / 2^G because v and -v give the
# same W. _fd_bootstrap_p below is that computation, written independently of
# the app's within-transformation code.

def _pt(changes, treated):
    return _check_parallel_trends(_two_period(changes, treated, extra_period=2),
                                  "Y", "unit", "period", "treated_unit", 2)


def _fd_bootstrap_p(changes: dict, treated: set) -> float:
    units = sorted(changes)
    delta = np.array([changes[u] for u in units], float)
    d = np.array([u in treated for u in units], float)

    def wald(y):
        b = y[d == 1].mean() - y[d == 0].mean()
        e = np.where(d == 1, y - y[d == 1].mean(), y - y[d == 0].mean())
        hc0 = np.sum(e[d == 1] ** 2) / d.sum() ** 2 + np.sum(e[d == 0] ** 2) / (1 - d).sum() ** 2
        return b * b / hc0

    r = delta - delta.mean()
    observed = wald(delta)
    stats_ = [wald(r * np.array(v)) for v in itertools.product([-1.0, 1.0], repeat=len(units))]
    return float(np.mean(np.array(stats_) >= observed * (1 - 1e-9)))


def test_parallel_trends_equal_pre_trends_by_hand():
    # Treated changes 1, 3 (mean 2); controls 0, 2, 4 (mean 2): coefficient 0, so W(1) = 0
    # and every pattern has W(v) >= 0: p = 32/32 = 1.
    check = _pt({1: 1, 2: 3, 3: 0, 4: 2, 5: 4}, {1, 2})
    assert abs(check.p_value - 1.0) < 1e-12, check.p_value
    assert check.verdict == PASS and check.assessment == "plausible"


def test_parallel_trends_warns_between_five_and_ten_percent_at_the_floor():
    # Pins the 10% warning threshold. With 5 units p >= 2/32 = 0.0625; a pre-trend of 20
    # against residuals of +-1 makes the observed pattern and its opposite the only two with
    # the largest W, so p is exactly that floor: between 5% and 10%, WARNING "questionable".
    changes = {1: 19, 2: 21, 3: -1, 4: 0, 5: 1}
    check = _pt(changes, {1, 2})
    assert abs(check.p_value - 2 / 32) < 1e-12 and _fd_bootstrap_p(changes, {1, 2}) == 2 / 32, check.p_value
    assert check.verdict == WARNING and check.assessment == "questionable"


def test_parallel_trends_questionable_against_first_differences():
    # 6 units: p >= 2/64 = 0.03125, so 0.01 <= p < 0.05 is reachable: "questionable".
    changes = {1: 19, 2: 21, 3: 20, 4: -1, 5: 0, 6: 1}
    check = _pt(changes, {1, 2, 3})
    expected = _fd_bootstrap_p(changes, {1, 2, 3})
    assert abs(check.p_value - expected) < 1e-12 and 0.01 <= expected < 0.05, (check.p_value, expected)
    assert check.verdict == WARNING and check.assessment == "questionable"


def test_parallel_trends_violated_against_first_differences():
    # 8 units: p can fall to 2/256 = 0.0078 < 0.01: "violated".
    changes = {1: 19, 2: 21, 3: 20, 4: 22, 5: -1, 6: 0, 7: 1, 8: 2}
    check = _pt(changes, {1, 2, 3, 4})
    expected = _fd_bootstrap_p(changes, {1, 2, 3, 4})
    assert abs(check.p_value - expected) < 1e-12 and expected < 0.01, (check.p_value, expected)
    assert check.verdict == WARNING and check.assessment == "violated"


def test_parallel_trends_matches_first_differences_on_an_ordinary_design():
    # 9 units, 512 patterns, a p far from both the floor and 1, where every part of the
    # bootstrap (restricted residuals, re-projection of each draw, the exceedance count)
    # affects the value.
    changes = {1: 1.3, 2: -0.4, 3: 2.1, 4: 0.6, 5: -1.2, 6: 0.2, 7: 1.0, 8: -0.7, 9: 0.4}
    check = _pt(changes, {1, 2, 3, 4})
    expected = _fd_bootstrap_p(changes, {1, 2, 3, 4})
    assert abs(check.p_value - expected) < 1e-12 and 0.1 < expected < 0.9, (check.p_value, expected)


def test_parallel_trends_random_draws_beyond_nine_units():
    # 12 units: 2^12 = 4096 patterns > 1000, so 999 random sign draws with a fixed seed are
    # used, p = (1 + #exceed) / 1000. Same p on every run, close to the exact enumeration.
    rng = np.random.default_rng(3)
    changes = {u: float(rng.normal() + (1.5 if u <= 6 else 0.0)) for u in range(1, 13)}
    first, second = _pt(changes, set(range(1, 7))), _pt(changes, set(range(1, 7)))
    exact = _fd_bootstrap_p(changes, set(range(1, 7)))
    assert first.p_value == second.p_value
    assert abs(first.p_value * 1000 - round(first.p_value * 1000)) < 1e-9
    assert abs(first.p_value - exact) < 4 * sqrt(exact * (1 - exact) / 999) + 1e-3, (first.p_value, exact)


def test_parallel_trends_not_computable_edge_cases():
    # One pre-treatment period only (treatment in period 1): no pre-trend to test.
    one_pre = _check_parallel_trends(_two_period({1: 1, 2: 3, 3: 0, 4: 4, 5: 2}, {1, 2}),
                                     "Y", "unit", "period", "treated_unit", 1)
    # No control unit at all: nothing to compare the treated trend with.
    no_controls = _check_parallel_trends(_two_period({1: 1, 2: 3}, {1, 2}, extra_period=2),
                                         "Y", "unit", "period", "treated_unit", 2)
    # 4 units: p >= 2/16 = 0.125, so the test could never warn at 10%; N/A, not PASS.
    four_units = _pt({1: 19, 2: 21, 3: -1, 4: 1}, {1, 2})
    assert one_pre.verdict == NOT_APPLICABLE and no_controls.verdict == NOT_APPLICABLE
    assert four_units.verdict == NOT_APPLICABLE and four_units.message.key == "stress.pt.too_few_units"


# ---------------------------------------------------------------- Anticipation
# Treatment in period 2: the check regresses each unit's change between periods
# 0 and 1 on the treated indicator, with HC1. With 4 units and 2 parameters,
# HC1 = HC0 * 4/2 = 2, so SE = sqrt(2).

def _anticipation(df, treatment_period=2):
    return _check_anticipation(df, "Y", "unit", "period", "treated_unit", treatment_period)


def test_anticipation_no_jump_by_hand():
    # Treated 1, 3 (mean 2); controls -1, 1 (mean 0): coefficient 2, z = 2 / sqrt(2) = sqrt(2),
    # p = erfc(sqrt(2) / sqrt(2)) = erfc(1) = 0.157299 >= 0.10: PASS.
    check = _anticipation(_two_period({1: 1, 2: 3, 3: -1, 4: 1}, {1, 2}, extra_period=2))
    assert abs(check.p_value - erfc(1)) < 1e-9, check.p_value
    assert check.verdict == PASS


def test_anticipation_jump_by_hand():
    # Treated 3, 5 (mean 4); controls -1, 1: coefficient 4, z = 4 / sqrt(2) = 2*sqrt(2),
    # p = erfc(2) = 0.004678 < 0.10: WARNING.
    check = _anticipation(_two_period({1: 3, 2: 5, 3: -1, 4: 1}, {1, 2}, extra_period=2))
    assert abs(check.p_value - erfc(2)) < 1e-9, check.p_value
    assert check.verdict == WARNING


def test_anticipation_not_computable_edge_cases():
    # Treatment in period 1: period -1 does not exist, so there are not two pre-treatment periods.
    too_early = _anticipation(_two_period({1: 3, 2: 5, 3: -1, 4: 1}, {1, 2}), treatment_period=1)
    # Missing values: both controls lack period 1, so no control change can be formed.
    df = _two_period({1: 3, 2: 5, 3: -1, 4: 1}, {1, 2}, extra_period=2)
    df.loc[(df["treated_unit"] == 0) & (df["period"] == 1), "Y"] = float("nan")
    missing = _anticipation(df)
    assert too_early.verdict == NOT_APPLICABLE and missing.verdict == NOT_APPLICABLE


# ---------------------------------------------------------------- Spillovers
# Unit 5 is treated; controls 4 and 6 are adjacent (ids differ by 1), controls
# 10 and 12 are not. Treatment in period 1. The check runs a DiD of adjacent
# vs. far controls on the controls only, clustered by unit; by (a) its
# coefficient is mean change adjacent - mean change far.

def _spill(changes, ids_encode_neighbourhood=True):
    df = _two_period({5: 0, **changes}, {5})
    return _check_spillovers(df, "Y", "unit", "period", "treated_unit", 1, ids_encode_neighbourhood)


def test_spillovers_shift_by_hand():
    # Adjacent 2, 4 (mean 3); far -1, 1 (mean 0): effect 3, variance 28/15,
    # z = 3 / sqrt(28/15) = 2.195775, p = erfc(z / sqrt(2)) = 0.028108 < 0.10: WARNING.
    check = _spill({4: 2, 6: 4, 10: -1, 12: 1})
    z = 3 / sqrt(CLUSTER_VAR)
    assert abs(check.statistic - 3.0) < 1e-9, check.statistic
    assert abs(check.p_value - erfc(z / sqrt(2))) < 1e-9, check.p_value
    assert check.verdict == WARNING


def test_spillovers_small_shift_by_hand():
    # Pins the 10% threshold. Adjacent 1.5, 3.5 (mean 2.5); far -1, 1: effect 2.5,
    # z = 2.5 / sqrt(28/15) = 1.829813, p = 0.067278: still WARNING.
    check = _spill({4: 1.5, 6: 3.5, 10: -1, 12: 1})
    z = 2.5 / sqrt(CLUSTER_VAR)
    assert abs(check.statistic - 2.5) < 1e-9, check.statistic
    assert abs(check.p_value - erfc(z / sqrt(2))) < 1e-9 and 0.05 < check.p_value < 0.10, check.p_value
    assert check.verdict == WARNING


def test_spillovers_no_shift_by_hand():
    # Adjacent 0, 2 (mean 1); far -1, 3 (mean 1): effect 0, z = 0, p = 1: PASS.
    check = _spill({4: 0, 6: 2, 10: -1, 12: 3})
    assert abs(check.statistic) < 1e-9 and abs(check.p_value - 1.0) < 1e-9
    assert check.verdict == PASS


def test_spillovers_not_computable_edge_cases():
    # Only one adjacent control (6 is now 7, two ids away from 5): the check needs at least 2.
    one_adjacent = _spill({4: 3, 7: 5, 10: -1, 12: 1})
    # Ids that do not encode a neighbourhood (uploaded or real data): not testable.
    no_neighbourhood = _spill({4: 3, 6: 5, 10: -1, 12: 1}, ids_encode_neighbourhood=False)
    assert one_adjacent.verdict == NOT_APPLICABLE and no_neighbourhood.verdict == NOT_APPLICABLE


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("test_stress_hand_computed_regressions: OK")
