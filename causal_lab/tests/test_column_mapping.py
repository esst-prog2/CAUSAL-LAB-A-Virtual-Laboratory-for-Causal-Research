import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from utils.column_mapping import prepare_mapped_frame, validate_mapping

DF = pd.DataFrame({
    "y": [1.0, 2.0, np.nan, 4.0],
    "d": [0, 1, 0, 1],
    "z": [1, 0, 1, 0],
    "name": ["a", "b", "c", "d"],
})


def test_valid_mapping_has_no_problems():
    assert validate_mapping(DF, "iv", {"outcome": "y", "treatment": "d", "instruments": ["z"]}) == []


def test_unmapped_required_role_is_named():
    problems = validate_mapping(DF, "iv", {"outcome": "y", "treatment": "d", "instruments": []})
    assert any(p.startswith("Instrument(s)") for p in problems)


def test_duplicate_column_is_reported():
    problems = validate_mapping(DF, "rct", {"outcome": "y", "treatment": "y"})
    assert any("already used" in p and p.startswith("Treatment") for p in problems)


def test_non_numeric_column_is_reported():
    problems = validate_mapping(DF, "dml", {"outcome": "y", "treatment": "d", "covariates": ["name"]})
    assert any("must be numeric" in p and p.startswith("Covariates") for p in problems)


def test_non_numeric_unit_allowed_for_synthetic_control():
    problems = validate_mapping(DF, "synthetic_control", {"unit": "name", "period": "z", "outcome": "y"})
    assert problems == []


def test_missing_rows_are_dropped_and_counted():
    clean, dropped = prepare_mapped_frame(DF, "rct", {"outcome": "y", "treatment": "d", "covariates": []})
    assert dropped == 1 and len(clean) == 3
    assert list(clean.columns) == ["y", "d"]


if __name__ == "__main__":
    test_valid_mapping_has_no_problems()
    test_unmapped_required_role_is_named()
    test_duplicate_column_is_reported()
    test_non_numeric_column_is_reported()
    test_non_numeric_unit_allowed_for_synthetic_control()
    test_missing_rows_are_dropped_and_counted()
    print("test_column_mapping: OK")
