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
from utils.i18n import t

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


def _button(at: AppTest, key: str):
    """The button labelled with the English text of `key`."""
    return next(b for b in at.button if b.label == t(key, "en"))


def _goto(at: AppTest, page: str) -> None:
    at.sidebar.radio(key="page").set_value(page).run()
    assert not at.exception, [e.message for e in at.exception]


def test_dashboard_shortcut_opens_its_page():
    at = _run_app()
    _button(at, "home.start_experiment").click().run()
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
        _button(at, "virtual.generate").click().run()
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
    _button(at, "virtual.generate").click().run()
    generated_period = at.session_state.virtual_cfg.treatment_period
    at.number_input[2].set_value(generated_period - 2).run()   # edit the widget after generating
    assert at.session_state.virtual_cfg.treatment_period == generated_period


def test_card_krueger_button_loads_real_data_without_truth():
    at = _run_app()
    _goto(at, "virtual_lab")
    _button(at, "virtual.load_card_krueger").click().run()
    assert not at.exception
    assert at.session_state.uploaded_df is not None
    assert at.session_state.virtual_truth is None and at.session_state.virtual_cfg is None
    _goto(at, "estimation")
    assert "True ATT" not in [m.label for m in at.metric]



def _html(at: AppTest) -> list[str]:
    return [e.proto.body for e in at.get("html")]


def test_sidebar_sections_follow_the_workflow_and_the_language():
    # app-navigation spec: six sections, in workflow order, none longer than four
    # pages, headed in the interface language; switching language keeps the page.
    from ui.style import NAV_SECTIONS
    assert [first for _, first in NAV_SECTIONS] == ["dashboard", "research_question", "virtual_lab", "estimation",
                                                    "break_my_design", "code"]
    at = _run_app()
    _goto(at, "estimation")
    for lang, headings in (("en", ["Start", "Research design", "Data", "Analysis", "Stress test", "Output"]),
                            ("fr", None)):
        if lang == "fr":
            at.sidebar.radio[0].set_value("fr").run()
            headings = [t(f"nav.group.{section}", "fr") for section, _ in NAV_SECTIONS]
            assert headings[0] != "Start"
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


def test_every_page_is_titled_with_its_sidebar_name():
    # Impeccable critique 2026-10-31: "Virtual Lab" opened a page titled "Virtual World".
    at = _run_app()
    for page in ("demo", "research_question", "diagnosis", "recommendation", "virtual_lab", "data_sources",
                 "estimation", "methods", "theory", "break_my_design", "robustness", "code", "report", "settings"):
        _goto(at, page)
        assert at.title[0].value == t(f"nav.{page}", "en"), page


def test_empty_pages_offer_a_way_out():
    at = _run_app()
    for page in ("estimation", "break_my_design", "robustness"):
        _goto(at, page)
        _button(at, "empty.load_example").click().run()
        assert not at.exception and at.session_state.uploaded_df is not None
        at.session_state.uploaded_df = None
    for page in ("diagnosis", "recommendation"):
        _goto(at, page)
        _button(at, "empty.open_wizard").click().run()
        assert at.session_state.page == "research_question"


def test_dashboard_states_the_demo_finding_and_opens_the_demo():
    at = _run_app()
    assert any("cl-finding" in body for body in _html(at))
    _button(at, "home.open_demo").click().run()
    assert at.session_state.page == "demo"


def test_recommendation_says_when_no_credible_design_is_supported():
    # Method-selection discipline: a self-selected treatment observed once, with no
    # instrument and unmeasured confounders, supports no causal design; the page says so.
    from causal_engine.diagnosis import ResearchDesignInput
    at = _run_app()
    at.session_state.design = ResearchDesignInput(
        assignment_mechanism="self_selected", data_structure="cross_section", has_pre_treatment_periods=False,
        n_pre_periods=0, instrument="none", confounders_observed="not_measured")
    _goto(at, "research_question")
    _button(at, "wizard.run").click().run()
    _goto(at, "recommendation")
    assert any(t("recommendation.none_title", "en") in e.value for e in at.error)
    assert not any(m.value.startswith("### " + t("recommendation.recommended", "en")) for m in at.markdown)


def test_recommendation_asks_when_the_question_contradicts_the_form():
    # The scholarship-at-the-cutoff question with the form at its defaults: the page asks
    # whether the cutoff decides treatment, and says the answers are still the defaults.
    at = _run_app()
    _goto(at, "research_question")
    at.text_area[0].set_value("What is the effect of a scholarship on enrollment for students near the "
                              "eligibility cutoff?").run()
    _button(at, "wizard.run").click().run()
    _goto(at, "recommendation")
    assert any(t("recommendation.ask_title", "en") in w.value for w in at.warning)
    assert any(m.value == t("recommendation.defaults_warning", "en") for m in at.info)
    assert any("threshold" in m.value for m in at.markdown)


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
    test_every_page_is_titled_with_its_sidebar_name()
    test_empty_pages_offer_a_way_out()
    test_dashboard_states_the_demo_finding_and_opens_the_demo()
    test_recommendation_says_when_no_credible_design_is_supported()
    test_recommendation_asks_when_the_question_contradicts_the_form()
    print("test_app_flows: OK")
