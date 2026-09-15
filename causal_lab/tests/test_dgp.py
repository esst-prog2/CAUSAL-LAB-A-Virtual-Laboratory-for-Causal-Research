import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from simulation_engine.dgp import VirtualWorldConfig, generate


def test_generate_shape():
    cfg = VirtualWorldConfig(n_units=50, n_periods=10, treatment_period=5, seed=1)
    df, truth = generate(cfg)
    assert len(df) == 50 * 10
    assert set(["unit", "period", "D", "Y", "treated_unit"]).issubset(df.columns)
    assert df["treated_unit"].sum() > 0
    assert "true_att" in truth


def test_no_treatment_before_adoption():
    cfg = VirtualWorldConfig(n_units=30, n_periods=8, treatment_period=4, seed=2)
    df, _ = generate(cfg)
    assert (df.loc[df["period"] < 4, "D"] == 0).all()


if __name__ == "__main__":
    test_generate_shape()
    test_no_treatment_before_adoption()
    print("test_dgp: OK")
