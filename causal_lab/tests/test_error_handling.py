"""Errors are explicit: reported, or caught only where expected (hw6 review 5).

Each test names the silent behaviour it replaces.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pytest

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


def test_text_treatment_is_an_error_not_a_nan_estimate():
    # Before: params.get("D", nan) returned NaN, because a text or boolean D
    # enters the formula as a category named "D[T.…]".
    df = _world()
    with pytest.raises(LocalizedError, match="not numeric"):
        estimate_did(df.assign(D=df["D"].map({1: "yes", 0: "no"})))
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


def test_a_regression_that_cannot_be_computed_is_na_and_a_bug_is_not_hidden(monkeypatch):
    # Before: any exception became a WARNING, i.e. counted as a threat.
    df = _world()

    def singular(*args, **kwargs):
        raise np.linalg.LinAlgError("Singular matrix")
    monkeypatch.setattr(stress.smf, "ols", singular)
    report = stress.run_stress_test(df, treatment_period=4, ids_encode_neighbourhood=True)
    for name in ("Parallel Trends", "Anticipation", "Spillovers", "Serial Correlation"):
        check = next(c for c in report.checks if c.name == name)
        assert check.verdict == stress.NOT_APPLICABLE and "Singular matrix" in str(check.message), name

    def bug(*args, **kwargs):
        raise TypeError("a programming error")
    monkeypatch.setattr(stress.smf, "ols", bug)
    with pytest.raises(TypeError):
        stress.run_stress_test(df, treatment_period=4, ids_encode_neighbourhood=True)


def test_leave_one_out_skips_only_units_whose_removal_removes_the_treatment(monkeypatch):
    # Before: `except Exception: continue` also skipped real failures.
    df = _world()
    calls = {"n": 0}
    real = robustness.estimate_did

    def failing_on_loo(sub, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] > 3:                # baseline and the two windows succeed
            raise TypeError("a programming error")
        return real(sub, *args, **kwargs)
    monkeypatch.setattr(robustness, "estimate_did", failing_on_loo)
    with pytest.raises(TypeError):
        robustness.run_robustness_battery(df, 4, ids_encode_neighbourhood=False)


def test_matching_reports_how_many_bootstrap_replications_were_usable():
    df, truth = mw.matching_world(mw.MatchingWorldConfig(seed=2))
    roles = truth["roles"]
    result = estimate_matching(df, roles["outcome"], roles["treatment"], roles["covariates"])
    used = result.details["ipw_bootstrap_used"]
    assert 1 < used <= N_BOOTSTRAP


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
