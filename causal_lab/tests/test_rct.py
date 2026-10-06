import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from estimators.rct import estimate_rct
from simulation_engine.method_worlds import RCTWorldConfig, rct_world


def test_rct_recovers_ate_and_adjustment_helps():
    df, truth = rct_world(RCTWorldConfig(n=800, seed=5))
    covs = truth["roles"]["covariates"]
    adjusted = estimate_rct(df, covariate_cols=covs)
    unadjusted = estimate_rct(df)
    print("RCT adjusted:", adjusted.estimate, "unadjusted:", unadjusted.estimate, "truth:", truth["true_effect"])
    assert abs(adjusted.estimate - truth["true_effect"]) < 3 * adjusted.se
    assert adjusted.se < unadjusted.se
    assert unadjusted.estimate == adjusted.details["difference_in_means"]
    assert len(adjusted.details["balance"]) == len(covs)


def test_rct_rejects_non_binary_treatment():
    df, _ = rct_world(RCTWorldConfig(seed=1))
    df["D"] = np.where(df.index % 3 == 0, 2, df["D"])
    try:
        estimate_rct(df)
    except ValueError as exc:
        assert "binary" in str(exc)
    else:
        raise AssertionError("expected ValueError for a 3-valued treatment")


def test_rct_flags_imbalanced_covariate():
    df, _ = rct_world(RCTWorldConfig(n=400, seed=2))
    df.loc[df["D"] == 1, "X2"] += 1.0          # break balance on purpose
    result = estimate_rct(df, covariate_cols=["X1", "X2"])
    flagged = result.details["balance"].set_index("covariate")["imbalanced"]
    assert bool(flagged["X2"])
    assert result.warnings


if __name__ == "__main__":
    test_rct_recovers_ate_and_adjustment_helps()
    test_rct_rejects_non_binary_treatment()
    test_rct_flags_imbalanced_covariate()
    print("test_rct: OK")
