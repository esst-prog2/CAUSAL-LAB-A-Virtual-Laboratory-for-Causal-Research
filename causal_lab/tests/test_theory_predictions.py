import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from theory_engine.calibration import ParameterSource
from theory_engine.game import build_custom_game
from theory_engine.predictions import (VERDICT_CONSISTENT, VERDICT_MAGNITUDE, VERDICT_SIGN, compare_with_estimate,
                                       delta_from_data, predict_shift)

SYMMETRIC_TULLOCK = build_custom_game("Tullock", {"V": 10}, [
    dict(name="A", strategy="x1", lower="0", upper="V", utility="V*x1/(x1+x2) - x1"),
    dict(name="B", strategy="x2", lower="0", upper="V", utility="V*x2/(x1+x2) - x2"),
], {"total effort": "x1 + x2"})


def test_prize_shift_raises_total_effort_by_half_delta():
    prediction = predict_shift(SYMMETRIC_TULLOCK, {"V": 10.0}, "V", 4.0)
    assert abs(prediction.effects["total effort"] - 2.0) < 1e-4
    assert abs(prediction.derivatives["total effort"] - 0.5) < 1e-3


def test_delta_from_treated_minus_control():
    df = pd.DataFrame({"D": [1, 1, 0, 0], "prize": [14.0, 16.0, 9.0, 11.0]})
    src = ParameterSource(kind="statistic", statistic="mean", column="prize")
    assert delta_from_data(df, src, "D", "V") == 5.0


def test_verdicts():
    assert compare_with_estimate(0.9, 1.0, 0.7, 1.2) == VERDICT_CONSISTENT
    assert compare_with_estimate(0.5, -0.5, -0.9, -0.2) == VERDICT_SIGN
    assert compare_with_estimate(3.0, 1.0, 0.7, 1.2) == VERDICT_MAGNITUDE
    assert compare_with_estimate(-0.1, 0.4, -0.2, 1.0) == VERDICT_CONSISTENT


if __name__ == "__main__":
    test_prize_shift_raises_total_effort_by_half_delta()
    test_delta_from_treated_minus_control()
    test_verdicts()
    print("test_theory_predictions: OK")
