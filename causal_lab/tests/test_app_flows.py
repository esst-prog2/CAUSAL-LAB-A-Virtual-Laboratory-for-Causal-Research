"""App-level behaviour, driven headlessly with Streamlit's AppTest (hw6 review 2).

These behaviours were added in earlier sessions and were only checked by
scripts outside the repository. Each test states the rule it protects;
expected values come from the specs (app-navigation, real-world-data-upload,
virtual-world-generation), not from the program's output.

st.file_uploader cannot be driven by AppTest, so it is replaced by a stub
that returns a small CSV built here.
"""
import io
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from streamlit.testing.v1 import AppTest

from simulation_engine.dgp import VirtualWorldConfig, generate

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = 300


class _Upload(io.BytesIO):
    file_id, name = "test-panel-upload", "panel.csv"


def _panel_csv() -> bytes:
    df, _ = generate(VirtualWorldConfig(n_units=40, n_periods=12, treatment_period=6, seed=9))
    return df[["unit", "period", "D", "Y", "treated_unit"]].to_csv(index=False).encode()


def _run_app(upload: bytes | None = None) -> AppTest:
    original = st.file_uploader
    st.file_uploader = (lambda *a, key=None, **k: _Upload(upload) if (upload and key is None) else None)
    try:
        at = AppTest.from_file(APP, default_timeout=TIMEOUT).run()
    finally:
        st.file_uploader = original
    return at


def _goto(at: AppTest, page: str) -> None:
    at.sidebar.radio(key="page").set_value(page).run()
    assert not at.exception, [e.message for e in at.exception]


def test_dashboard_shortcut_opens_its_page():
    at = _run_app()
    at.button[1].click().run()            # "Start a Virtual Experiment"
    assert at.session_state.page == "virtual_lab"


def test_language_switch_keeps_the_page():
    at = _run_app()
    _goto(at, "break_my_design")
    at.sidebar.radio[0].set_value("fr").run()
    assert not at.exception
    assert at.session_state.page == "break_my_design"


def test_pages_with_shared_language_helpers_follow_the_session_language():
    # hw6 review 4: the Methods and Theory pages now read the language from
    # the session, through ui/page_text.py, instead of a module global.
    # The model selector's labels go through R() inside a format_func closure.
    from theory_engine.catalogue import CATALOGUE
    from utils.i18n import render
    first = next(iter(CATALOGUE.values()))
    expected = {lang: f"{render(first.category, lang)} — {render(first.label, lang)}" for lang in ("en", "fr")}
    assert expected["en"] != expected["fr"]
    at = _run_app()
    at.sidebar.radio[0].set_value("fr").run()
    _goto(at, "methods")
    _goto(at, "theory")
    assert at.selectbox[0].options[0] == expected["fr"]


def test_uploaded_data_has_no_ground_truth_and_a_later_generation_wins():
    original = st.file_uploader
    st.file_uploader = (lambda *a, key=None, **k: _Upload(_panel_csv()) if key is None else None)
    try:
        at = AppTest.from_file(APP, default_timeout=TIMEOUT).run()
        _goto(at, "virtual_lab")
        assert at.session_state.uploaded_df is not None
        assert at.session_state.virtual_truth is None
        _goto(at, "estimation")
        assert "True ATT" not in [m.label for m in at.metric]
        _goto(at, "virtual_lab")
        next(b for b in at.button if b.label.startswith("⚗️")).click().run()
        at.run()                           # the uploader still holds the same file
        assert at.session_state.uploaded_df is None
        assert at.session_state.virtual_df is not None
    finally:
        st.file_uploader = original


