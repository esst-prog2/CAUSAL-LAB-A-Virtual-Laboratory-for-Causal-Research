"""Saving a project to a .causallab file and opening it again."""
import io
import json
import sys
import zipfile
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

import utils.project_file as project_file
from causal_engine.diagnosis import ResearchDesignInput
from simulation_engine.dgp import VirtualWorldConfig, generate
from simulation_engine.method_worlds import (MatchingWorldConfig, SyntheticControlWorldConfig, matching_world,
                                             synthetic_control_world)
from utils.i18n import LocalizedError, Msg
from utils.project_file import apply_project, load_project, project_file_name, save_project
from utils.real_data import load_card_krueger

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _raises_key(key, fn, *args):
    try:
        fn(*args)
    except LocalizedError as exc:
        assert exc.msg.key == key, (exc.msg.key, key)
    else:
        raise AssertionError(f"expected LocalizedError {key}")


def _full_state():
    cfg = VirtualWorldConfig(seed=7, n_units=40, n_periods=8, treatment_period=5, staggered_adoption=True,
                             confounding="medium")
    df, truth = generate(cfg)
    m_df, m_truth = matching_world(MatchingWorldConfig(seed=2))
    sc_df, sc_truth = synthetic_control_world(SyntheticControlWorldConfig(seed=3))
    return {
        "lang": "fr", "page": "estimation",
        "design": ResearchDesignInput(research_question="Do mines raise child mortality?", n_pre_periods=4),
        "diagnosis": object(),          # only "was it run" is saved
        "vw_config": replace(cfg, seed=8),
        "virtual_df": df, "virtual_truth": truth, "virtual_cfg": cfg,
        "uploaded_df": None, "uploaded_file_id": None,
        "method_data": {
            "matching": {"df": m_df, "truth": m_truth, "mapping": dict(m_truth["roles"]), "options": {},
                         "source": "virtual", "result": object(), "error": None, "dropped": 0, "file_id": None},
            "synthetic_control": {"df": sc_df, "truth": sc_truth, "mapping": dict(sc_truth["roles"]),
                                  "options": {"treated_unit": sc_truth["roles"]["treated_unit"],
                                              "treatment_period": sc_truth["roles"]["treatment_period"]},
                                  "source": "virtual", "result": None, "error": None, "dropped": 0,
                                  "file_id": None},
            "rdd": {"df": None, "truth": None, "mapping": None, "options": {}, "source": None,
                    "result": None, "error": None, "dropped": 0, "file_id": None},
        },
    }


def test_round_trip_keeps_every_dataset_setting_and_ground_truth():
    state = _full_state()
    opened = load_project(save_project(state))
    pd.testing.assert_frame_equal(opened["virtual_df"], state["virtual_df"])     # values and dtypes
    assert opened["virtual_truth"] == state["virtual_truth"]                      # int unit keys included
    assert opened["virtual_cfg"] == state["virtual_cfg"] and opened["vw_config"] == state["vw_config"]
    assert opened["design"] == state["design"] and opened["diagnosed"] is True
    assert (opened["lang"], opened["page"]) == ("fr", "estimation")
    assert opened["uploaded_df"] is None
    assert set(opened["method_data"]) == {"matching", "synthetic_control"}       # rdd had no data
    for method in ("matching", "synthetic_control"):
        saved, back = state["method_data"][method], opened["method_data"][method]
        pd.testing.assert_frame_equal(back["df"], saved["df"])
        for key in ("truth", "mapping", "options", "source", "dropped"):
            assert back[key] == saved[key], (method, key)
        assert back["result"] is None and back["error"] is None                  # results are recomputed
    estimand = opened["method_data"]["matching"]["truth"]["estimand"]
    assert isinstance(estimand, Msg) and estimand.key == state["method_data"]["matching"]["truth"]["estimand"].key


def test_uploaded_real_data_round_trip():
    ck = load_card_krueger()
    opened = load_project(save_project({"uploaded_df": ck, "uploaded_file_id": "card_krueger_1994"}))
    pd.testing.assert_frame_equal(opened["uploaded_df"], ck)
    assert opened["uploaded_file_id"] == "card_krueger_1994" and opened["virtual_df"] is None
    assert opened["diagnosed"] is False and opened["design"] == ResearchDesignInput()


