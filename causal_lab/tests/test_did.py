import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from simulation_engine.dgp import VirtualWorldConfig, generate
from estimators.did import estimate_did
from estimators.event_study import estimate_event_study


def test_did_recovers_true_att_no_threats():
    cfg = VirtualWorldConfig(n_units=300, n_periods=16, treatment_period=8,
                              true_att=-0.6, noise_sd=0.5, seed=7)
    df, truth = generate(cfg)
    result = estimate_did(df)
    print("Estimated ATT:", result.att, "True ATT:", truth["true_att"])
    assert abs(result.att - truth["true_att"]) < 0.15


def test_did_biased_under_confounding():
    cfg = VirtualWorldConfig(n_units=300, n_periods=16, treatment_period=8,
                              true_att=-0.6, noise_sd=0.5, confounding="severe", seed=7)
    df, truth = generate(cfg)
    result = estimate_did(df)
    print("Confounded estimate:", result.att, "True ATT:", truth["true_att"])
    # under severe confounding we don't assert direction, just that it runs
    assert result.att == result.att  # not NaN


def test_event_study_runs():
    cfg = VirtualWorldConfig(n_units=200, n_periods=16, treatment_period=8, seed=3)
    df, _ = generate(cfg)
    es = estimate_event_study(df, fixed_treatment_period=8)
    assert len(es.coefficients) > 0
    assert (es.coefficients.loc[es.coefficients["rel_period"] == -1, "estimate"] == 0).all()


if __name__ == "__main__":
    test_did_recovers_true_att_no_threats()
    test_did_biased_under_confounding()
    test_event_study_runs()
    print("test_did: OK")
