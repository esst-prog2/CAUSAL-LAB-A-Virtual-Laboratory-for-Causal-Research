"""Checks that cannot be computed are N/A and do not count in the score
(hw6 review 3; decisions by the user in PLANNING_LOG.md, 2026-10-16).

Before: on a two-period panel, Parallel Trends and Anticipation returned
WARNING, Serial Correlation always returned WARNING (rho = 1 by
construction), and Spillovers used store-id adjacency on real data, so
the Card & Krueger score (40/100) measured the shape of the data, not
the design.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from robustness_engine.stress_test import NOT_APPLICABLE, run_stress_test
from simulation_engine.dgp import VirtualWorldConfig, generate
from utils.real_data import load_card_krueger


def test_two_period_real_data_reports_na_instead_of_warnings():
    report = run_stress_test(load_card_krueger(), treatment_period=1, ids_encode_neighbourhood=False)
    verdicts = {c.name: c.verdict for c in report.checks}
    for name in ("Parallel Trends", "Anticipation", "Spillovers", "Serial Correlation"):
        assert verdicts[name] == NOT_APPLICABLE, verdicts
    (only,) = [c for c in report.checks if c.verdict != NOT_APPLICABLE]
    assert report.n_computable == 1
    # Constants, not the program's formula (instructor feedback on hw6): with a
    # single computable check the score is 100 if it passes and 0 if it warns.
    assert report.identification_strength == {"PASS": 100.0, "WARNING": 0.0}[only.verdict]


def test_spillovers_need_ids_that_encode_a_neighbourhood():
    df, _ = generate(VirtualWorldConfig(seed=3))
    with_ids = run_stress_test(df, treatment_period=10, ids_encode_neighbourhood=True)
    without = run_stress_test(df, treatment_period=10, ids_encode_neighbourhood=False)
    spill = lambda r: next(c for c in r.checks if c.name == "Spillovers").verdict
    assert spill(with_ids) in ("PASS", "WARNING")
    assert spill(without) == NOT_APPLICABLE
    assert without.n_computable == 4


def test_no_computable_check_gives_no_score():
    df, _ = generate(VirtualWorldConfig(n_units=4, n_periods=2, treatment_period=1, seed=1))
    report = run_stress_test(df, treatment_period=1, ids_encode_neighbourhood=False)
    assert all(c.verdict == NOT_APPLICABLE for c in report.checks), [(c.name, c.verdict) for c in report.checks]
    assert report.identification_strength is None and report.n_computable == 0


if __name__ == "__main__":
    test_two_period_real_data_reports_na_instead_of_warnings()
    test_spillovers_need_ids_that_encode_a_neighbourhood()
    test_no_computable_check_gives_no_score()
    print("test_stress_not_applicable: OK")
