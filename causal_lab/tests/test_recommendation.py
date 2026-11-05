"""Method Recommendation Engine: each test states the method-selection rule it
protects. A method is recommended only when the conditions without which it
does not identify a causal effect hold; no method is a default."""
import itertools
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from causal_engine.diagnosis import ResearchDesignInput, diagnose, Level
from causal_engine.recommendation import (METHOD_KEYS, NEEDS_INFO, NOT_SUPPORTED, SUPPORTED, recommend,
                                          recommended)

LOCALES = Path(__file__).resolve().parent.parent / "locales"
NO_PRE = dict(has_pre_treatment_periods=False, n_pre_periods=0)


def _best(**fields):
    design = ResearchDesignInput(**fields)
    best = recommended(recommend(design, diagnose(design)))
    return best.key if best else None


def _status(key, **fields):
    design = ResearchDesignInput(**fields)
    return next(r for r in recommend(design, diagnose(design)) if r.key == key).status


def test_diagnosis_flags_spillovers():
    design = ResearchDesignInput(
        research_question="Effect of mining on health in neighboring territories",
        data_structure="panel", assignment_mechanism="policy",
        treatment_timing="single_date",
    )
    diag = diagnose(design)
    assert diag.potential_spillovers == Level.HIGH


def test_each_design_gets_the_method_that_identifies_it():
    assert _best(assignment_mechanism="random", data_structure="experimental") == "rct"
    assert _best(assignment_mechanism="threshold", data_structure="panel", n_pre_periods=3) == "rdd"
    assert _best(assignment_mechanism="threshold", data_structure="cross_section", **NO_PRE) == "rdd"
    assert _best(assignment_mechanism="policy", data_structure="panel", n_pre_periods=4) in ("did", "event_study")
    assert _best(assignment_mechanism="policy", data_structure="panel", n_pre_periods=10,
                 n_treated_units="one") == "synthetic_control"
    assert _best(assignment_mechanism="policy", data_structure="time_series", n_pre_periods=24,
                 has_control_group=False, n_treated_units="one") == "its"
    assert _best(assignment_mechanism="self_selected", data_structure="cross_section", instrument="available",
                 **NO_PRE) == "iv"
    assert _best(assignment_mechanism="self_selected", data_structure="cross_section", instrument="none",
                 confounders_observed="measured", **NO_PRE) == "matching"


def test_a_policy_or_panel_does_not_imply_did():
    # A policy evaluated on cross-sectional data, a panel without comparison units,
    # and a panel without pre-treatment periods.
    assert _status("did", assignment_mechanism="policy", data_structure="cross_section", **NO_PRE) == NOT_SUPPORTED
    assert _status("did", assignment_mechanism="policy", data_structure="panel", n_pre_periods=3,
                   has_control_group=False) == NOT_SUPPORTED
    assert _status("did", assignment_mechanism="policy", data_structure="panel", **NO_PRE) == NOT_SUPPORTED


def test_rdd_iv_and_synthetic_control_need_their_conditions():
    assert _status("rdd", assignment_mechanism="policy") == NOT_SUPPORTED
    assert _status("iv", instrument="none") == NOT_SUPPORTED
    assert _status("iv", instrument="unsure") == NEEDS_INFO
    assert _status("iv", instrument="available") == SUPPORTED
    assert _status("synthetic_control", n_treated_units="many", n_pre_periods=10) == NOT_SUPPORTED
    assert _status("synthetic_control", n_treated_units="one", n_pre_periods=3) == NOT_SUPPORTED
    assert _status("matching", confounders_observed="not_measured") == NOT_SUPPORTED


def test_no_credible_design_is_said_and_explained():
    design = ResearchDesignInput(assignment_mechanism="self_selected", data_structure="cross_section",
                                 instrument="unsure", **NO_PRE)
    recs = recommend(design, diagnose(design))
    assert recommended(recs) is None
    assert [r.key for r in recs if r.status == NEEDS_INFO] == ["iv", "matching"]
    assert all(r.unmet for r in recs if not r.supported)


SCHOLARSHIP = ("What is the causal effect of receiving a scholarship on university enrollment among students "
               "whose entrance exam scores are near the scholarship eligibility cutoff?")


def test_a_question_about_a_cutoff_is_not_answered_by_did():
    # User report 2026-11-01: with the form left at its defaults (policy, panel), this
    # question got DiD. Its estimand is the effect at the cutoff: the engine must ask how
    # treatment is assigned, not answer another question.
    design = ResearchDesignInput(research_question=SCHOLARSHIP)
    diag = diagnose(design)
    recs = recommend(design, diag)
    assert diag.cutoff_in_question and recommended(recs) is None
    assert recs[0].key == "rdd" and recs[0].status == NEEDS_INFO
    assert all(r.status != SUPPORTED for r in recs)
    assert any(m.key == "diagnosis.note.cutoff_language" for m in diag.notes)


