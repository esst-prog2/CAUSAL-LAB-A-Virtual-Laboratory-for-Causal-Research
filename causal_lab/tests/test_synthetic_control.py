import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from estimators.synthetic_control import estimate_synthetic_control
from simulation_engine.method_worlds import SyntheticControlWorldConfig, synthetic_control_world


def test_synthetic_control_recovers_effect():
    cfg = SyntheticControlWorldConfig(seed=9)
    df, truth = synthetic_control_world(cfg)
    result = estimate_synthetic_control(df, treated_unit="treated", treatment_period=cfg.treatment_period)
    weights = result.details["weights"]["weight"]
    print("SC:", result.estimate, "truth:", truth["true_effect"], "p:", result.p_value)
    assert (weights >= 0).all() and abs(weights.sum() - 1) < 1e-6
    assert abs(result.estimate - truth["true_effect"]) < 0.5
    assert result.se is None


def test_placebo_p_value_is_rank_based():
    cfg = SyntheticControlWorldConfig(n_donors=19, seed=9)
    df, _ = synthetic_control_world(cfg)
    result = estimate_synthetic_control(df, treated_unit="treated", treatment_period=cfg.treatment_period)
    n_units = cfg.n_donors + 1
    k = result.p_value * n_units
    assert abs(k - round(k)) < 1e-9 and 1 <= round(k) <= n_units   # p = k / (J + 1)
    assert result.p_value <= 0.1                                    # a real effect ranks near the top


def test_unbalanced_panel_rejected():
    cfg = SyntheticControlWorldConfig(seed=9)
    df, _ = synthetic_control_world(cfg)
    df = df.drop(index=df.index[5])
    try:
        estimate_synthetic_control(df, treated_unit="treated", treatment_period=cfg.treatment_period)
    except ValueError as exc:
        assert "balanced" in str(exc)
    else:
        raise AssertionError("expected ValueError for an unbalanced panel")


if __name__ == "__main__":
    test_synthetic_control_recovers_effect()
    test_placebo_p_value_is_rank_based()
    test_unbalanced_panel_rejected()
    print("test_synthetic_control: OK")
