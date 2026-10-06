import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from simulation_engine.method_worlds import (
    DMLWorldConfig, IVWorldConfig, MatchingWorldConfig, RCTWorldConfig, RDDWorldConfig,
    SyntheticControlWorldConfig, dml_world, iv_world, matching_world, rct_world, rdd_world,
    synthetic_control_world,
)

WORLDS = [
    (rct_world, RCTWorldConfig, {"Y", "D", "X1", "X2", "X3"}),
    (matching_world, MatchingWorldConfig, {"Y", "D", "X1", "X2", "X3"}),
    (iv_world, IVWorldConfig, {"Y", "D", "Z", "X"}),
    (rdd_world, RDDWorldConfig, {"Y", "X", "D"}),
    (synthetic_control_world, SyntheticControlWorldConfig, {"unit", "period", "Y"}),
    (dml_world, DMLWorldConfig, {"Y", "D", "X1", "X10"}),
]


def test_worlds_are_reproducible_and_documented():
    for generate, config_cls, columns in WORLDS:
        df_a, truth_a = generate(config_cls(seed=3))
        df_b, truth_b = generate(config_cls(seed=3))
        assert df_a.equals(df_b), generate.__name__
        assert truth_a["true_effect"] == truth_b["true_effect"]
        assert columns.issubset(df_a.columns), generate.__name__


def test_different_seeds_give_different_data():
    for generate, config_cls, _ in WORLDS:
        df_a, _ = generate(config_cls(seed=1))
        df_b, _ = generate(config_cls(seed=2))
        assert not df_a.equals(df_b), generate.__name__


def test_matching_world_att_differs_from_ate():
    _, truth = matching_world(MatchingWorldConfig(effect_heterogeneity=1.0))
    assert abs(truth["true_effect"] - truth["true_ate"]) > 0.1


if __name__ == "__main__":
    test_worlds_are_reproducible_and_documented()
    test_different_seeds_give_different_data()
    test_matching_world_att_differs_from_ate()
    print("test_method_worlds: OK")
