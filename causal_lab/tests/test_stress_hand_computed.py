"""Break My Design checked against values worked out by hand.

The other stress-test tests judge the checks through their verdicts on
simulated worlds, and test_stress_not_applicable.py used to compute the
expected score with the same formula as run_stress_test, so a wrong formula
or a wrong statistic could still pass (instructor feedback on hw6). Here
every expected number is derived on paper in the comments, from tiny
constant panels, independently of the code.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from robustness_engine.stress_test import (NOT_APPLICABLE, PASS, WARNING, CheckResult,
                                           _check_heterogeneous_effects, _check_serial_correlation,
                                           identification_strength)
from utils.i18n import Msg


def _panel(rows):
    return pd.DataFrame(rows, columns=["unit", "period", "treated_unit", "D", "Y"])


def test_heterogeneity_variance_ratio_and_p_value_by_hand():
    # Six two-period units, treatment from period 1; Y = 0 before, Y = change after.
    # Treated changes 1, 2, 3:   mean 2, squared deviations 1 + 0 + 1 = 2, variance 2/2 = 1.
    # Control changes 1, 1.5, 2: mean 1.5, squared deviations 0.25 + 0 + 0.25 = 0.5, variance 0.25.
    # Variance ratio = 1 / 0.25 = 4.0. For F(2, 2), P(F > x) = 1 / (1 + x), so p = 1/5 = 0.2.
    # p >= 0.10, so the verdict is PASS.
    rows = []
    for unit, (treated, change) in enumerate([(1, 1), (1, 2), (1, 3), (0, 1), (0, 1.5), (0, 2)]):
        rows += [(unit, 0, treated, 0, 0.0), (unit, 1, treated, treated, float(change))]
    check = _check_heterogeneous_effects(_panel(rows), "Y", "unit", "period", "treated_unit", 1)
    assert abs(check.statistic - 4.0) < 1e-12, check.statistic
    assert abs(check.p_value - 0.2) < 1e-12, check.p_value
    assert check.verdict == PASS


def test_heterogeneity_unequal_groups_warns_by_hand():
    # Added in the review of PR #8: with two groups of 3, a variance computed
    # with ddof=0 gives the same ratio, and the case above never reaches WARNING.
    # Treated changes 1, 2, 3: variance 2/2 = 1, numerator df = 2.
    # Control changes 1, 1.5, 2, 1.5, 1.5: mean 1.5, squared deviations 0.25 + 0 + 0.25 + 0 + 0 = 0.5,
    #   variance 0.5/4 = 0.125, denominator df = 4.
    # Variance ratio = 1 / 0.125 = 8.0 (with ddof=0 it would be (2/3) / 0.1 = 6.67).
    # For F(2, d2) the density is (1 + 2x/d2)^-(d2/2 + 1), so P(F > x) = (1 + 2x/d2)^(-d2/2):
    #   P(F(2, 4) > 8) = (1 + 4)^-2 = 1/25 = 0.04 < 0.10, so the verdict is WARNING.
    rows = []
    for unit, (treated, change) in enumerate([(1, 1), (1, 2), (1, 3),
                                              (0, 1), (0, 1.5), (0, 2), (0, 1.5), (0, 1.5)]):
        rows += [(unit, 0, treated, 0, 0.0), (unit, 1, treated, treated, float(change))]
    check = _check_heterogeneous_effects(_panel(rows), "Y", "unit", "period", "treated_unit", 1)
    assert abs(check.statistic - 8.0) < 1e-12, check.statistic
    assert abs(check.p_value - 0.04) < 1e-12, check.p_value
    assert check.verdict == WARNING


def test_serial_correlation_durbin_watson_by_hand():
    # Units A and B, periods 0, 1, 2; only B is treated, in period 2 (D = 1 in one cell).
    #   Y_A = (0, 0, 5), Y_B = (0, 4, 7).
    # Two-way fixed-effects residuals of Y ~ D + unit + period:
    #   - the cell (B, 2) is the only one with D = 1, so D fits it exactly: residual 0;
    #   - then (A, 2) is the only other period-2 cell, so the period-2 effect fits it: residual 0;
    #   - the rest is the 2 x 2 block of periods 0-1, whose residual is the interaction
    #     y - row mean - column mean + grand mean, with row means A 0, B 2, column means 0, 2,
    #     grand mean 1:  A: (0-0-0+1, 0-0-2+1) = (1, -1),  B: (0-2-0+1, 4-2-2+1) = (-1, 1).
    # Residuals by unit: A (1, -1, 0), B (-1, 1, 0); sum of squares = 4.
    # Within-unit differences: A (-2, 1), B (2, -1); sum of squares = 4 + 1 + 4 + 1 = 10.
    # DW = 10 / 4 = 2.5. Corrected rho = (1 - 2.5/2) + 1/(3 - 1) = -0.25 + 0.5 = 0.25 > 0.2: WARNING.
    df = _panel([("A", 0, 0, 0, 0.0), ("A", 1, 0, 0, 0.0), ("A", 2, 0, 0, 5.0),
                 ("B", 0, 1, 0, 0.0), ("B", 1, 1, 0, 4.0), ("B", 2, 1, 1, 7.0)])
    check = _check_serial_correlation(df, "Y", "unit", "period", "D")
    assert abs(check.statistic - 2.5) < 1e-9, check.statistic
    assert check.verdict == WARNING
    assert "0.25" in str(check.message)          # the corrected rho, as shown to the user


def _check(verdict):
    return CheckResult("x", verdict, Msg("verdict.PASS"))


def test_score_counts_pass_over_computable_checks():
    # 2 PASS, 1 WARNING, 2 N/A: 3 computable checks, 2 of them PASS -> 100 * 2 / 3 = 66.67.
    checks = [_check(PASS), _check(PASS), _check(WARNING), _check(NOT_APPLICABLE), _check(NOT_APPLICABLE)]
    assert round(identification_strength(checks), 2) == 66.67
    # One computable check: 100 if it passes, 0 if it warns; none computable: no score.
    assert identification_strength([_check(PASS)] + [_check(NOT_APPLICABLE)] * 4) == 100.0
    assert identification_strength([_check(WARNING)] + [_check(NOT_APPLICABLE)] * 4) == 0.0
    assert identification_strength([_check(NOT_APPLICABLE)] * 5) is None


if __name__ == "__main__":
    test_heterogeneity_variance_ratio_and_p_value_by_hand()
    test_heterogeneity_unequal_groups_warns_by_hand()
    test_serial_correlation_durbin_watson_by_hand()
    test_score_counts_pass_over_computable_checks()
    print("test_stress_hand_computed: OK")
