import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from estimators.matching import estimate_matching
from simulation_engine.method_worlds import MatchingWorldConfig, matching_world


def test_matching_and_ipw_recover_att_naive_is_biased():
    df, truth = matching_world(MatchingWorldConfig(n=1500, seed=4))
    result = estimate_matching(df, covariate_cols=truth["roles"]["covariates"])
    att = truth["true_effect"]
    print("Matching:", result.estimate, "IPW:", result.details["ipw_att"],
          "naive:", result.details["naive_difference"], "truth:", att)
    assert abs(result.estimate - att) < 3 * result.se
    assert abs(result.details["ipw_att"] - att) < 3 * result.details["ipw_se"]
    assert abs(result.details["naive_difference"] - att) > 3 * result.se


def test_matching_improves_balance():
    df, truth = matching_world(MatchingWorldConfig(n=1500, seed=4))
    balance = estimate_matching(df, covariate_cols=truth["roles"]["covariates"]).details["balance"]
    assert (balance["std_diff_after"].abs() < balance["std_diff_before"].abs()).all()


def test_propensity_scores_in_unit_interval():
    df, truth = matching_world(MatchingWorldConfig(seed=1))
    ps = estimate_matching(df, covariate_cols=truth["roles"]["covariates"]).details["propensity"]["propensity"]
    assert ((ps > 0) & (ps < 1)).all()


def test_matching_requires_covariates():
    df, _ = matching_world(MatchingWorldConfig(seed=1))
    try:
        estimate_matching(df, covariate_cols=[])
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError without covariates")


if __name__ == "__main__":
    test_matching_and_ipw_recover_att_naive_is_biased()
    test_matching_improves_balance()
    test_propensity_scores_in_unit_interval()
    test_matching_requires_covariates()
    print("test_matching: OK")
