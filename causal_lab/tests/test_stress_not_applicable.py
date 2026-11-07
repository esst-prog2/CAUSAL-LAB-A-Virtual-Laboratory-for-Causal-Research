"""Checks that cannot be computed are N/A and say nothing either way
(hw6 review 3; decisions by the user in PLANNING_LOG.md, 2026-10-16).

Before: on a two-period panel, Parallel Trends and Anticipation returned
WARNING, Serial Correlation always returned WARNING (rho = 1 by
construction), and Spillovers used store-id adjacency on real data, so
the Card & Krueger score (40/100, since removed) measured the shape of the data, not
the design.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from robustness_engine.stress_test import NOT_APPLICABLE, run_stress_test
from simulation_engine.dgp import VirtualWorldConfig, generate
from utils.real_data import load_card_krueger, read_card_krueger_raw


def test_two_period_real_data_reports_na_instead_of_warnings():
    report = run_stress_test(load_card_krueger(), treatment_period=1, ids_encode_neighbourhood=False)
    verdicts = {c.name: c.verdict for c in report.checks}
    for name in ("Parallel Trends", "Anticipation", "Spillovers", "Serial Correlation"):
        assert verdicts[name] == NOT_APPLICABLE, verdicts
    (only,) = [c for c in report.checks if c.verdict != NOT_APPLICABLE]
    assert report.n_computable == 1
    # The computable check concerns effect heterogeneity, not the identifying assumption:
    # whatever its verdict, these data say nothing about parallel trends.
    assert only.name == "Heterogeneous Effects" and report.summary == "insufficient"


def test_spillovers_need_ids_that_encode_a_neighbourhood():
    df, _ = generate(VirtualWorldConfig(seed=3))
    with_ids = run_stress_test(df, treatment_period=10, ids_encode_neighbourhood=True)
    without = run_stress_test(df, treatment_period=10, ids_encode_neighbourhood=False)
    spill = lambda r: next(c for c in r.checks if c.name == "Spillovers").verdict
    assert spill(with_ids) in ("PASS", "WARNING")
    assert spill(without) == NOT_APPLICABLE
    assert without.n_computable == 4


def test_no_computable_check_says_nothing():
    df, _ = generate(VirtualWorldConfig(n_units=4, n_periods=2, treatment_period=1, seed=1))
    report = run_stress_test(df, treatment_period=1, ids_encode_neighbourhood=False)
    assert all(c.verdict == NOT_APPLICABLE for c in report.checks), [(c.name, c.verdict) for c in report.checks]
    assert report.summary == "insufficient" and report.n_computable == 0


def test_card_krueger_only_the_heterogeneity_check_can_run():
    # Post-hw6 review of "100/100 on 1 of 5 checks". Each N/A must be a genuine
    # impossibility or a documented rule, not a computation failure:
    #   - Parallel Trends: one pre-treatment wave; a pre-trend needs two pre periods;
    #   - Anticipation: needs periods t-1 and t-2 before treatment; t-2 = -1 does not exist;
    #   - Spillovers: store numbers do not encode a neighbourhood (user decision, 2026-10-16);
    #   - Serial Correlation: two periods; within-unit residuals are mechanically opposite.
    report = run_stress_test(load_card_krueger(), treatment_period=1, ids_encode_neighbourhood=False)
    reasons = {c.name: c.message.key for c in report.checks if c.verdict == NOT_APPLICABLE}
    assert reasons == {"Parallel Trends": "stress.pt.not_enough",
                       "Anticipation": "stress.anticipation.not_enough",
                       "Spillovers": "stress.spillovers.no_neighbourhood",
                       "Serial Correlation": "stress.serial.not_enough"}, reasons

    # The one computable check, recomputed from the raw fixed-width file without the
    # app's loader or the check: FTE change of every store observed in both waves,
    # variance (ddof = 1) in New Jersey over Pennsylvania, upper tail of F(n_NJ - 1, n_PA - 1).
    from scipy import stats
    raw = read_card_krueger_raw()
    before = raw["EMPPT"] * 0.5 + raw["EMPFT"] + raw["NMGRS"]
    after = raw["EMPPT2"] * 0.5 + raw["EMPFT2"] + raw["NMGRS2"]
    change = (after - before).dropna()
    nj, pa = change[raw.loc[change.index, "STATE"] == 1], change[raw.loc[change.index, "STATE"] == 0]
    ratio = nj.var() / pa.var()
    (heterogeneity,) = [c for c in report.checks if c.verdict != NOT_APPLICABLE]
    assert (len(nj), len(pa)) == (309, 75)                     # Card & Krueger, Table 3, row 4 sample
    assert abs(heterogeneity.statistic - ratio) < 1e-9
    assert abs(heterogeneity.p_value - stats.f.sf(ratio, len(nj) - 1, len(pa) - 1)) < 1e-9
    # Changes vary less in New Jersey than in Pennsylvania (ratio < 1), so this
    # one-sided test cannot signal heterogeneity among the treated stores: PASS, which says
    # nothing about identification. (The removed score read 100/100 on this.)
    assert ratio < 1 and heterogeneity.verdict == "PASS" and report.summary == "insufficient"


if __name__ == "__main__":
    test_card_krueger_only_the_heterogeneity_check_can_run()
    test_two_period_real_data_reports_na_instead_of_warnings()
    test_spillovers_need_ids_that_encode_a_neighbourhood()
    test_no_computable_check_says_nothing()
    print("test_stress_not_applicable: OK")