def test_the_scholarship_question_gets_a_regression_discontinuity():
    design = ResearchDesignInput(research_question=SCHOLARSHIP, assignment_mechanism="threshold",
                                 data_structure="cross_section", outcome_type="binary", **NO_PRE)
    best = recommended(recommend(design, diagnose(design)))
    assert best.key == "rdd" and best.status == SUPPORTED
    assert not diagnose(design).notes or all(m.key != "diagnosis.note.cutoff_language"
                                             for m in diagnose(design).notes)


def test_an_eligibility_expansion_over_time_is_not_mistaken_for_a_cutoff():
    design = ResearchDesignInput(research_question="Did the 2014 Medicaid eligibility expansion raise coverage?",
                                 n_pre_periods=3)
    assert not diagnose(design).cutoff_in_question
    assert recommended(recommend(design, diagnose(design))).key in ("did", "event_study")


def test_ruled_out_methods_are_never_ranked_above_supported_ones():
    options = itertools.product(["random", "policy", "geographic", "self_selected", "threshold"],
                                ["cross_section", "panel", "time_series", "spatio_temporal_panel"],
                                [0, 2, 6], [True, False], ["one", "many"], ["available", "none", "unsure"],
                                ["measured", "not_measured", "unsure"])
    for mech, data, pre, control, treated, instrument, confounders in options:
        design = ResearchDesignInput(assignment_mechanism=mech, data_structure=data, n_pre_periods=pre,
                                     has_pre_treatment_periods=pre > 0, has_control_group=control,
                                     n_treated_units=treated, instrument=instrument,
                                     confounders_observed=confounders)
        recs = recommend(design, diagnose(design))
        statuses = [r.status for r in recs]
        assert statuses == sorted(statuses, key=[SUPPORTED, NEEDS_INFO, NOT_SUPPORTED].index)
        assert all(r.unmet for r in recs if r.status == NOT_SUPPORTED)
        if mech == "random":
            assert recommended(recs).key == "rct"
        if mech == "threshold":
            assert recommended(recs).key == "rdd"


def test_no_numerical_credibility_is_attached_to_a_method():
    # The order is argued, not measured: nothing in the engine or on the page suggests a
    # precision that has not been established empirically.
    design = ResearchDesignInput(assignment_mechanism="policy", n_pre_periods=4, instrument="available",
                                 confounders_observed="measured")
    for method in recommend(design, diagnose(design)):
        assert not any(hasattr(method, name) for name in ("overall", "components", "confidence"))
    for lang in ("en", "fr"):
        texts = json.loads((LOCALES / f"{lang}.json").read_text(encoding="utf-8"))
        assert not [k for k in texts if k.startswith("rec.component.") or k in ("recommendation.score",
                                                                                 "recommendation.score_axis")]
        assert not any("/100" in texts[f"rec.{key}.{part}"] for key in METHOD_KEYS
                       for part in ("internal", "external", "rank"))


def test_the_argued_order_of_the_supported_methods():
    def order(**fields):
        design = ResearchDesignInput(**fields)
        return [r.key for r in recommend(design, diagnose(design)) if r.supported]
    many = order(assignment_mechanism="policy", n_pre_periods=4, instrument="available", confounders_observed="measured")
    assert many == ["did", "event_study", "iv", "its", "matching"]
    # One treated unit: the counterfactual is built explicitly and its fit can be inspected.
    one = order(assignment_mechanism="policy", n_pre_periods=12, n_treated_units="one", instrument="none",
                confounders_observed="measured")
    assert one.index("synthetic_control") < one.index("did")
    few = order(assignment_mechanism="policy", n_pre_periods=12, n_treated_units="few", instrument="none",
                confounders_observed="measured")
    assert few.index("synthetic_control") < few.index("did")
    short = order(assignment_mechanism="policy", n_pre_periods=6, n_treated_units="few", instrument="none",
                  confounders_observed="measured")
    assert short.index("did") < short.index("synthetic_control")


def test_a_question_alone_never_yields_a_method():
    # The form at its defaults says nothing about the data: no DiD by default, whatever the question.
    question = "What is the effect of the minimum wage on employment?"
    design = ResearchDesignInput(research_question=question)
    assert recommended(recommend(design, diagnose(design))) is None
    # The researcher confirms that these answers do describe the study: the conditions then decide.
    confirmed = ResearchDesignInput(research_question=question, answers_confirmed=True)
    assert recommended(recommend(confirmed, diagnose(confirmed))).key == "did"


def test_every_method_has_the_structured_answer_in_both_languages():
    for lang in ("en", "fr"):
        texts = json.loads((LOCALES / f"{lang}.json").read_text(encoding="utf-8"))
        for key in METHOD_KEYS:
            assert f"method.{key}" in texts, (lang, key)
            for part in ("intro", "estimand", "identification", "assumptions", "diagnostics", "when", "assumption",
                         "internal", "external", "rank"):
                assert f"rec.{key}.{part}" in texts, (lang, key, part)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("test_recommendation: OK")
