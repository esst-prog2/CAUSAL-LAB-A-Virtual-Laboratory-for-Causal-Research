"""Second-stage review, 2026-11-07: examples written independently of the corrections.
Estimators against values computed by hand; what the question analysis must not infer;
what the recommendation must not offer; and the agreement between modules."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

from causal_engine.diagnosis import Level, ResearchDesignInput as D, diagnose
from causal_engine.question_analysis import analyze
from causal_engine.question_reading import AMBIGUOUS, CAUSAL, read_question
from causal_engine.recommendation import NOT_SUPPORTED, recommend, recommended
from estimators.did import estimate_did
from estimators.iv import estimate_iv
from estimators.matching import estimate_matching
from estimators.rct import estimate_rct
from estimators.rdd import estimate_rdd
from estimators.synthetic_control import estimate_synthetic_control
from utils.i18n import t

NO_PRE = dict(has_pre_treatment_periods=False, n_pre_periods=0)
APP = Path(__file__).resolve().parent.parent / "app.py"


# --------------------------------------------------------------------------
# Estimators against hand computations
# --------------------------------------------------------------------------
def test_did_on_a_two_by_two_table():
    # Treated means 10 -> 16, control means 8 -> 11: DiD = 6 - 3 = 3.
    cells = {("t1", 0): 9, ("t1", 1): 15, ("t2", 0): 11, ("t2", 1): 17, ("c1", 0): 7, ("c1", 1): 10, ("c2", 0): 9, ("c2", 1): 12}
    df = pd.DataFrame([dict(unit=u, period=p, Y=float(y), D=int(u[0] == "t" and p == 1)) for (u, p), y in cells.items()])
    assert abs(estimate_did(df).att - 3) < 1e-10


def test_rct_is_a_difference_in_means_with_the_neyman_variance():
    r = np.random.default_rng(5)
    y1, y0 = r.normal(2, 1, 30), r.normal(0, 2, 50)
    e = estimate_rct(pd.DataFrame(dict(Y=np.r_[y1, y0], D=np.r_[np.ones(30), np.zeros(50)])))
    assert abs(e.estimate - (y1.mean() - y0.mean())) < 1e-10
    assert abs(e.se - np.sqrt(y1.var(ddof=1) / 30 + y0.var(ddof=1) / 50)) < 1e-10


def test_iv_with_a_binary_instrument_is_the_wald_ratio():
    r = np.random.default_rng(6)
    z = r.integers(0, 2, 500)
    u = r.normal(size=500)
    d = ((z + u + r.normal(size=500)) > 0.5).astype(int)
    y = 2 * d + u + r.normal(size=500)
    e = estimate_iv(pd.DataFrame(dict(Y=y, D=d, Z=z)), "Y", "D", ["Z"])
    wald = (y[z == 1].mean() - y[z == 0].mean()) / (d[z == 1].mean() - d[z == 0].mean())
    assert abs(e.estimate - wald) < 1e-8
    assert e.details["ar_kind"] == "interval" and e.details["ar_low"] < e.estimate < e.details["ar_high"]


def test_rdd_recovers_an_exact_jump_on_a_noiseless_line():
    x = np.linspace(-1, 1, 401)
    e = estimate_rdd(pd.DataFrame(dict(Y=2 + 0.5 * x + 1.5 * (x >= 0), X=x)), "Y", "X", 0.0, 0.5)
    assert abs(e.estimate - 1.5) < 1e-10


def test_matching_with_exact_matches():
    # Treated at X = 1 and 2, each with a control at the same X: (5 - 1 + 7 - 2) / 2 = 4.5.
    df = pd.DataFrame(dict(Y=[5., 7., 1., 2., 3., 9.], D=[1, 1, 0, 0, 0, 0], X=[1., 2., 1., 2., 3., 4.]))
    assert abs(estimate_matching(df, "Y", "D", ["X"], n_bootstrap=0).estimate - 4.5) < 1e-8


def test_synthetic_control_finds_the_exact_combination():
    r = np.random.default_rng(7)
    a, b, c = (np.cumsum(r.normal(size=12)) for _ in range(3))
    treated = 0.5 * a + 0.5 * b + 3 * (np.arange(12) >= 8)
    rows = [dict(unit=n, period=p, Y=v) for n, s in dict(treated=treated, a=a, b=b, c=c).items() for p, v in enumerate(s)]
    e = estimate_synthetic_control(pd.DataFrame(rows), "unit", "period", "Y", "treated", 8)
    assert abs(e.estimate - 3) < 1e-3
    weights = e.details["weights"].set_index("donor")["weight"]
    assert abs(weights["a"] - 0.5) < 1e-3 and abs(weights["b"] - 0.5) < 1e-3


# --------------------------------------------------------------------------
# The question: what must not be inferred
# --------------------------------------------------------------------------
def test_assignment_is_not_read_from_the_outcome():
    for question, expected in (("What is the effect of a tax credit on labour force participation?", "policy"),
                               ("Does education increase political participation?", None),
                               ("What is the effect of schooling on tax compliance?", None),
                               ("Quel est l'effet des bourses sur la participation électorale ?", None),
                               ("Does joining a union raise wages?", "self_selected")):
        assert analyze(D(research_question=question)).inferred.get("assignment_mechanism") == expected, question
    # A rule that decides is no self-selection; deciding to take it up is.
    assert analyze(D(research_question="What is the effect of a rule that decides who is treated on wages?")
                   ).inferred.get("assignment_mechanism") != "self_selected"


def test_counterfactuals_with_any_verb_and_responsibility_are_causal():
    assert read_question("Would crime rise without street lighting?").intent == CAUSAL
    assert (read_question("Would crime rise without street lighting?").treatment,
            read_question("Would crime rise without street lighting?").outcome) == ("street lighting", "crime")
    reading = read_question("Is the minimum wage responsible for job losses?")
    assert (reading.intent, reading.treatment, reading.outcome) == (CAUSAL, "the minimum wage", "job losses")


def test_an_unknown_verb_is_read_as_causal_with_roles_to_confirm_in_english():
    # Version 3: the verb class is open in English. The roles are never quoted as stated.
    reading = read_question("Does job insecurity erode trust?")
    assert (reading.intent, reading.treatment, reading.outcome, reading.certain) == (CAUSAL, "job insecurity", "trust",
                                                                                      False)
    # French keeps the closed list: the reader asks, it does not call this non-causal.
    assert read_question("Le salaire minimum détruit-il des emplois ?").intent == AMBIGUOUS


def test_the_open_verb_class_keeps_describing_verbs_and_groups_out():
    for question in ("Do physicians follow clinical guidelines?", "Do consumers prefer green products?",
                     "Do we know what works?", "Does income inequality differ across regions?",
                     "Do firms export to China?", "Do children of immigrants attend college?"):
        assert read_question(question).intent == AMBIGUOUS, question


def test_a_reaction_verb_gives_causal_intent_without_guessing_roles():
    reading = read_question("Do firms respond to gender pay gap transparency?")
    assert (reading.intent, reading.treatment, reading.outcome, reading.certain) == (CAUSAL, "", "", False)


def test_a_named_effect_without_of_is_causal_with_roles_to_confirm():
    reading = read_question("Is there a minimum wage effect on employment?")
    assert (reading.intent, reading.treatment, reading.outcome, reading.certain) == (CAUSAL, "minimum wage", "employment",
                                                                                      False)
    assert read_question("How large are peer effects?").intent == CAUSAL


# --------------------------------------------------------------------------
# The recommendation: what must not be offered
# --------------------------------------------------------------------------
def test_designs_that_compare_need_someone_to_compare_with():
    for fields in (dict(assignment_mechanism="random", has_control_group=False, data_structure="experimental", **NO_PRE),
                   dict(assignment_mechanism="threshold", has_control_group=False, data_structure="cross_section", **NO_PRE),
                   dict(assignment_mechanism="self_selected", has_control_group=False, data_structure="cross_section",
                        confounders_observed="measured", instrument="available", **NO_PRE),
                   dict(assignment_mechanism="random", n_treated_units="one", data_structure="experimental", **NO_PRE),
                   dict(assignment_mechanism="self_selected", n_treated_units="one", data_structure="cross_section",
                        confounders_observed="measured", instrument="available", **NO_PRE)):
        design = D(**fields)
        recs = recommend(design, diagnose(design))
        assert recommended(recs) is None, fields
        assert all(r.status == NOT_SUPPORTED for r in recs if r.key in ("rct", "rdd", "iv", "matching")), fields


def test_nothing_known_nothing_recommended():
    design = D()
    assert recommended(recommend(design, diagnose(design))) is None
    confirmed = D(answers_confirmed=True)
    assert recommended(recommend(confirmed, diagnose(confirmed))).key == "did"


def test_diagnosis_flags_do_not_fire_on_the_words_of_an_ordinary_question():
    base = dict(n_pre_periods=3)
    assert diagnose(D(research_question="What is the effect of training on income?", **base)
                    ).treatment_heterogeneity == Level.MEDIUM
    assert diagnose(D(research_question="How does age at school entry affect grades?", **base)
                    ).treatment_heterogeneity == Level.MEDIUM
    assert diagnose(D(research_question="What is the effect of the reform on employment in the region?", **base)
                    ).potential_spillovers == Level.LOW
    assert diagnose(D(research_question="Does demand for housing raise prices?", **base)
                    ).potential_endogeneity == Level.MEDIUM
    # The words that do ask for it still do.
    assert diagnose(D(research_question="Does the effect of training on wages vary by gender?", **base)
                    ).treatment_heterogeneity == Level.HIGH


# --------------------------------------------------------------------------
# Between the modules, in the app
# --------------------------------------------------------------------------
def _button(at, key):
    return next(b for b in at.button if b.label == t(key, "en"))


def _goto(at, page):
    at.session_state.page = page
    at.run()


def test_form_widgets_keep_their_identity_when_their_value_changes():
    # A widget whose default follows the value gets a new identity at each change, and the
    # browser's next edit goes to the old one and is lost: every second edit did nothing.
    # AppTest re-reads the widgets, so it cannot see the lost edit; it can see the identity.
    at = AppTest.from_file(str(APP), default_timeout=120).run()
    _goto(at, "research_question")
    before = at.text_area[0].id
    at.text_area[0].set_value("Is smoking associated with lung cancer?").run()
    at.text_area[0].set_value("Does smoking cause lung cancer?").run()
    assert at.text_area[0].id == before
    assert at.session_state.design.research_question == "Does smoking cause lung cancer?"
    number = at.number_input[0]
    number_id = number.id
    number.set_value(3).run()
    at.number_input[0].set_value(7).run()
    assert at.number_input[0].id == number_id and at.session_state.design.n_pre_periods == 7
    _goto(at, "virtual_lab")
    world = at.number_input[0].id
    at.number_input[0].set_value(150).run()
    at.number_input[0].set_value(220).run()
    assert at.number_input[0].id == world and at.session_state.vw_config.n_units == 220


def test_the_button_that_applies_the_question_reaches_the_form():
    # A value changed from outside the widget still shows in it.
    at = AppTest.from_file(str(APP), default_timeout=120).run()
    _goto(at, "research_question")
    at.text_area[0].set_value("What is the effect of a scholarship for students near the eligibility cutoff?").run()
    _button(at, "qa.apply").click().run()
    assert at.session_state.design.assignment_mechanism == "threshold"
    assert at.session_state["form_wizard.assignment_mechanism"] == "threshold"


def test_a_stated_causal_aim_belongs_to_its_question():
    at = AppTest.from_file(str(APP), default_timeout=120).run()
    _goto(at, "research_question")
    at.text_area[0].set_value("Is class size associated with test scores?").run()
    at.checkbox(key="qa_confirm_causal").check().run()
    assert at.session_state.design.causal_confirmed
    at.text_area[0].set_value("Can we predict dropout using grades?").run()
    assert not at.session_state.design.causal_confirmed
    assert any(t("qa.intent.predictive", "en") in m.value for m in at.markdown)


def test_the_recommendation_page_says_when_the_form_has_changed_since_the_diagnosis():
    at = AppTest.from_file(str(APP), default_timeout=120).run()
    _goto(at, "research_question")
    at.text_area[0].set_value("What is the effect of class size on grades?").run()
    _button(at, "wizard.run").click().run()
    _goto(at, "recommendation")
    assert not any(w.value == t("recommendation.stale", "en") for w in at.warning)
    at.session_state.design.instrument = "none"
    at.run()
    assert any(w.value == t("recommendation.stale", "en") for w in at.warning)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("test_independent_examples: OK")
