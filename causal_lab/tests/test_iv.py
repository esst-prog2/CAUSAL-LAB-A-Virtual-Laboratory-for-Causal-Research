import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from estimators.iv import estimate_iv
from simulation_engine.method_worlds import IVWorldConfig, iv_world


def test_2sls_recovers_effect_ols_is_biased():
    df, truth = iv_world(IVWorldConfig(n=4000, instrument_strength=1.5, seed=8))
    result = estimate_iv(df, instrument_cols=["Z"], control_cols=["X"])
    print("2SLS:", result.estimate, "OLS:", result.details["ols_estimate"], "truth:", truth["true_effect"])
    assert abs(result.estimate - truth["true_effect"]) < 3 * result.se
    assert abs(result.details["ols_estimate"] - truth["true_effect"]) > 3 * result.details["ols_se"]
    assert result.details["first_stage_f"] > 10
    assert not result.warnings


def test_weak_instrument_warning():
    df, _ = iv_world(IVWorldConfig(n=1000, instrument_strength=0.05, seed=8))
    result = estimate_iv(df, instrument_cols=["Z"], control_cols=["X"])
    assert result.details["first_stage_f"] < 10
    assert any("Weak instrument" in w for w in result.warnings)


if __name__ == "__main__":
    test_2sls_recovers_effect_ols_is_biased()
    test_weak_instrument_warning()
    print("test_iv: OK")