def test_the_archive_holds_only_json_and_parquet():
    with zipfile.ZipFile(io.BytesIO(save_project(_full_state()))) as archive:
        names = archive.namelist()
    assert names[0] == "manifest.json"
    assert all(n.startswith("data/") and n.endswith(".parquet") for n in names[1:]), names


def _archive(manifest, members=None) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        if manifest is not None:
            archive.writestr("manifest.json", manifest if isinstance(manifest, str) else json.dumps(manifest))
        for name, content in (members or {}).items():
            archive.writestr(name, content)
    return buffer.getvalue()


def test_files_that_are_not_valid_projects_are_refused_with_a_reason():
    good = json.loads(zipfile.ZipFile(io.BytesIO(save_project(_full_state()))).read("manifest.json"))
    _raises_key("err.project_not_a_project", load_project, b"unit,period,D,Y\n1,1,0,2.0\n")
    _raises_key("err.project_not_a_project", load_project, _archive(None, {"data/x.parquet": b""}))
    _raises_key("err.project_not_a_project", load_project, _archive({**good, "format": "something-else"}))
    _raises_key("err.project_invalid", load_project, _archive("{not json"))
    _raises_key("err.project_newer_version", load_project, _archive({**good, "version": 99}))
    # The manifest names a Virtual World but the archive lacks its data, or the data are damaged.
    _raises_key("err.project_invalid", load_project, _archive(good))
    _raises_key("err.project_invalid", load_project, _archive(good, {"data/virtual.parquet": b"garbage"}))


def test_archives_that_unpack_too_large_are_refused():
    saved, project_file.MAX_UNCOMPRESSED_BYTES = project_file.MAX_UNCOMPRESSED_BYTES, 1000
    try:
        _raises_key("err.project_too_large", load_project, save_project(_full_state()))
    finally:
        project_file.MAX_UNCOMPRESSED_BYTES = saved


def test_settings_from_other_versions_keep_defaults_and_ignore_unknown_fields():
    manifest = json.loads(zipfile.ZipFile(io.BytesIO(save_project({}))).read("manifest.json"))
    del manifest["design"]["n_pre_periods"]
    manifest["vw_config"]["a_future_setting"] = 3
    opened = load_project(_archive(manifest))
    assert opened["design"].n_pre_periods == ResearchDesignInput().n_pre_periods
    assert opened["vw_config"] == VirtualWorldConfig()


def test_file_name_comes_from_the_research_question():
    name = project_file_name({"design": ResearchDesignInput(research_question="Mines & child health?")})
    assert name == "Mines___child_health.causallab", name
    assert project_file_name({}).startswith("causal_lab_") and project_file_name({}).endswith(".causallab")


def test_opening_replaces_the_project_and_recomputes_the_diagnosis():
    from causal_engine.diagnosis import diagnose
    design = ResearchDesignInput(research_question="q", treatment_timing="staggered")
    session = {"virtual_df": "stale", "diagnosis": "stale", "recommendations": "stale", "widget": 1}
    apply_project(session, load_project(save_project({"design": design, "diagnosis": diagnose(design)})))
    assert session["virtual_df"] is None and session["widget"] == 1
    assert session["diagnosis"] == diagnose(design) and session["recommendations"]
    apply_project(session, load_project(save_project({"design": design})))      # saved without a diagnosis
    assert session["diagnosis"] is None and session["recommendations"] is None


def test_an_opened_project_runs_in_the_app():
    from streamlit.testing.v1 import AppTest
    opened = load_project(save_project(_full_state()))
    for page in ("estimation", "break_my_design", "methods", "settings"):
        at = AppTest.from_file(APP, default_timeout=300)
        session = {}
        apply_project(session, opened)
        for key, value in session.items():
            at.session_state[key] = value
        at.session_state["page"] = page
        at.run()
        assert not at.exception, (page, [e.value for e in at.exception])
    labels = [b.label for b in at.get("download_button")]
    assert any("Enregistrer le projet" in label for label in labels), labels     # lang "fr" restored


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("test_project_file: OK")
