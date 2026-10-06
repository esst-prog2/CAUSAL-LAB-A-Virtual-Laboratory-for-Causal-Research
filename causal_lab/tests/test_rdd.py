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


if __name__ == "__main__":
    test_rdd_recovers_jump()
    test_user_bandwidth_restricts_sample()
    test_cutoff_outside_data_rejected()
    test_manipulation_warning_on_bunching()
    print("test_rdd: OK")
