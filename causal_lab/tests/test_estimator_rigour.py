"""Corrections made after the estimator validation study (spike/estimator_validation.py).

- IV: the Anderson-Rubin confidence set, robust to weak instruments, equals an
  independent inversion of the heteroskedasticity-robust test (statsmodels).
- RDD: the app reports robust bias-corrected inference by default.
- Synthetic control: with fewer than 19 donors the placebo test cannot reject at
  5%, and the result says so.
"""
import sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import statsmodels.api as sm

from estimators.iv import estimate_iv
from estimators.rdd import APP_INFERENCE
from estimators.registry import WORLDS, run_method, virtual_options


def _robust_p(df, b0, instruments, controls=("X",)):
    """p-value of the HC0 Wald test that the instruments do not predict Y - b0 D."""
    x = sm.add_constant(df[list(controls) + list(instruments)], has_constant="add")
    fit = sm.OLS(df["Y"] - b0 * df["D"], x).fit(cov_type="HC0")
    return float(fit.wald_test(", ".join(f"{z} = 0" for z in instruments), scalar=True).pvalue)


def _iv_world(**changes):
    world = WORLDS["iv"]
    df, _ = world.generate(replace(world.config_cls(), **changes))
    return df


def test_anderson_rubin_set_inverts_the_robust_test():
    df = _iv_world(n=500, seed=3)
    d = estimate_iv(df, "Y", "D", ["Z"], ["X"]).details
    assert d["ar_kind"] == "interval"
    for bound in (d["ar_low"], d["ar_high"]):
        assert abs(_robust_p(df, bound, ["Z"]) - 0.05) < 1e-6
    assert _robust_p(df, (d["ar_low"] + d["ar_high"]) / 2, ["Z"]) > 0.05
    assert _robust_p(df, d["ar_high"] + 0.1, ["Z"]) < 0.05
    assert abs(d["ar_p_zero"] - _robust_p(df, 0.0, ["Z"])) < 1e-9


def test_anderson_rubin_set_with_two_instruments():
    df = _iv_world(n=500, seed=3)
    df["Z2"] = 0.5 * df["Z"] + np.random.default_rng(0).normal(size=len(df))
    d = estimate_iv(df, "Y", "D", ["Z", "Z2"], ["X"]).details
    assert d["ar_kind"] == "interval"
    for bound in (d["ar_low"], d["ar_high"]):
        assert abs(_robust_p(df, bound, ["Z", "Z2"]) - 0.05) < 1e-6
    assert abs(d["ar_p_zero"] - _robust_p(df, 0.0, ["Z", "Z2"])) < 1e-9


def test_anderson_rubin_set_is_unbounded_when_the_instrument_is_useless():
    # With an almost irrelevant instrument every value is plausible: an honest
    # answer where the 2SLS Wald interval would be finite and misleading.
    result = estimate_iv(_iv_world(n=200, instrument_strength=0.1, seed=5), "Y", "D", ["Z"], ["X"])
    assert result.details["first_stage_f"] < 10 and result.details["ar_kind"] in ("line", "rays")
    assert any(w.key == "warn.weak_instrument" for w in result.warnings)
    assert result.summary_lines[-1].key.startswith("summary.iv.ar_")


def test_rdd_reports_robust_inference_by_default():
    world = WORLDS["rdd"]
    df, truth = world.generate(world.config_cls())
    options = virtual_options("rdd", truth)
    assert APP_INFERENCE == "robust" and options["inference"] == "robust"
    result = run_method("rdd", df, dict(truth["roles"]), options)
    assert result.details["inference"] == "robust"


def test_synthetic_control_warns_when_the_placebo_test_cannot_reject():
    world = WORLDS["synthetic_control"]
    for donors, warned in ((8, True), (20, False)):
        df, truth = world.generate(replace(world.config_cls(), n_donors=donors))
        result = run_method("synthetic_control", df, dict(truth["roles"]), virtual_options("synthetic_control", truth))
        keys = [w.key for w in result.warnings]
        assert ("warn.sc_few_donors" in keys) is warned, (donors, keys)
        assert result.p_value >= 1 / (donors + 1) - 1e-12


def test_staggered_did_reports_its_smallest_cohort_and_the_report_warns():
    from datetime import datetime
    from estimators.staggered_did import SMALL_COHORT, estimate_staggered_did
    from report_engine.builder import Paragraph, build_report
    from simulation_engine.dgp import VirtualWorldConfig, generate
    small, _ = generate(replace(VirtualWorldConfig(staggered_adoption=True), seed=1))
    large, _ = generate(replace(VirtualWorldConfig(staggered_adoption=True, n_units=400), seed=1))
    assert estimate_staggered_did(small).min_cohort_size < SMALL_COHORT <= estimate_staggered_did(large).min_cohort_size
    cfg = replace(VirtualWorldConfig(staggered_adoption=True), seed=1)
    df, truth = generate(cfg)
    texts = [b.text for b in build_report({"virtual_df": df, "virtual_truth": truth, "virtual_cfg": cfg}, "en",
                                          now=datetime(2026, 10, 31)).blocks if isinstance(b, Paragraph)]
    assert any("smallest adoption cohort has only" in t for t in texts)


def test_staggered_analytic_inference_is_welch_in_the_two_group_case():
    # One cohort treated in period 1, never-treated controls, two periods: the ATT is a
    # difference of two means of outcome changes, and the analytic test must be Welch's.
    import pandas as pd
    from scipy import stats
    from estimators.staggered_did import estimate_staggered_did
    rng = np.random.default_rng(7)
    n_t, n_c = 6, 15
    rows = []
    for u in range(n_t + n_c):
        treated = u < n_t
        y0 = rng.normal()
        rows += [(u, 0, 0, y0), (u, 1, int(treated), y0 + rng.normal(0.4 if treated else 0.0, 1.0 + treated))]
    df = pd.DataFrame(rows, columns=["unit", "period", "D", "Y"])
    result = estimate_staggered_did(df)
    change = df.pivot(index="unit", columns="period", values="Y").diff(axis=1)[1]
    welch = stats.ttest_ind(change[:n_t], change[n_t:], equal_var=False)
    assert result.inference == "analytic"
    assert abs(result.att - (change[:n_t].mean() - change[n_t:].mean())) < 1e-12
    assert abs(result.p_value - welch.pvalue) < 1e-10
    assert abs(result.df - welch.df) < 1e-8


def test_staggered_analytic_inference_handles_a_one_unit_cohort():
    from estimators.staggered_did import estimate_staggered_did
    from simulation_engine.dgp import VirtualWorldConfig, generate
    for seed in range(40):              # find a world with a one-unit cohort
        df, _ = generate(replace(VirtualWorldConfig(staggered_adoption=True), seed=seed))
        result = estimate_staggered_did(df)
        if result.min_cohort_size == 1:
            break
    assert result.min_cohort_size == 1
    assert result.inference == "analytic" and np.isfinite(result.se) and result.se > 0
    assert np.isfinite(result.event_study["se"]).all()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("test_estimator_rigour: OK")
