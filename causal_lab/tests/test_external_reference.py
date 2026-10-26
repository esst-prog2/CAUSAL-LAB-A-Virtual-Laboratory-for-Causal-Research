"""The six Causal Methods estimators checked against established implementations.

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

from make_reference import load

from estimators.dml import estimate_dml
from estimators.iv import estimate_iv
from estimators.matching import estimate_matching
from estimators.rct import estimate_rct
from estimators.rdd import estimate_rdd
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


def test_rdd_matches_rdrobust():
    # rdrobust(y, x, c = 0, h = 0.4, kernel = "triangular", p = 1, vce = "hc1"), conventional row.
    result = estimate_rdd(load("rdd"), bandwidth=SETTINGS["rdd_bandwidth"])
    _close(result.estimate, "rdd.estimate")
    _close(result.se, "rdd.se", rel=1e-4)
    assert (result.details["n_left"], result.details["n_right"]) == \
        (EXPECTED["rdd.n_left"], EXPECTED["rdd.n_right"])


# Matching: R Matching::Match(estimand = "ATT", M = 1, Weight = 2 (Mahalanobis),
# BiasAdjust = TRUE, Var.calc = 1). Both pick the same matches, but the bias
# correction regression differs: Causal Lab fits Y on X on all controls, R
# (like Stata's nnmatch and Abadie & Imbens 2011) on the matched controls
# weighted by their use. Both are consistent; they differ in finite samples.
#
# 1. matching_linear.csv: controls are exactly linear in X, so both
#    regressions recover the same coefficients and everything else (matches,
#    bias correction, Abadie-Imbens variance) must agree exactly.
# 2. matching.csv: noisy controls; only the regression sample differs. The
#    gap was 0.04 SE (estimate) and 0.03% (SE) when this test was written.

def test_matching_matches_r_matching_exactly_when_the_bias_regression_cannot_differ():
    result = estimate_matching(load("matching_linear"), covariate_cols=["X1", "X2"])
    _close(result.estimate, "matching_linear.adjusted.estimate")
    _close(result.se, "matching_linear.adjusted.se")


def test_matching_is_close_to_r_matching_on_noisy_data():
    result = estimate_matching(load("matching"), covariate_cols=["X1", "X2"])
    gap = abs(result.estimate - EXPECTED["matching.adjusted.estimate"])
    assert gap < 0.1 * result.se, (result.estimate, EXPECTED["matching.adjusted.estimate"], result.se)
    _close(result.se, "matching.adjusted.se", rel=0.01)


def test_synthetic_control_matches_pysyncon():
    # pysyncon Synth with the outcome in each pre-period as predictors and a
    # custom V that cancels its predictor scaling: min_w ||y1_pre - Y0_pre w||^2.
    result = estimate_synthetic_control(load("sc"), treated_unit="u0",
                                        treatment_period=SETTINGS["sc_treatment_period"])
    weights = result.details["weights"].set_index("donor")["weight"]
    for donor, weight in weights.items():
        assert abs(weight - EXPECTED[f"sc.weight.{donor}"]) < 1e-4, (donor, weight)
    _close(result.estimate, "sc.estimate", rel=1e-4)


def test_dml_matches_doubleml():
    # DoubleMLPLR, score "partialling out", with Causal Lab's folds and forests.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = estimate_dml(load("dml"), covariate_cols=["X1", "X2", "X3"],
                              n_folds=SETTINGS["dml_folds"], seed=SETTINGS["dml_seed"])
    _close(result.estimate, "dml.estimate")
    _close(result.se, "dml.se")


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("test_external_reference: OK")
