"""Errors are explicit: reported, or caught only where expected (hw6 review 5).

Each test names the silent behaviour it replaces. Like every test file here,
it runs as a plain script and needs no test framework (hw6 review 6).
"""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

import robustness_engine.robustness as robustness
import robustness_engine.stress_test as stress
from estimators.did import estimate_did
from estimators.matching import N_BOOTSTRAP, estimate_matching
from simulation_engine import method_worlds as mw
from simulation_engine.dgp import VirtualWorldConfig, generate
from utils.i18n import LocalizedError
from utils.validation import invalid_required_columns


def _world():
    return generate(VirtualWorldConfig(n_units=40, n_periods=8, treatment_period=4, seed=5))[0]


def _raises(exc_type, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc_type as exc:
        return exc
    raise AssertionError(f"expected {exc_type.__name__}")


def test_text_treatment_is_an_error_not_a_nan_estimate():
    # Before: params.get("D", nan) returned NaN, because a text or boolean D
    # enters the formula as a category named "D[T.…]".
    df = _world()
    exc = _raises(LocalizedError, estimate_did, df.assign(D=df["D"].map({1: "yes", 0: "no"})))
    assert "not numeric" in str(exc)
    assert estimate_did(df.assign(D=df["D"].astype(bool))).att == estimate_did(df).att


def test_upload_rejects_columns_the_estimators_cannot_use():
    # Spec real-world-data-upload: D and treated_unit are 0/1 indicators.
    df = _world()
    assert invalid_required_columns(df) == []
    assert invalid_required_columns(df.assign(D=df["D"].astype(bool))) == []
    assert invalid_required_columns(df.assign(D=df["D"].map({1: "yes", 0: "no"}))) == ["D"]
    assert invalid_required_columns(df.assign(treated_unit=df["treated_unit"] * 2, Y=df["Y"].astype(str))) \
        == ["treated_unit", "Y"]
    assert invalid_required_columns(df.assign(D=df["D"].where(df.index > 0))) == ["D"]


def test_a_regression_that_cannot_be_computed_is_na_and_a_bug_is_not_hidden():
    # Before: any exception became a WARNING, i.e. counted as a threat.
    df = _world()
    with patch.object(stress.smf, "ols", side_effect=np.linalg.LinAlgError("Singular matrix")):
        report = stress.run_stress_test(df, treatment_period=4, ids_encode_neighbourhood=True)
    for name in ("Parallel Trends", "Anticipation", "Spillovers", "Serial Correlation"):
        check = next(c for c in report.checks if c.name == name)
        assert check.verdict == stress.NOT_APPLICABLE and "Singular matrix" in str(check.message), name
    with patch.object(stress.smf, "ols", side_effect=TypeError("a programming error")):
        _raises(TypeError, stress.run_stress_test, df, treatment_period=4, ids_encode_neighbourhood=True)


def test_leave_one_out_skips_only_units_whose_removal_removes_the_treatment():
    # Before: `except Exception: continue` also skipped real failures.
    df = _world()
    real = robustness.estimate_did
    calls = {"n": 0}

    def failing_on_loo(sub, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] > 3:                # baseline and the two windows succeed
            raise TypeError("a programming error")
        return real(sub, *args, **kwargs)
    with patch.object(robustness, "estimate_did", failing_on_loo):
        _raises(TypeError, robustness.run_robustness_battery, df, 4, ids_encode_neighbourhood=False)


def test_matching_reports_how_many_bootstrap_replications_were_usable():
    df, truth = mw.matching_world(mw.MatchingWorldConfig(seed=2))
    roles = truth["roles"]
    result = estimate_matching(df, roles["outcome"], roles["treatment"], roles["covariates"])
    used = result.details["ipw_bootstrap_used"]
    assert 1 < used <= N_BOOTSTRAP


if __name__ == "__main__":
    test_text_treatment_is_an_error_not_a_nan_estimate()
    test_upload_rejects_columns_the_estimators_cannot_use()
    test_a_regression_that_cannot_be_computed_is_na_and_a_bug_is_not_hidden()
    test_leave_one_out_skips_only_units_whose_removal_removes_the_treatment()
    test_matching_reports_how_many_bootstrap_replications_were_usable()
    print("test_error_handling: OK")
