"""The Causal Methods estimators and Callaway & Sant'Anna checked against established implementations.

Each estimator runs on a committed dataset and is compared with the value an
external reference package gives on the same data, with the same settings
(tests/external_reference/expected.json, written by make_reference.py; see
its docstring for the package and options behind each number). The
reference packages are not needed here, only their stored output.

Tolerances follow what each comparison can achieve:
- closed-form estimators (RCT, IV, RDD estimate, DML): 1e-9 relative, i.e.
  floating-point rounding only;
- iterative ones (synthetic control weights): 1e-4, the optimizers' precision;
- the RDD standard error: 1e-4 relative. rdrobust computes its HC1 variance
  side by side, Causal Lab in one weighted regression; the gap is 2.6e-5.
Matching has two comparisons; see the comment above its tests.
"""
import json
import sys
import warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "external_reference"))

import numpy as np

from make_reference import load

from estimators.dml import estimate_dml
from estimators.iv import estimate_iv
from estimators.matching import estimate_matching
from estimators.rct import estimate_rct
from estimators.rdd import estimate_rdd, ik_bandwidth
from estimators.staggered_did import estimate_staggered_did
from estimators.synthetic_control import estimate_synthetic_control

EXPECTED = json.loads((Path(__file__).resolve().parent / "external_reference" / "expected.json")
                      .read_text(encoding="utf-8"))
SETTINGS = EXPECTED["settings"]
EXACT = 1e-9


def _close(actual: float, key: str, rel: float = EXACT) -> None:
    expected = EXPECTED[key]
    assert abs(actual - expected) <= rel * abs(expected), (key, actual, expected)


def test_rct_matches_estimatr():
    # estimatr::lm_robust(Y ~ D, se_type = "HC2"): difference in means.
    plain = estimate_rct(load("rct"))
    _close(plain.estimate, "rct.diff.estimate")
    _close(plain.se, "rct.diff.se")
    # estimatr::lm_lin(Y ~ D, covariates = ~ X, se_type = "HC2"): Lin (2013).
    lin = estimate_rct(load("rct"), covariate_cols=["X"])
    _close(lin.estimate, "rct.lin.estimate")
    _close(lin.se, "rct.lin.se")


def test_iv_matches_estimatr():
    # estimatr::iv_robust(Y ~ D + W | Z + W, se_type = "HC0").
    result = estimate_iv(load("iv"), instrument_cols=["Z"], control_cols=["W"])
    _close(result.estimate, "iv.estimate")
    _close(result.se, "iv.se")


def test_iv_first_stage_f_matches_estimatr():
    # estimatr::iv_robust(..., se_type = "HC0", diagnostics = TRUE): first-stage F of Z.
    result = estimate_iv(load("iv"), instrument_cols=["Z"], control_cols=["W"])
    _close(result.details["first_stage_f"], "iv.first_stage_f")


def test_ik_bandwidth_is_close_to_rdrobust_0_80():
    # R rdrobust 0.80, rdbwselect(bwselect = "IK", kernel = "tri", p = 1): the last
    # implementation of Imbens & Kalyanaraman (2012) by rdrobust's authors. The gap was
    # 0.4% when this test was written (pilot steps differ in detail). R rdd 0.57 gives
    # 0.752 instead: it follows the 2009 working paper (regularization 720 instead of
    # 2160, pooled variance), which a line-by-line port reproduces to 1e-15.
    data = load("rdd")
    h = ik_bandwidth(data["X"].to_numpy(float), data["Y"].to_numpy(float), 0.0)
    _close(h, "rdd.ik_bandwidth", rel=0.01)


def test_rdd_matches_rdrobust():
    # rdrobust(y, x, c = 0, h = 0.4, kernel = "triangular", p = 1, vce = "hc1"). Since
    # 2026-10-25 Causal Lab computes the HC1 variance side by side as rdrobust does, so
    # the conventional SE agrees to rounding (it was 2.6e-5 apart before).
    result = estimate_rdd(load("rdd"), bandwidth=SETTINGS["rdd_bandwidth"])
    _close(result.estimate, "rdd.estimate")
    _close(result.se, "rdd.se")
    assert (result.details["n_left"], result.details["n_right"]) == \
        (EXPECTED["rdd.n_left"], EXPECTED["rdd.n_right"])
    # Robust bias-corrected row (CCT 2014), b = h.
    robust = estimate_rdd(load("rdd"), bandwidth=SETTINGS["rdd_bandwidth"], inference="robust")
    _close(robust.details["robust"]["estimate_bc"], "rdd.robust.estimate_bc")
    _close(robust.se, "rdd.robust.se")