def test_upload_with_a_text_treatment_is_rejected():
    # hw6 review 5: D = "yes"/"no" used to load, then every DiD came back NaN.
    df, _ = generate(VirtualWorldConfig(n_units=20, n_periods=6, treatment_period=3, seed=9))
    df["D"] = df["D"].map({1: "yes", 0: "no"})
    csv = df[["unit", "period", "D", "Y", "treated_unit"]].to_csv(index=False).encode()
    original = st.file_uploader
    st.file_uploader = (lambda *a, key=None, **k: _Upload(csv) if key is None else None)
    try:
        at = AppTest.from_file(APP, default_timeout=TIMEOUT).run()
        _goto(at, "virtual_lab")
        assert at.session_state.uploaded_df is None
        assert any("D" in e.value and "0/1" in e.value for e in at.error), [e.value for e in at.error]
    finally:
        st.file_uploader = original


def test_analysis_keeps_the_generating_configuration():
    at = _run_app()
    _goto(at, "virtual_lab")
    next(b for b in at.button if b.label.startswith("⚗️")).click().run()
    generated_period = at.session_state.virtual_cfg.treatment_period
    at.number_input[2].set_value(generated_period - 2).run()   # edit the widget after generating
    assert at.session_state.virtual_cfg.treatment_period == generated_period


def test_card_krueger_button_loads_real_data_without_truth():
    at = _run_app()
    _goto(at, "virtual_lab")
    next(b for b in at.button if b.label.startswith("📂")).click().run()
    assert not at.exception
    assert at.session_state.uploaded_df is not None
    assert at.session_state.virtual_truth is None and at.session_state.virtual_cfg is None
    _goto(at, "estimation")
    assert "True ATT" not in [m.label for m in at.metric]



def _html(at: AppTest) -> list[str]:
    return [e.proto.body for e in at.get("html")]


def test_sidebar_sections_follow_the_workflow_and_the_language():
    # app-navigation spec: five sections, in workflow order, headed in the
    # interface language; switching language keeps the page.
    from ui.style import NAV_SECTIONS
    from utils.i18n import t
    assert [first for _, first in NAV_SECTIONS] == ["dashboard", "virtual_lab", "estimation", "break_my_design", "code"]
    at = _run_app()
    _goto(at, "estimation")
    for lang, headings in (("en", ["Start", "Data", "Analysis", "Stress test", "Output"]), ("fr", None)):
        if lang == "fr":
            at.sidebar.radio[0].set_value("fr").run()
            headings = [t(f"nav.group.{section}", "fr") for section, _ in NAV_SECTIONS]
            assert headings != ["Start", "Data", "Analysis", "Stress test", "Output"]
        css = next(body for body in _html(at) if "st-key-nav" in body)
        positions = [css.index(f'content: "{h}"') for h in headings]
        assert positions == sorted(positions)
        assert at.session_state.page == "estimation"


def test_dashboard_progress_cards_follow_the_workflow():
    # app-navigation spec: after a question and a diagnosis, with no data,
    # three cards are done (recommendations give their number) and one is not.
    at = _run_app()
    cards = next(body for body in _html(at) if "cl-steps" in body)
    assert cards.count("cl-step todo") == 4 and "cl-step done" not in cards
    _goto(at, "research_question")
    at.text_area[0].set_value("Did the minimum wage reduce employment?").run()
    at.button[0].click().run()
    assert not at.exception
    n = len(at.session_state.recommendations)
    assert n > 0
    _goto(at, "dashboard")
    cards = next(body for body in _html(at) if "cl-steps" in body)
    steps = cards.split('<div class="cl-step ')[1:]
    assert [step.startswith("done") for step in steps] == [True, True, True, False]
    assert f'<span class="cl-badge">{n}</span>' in steps[2]


if __name__ == "__main__":
    test_dashboard_shortcut_opens_its_page()
    test_language_switch_keeps_the_page()
    test_pages_with_shared_language_helpers_follow_the_session_language()
    test_uploaded_data_has_no_ground_truth_and_a_later_generation_wins()
    test_upload_with_a_text_treatment_is_rejected()
    test_analysis_keeps_the_generating_configuration()
    test_card_krueger_button_loads_real_data_without_truth()
    test_sidebar_sections_follow_the_workflow_and_the_language()
    test_dashboard_progress_cards_follow_the_workflow()
    print("test_app_flows: OK")
