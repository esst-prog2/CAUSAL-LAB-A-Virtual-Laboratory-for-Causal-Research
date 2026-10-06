import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from estimators.dml import estimate_dml
from simulation_engine.method_worlds import DMLWorldConfig, dml_world


def test_dml_recovers_theta_and_beats_naive_ols():
    df, truth = dml_world(DMLWorldConfig(n=1500, seed=10))
    result = estimate_dml(df, covariate_cols=truth["roles"]["covariates"], seed=1)
    theta = truth["true_effect"]
    print("DML:", result.estimate, "OLS:", result.details["ols_estimate"], "truth:", theta)
    assert abs(result.estimate - theta) < 3 * result.se
    assert abs(result.details["ols_estimate"] - theta) > abs(result.estimate - theta)


def test_dml_is_reproducible():
    df, truth = dml_world(DMLWorldConfig(n=400, seed=11))
    covs = truth["roles"]["covariates"]
    a = estimate_dml(df, covariate_cols=covs, seed=3)
    b = estimate_dml(df, covariate_cols=covs, seed=3)
    assert a.estimate == b.estimate and a.se == b.se


if __name__ == "__main__":
    test_dml_recovers_theta_and_beats_naive_ols()
    test_dml_is_reproducible()
    print("test_dml: OK")
