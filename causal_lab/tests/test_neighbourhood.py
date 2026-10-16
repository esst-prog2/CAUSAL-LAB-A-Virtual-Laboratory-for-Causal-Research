"""One neighbourhood rule for the Spillovers check and the robustness battery
(hw6 review 4). The rule (ids differing by 1) comes from the Virtual World's
generator; outside it, neither feature uses it (user decisions, PLANNING_LOG
2026-10-16).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from robustness_engine.neighbourhood import adjacent_control_ids
from robustness_engine.robustness import run_robustness_battery
from simulation_engine.dgp import VirtualWorldConfig, generate


def test_adjacent_controls_are_controls_next_to_a_treated_id():
    df = pd.DataFrame({"unit": [1, 2, 3, 4, 5, 7], "treated_unit": [0, 1, 0, 0, 1, 0]})
    assert adjacent_control_ids(df, "unit", "treated_unit") == {1, 3, 4}
    df["unit"] = df["unit"].map("u{}".format)
    assert adjacent_control_ids(df, "unit", "treated_unit") == set()


def test_robustness_row_only_where_ids_encode_a_neighbourhood():
    df, _ = generate(VirtualWorldConfig(n_units=40, n_periods=10, treatment_period=5, seed=2))
    label = "Excluding spillover-adjacent controls"
    expected = len(adjacent_control_ids(df, "unit", "treated_unit"))
    assert expected > 0
    with_ids = [r for r in run_robustness_battery(df, 5, ids_encode_neighbourhood=True) if str(r.specification) == label]
    without = [r for r in run_robustness_battery(df, 5, ids_encode_neighbourhood=False) if str(r.specification) == label]
    assert len(with_ids) == 1 and str(with_ids[0].note).startswith(f"{expected} control")
    assert without == []


if __name__ == "__main__":
    test_adjacent_controls_are_controls_next_to_a_treated_id()
    test_robustness_row_only_where_ids_encode_a_neighbourhood()
    print("test_neighbourhood: OK")
