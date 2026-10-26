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


def test_covariates_leave_the_outcome_unchanged_and_are_time_invariant():
    plain, _ = synthetic_control_world(SyntheticControlWorldConfig(seed=9))
    with_x, truth = synthetic_control_world(SyntheticControlWorldConfig(seed=9, n_covariates=2))
    assert with_x[plain.columns].equals(plain) and truth["roles"]["covariates"] == ["X1", "X2"]
    assert (with_x.groupby("unit")[["X1", "X2"]].nunique() == 1).all().all()


def test_covariate_synthetic_control_matches_the_predictors():
    cfg = SyntheticControlWorldConfig(seed=9, n_covariates=3)
    df, truth = synthetic_control_world(cfg)
    result = estimate_synthetic_control(df, treated_unit="treated", treatment_period=cfg.treatment_period,
                                        covariate_cols=truth["roles"]["covariates"])
    table = result.details["predictors"]
    assert list(table["predictor"]) == ["X1", "X2", "X3", "Y"]
    assert abs(table["v_weight"].sum() - 1) < 1e-9 and (table["v_weight"] >= 0).all()
    # The synthetic unit is closer to the treated unit than the plain donor average, predictor by predictor.
    gap_synthetic = (table["synthetic"] - table["treated"]).abs()
    gap_average = (table["donor_mean"] - table["treated"]).abs()
    assert (gap_synthetic <= gap_average + 1e-9).sum() >= 3, table
    assert abs(result.estimate - truth["true_effect"]) < 0.75
    again = estimate_synthetic_control(df, treated_unit="treated", treatment_period=cfg.treatment_period,
                                       covariate_cols=truth["roles"]["covariates"])
    assert again.estimate == result.estimate                    # deterministic search
    plain = estimate_synthetic_control(df, treated_unit="treated", treatment_period=cfg.treatment_period)
    assert plain.details["predictors"] is None


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("test_synthetic_control: OK")
