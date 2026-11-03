"""Research Question Analysis: what the question states, what can be inferred
from it, what remains unknown, and the follow-up questions. Each test states
the rule it protects; questions come from published studies or the user."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from causal_engine.diagnosis import ResearchDesignInput, diagnose
from causal_engine.question_analysis import INFERRED, STATED, UNKNOWN, analyze
from causal_engine.recommendation import recommend, recommended

SCHOLARSHIP = ("What is the causal effect of receiving a scholarship on university enrollment among students whose "
               "entrance exam scores are near the scholarship eligibility cutoff?")


def _a(question, **form):
    return analyze(ResearchDesignInput(research_question=question, **form))


def _texts(analysis):
    return {name: str(e.text) for name, e in analysis.elements.items()}


def test_treatment_outcome_and_population_are_quoted_from_the_question():
    a = _a(SCHOLARSHIP)
    assert (a.elements["treatment"].text, a.elements["outcome"].text) == ("receiving a scholarship",
                                                                        "university enrollment")
    assert a.elements["population"].text.startswith("students whose entrance exam scores")
    assert all(a.status(n) == STATED for n in ("treatment", "outcome", "population"))
    cases = {
        "What is the effect of New Jersey's minimum wage increase on fast-food employment, compared with "
        "Pennsylvania?": ("New Jersey's minimum wage increase", "fast-food employment", ""),
        "What is the effect of state Medicaid expansions, adopted in different years, on mortality?":
            ("state Medicaid expansions, adopted in different years", "mortality", ""),
        "What is the effect of a tax on sugar on obesity?": ("a tax on sugar", "obesity", ""),
        "What is the effect of microcredit on income for women in rural Bangladesh?":
            ("microcredit", "income", "women in rural Bangladesh"),
        "What is the effect of the nationwide smoking ban on hospital admissions for heart attacks?":
            ("the nationwide smoking ban", "hospital admissions for heart attacks", ""),
        "Does joining a gym improve health?": ("joining a gym", "health", ""),
        "What is the economic cost of terrorism in the Basque Country?":
            ("terrorism", "economic cost", "the Basque Country"),
        "Quel est l'effet d'une bourse sur l'inscription à l'université pour les élèves proches du seuil ?":
            ("une bourse", "l'inscription à l'université", "les élèves proches du seuil"),
        "La réforme a-t-elle réduit le chômage des jeunes ?": ("La réforme", "le chômage des jeunes", ""),
    }
    for question, (treatment, outcome, population) in cases.items():
        e = _a(question).elements
        assert (e["treatment"].text, e["outcome"].text, e["population"].text or "") == (treatment, outcome,
                                                                                        population), question


def test_stated_inferred_and_unknown_are_kept_apart():
    a = _a(SCHOLARSHIP)
    # The cutoff is named; that it decides treatment is an inference, and the estimand follows from it.
    assert a.status("assignment") == INFERRED and a.inferred["assignment_mechanism"] == "threshold"
    assert a.status("estimand") == INFERRED and a.elements["estimand"].text.key == "qa.estimand.local"
    assert a.status("data") == UNKNOWN and a.status("confounding") == INFERRED
    assert _a("What is the effect of a training program on earnings among workers who were randomly assigned?"
              ).status("assignment") == STATED


def test_unknown_elements_get_targeted_follow_up_questions():
    keys = [m.key for m in _a("How does class size affect test scores among third graders?").follow_up]
    assert "qa.ask.assignment" in keys and "qa.ask.estimand" in keys and "qa.ask.data" in keys
    assert "qa.ask.population" not in keys                     # the population is stated
    assert "qa.ask.cutoff" in [m.key for m in _a(SCHOLARSHIP).follow_up]


def test_a_ranking_waits_for_the_essential_elements():
    # Assignment neither stated nor in the form: ask, do not rank.
    design = ResearchDesignInput(research_question="How does class size affect test scores among third graders?")
    recs = recommend(design, diagnose(design))
    assert recommended(recs) is None and all(any(m.key == "rec.ask.analysis" for m in r.unmet)
                                             for r in recs if r.unmet and r.status == "needs_info")
    # The same question once the researcher has described the design: a recommendation.
    filled = ResearchDesignInput(research_question=design.research_question, assignment_mechanism="threshold",
                                 data_structure="cross_section", has_pre_treatment_periods=False, n_pre_periods=0)
    assert recommended(recommend(filled, diagnose(filled))).key == "rdd"
    # A question without a treatment is not causal.
    assert [m.key for m in _a("Which student characteristics predict dropout?").blocking] == ["qa.block.not_causal"]


def test_a_lottery_is_the_treatment_or_an_instrument_depending_on_the_question():
    won = _a("What is the effect of winning a housing lottery on children's outcomes?")
    assert won.inferred["assignment_mechanism"] == "random" and "instrument" not in won.inferred
    draft = _a("What is the effect of military service on later earnings, using the Vietnam draft lottery?")
    assert draft.inferred.get("instrument") == "available" and "assignment_mechanism" not in draft.inferred
    assert draft.elements["estimand"].text.key == "qa.estimand.late_iv"


def test_self_selection_in_the_question_holds_back_a_policy_form():
    design = ResearchDesignInput(research_question="Does joining a gym improve health?", assignment_mechanism="policy",
                                 n_pre_periods=3)
    recs = recommend(design, diagnose(design))
    assert recommended(recs) is None
    assert any(m.key == "rec.ask.self_selection" for r in recs for m in r.unmet)


def test_short_words_are_not_read_inside_longer_ones():
    assert "assignment_mechanism" not in _a("What is the effect of microcredit on income for women in rural "
                                            "Bangladesh?").inferred          # "ban" in "Bangladesh"
    assert "n_treated_units" not in _a("What is the effect of the National Supported Work program on "
                                       "earnings?").inferred                 # "National" is a name


def test_confounding_is_reasoned_from_the_assignment_and_the_domain():
    gym = _a("Does joining a gym improve health?").elements["confounding"].text
    assert gym.key == "qa.confounding.self_selected" and gym.params["domain"].key == "qa.domain.health"
    scholarship = _a(SCHOLARSHIP).elements["confounding"].text
    assert scholarship.key == "qa.confounding.threshold" and scholarship.params["domain"].key == "qa.domain.education"


def test_no_question_no_analysis():
    assert analyze(ResearchDesignInput()) is None


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("test_question_analysis: OK")
