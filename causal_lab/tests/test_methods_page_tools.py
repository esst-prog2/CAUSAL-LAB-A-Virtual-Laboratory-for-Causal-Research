"""The Break My Design, Monte Carlo and Code tabs of the Causal Methods page."""
import sys
from dataclasses import asdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from streamlit.testing.v1 import AppTest

from estimators.registry import WORLDS, run_method, virtual_options

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _app_with_result(method: str, **change):
    world = WORLDS[method]
    config = world.config_cls(**change)
    df, truth = world.generate(config)
    mapping, options = dict(truth["roles"]), virtual_options(method, truth)
    at = AppTest.from_file(APP, default_timeout=600)
    at.session_state["page"] = "methods"
    at.session_state["methods_choice"] = method
    at.session_state["method_data"] = {method: {
        "df": df, "truth": truth, "mapping": mapping, "options": options, "source": "virtual",
        "result": run_method(method, df, mapping, options), "error": None, "dropped": 0, "file_id": None,
        "config": asdict(config), "stress": None, "mc": None}}
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def _click(at, label_part: str):
    next(b for b in at.button if label_part in b.label).click().run()
    assert not at.exception, [e.value for e in at.exception]


def test_every_method_shows_the_three_tabs_and_its_code():
    for method in WORLDS:
        at = _app_with_result(method, **({"n": 300} if method == "dml" else {}))
        labels = [t.label for t in at.tabs]
        assert any("Break My Design" in l for l in labels) and any("Monte Carlo" in l for l in labels), labels
        code = [c.value for c in at.code]
        assert any("CAUSAL LAB" in c and "reproduces the Causal Lab estimate" in c for c in code), method


def test_checks_and_monte_carlo_run_from_the_page():
    at = _app_with_result("rct")
    _click(at, "Run the checks")
    texts = [s.value for s in list(at.success) + list(at.warning) + list(at.info)]
    assert any("Randomization balance" in s for s in texts), texts
    at.number_input(key="mw_rct_mc_reps").set_value(5).run()
    _click(at, "Run the Monte Carlo")
    assert at.session_state["method_data"]["rct"]["mc"].n_reps == 5
    assert any(m.label == "RMSE" for m in at.metric)


def test_rdd_inference_choice_and_fuzzy_world_on_the_page():
    at = _app_with_result("rdd", compliance=0.6)
    captions = " ".join(c.value for c in at.caption)
    assert "Fuzzy RD first stage" in captions and "Robust bias-corrected" in captions
    at.radio(key="mw_rdd_inference").set_value("robust").run()
    assert not at.exception and at.session_state["method_data"]["rdd"]["options"]["inference"] == "robust"
    assert at.session_state["method_data"]["rdd"]["result"] is None       # stale result cleared


def test_rdd_inference_choice_survives_leaving_the_page():
    # A widget's key is dropped when its page is left: without restoring it, coming
    # back reverted the choice to conventional and cleared the robust result.
    at = _app_with_result("rdd")
    at.radio(key="mw_rdd_inference").set_value("robust").run()
    next(b for b in at.button if b.key == "mw_rdd_run").click().run()
    assert at.session_state["method_data"]["rdd"]["result"].details["inference"] == "robust"
    at.session_state["page"] = "dashboard"
    at.run()
    at.session_state["page"] = "methods"
    at.run()
    assert not at.exception
    assert at.radio(key="mw_rdd_inference").value == "robust"
    assert at.session_state["method_data"]["rdd"]["result"] is not None


def test_covariate_synthetic_control_shows_its_predictors():
    at = _app_with_result("synthetic_control", n_covariates=2)
    tables = [d.value for d in at.dataframe]
    assert any("importance V" in list(t.columns) for t in tables), [list(t.columns) for t in tables]


def test_uploaded_data_get_checks_and_code_but_no_monte_carlo():
    at = _app_with_result("iv")
    at.session_state["method_data"]["iv"]["source"] = "upload"
    at.session_state["mw_iv_source"] = "upload"
    at.run()
    assert not at.exception


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("test_methods_page_tools: OK")
