import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from causal_engine.diagnosis import ResearchDesignInput, diagnose, Level
from causal_engine.recommendation import recommend


def test_diagnosis_flags_spillovers():
    design = ResearchDesignInput(
        research_question="Effect of mining on health in neighboring territories",
        data_structure="panel", assignment_mechanism="policy",
        treatment_timing="single_date",
    )
    diag = diagnose(design)
    assert diag.potential_spillovers == Level.HIGH


def test_recommendation_favors_did_for_panel_policy():
    design = ResearchDesignInput(
        research_question="Effect of a mining code reform on local economic activity",
        data_structure="panel", assignment_mechanism="policy",
        treatment_timing="single_date", has_pre_treatment_periods=True, n_pre_periods=3,
    )
    diag = diagnose(design)
    recs = recommend(design, diag)
    top_methods = [r.method for r in recs[:2]]
    print("Top methods:", top_methods)
    assert "Difference-in-Differences" in top_methods or "Event Study" in top_methods


def test_recommendation_favors_rct_when_random():
    design = ResearchDesignInput(assignment_mechanism="random", data_structure="experimental")
    diag = diagnose(design)
    recs = recommend(design, diag)
    print("Best method (random assignment):", recs[0].method, recs[0].overall)
    assert recs[0].method == "Randomized Controlled Trial"


if __name__ == "__main__":
    test_diagnosis_flags_spillovers()
    test_recommendation_favors_did_for_panel_policy()
    test_recommendation_favors_rct_when_random()
    print("test_recommendation: OK")
