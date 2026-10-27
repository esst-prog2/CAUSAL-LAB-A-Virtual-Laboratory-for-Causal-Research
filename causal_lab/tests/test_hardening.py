"""Regressions found by fuzzing the app before putting it online (2026-10-27).

Odd but plausible inputs were sent through every entry point: 19 panels
through the CSV upload, odd column mappings through the Causal Methods page,
odd files through the Theoretical Model page, and hand-edited project files.
Each test below is one crash or misleading message that run found.
"""
import ast
import io
import sys
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import streamlit as st
from streamlit.testing.v1 import AppTest

from estimators.iv import estimate_iv
from robustness_engine.method_stress import run_method_stress_test
from simulation_engine.dgp import VirtualWorldConfig, generate
from utils.column_mapping import validate_mapping
from utils.i18n import LocalizedError
from utils.project_file import load_project, save_project
from utils.validation import drop_incomplete_rows

APP_DIR = Path(__file__).resolve().parent.parent
APP = str(APP_DIR / "app.py")


def _panel() -> pd.DataFrame:
    df, _ = generate(VirtualWorldConfig(n_units=30, n_periods=8, treatment_period=4, seed=1))
    return df[["unit", "period", "D", "Y", "treated_unit"]].copy()


class _Upload(io.BytesIO):
    file_id, name = "hardening-upload", "panel.csv"


def test_missing_outcomes_are_left_out_at_upload_and_every_page_runs():
    # Was: a CSV with empty Y cells loaded, then Estimation, Break My Design,
    # Robustness and the report crashed (arrays of different lengths).
    df = _panel()
    df.loc[::10, "Y"] = np.nan
    n_missing = int(df["Y"].isna().sum())
    clean, dropped = drop_incomplete_rows(df)
    assert dropped == n_missing and len(clean) == len(df) - n_missing and clean["Y"].notna().all()

    data = df.to_csv(index=False).encode()
    original = st.file_uploader
    st.file_uploader = lambda *a, key=None, **k: _Upload(data) if key is None else None
    try:
        at = AppTest.from_file(APP, default_timeout=600).run()
        at.sidebar.radio(key="page").set_value("virtual_lab").run()
        assert any(str(n_missing) in str(w.value) for w in at.warning)
        assert len(at.session_state.uploaded_df) == len(df) - n_missing
        for page in ("estimation", "break_my_design", "robustness", "report"):
            at.sidebar.radio(key="page").set_value(page).run()
            assert not at.exception, (page, [e.message for e in at.exception])
    finally:
        st.file_uploader = original


def test_iv_with_no_residual_degree_of_freedom_is_refused():
    # Was: ZeroDivisionError from the robust covariance on 2 complete rows.
    df = pd.DataFrame({"y": [1.0, 2.0, 3.0], "d": [0, 1, 1], "z": [0.1, 0.9, 0.7]})
    try:
        estimate_iv(df, "y", "d", ["z"])
    except LocalizedError as exc:
        assert exc.msg.key == "err.iv_too_few"
    else:
        raise AssertionError("expected err.iv_too_few")


def test_rct_balance_check_is_not_applicable_on_too_few_rows():
    # Was: statsmodels refused the Wald test (no residual degrees of freedom).
    df = pd.DataFrame({"y": [1.0, 2.0, 3.0], "d": [0, 1, 1], "x": [0.3, 0.1, 0.4]})
    report = run_method_stress_test("rct", df, {"outcome": "y", "treatment": "d", "covariates": ["x"]}, {})
    balance = next(c for c in report.checks if c.slug == "rct_balance")
    assert balance.verdict == "N/A" and balance.message.key == "mstress.rct_balance.too_few"


def test_an_empty_mapped_column_is_named_as_empty():
    # Was: an all-empty covariate emptied the data, and the message blamed the treatment.
    df = pd.DataFrame({"y": [1.0, 2.0], "d": [0, 1], "x": [np.nan, np.nan]})
    problems = validate_mapping(df, "matching", {"outcome": "y", "treatment": "d", "covariates": ["x"]})
    assert [p.key for p in problems] == ["mapping.all_missing"]


def test_a_project_whose_panel_lacks_required_columns_is_refused():
    # A hand-edited project file must not bypass the upload checks.
    state = {"uploaded_df": _panel().drop(columns=["treated_unit"]), "uploaded_file_id": "x"}
    try:
        load_project(save_project(state))
    except LocalizedError as exc:
        assert exc.msg.key == "err.project_invalid" and "treated_unit" in str(exc.msg.params)
    else:
        raise AssertionError("expected err.project_invalid")
    # ... and a valid one with empty outcomes opens without them.
    df = _panel()
    df.loc[:4, "Y"] = np.nan
    opened = load_project(save_project({"uploaded_df": df, "uploaded_file_id": "x"}))
    assert len(opened["uploaded_df"]) == len(df) - 5
    assert zipfile.is_zipfile(io.BytesIO(save_project({"uploaded_df": df})))


def test_the_app_script_never_rebinds_an_imported_name():
    # Was: the Break My Design page assigned `style = {...}`, hiding the
    # `ui.style` module for the rest of the run.
    tree = ast.parse((APP_DIR / "app.py").read_text(encoding="utf-8"))
    imported = {(a.asname or a.name).split(".")[0]
                for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for a in node.names}
    rebound = sorted({n.id for n in ast.walk(tree)
                      if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and n.id in imported})
    assert not rebound, rebound


if __name__ == "__main__":
    test_missing_outcomes_are_left_out_at_upload_and_every_page_runs()
    test_iv_with_no_residual_degree_of_freedom_is_refused()
    test_rct_balance_check_is_not_applicable_on_too_few_rows()
    test_an_empty_mapped_column_is_named_as_empty()
    test_a_project_whose_panel_lacks_required_columns_is_refused()
    test_the_app_script_never_rebinds_an_imported_name()
    print("test_hardening: OK")
