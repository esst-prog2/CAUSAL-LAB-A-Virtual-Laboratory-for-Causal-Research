import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from utils.validation import REQUIRED_COLUMNS, missing_required_columns


def test_no_missing_columns_when_all_present():
    df = pd.DataFrame({c: [] for c in REQUIRED_COLUMNS})
    assert missing_required_columns(df) == []


def test_reports_single_missing_column():
    df = pd.DataFrame({c: [] for c in REQUIRED_COLUMNS if c != "D"})
    assert missing_required_columns(df) == ["D"]


def test_reports_multiple_missing_columns_in_canonical_order():
    df = pd.DataFrame({c: [] for c in ("Y", "unit")})
    assert missing_required_columns(df) == ["period", "D", "treated_unit"]


def test_extra_columns_do_not_affect_result():
    df = pd.DataFrame({c: [] for c in (*REQUIRED_COLUMNS, "extra_col")})
    assert missing_required_columns(df) == []


if __name__ == "__main__":
    test_no_missing_columns_when_all_present()
    test_reports_single_missing_column()
    test_reports_multiple_missing_columns_in_canonical_order()
    test_extra_columns_do_not_affect_result()
    print("test_validation: OK")