def test_fuzzy_rdd_matches_rdrobust():
    # rdrobust(..., fuzzy = D): local Wald estimate, conventional and robust rows.
    result = estimate_rdd(load("rdd_fuzzy"), bandwidth=SETTINGS["rdd_bandwidth"], treatment_col="D",
                          inference="robust")
    _close(result.estimate, "rdd_fuzzy.estimate")
    _close(result.details["conventional"]["se"], "rdd_fuzzy.se")
    _close(result.details["robust"]["estimate_bc"], "rdd_fuzzy.robust.estimate_bc")
    _close(result.se, "rdd_fuzzy.robust.se")


# Matching: R Matching::Match(estimand = "ATT", M = 1, Weight = 2 (Mahalanobis),
# BiasAdjust = TRUE, Var.calc = 1). Since 2026-10-25 Causal Lab fits the bias
# correction regression as R does (matched controls weighted by their use), so
# both datasets must agree to rounding. Before, it used all controls: the
# estimate on matching.csv was 0.04 SE away. matching_linear.csv (controls
# exactly linear in X) agreed even then, since there both regressions recover
# the same coefficients; it now checks matches and variance on their own.

def test_matching_matches_r_matching_when_the_bias_regression_cannot_differ():
    result = estimate_matching(load("matching_linear"), covariate_cols=["X1", "X2"])
    _close(result.estimate, "matching_linear.adjusted.estimate")
    _close(result.se, "matching_linear.adjusted.se")


def test_matching_matches_r_matching_on_noisy_data():
    result = estimate_matching(load("matching"), covariate_cols=["X1", "X2"])
    _close(result.estimate, "matching.adjusted.estimate")
    _close(result.se, "matching.adjusted.se")


def test_synthetic_control_matches_pysyncon():
    # pysyncon Synth with the outcome in each pre-period as predictors and a
    # custom V that cancels its predictor scaling: min_w ||y1_pre - Y0_pre w||^2.
    result = estimate_synthetic_control(load("sc"), treated_unit="u0",
                                        treatment_period=SETTINGS["sc_treatment_period"])
    weights = result.details["weights"].set_index("donor")["weight"]
    for donor, weight in weights.items():
        assert abs(weight - EXPECTED[f"sc.weight.{donor}"]) < 1e-4, (donor, weight)
    _close(result.estimate, "sc.estimate", rel=1e-4)


def test_covariate_synthetic_control_fits_at_least_about_as_well_as_pysyncon():
    # Choosing the predictor importance V is not convex: neither optimizer is sure to find
    # the global optimum. On 6 worlds Causal Lab's pre-treatment MSPE was lower than
    # pysyncon's in 4 and at most 9% higher in 2 (2026-10-25), hence the 15% tolerance.
    data = load("sc_cov")
    result = estimate_synthetic_control(data, treated_unit="treated", treatment_period=20,
                                        covariate_cols=["X1", "X2", "X3"])
    wide = data.pivot(index="period", columns="unit", values="Y")
    weights = result.details["weights"].set_index("donor")["weight"]
    gaps = wide["treated"].to_numpy()[:20] - wide[weights.index].to_numpy()[:20] @ weights.to_numpy()
    assert float(np.mean(gaps ** 2)) <= 1.15 * EXPECTED["sc_cov.pre_mspe"], (np.mean(gaps ** 2),
                                                                            EXPECTED["sc_cov.pre_mspe"])
    v = result.details["predictors"]["v_weight"]
    assert abs(v.sum() - 1) < 1e-9 and (v >= 0).all() and abs(weights.sum() - 1) < 1e-9


def test_dml_matches_doubleml():
    # DoubleMLPLR, score "partialling out", with Causal Lab's folds and forests.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = estimate_dml(load("dml"), covariate_cols=["X1", "X2", "X3"],
                              n_folds=SETTINGS["dml_folds"], seed=SETTINGS["dml_seed"])
    _close(result.estimate, "dml.estimate")
    _close(result.se, "dml.se")


def test_callaway_santanna_matches_did():
    # R did: att_gt(base_period = "universal", control_group = ...), then aggte "simple"
    # (overall ATT) and "dynamic" (event study). Point estimates must agree to rounding.
    # SEs: both analytic. Causal Lab uses the unbiased (n - 1) variance within each cohort
    # and did uses n, so ours is slightly larger: 3.5% here (smallest cohort: 7 units).
    for ours, theirs in (("never_treated", "nevertreated"), ("not_yet_treated", "notyettreated")):
        result = estimate_staggered_did(load("cs"), comparison=ours)
        _close(result.att, f"cs.{theirs}.att")
        assert result.inference == "analytic"
        assert 1.0 < result.se / EXPECTED[f"cs.{theirs}.se"] < 1.05
        for row in result.event_study.itertuples():
            _close(row.estimate, f"cs.{theirs}.event.{row.rel_period}")
        # The reference period e = -1 is 0 by construction in did and left out by Causal Lab.
        assert EXPECTED[f"cs.{theirs}.event.-1"] == 0.0
        assert -1 not in set(result.event_study["rel_period"])


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("test_external_reference: OK")
