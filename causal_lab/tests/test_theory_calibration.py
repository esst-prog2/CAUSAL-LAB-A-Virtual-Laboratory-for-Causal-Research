import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from simulation_engine.dgp import VirtualWorldConfig, generate
from theory_engine.calibration import (CalibrationError, ParameterSource, compute_parameter, detect_structure,
                                       solve_by_scope)
from theory_engine.catalogue import build

DF = pd.DataFrame({"group": ["A", "A", "B", "B"], "income": [10.0, 20.0, 30.0, 50.0], "x": [1, 2, 3, 4]})


def test_filtered_mean():
    src = ParameterSource(kind="statistic", statistic="mean", column="income",
                          filter_column="group", filter_value="A")
    assert compute_parameter(DF, src, "w1") == 15.0


def test_regression_slope():
    src = ParameterSource(kind="regression", y="income", x="x", coefficient="slope")
    assert abs(compute_parameter(DF, src, "b") - 13.0) < 1e-9


def test_missing_column_names_the_parameter():
    try:
        compute_parameter(DF, ParameterSource(kind="statistic", column="nope"), "V1")
    except CalibrationError as exc:
        assert "V1" in str(exc) and "nope" in str(exc)
    else:
        raise AssertionError("expected CalibrationError")


def test_structure_detection():
    panel, _ = generate(VirtualWorldConfig(n_units=20, n_periods=6, treatment_period=3, seed=1))
    assert detect_structure(panel, "unit", "period") == "panel"
    assert detect_structure(DF, None, None) == "cross-section"
    ts = pd.DataFrame({"period": range(10), "y": range(10)})
    assert detect_structure(ts, None, "period") == "time series"
    rcs = pd.DataFrame({"period": [1, 1, 2, 2], "id": [1, 2, 3, 4]})
    assert detect_structure(rcs, "id", "period") == "repeated cross-section"


def test_equilibrium_path_one_row_per_period():
    panel, _ = generate(VirtualWorldConfig(n_units=30, n_periods=8, treatment_period=4, seed=2))
    panel["prize"] = 10 + panel["period"]
    game = build("tullock", 2)
    sources = {"V1": ParameterSource(kind="statistic", statistic="mean", column="prize"),
               "V2": ParameterSource(kind="manual", value=10.0)}
    path = solve_by_scope(game, panel, sources, scope="period", scope_column="period")
    assert list(path["unit"]) == list(range(8))
    assert (path["status"] == "verified").all()
    assert path["param:V1"].tolist() == [10.0 + p for p in range(8)]
    effort = path["outcome:Total rent-seeking effort"]
    assert effort.is_monotonic_increasing


def test_calibration_error_is_reported_per_unit():
    game = build("tullock", 2)
    sources = {"V1": ParameterSource(kind="statistic", column="income", filter_column="group", filter_value="C"),
               "V2": ParameterSource(kind="manual", value=1.0)}
    table = solve_by_scope(game, DF, sources)
    assert "no rows" in table.loc[0, "status"]


if __name__ == "__main__":
    test_filtered_mean()
    test_regression_slope()
    test_missing_column_names_the_parameter()
    test_structure_detection()
    test_equilibrium_path_one_row_per_period()
    test_calibration_error_is_reported_per_unit()
    print("test_theory_calibration: OK")
