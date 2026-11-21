"""The Method Guide page: every design is explained in English and French with
the same structure, and its key readings are peer-reviewed journal articles
with a DOI."""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from streamlit.testing.v1 import AppTest

from ui.guide_page import GUIDE_DIR, GUIDE_METHODS, guide_text
from utils.i18n import t
from utils.references import METHOD_READINGS, REFERENCES

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_every_design_has_a_text_in_both_languages_with_the_same_sections():
    for method in GUIDE_METHODS:
        en, fr = guide_text(method, "en"), guide_text(method, "fr")
        sections_en, sections_fr = re.findall(r"^#### ", en, re.M), re.findall(r"^#### ", fr, re.M)
        assert len(sections_en) == len(sections_fr) == 5, method
        assert en.count("$$") == fr.count("$$"), method        # same displayed equations
    files = {p.stem for lang in ("en", "fr") for p in (GUIDE_DIR / lang).glob("*.md")}
    assert files == set(GUIDE_METHODS)


def test_every_design_has_a_name_and_journal_readings():
    for method in GUIDE_METHODS:
        assert t(f"method.{method}", "en") != f"method.{method}"
        keys = METHOD_READINGS[method]
        assert keys, method
        for key in keys:
            ref = REFERENCES[key]
            assert ref.kind == "article" and ref.doi, key


def test_the_guide_says_what_causal_lab_does_not_do():
    # Advice only for interrupted time series; no density test in the RD yet.
    assert "no interrupted time series estimator" in guide_text("its", "en")
    assert "does not yet run" in guide_text("rdd", "en")


def test_the_page_renders_in_both_languages():
    at = AppTest.from_file(APP, default_timeout=300).run()
    at.sidebar.radio(key="page").set_value("method_guide").run()
    assert not at.exception
    assert at.title[0].value == "Method Guide"
    at.selectbox(key="guide_method").set_value("iv").run()
    assert not at.exception
    assert any("Anderson–Rubin" in m.value for m in at.markdown)
    at.sidebar.radio[0].set_value("fr").run()
    assert not at.exception and at.title[0].value == "Guide des méthodes"
