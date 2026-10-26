"""Break My Design for the six Causal Methods."""
import sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import statsmodels.api as sm

from estimators.registry import WORLDS, virtual_options
from robustness_engine.method_stress import CHECKS, run_method_stress_test
from utils.i18n import render


def _report(method, **change):
    world = WORLDS[method]
    df, truth = world.generate(replace(world.config_cls(), **change))
    return run_method_stress_test(method, df, dict(truth["roles"]), virtual_options(method, truth))


def _verdict(report, slug):
    return next(c.verdict for c in report.checks if c.slug == slug)


def test_every_method_runs_its_checks_with_translated_messages():
    for method in CHECKS:
        report = _report(method, **({"n": 400} if method == "dml" else {}))
        assert [c.slug for c in report.checks] == list(CHECKS[method]), method
        for check in report.checks:
            assert check.verdict in ("PASS", "WARNING", "N/A")
            for lang in ("en", "fr"):
                text = render(check.message, lang)
                assert text and "{" not in text and not text.startswith("mstress."), (method, lang, text)
        assert report.identification_strength is None or 0 <= report.identification_strength <= 100


def test_threats_turned_on_in_the_worlds_are_flagged():
    assert _verdict(_report("iv", instrument_strength=0.05), "iv_weak_instrument") == "WARNING"
    assert _verdict(_report("rct", n=40), "rct_arm_size") == "WARNING"
    confounded = _report("matching", confounding_strength=3.0)
    assert _verdict(confounded, "matching_balance") == "WARNING"
    assert _verdict(confounded, "matching_extreme_ps") == "WARNING"
    assert _verdict(_report("synthetic_control", noise_sd=3.0), "sc_pre_fit") == "WARNING"


def test_rct_balance_is_the_joint_hc1_wald_test():
    world = WORLDS["rct"]
    df, truth = world.generate(world.config_cls(seed=3))
    report = run_method_stress_test("rct", df, dict(truth["roles"]), {})
    covariates = truth["roles"]["covariates"]
    fit = sm.OLS(df["D"].astype(float), sm.add_constant(df[covariates])).fit(cov_type="HC1")
    expected = float(fit.f_test(np.eye(len(covariates) + 1)[1:]).pvalue)
    check = report.checks[0]
    assert abs(check.p_value - expected) < 1e-12 and check.verdict == ("WARNING" if expected < 0.1 else "PASS")
    # Assignment that depends on X1 is caught.
    df2 = df.copy()
    df2["D"] = (df2["X1"] + np.random.default_rng(0).normal(scale=0.5, size=len(df2)) > 0).astype(int)
    assert run_method_stress_test("rct", df2, dict(truth["roles"]), {}).checks[0].verdict == "WARNING"
    no_cov = run_method_stress_test("rct", df, {"outcome": "Y", "treatment": "D", "covariates": []}, {})
    assert no_cov.checks[0].verdict == "N/A"


def _two_instrument_data(invalid: bool, seed=1, n=3000):
    rng = np.random.default_rng(seed)
    z1, z2, u = rng.normal(size=n), rng.normal(size=n), rng.normal(size=n)
    d = z1 + z2 + u + rng.normal(size=n)
    y = 2 * d + u + (1.0 * z2 if invalid else 0.0) + rng.normal(size=n)
    return pd.DataFrame(dict(Y=y, D=d, Z1=z1, Z2=z2))


def test_weak_instrument_threshold_is_ten():
    # instrument_strength 0.3 gives F = 4.4 (seed 42): below 10, above any looser rule of thumb.
    moderate = _report("iv", instrument_strength=0.3)
    f = moderate.checks[0].statistic
    assert 1 < f < 10 and _verdict(moderate, "iv_weak_instrument") == "WARNING", f
    strong = _report("iv", instrument_strength=0.5)
    assert strong.checks[0].statistic > 10 and _verdict(strong, "iv_weak_instrument") == "PASS"


def test_overidentification_uses_the_robust_wooldridge_score_test():
    from linearmodels.iv import IV2SLS
    data = _two_instrument_data(False, seed=4)
    mapping = {"outcome": "Y", "treatment": "D", "instruments": ["Z1", "Z2"], "controls": []}
    check = next(c for c in run_method_stress_test("iv", data, mapping, {}).checks if c.slug == "iv_overidentification")
    fit = IV2SLS(data["Y"], sm.add_constant(data[[]], has_constant="add"), data[["D"]],
                 data[["Z1", "Z2"]]).fit(cov_type="robust")
    assert abs(check.p_value - float(fit.wooldridge_overid.pval)) < 1e-12
    assert abs(check.p_value - float(fit.sargan.pval)) > 1e-6        # not the homoskedastic Sargan test


def test_overidentification_flags_an_instrument_that_enters_the_outcome():
    mapping = {"outcome": "Y", "treatment": "D", "instruments": ["Z1", "Z2"], "controls": []}
    valid = run_method_stress_test("iv", _two_instrument_data(False), mapping, {})
    invalid = run_method_stress_test("iv", _two_instrument_data(True), mapping, {})
    assert _verdict(valid, "iv_overidentification") == "PASS"
    assert _verdict(invalid, "iv_overidentification") == "WARNING"
    one = run_method_stress_test("iv", _two_instrument_data(False), {**mapping, "instruments": ["Z1"]}, {})
    assert _verdict(one, "iv_overidentification") == "N/A"


def test_rdd_placebo_cutoff_flags_a_second_jump():
    rng = np.random.default_rng(2)
    x = rng.uniform(-1, 1, 4000)
    y = 0.5 * x + 1.0 * (x >= 0) + 1.5 * (x >= -0.5) + rng.normal(scale=0.3, size=4000)
    df = pd.DataFrame(dict(Y=y, X=x))
    report = run_method_stress_test("rdd", df, {"outcome": "Y", "running": "X"}, {"cutoff": 0.0, "bandwidth": None})
    assert _verdict(report, "rdd_placebo_cutoffs") == "WARNING"


def test_score_counts_passes_among_computable_checks():
    report = _report("iv")                       # weak-instrument PASS, overidentification N/A
    assert report.n_computable == 1 and report.identification_strength == 100.0


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("test_method_stress: OK")
