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
(d) F(1, 3) is t(3) squared, and for 3 degrees of freedom
    P(|T| > t) = 1 - (2/pi) * (atan(a) + a / (1 + a^2)) with a = t / sqrt(3).
    Two-sided normal: p = erfc(|z| / sqrt(2)).

In every design below each group has 2 units whose changes are m - 1 and
m + 1, so every first-difference residual is +-1 and (b) gives HC0 = 2/4 + 2/4 = 1.
With 4 units and 2 periods, N = 8 and K = 6 (intercept, regressor, 3 unit
dummies, 1 period dummy), so the cluster factor in (c) is 4/3 * 7/2 = 14/3.
"""
import sys
from math import atan, erfc, pi, sqrt
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from robustness_engine.stress_test import (NOT_APPLICABLE, PASS, WARNING, _check_anticipation,
                                           _check_parallel_trends, _check_spillovers)

CLUSTER_VAR = 14 / 3          # HC0 of 1, times the cluster factor in (c)


def _p_f_1_3(f_stat: float) -> float:
    """P(F(1, 3) > f_stat), from the closed form of t(3) in (d)."""
    a = sqrt(f_stat) / sqrt(3)
    return 1 - (2 / pi) * (atan(a) + a / (1 + a * a))


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

def _pt(changes, treated):
    return _check_parallel_trends(_two_period(changes, treated, extra_period=2),
                                  "Y", "unit", "period", "treated_unit", 2)


def test_parallel_trends_equal_pre_trends_by_hand():
    # Treated changes 1, 3 (mean 2); controls 0, 4 (mean 2): coefficient 0, Wald F = 0, p = 1.
    check = _pt({1: 1, 2: 3, 3: 0, 4: 4}, {1, 2})
    assert abs(check.p_value - 1.0) < 1e-9, check.p_value
    assert check.verdict == PASS and check.assessment == "plausible"


def test_parallel_trends_questionable_by_hand():
    # Treated 9, 11 (mean 10); controls -1, 1 (mean 0): coefficient -10, variance 14/3,
    # F = 100 / (14/3) = 150/7 = 21.43 on (1, G - 1 = 3) degrees of freedom; by (d) p = 0.018986.
    # 0.01 <= p < 0.10: WARNING, "questionable".
    check = _pt({1: 9, 2: 11, 3: -1, 4: 1}, {1, 2})
    expected = _p_f_1_3(150 / 7)
    assert abs(check.p_value - expected) < 1e-9, (check.p_value, expected)
    assert check.verdict == WARNING and check.assessment == "questionable"


def test_parallel_trends_warns_between_five_and_ten_percent_by_hand():
    # Pins the 10% warning threshold: a p between 0.05 and 0.10 must still warn.
    # Treated 5, 7 (mean 6); controls -1, 1: F = 36 / (14/3) = 54/7 = 7.71; by (d) p = 0.069137.
    check = _pt({1: 5, 2: 7, 3: -1, 4: 1}, {1, 2})
    expected = _p_f_1_3(54 / 7)
    assert abs(check.p_value - expected) < 1e-9 and 0.05 < expected < 0.10, (check.p_value, expected)
    assert check.verdict == WARNING and check.assessment == "questionable"


def test_parallel_trends_violated_by_hand():
    # Treated 21, 23 (mean 22); controls -1, 1: F = 484 / (14/3) = 726/7 = 103.71,
    # by (d) p = 0.002018 < 0.01: "violated".
    check = _pt({1: 21, 2: 23, 3: -1, 4: 1}, {1, 2})
    expected = _p_f_1_3(726 / 7)
    assert abs(check.p_value - expected) < 1e-9, (check.p_value, expected)
    assert check.verdict == WARNING and check.assessment == "violated"


def test_parallel_trends_not_computable_edge_cases():
    # One pre-treatment period only (treatment in period 1): no pre-trend to test.
    one_pre = _check_parallel_trends(_two_period({1: 1, 2: 3, 3: 0, 4: 4}, {1, 2}),
                                     "Y", "unit", "period", "treated_unit", 1)
    # No control unit at all: nothing to compare the treated trend with.
    no_controls = _check_parallel_trends(_two_period({1: 1, 2: 3}, {1, 2}, extra_period=2),
                                         "Y", "unit", "period", "treated_unit", 2)
    assert one_pre.verdict == NOT_APPLICABLE and no_controls.verdict == NOT_APPLICABLE


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
    # Adjacent 3, 5 (mean 4); far -1, 1 (mean 0): effect 4, variance 14/3,
    # z = 4 / sqrt(14/3) = 1.851640, p = erfc(z / sqrt(2)) = 0.064078 < 0.10: WARNING.
    check = _spill({4: 3, 6: 5, 10: -1, 12: 1})
    z = 4 / sqrt(CLUSTER_VAR)
    assert abs(check.statistic - 4.0) < 1e-9, check.statistic
    assert abs(check.p_value - erfc(z / sqrt(2))) < 1e-9, check.p_value
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
