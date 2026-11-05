"""How a question is read: its intent, its treatment and outcome, and its thresholds.
These wordings were written to develop the reader: they are not the frozen
evaluation set in docs/evaluation, which is never used to tune it."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from causal_engine.diagnosis import ResearchDesignInput, diagnose
from causal_engine.question_analysis import INFERRED, STATED, UNCERTAIN, UNKNOWN, analyze
from causal_engine.question_reading import (AMBIGUOUS, CAUSAL, DESCRIPTIVE, PREDICTIVE, THRESHOLD_ASSIGNMENT,
                                            THRESHOLD_ORDINARY, THRESHOLD_UNCLEAR, read_question, threshold_kind)
from causal_engine.recommendation import recommend, recommended


def _intent(question):
    return read_question(question).intent


def test_explicitly_causal_wordings_in_their_variations():
    for question in ("Does education increase income?",
                     "Did education increase income?",
                     "Doesn't education increase income?",
                     "Does education not increase income?",
                     "Has education increased income?",
                     "Is smoking a cause of lung cancer?",
                     "Are poor diets one of the main causes of heart disease?",
                     "What happens to employment when the minimum wage changes?",
                     "What would happen to prices if taxes were changed?",
                     "Would mortality be different in the absence of the vaccine?",
                     "Would employment have been higher without the reform?",
                     "Does tutoring make grades increase?",
                     "Do bonuses make turnover decrease?",
                     "How does class size affect test scores?",
                     "To what extent do subsidies reduce poverty?",
                     "How much do hospital mergers raise prices?",
                     "Does trade have an effect on wages?",
                     "Is income affected by schooling?",
                     "Does gender diversity matter for firm performance?",
                     "Is tutoring effective at raising grades?",
                     "The effect of microcredit on income",
                     "Estimating the impact of class size on achievement",
                     "What are the returns to schooling?",
                     "L'éducation augmente-t-elle le revenu ?",
                     "La réforme a-t-elle réduit le chômage des jeunes ?",
                     "Le tabac est-il une cause de cancer ?",
                     "Que se passe-t-il pour l'emploi quand le salaire minimum augmente ?",
                     "Quel est l'effet d'une bourse sur l'inscription ?",
                     "Quel impact la baisse de la TVA a-t-elle sur l'emploi ?",
                     "Est-ce que le télétravail améliore la productivité ?"):
        assert _intent(question) == CAUSAL, question


def test_explicit_prediction_and_description_are_the_only_non_causal_readings():
    for question in ("Can we predict dropout using grades?",
                     "Which student characteristics predict dropout?",
                     "Forecasting inflation with machine learning",
                     "Peut-on prédire le décrochage à partir des notes ?"):
        assert _intent(question) == PREDICTIVE, question
    for question in ("How many students drop out each year?",
                     "What is the prevalence of diabetes among adults?",
                     "What share of firms export?",
                     "How has fertility changed since 1990?",
                     "Did unemployment increase in 2020?",
                     "Has the crime rate fallen since 2000?",
                     "Combien d'élèves abandonnent chaque année ?",
                     "Quelle est la part des femmes parmi les cadres ?"):
        assert _intent(question) == DESCRIPTIVE, question


def test_ambiguous_wordings_abstain_instead_of_deciding():
    for question in ("What is the relationship between education and income?",
                     "Is smoking associated with lung cancer?",
                     "What explains differences in wages?",
                     "Is income correlated with health?",
                     "What factors influence voter turnout?",
                     "Are individuals exposed to pollution less likely to live long?",
                     "Are vaccinated people less likely to be hospitalized?",
                     "Do students who attend charter schools score higher than those who don't?",
                     "Is coffee good for your heart?",
                     "Does income increase with age?",
                     "Did crime fall after the reform?",
                     "What are the side effects of statins?",
                     "Quelle est la relation entre le revenu et la santé ?",
                     "Le revenu est-il associé à la santé ?",
                     "Les boursiers réussissent-ils mieux que les non-boursiers ?",
                     "Something entirely unusual about schools"):
        assert _intent(question) == AMBIGUOUS, question


def test_words_alone_do_not_make_a_question_causal():
    assert _intent("What is the effect size reported in these trials?") == AMBIGUOUS
    assert _intent("What is the impact factor of this journal?") == AMBIGUOUS
    assert _intent("Did prices increase over the decade?") == DESCRIPTIVE
    # A causal question about a prediction stays causal.
    assert _intent("What is the effect of training on forecast accuracy?") == CAUSAL


def test_treatment_and_outcome_of_the_new_wordings():
    cases = {
        "Is smoking a cause of lung cancer?": ("smoking", "lung cancer"),
        "What happens to employment when the minimum wage rises?": ("the minimum wage rises", "employment"),
        "Would mortality be different in the absence of the vaccine?": ("the vaccine", "mortality"),
        "Does tutoring make grades increase?": ("tutoring", "grades"),
        "Does being elected to Congress make politicians richer?": ("being elected to Congress", "politicians richer"),
        "Do minimum wage increases reduce teen employment?": ("minimum wage increases", "teen employment"),
        "Does the increase in taxes reduce spending?": ("the increase in taxes", "spending"),
        "Is income affected by schooling?": ("schooling", "income"),
        "Impact of cash transfers on child nutrition in a randomized trial in Mexico": ("cash transfers", "child nutrition"),
        "L'ouverture d'une ligne de métro a-t-elle augmenté les prix immobiliers ?":
            ("L'ouverture d'une ligne de métro", "les prix immobiliers"),
        "Quel impact la baisse de la TVA a-t-elle sur l'emploi ?": ("la baisse de la TVA", "l'emploi"),
    }
    for question, expected in cases.items():
        reading = read_question(question)
        assert (reading.treatment, reading.outcome) == expected, question


def test_doubtful_readings_are_never_shown_as_stated():
    a = analyze(ResearchDesignInput(research_question="Are vaccinated people less likely to be hospitalized?"))
    assert a.status("treatment") == UNCERTAIN and a.status("outcome") == UNCERTAIN
    assert "qa.ask.intent" in [m.key for m in a.follow_up] and "qa.ask.confirm_reading" in [m.key for m in a.follow_up]
    a = analyze(ResearchDesignInput(research_question="Do students who attend charter schools score higher than those "
                                                     "who don't?"))
    assert a.status("treatment") == UNCERTAIN            # a relative clause, not a clean treatment
    a = analyze(ResearchDesignInput(research_question="The reform reduces employment."))    # a statement
    assert a.status("treatment") == UNCERTAIN and a.intent == CAUSAL
    a = analyze(ResearchDesignInput(research_question="What is the relationship between education and income?"))
    assert a.status("treatment") == UNCERTAIN and a.status("outcome") == UNCERTAIN
    # Nothing is invented when the words are not there.
    a = analyze(ResearchDesignInput(research_question="Something entirely unusual about schools"))
    assert a.status("treatment") == UNKNOWN and a.status("outcome") == UNKNOWN
    assert a.status("confounding") == UNKNOWN
    # A clear question keeps its quotes.
    a = analyze(ResearchDesignInput(research_question="Is smoking a cause of lung cancer?"))
    assert a.status("treatment") == STATED and a.status("outcome") == STATED


def test_implicit_and_explicit_assignment_thresholds():
    for question in ("Does Medicare eligibility at age 65 change health care use?",
                     "Students scoring above 70 receive tutoring. Does tutoring improve their grades?",
                     "What is the effect of admission determined by a minimum grade on later earnings?",
                     "Does a subsidy activated above 50 employees change firm size?",
                     "What is the effect of winning, comparing candidates who barely won or barely lost?",
                     "What is the effect of a scholarship for students near the eligibility cutoff?",
                     "What is the effect of a grant for students close to the threshold?",
                     "Quel est l'effet d'une bourse pour les élèves proches du seuil d'admissibilité ?"):
        kind, words = threshold_kind(question)
        assert kind == THRESHOLD_ASSIGNMENT and words, question
        a = analyze(ResearchDesignInput(research_question=question))
        assert a.status("assignment") == INFERRED and a.inferred["assignment_mechanism"] == "threshold", question


def test_a_number_is_not_a_regression_discontinuity():
    # The role of the number is unknown: the analysis asks and infers nothing.
    for question in ("Do people earning above 50000 live longer?",
                     "Does a BMI over 30 raise mortality?",
                     "Do patients who receive more than 3 doses recover faster?",
                     "Does retirement at age 65 improve health?",
                     "What is the effect of the cutoff on grades?"):
        kind, _ = threshold_kind(question)
        assert kind == THRESHOLD_UNCLEAR, question
        a = analyze(ResearchDesignInput(research_question=question, answers_confirmed=True, causal_confirmed=True))
        assert "assignment_mechanism" not in a.inferred and "qa.ask.threshold_role" in [m.key for m in a.follow_up]
    # An ordinary threshold says nothing about assignment.
    for question in ("Is there a debt threshold above which growth falls?",
                     "Are there threshold effects of aid on growth?",
                     "What is the effect of inflation on the poverty threshold?"):
        assert threshold_kind(question)[0] == THRESHOLD_ORDINARY, question
        assert "assignment_mechanism" not in analyze(ResearchDesignInput(research_question=question)).inferred
    # A duration or a year is no threshold; "eligibility" alone is no cutoff.
    assert threshold_kind("Did wages rise more than 10 years after the reform?")[0] is None
    assert threshold_kind("Did the 2014 Medicaid eligibility expansion raise coverage?")[0] is None


def test_an_unclear_threshold_holds_every_method_back():
    design = ResearchDesignInput(research_question="Does a BMI over 30 raise mortality?", assignment_mechanism="policy",
                                 n_pre_periods=3)
    recs = recommend(design, diagnose(design))
    assert recommended(recs) is None and recs[0].key == "rdd"
    assert any(m.key == "rec.gate.threshold_unclear" for m in recs[0].unmet)
    # The researcher declares the rule: the question and the form agree.
    design = ResearchDesignInput(research_question="Does a BMI over 30 raise mortality?",
                                 assignment_mechanism="threshold", data_structure="cross_section",
                                 has_pre_treatment_periods=False, n_pre_periods=0)
    assert recommended(recommend(design, diagnose(design))).key == "rdd"


def test_no_method_answers_a_question_that_is_not_causal_until_the_researcher_says_otherwise():
    filled = dict(assignment_mechanism="random", data_structure="experimental", answers_confirmed=True)
    for question in ("Can we predict dropout using grades?", "How many students drop out each year?",
                     "Is smoking associated with lung cancer?"):
        design = ResearchDesignInput(research_question=question, **filled)
        recs = recommend(design, diagnose(design))
        assert recommended(recs) is None, question
        assert all(r.unmet for r in recs if not r.supported)
    # Tick "my aim is causal": the wording no longer decides, the conditions of the methods do.
    design = ResearchDesignInput(research_question="Is smoking associated with lung cancer?", causal_confirmed=True,
                                 **filled)
    assert recommended(recommend(design, diagnose(design))).key == "rct"
    assert diagnose(design).analysis.intent == AMBIGUOUS and diagnose(design).analysis.causal


def test_a_late_start_is_not_a_late_estimand():
    a = analyze(ResearchDesignInput(research_question="What is the effect of late school entry on grades?"))
    assert a.status("estimand") == UNKNOWN
    a = analyze(ResearchDesignInput(research_question="What is the LATE of schooling on wages among compliers?"))
    assert a.status("estimand") == STATED


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("test_question_reading: OK")
