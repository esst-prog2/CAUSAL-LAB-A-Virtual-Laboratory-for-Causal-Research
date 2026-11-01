"""Method Recommendation Engine against published studies.

Each case is a well-known study: its research question, the form as its
authors would fill it in, and the design the study actually used. The engine
must recommend that design, or ask (recommend nothing) where the published
literature itself needs more than the question states. Cases cover every
method, French wording, and questions that contradict the form.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from causal_engine.diagnosis import ResearchDesignInput, diagnose
from causal_engine.recommendation import NEEDS_INFO, recommend, recommended

NO_PRE = dict(has_pre_treatment_periods=False, n_pre_periods=0)
CROSS = dict(data_structure="cross_section", **NO_PRE)

# (study, question, form answers, expected recommendation; None = the engine must ask)
CASES = [
    # Randomised experiments
    ("LaLonde (1986), National Supported Work",
     "What is the effect of the National Supported Work job-training program on earnings?",
     dict(assignment_mechanism="random", data_structure="experimental", **NO_PRE), "rct"),
    ("Miguel & Kremer (2004), deworming",
     "What is the effect of school-based deworming on school attendance, including spillovers to nearby schools?",
     dict(assignment_mechanism="random", data_structure="panel", n_pre_periods=1), "rct"),
    ("Finkelstein et al. (2012), Oregon lottery",
     "What is the effect of winning the Oregon Medicaid lottery on health care use?",
     dict(assignment_mechanism="random", data_structure="survey", **NO_PRE), "rct"),
    # Regression discontinuity
    ("Thistlethwaite & Campbell (1960), merit awards",
     "What is the causal effect of receiving a scholarship on university enrollment among students whose entrance "
     "exam scores are near the scholarship eligibility cutoff?",
     dict(assignment_mechanism="threshold", outcome_type="binary", **CROSS), "rdd"),
    ("Lee (2008), close elections",
     "What is the effect of party incumbency on winning the next election, comparing candidates who barely won "
     "or barely lost?",
     dict(assignment_mechanism="threshold", outcome_type="binary", **CROSS), "rdd"),
    ("Angrist & Lavy (1999), Maimonides' rule",
     "What is the effect of class size on test scores when classes are split at an enrollment cutoff of 40?",
     dict(assignment_mechanism="threshold", **CROSS), "rdd"),
    ("Dell (2010), mining mita",
     "What is the long-run effect of the colonial mita forced-labour system on household consumption across "
     "its historical boundary?",
     dict(assignment_mechanism="geographic", **CROSS), "rdd"),
    # Difference-in-differences and event studies
    ("Card & Krueger (1994), minimum wage",
     "What is the effect of New Jersey's minimum wage increase on fast-food employment, compared with "
     "Pennsylvania?",
     dict(assignment_mechanism="policy", data_structure="panel", n_pre_periods=1), "did"),
    ("Duflo (2001), school construction in Indonesia",
     "What is the effect of the Indonesian school construction program on years of education and wages?",
     dict(assignment_mechanism="geographic", data_structure="repeated_cross_section", n_pre_periods=1), "did"),
    ("Miller, Johnson & Wherry (2021), Medicaid expansions",
     "What is the effect of state Medicaid expansions, adopted in different years, on mortality?",
     dict(assignment_mechanism="policy", treatment_timing="staggered", data_structure="panel", n_pre_periods=5),
     ("did", "event_study")),
    # Synthetic control
    ("Abadie, Diamond & Hainmueller (2010), Proposition 99",
     "What is the effect of California's Proposition 99 tobacco control program on cigarette sales?",
     dict(assignment_mechanism="policy", data_structure="panel", n_pre_periods=19, n_treated_units="one"),
     "synthetic_control"),
    ("Abadie & Gardeazabal (2003), Basque Country",
     "What is the economic cost of terrorism in the Basque Country?",
     dict(assignment_mechanism="geographic", data_structure="panel", n_pre_periods=15, n_treated_units="one"),
     "synthetic_control"),
    # Interrupted time series
    ("Barone-Adesi et al. (2006), Italian smoking ban",
     "What is the effect of the nationwide smoking ban on hospital admissions for heart attacks?",
     dict(assignment_mechanism="policy", data_structure="time_series", n_pre_periods=60, n_treated_units="one",
          has_control_group=False), "its"),
    # Instrumental variables
    ("Angrist & Krueger (1991), quarter of birth",
     "What is the effect of years of schooling on earnings, using quarter of birth as an instrument?",
     dict(assignment_mechanism="self_selected", instrument="available", **CROSS), "iv"),
    ("Angrist (1990), Vietnam draft lottery",
     "What is the effect of military service on later earnings, using the Vietnam draft lottery?",
     dict(assignment_mechanism="self_selected", instrument="available", **CROSS), "iv"),
    ("Card (1995), college proximity",
     "What is the effect of education on wages, using proximity to a college as a source of exogenous variation?",
     dict(assignment_mechanism="self_selected", instrument="available", **CROSS), "iv"),
    # Selection on observables
    ("Dehejia & Wahba (1999), observational job training",
     "What is the effect of a job-training program on earnings, given rich pre-program earnings and demographics?",
     dict(assignment_mechanism="self_selected", instrument="none", confounders_observed="measured", **CROSS),
     "matching"),
    # French wording
    ("Question en français, seuil",
     "Quel est l'effet d'une bourse sur l'inscription à l'université pour les élèves proches du seuil "
     "d'admissibilité ?",
     dict(assignment_mechanism="threshold", **CROSS), "rdd"),
    # The engine must ask, not answer another question
    ("Cutoff in the question, form left at its defaults",
     "What is the causal effect of receiving a scholarship on university enrollment among students whose entrance "
     "exam scores are near the scholarship eligibility cutoff?", dict(), None),
    ("Lottery in the question, form says policy",
     "What is the effect of winning a housing lottery on children's outcomes?",
     dict(assignment_mechanism="policy", data_structure="panel", n_pre_periods=2), None),
    ("Nationwide change, form says many treated units",
     "What is the effect of the nationwide sugar tax on soda consumption?",
     dict(assignment_mechanism="policy", data_structure="panel", n_pre_periods=4), None),
    ("Predictive question",
     "Which student characteristics predict university dropout?",
     dict(assignment_mechanism="self_selected", **CROSS), None),
    ("Self-selection with nothing to identify it",
     "What is the effect of joining a gym on health?",
     dict(assignment_mechanism="self_selected", instrument="none", confounders_observed="not_measured", **CROSS),
     None),
]


def test_published_studies_get_the_design_their_authors_used():
    wrong = []
    for study, question, form, expected in CASES:
        design = ResearchDesignInput(research_question=question, **form)
        best = recommended(recommend(design, diagnose(design)))
        got = best.key if best else None
        if got != expected and not (isinstance(expected, tuple) and got in expected):
            wrong.append((study, expected, got))
    assert not wrong, wrong


def test_when_the_engine_asks_it_says_what_to_answer():
    for study, question, form, expected in CASES:
        if expected is not None:
            continue
        design = ResearchDesignInput(research_question=question, **form)
        recs = recommend(design, diagnose(design))
        assert all(r.unmet for r in recs if not r.supported), study


def test_the_lottery_question_points_to_the_randomised_design():
    design = ResearchDesignInput(research_question="What is the effect of winning a housing lottery on children's "
                                 "outcomes?", assignment_mechanism="policy", data_structure="panel", n_pre_periods=2)
    recs = recommend(design, diagnose(design))
    assert recs[0].key == "rct" and recs[0].status == NEEDS_INFO


def test_question_wording_adds_its_caveats():
    design = ResearchDesignInput(research_question="How does the long-run effect of the reform vary by income, and "
                                 "through which mechanism?", n_pre_periods=3)
    keys = {m.key for m in recommended(recommend(design, diagnose(design))).rationale}
    assert {"rec.note.heterogeneity", "rec.note.mechanism", "rec.note.dynamic"} <= keys


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("test_recommendation_benchmark: OK")
