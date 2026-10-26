import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from estimators.rdd import estimate_rdd
from simulation_engine.method_worlds import RDDWorldConfig, rdd_world


def test_rdd_recovers_jump():
    df, truth = rdd_world(RDDWorldConfig(n=3000, cutoff=0.5, seed=6))
    result = estimate_rdd(df, "Y", "X", cutoff=0.5)
    print("RDD:", result.estimate, "SE:", result.se, "h:", result.details["bandwidth"], "truth:", truth["true_effect"])
    assert abs(result.estimate - truth["true_effect"]) < 3 * result.se
    assert result.details["bandwidth"] > 0
    assert list(result.details["sensitivity"]["factor"]) == [0.5, 1.0, 2.0]


def test_user_bandwidth_restricts_sample():
    df, _ = rdd_world(RDDWorldConfig(n=2000, seed=6))
    result = estimate_rdd(df, "Y", "X", cutoff=0.0, bandwidth=0.2)
    within = (df["X"].abs() < 0.2).sum()
    assert result.n_obs == within
    assert result.details["bandwidth_rule"] == "user"


def test_cutoff_outside_data_rejected():
    df, _ = rdd_world(RDDWorldConfig(seed=6))
    try:
        estimate_rdd(df, "Y", "X", cutoff=5.0)
    except ValueError as exc:
        assert "Cutoff" in str(exc)
    else:
        raise AssertionError("expected ValueError for a cutoff outside the data")


def test_manipulation_warning_on_bunching():
    df, _ = rdd_world(RDDWorldConfig(n=2000, seed=6))
    rng = np.random.default_rng(0)
    bunch = df.sample(400, random_state=0).assign(X=rng.uniform(0.0, 0.05, 400))
    bunched = pd.concat([df, bunch], ignore_index=True)
    result = estimate_rdd(bunched, "Y", "X", cutoff=0.0, bandwidth=0.3)
    assert any("manipulation" in w for w in result.warnings)


def test_fuzzy_rdd_recovers_the_complier_effect():
    df, truth = rdd_world(RDDWorldConfig(n=6000, compliance=0.6, effect=2.0, seed=3))
    result = estimate_rdd(df, "Y", "X", cutoff=0.0, treatment_col=truth["roles"]["treatment"])
    first = result.details["first_stage"]
    assert result.details["design"] == "fuzzy" and result.estimand.key == "estimand.rdd_fuzzy"
    assert abs(first["jump"] - 0.6) < 3 * first["se"], first
    assert abs(result.estimate - 2.0) < 3 * result.se, (result.estimate, result.se)
    # Ignoring the fuzziness estimates the intention-to-treat jump, about 0.6 * 2.0.
    sharp = estimate_rdd(df, "Y", "X", cutoff=0.0, bandwidth=result.details["bandwidth"])
    assert abs(sharp.estimate - 1.2) < 3 * sharp.se


def test_fuzzy_rdd_needs_a_first_stage():
    df, _ = rdd_world(RDDWorldConfig(seed=6))
    df["T"] = 1
    try:
        estimate_rdd(df, "Y", "X", cutoff=0.0, treatment_col="T")
    except ValueError as exc:
        assert "first stage" in str(exc)
    else:
        raise AssertionError("expected an error without a first stage")


def test_compliance_one_keeps_the_sharp_world():
    sharp, truth = rdd_world(RDDWorldConfig(seed=9))
    assert "treatment" not in truth["roles"] and set(sharp["D"]) == {0, 1}
    assert ((sharp["X"] >= 0).astype(int) == sharp["D"]).all()


def test_robust_inference_is_centred_on_the_bias_corrected_estimate():
    df, _ = rdd_world(RDDWorldConfig(seed=6))
    conventional = estimate_rdd(df, "Y", "X", cutoff=0.0)
    robust = estimate_rdd(df, "Y", "X", cutoff=0.0, inference="robust")
    rb = robust.details["robust"]
    assert robust.estimate == conventional.estimate                    # same point estimate
    assert abs((robust.ci_low + robust.ci_high) / 2 - rb["estimate_bc"]) < 1e-12
    assert robust.se == rb["se"] > conventional.se                     # accounts for the bias estimate
    assert conventional.details["robust"] == rb                        # always computed
    try:
        estimate_rdd(df, "Y", "X", cutoff=0.0, inference="bootstrap")
    except ValueError:
        pass
    else:
        raise AssertionError("expected an error for an unknown inference")


def test_robust_ci_covers_when_a_wide_bandwidth_biases_the_estimate():
    # Curvature 5 with h = 0.6 chosen by hand: the conventional CI covered the true
    # effect in 69% of 300 worlds, the robust bias-corrected CI in 95% (2026-10-25).
    from simulation_engine.method_monte_carlo import run_method_monte_carlo
    config = RDDWorldConfig(curvature=5.0)
    conventional = run_method_monte_carlo("rdd", config, n_reps=150,
                                          extra_options={"inference": "conventional", "bandwidth": 0.6})
    robust = run_method_monte_carlo("rdd", config, n_reps=150,
                                    extra_options={"inference": "robust", "bandwidth": 0.6})
    assert conventional.coverage < 0.80 and robust.coverage > 0.90, (conventional.coverage, robust.coverage)


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("test_rdd: OK")
