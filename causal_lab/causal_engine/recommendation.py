"""
Method Recommendation Engine (CAUSAL LAB spec, Section 11-13).

Computes a transparent "CAUSAL LAB Method Suitability Score" for a
fixed library of candidate methods, based on the structured design
input and the diagnosis produced by causal_engine.diagnosis.

The score is explicitly NOT presented as ground truth (spec Section
12: "Never present the score as an absolute truth"). It is a
decomposed, explainable weighting of how well each method's
identifying assumptions match the described research design.

    AI / heuristic reasoning layer
            |
    Method Suitability Score (this module)
            |
    Ranked recommendation + explanation text
"""
from __future__ import annotations

from dataclasses import dataclass, field

from causal_engine.diagnosis import DiagnosisResult, Level, ResearchDesignInput

_LEVEL_TO_RISK = {Level.LOW: 0.15, Level.MEDIUM: 0.5, Level.HIGH: 0.9, Level.UNKNOWN: 0.5}


@dataclass
class MethodScore:
    method: str
    components: dict = field(default_factory=dict)   # component name -> 0-100
    overall: float = 0.0
    confidence: str = "MEDIUM"
    rationale: list[str] = field(default_factory=list)
    main_assumption: str = ""
    main_concern: str = ""

    def as_dict(self):
        return {
            "method": self.method,
            "overall": round(self.overall, 1),
            "confidence": self.confidence,
            "components": {k: round(v, 1) for k, v in self.components.items()},
            "rationale": self.rationale,
            "main_assumption": self.main_assumption,
            "main_concern": self.main_concern,
        }


def _confidence_from_score(score: float) -> str:
    if score >= 75:
        return "HIGH"
    if score >= 50:
        return "MEDIUM"
    return "LOW"


def _score_did(design: ResearchDesignInput, diag: DiagnosisResult) -> MethodScore:
    rationale = []
    data_structure = 95 if design.data_structure in ("panel", "spatio_temporal_panel") else 40
    timing = 90 if design.has_pre_treatment_periods and design.n_pre_periods >= 1 else 30
    if design.treatment_timing == "staggered":
        timing -= 20
        rationale.append(
            "Treatment adoption is staggered: a standard two-way "
            "fixed-effects DiD estimate can be contaminated by "
            "already-treated units used as controls. A "
            "heterogeneity-robust estimator (Callaway & Sant'Anna, "
            "de Chaisemartin & D'Haultfoeuille) is recommended over "
            "the canonical TWFE specification."
        )
    assignment = 85 if design.assignment_mechanism in ("policy", "threshold", "geographic") else 55
    identification = 100 - _LEVEL_TO_RISK[diag.potential_confounding] * 60
    spatial = 40 if diag.potential_spillovers == Level.HIGH else 85
    endogeneity = 100 - _LEVEL_TO_RISK[diag.potential_endogeneity] * 70

    components = {
        "Data structure": data_structure,
        "Treatment timing": timing,
        "Assignment mechanism": assignment,
        "Identification": identification,
        "Spatial compatibility": spatial,
        "Endogeneity": endogeneity,
    }
    overall = sum(components.values()) / len(components)

    rationale.insert(0,
        "Difference-in-Differences is potentially appropriate because "
        "treatment occurs at a defined point in time and the data "
        "contain treated and comparison units observed before and "
        "after the intervention.")
    if diag.potential_spillovers == Level.HIGH:
        rationale.append(
            "Because nearby or related units may also be affected "
            "(spillovers), a Spatial Spillover Analysis extension is "
            "recommended alongside the baseline DiD."
        )

    return MethodScore(
        method="Difference-in-Differences",
        components=components,
        overall=overall,
        confidence=_confidence_from_score(overall),
        rationale=rationale,
        main_assumption="Parallel trends between treated and comparison units in the absence of treatment.",
        main_concern="Spatial spillovers" if diag.potential_spillovers == Level.HIGH else "Pre-trend violations",
    )


def _score_event_study(design: ResearchDesignInput, diag: DiagnosisResult) -> MethodScore:
    base = _score_did(design, diag)
    components = dict(base.components)
    components["Pre-period availability"] = 90 if design.n_pre_periods >= 2 else 40
    overall = sum(components.values()) / len(components)
    rationale = [
        "An Event Study is a natural extension of DiD: it estimates "
        "period-by-period treatment effects and lets you inspect "
        "pre-treatment coefficients directly as an informal test of "
        "the parallel-trends assumption.",
    ]
    if design.n_pre_periods < 2:
        rationale.append(
            "Fewer than two pre-treatment periods are available, which "
            "limits the ability to visually or statistically assess "
            "pre-trends."
        )
    return MethodScore(
        method="Event Study",
        components=components,
        overall=overall,
        confidence=_confidence_from_score(overall),
        rationale=rationale,
        main_assumption="No anticipation effects; parallel trends in each pre-treatment period.",
        main_concern="Statistical power in periods far from the treatment date.",
    )


def _score_synthetic_control(design: ResearchDesignInput, diag: DiagnosisResult) -> MethodScore:
    few_treated = 85  # heuristic: SC shines with few treated units, cannot verify count here
    donor_pool = 80 if design.data_structure in ("panel", "spatio_temporal_panel") else 30
    identification = 100 - _LEVEL_TO_RISK[diag.potential_confounding] * 40
    components = {
        "Few treated units heuristic": few_treated,
        "Donor pool availability": donor_pool,
        "Identification": identification,
    }
    overall = sum(components.values()) / len(components)
    rationale = [
        "Synthetic Control is most useful when a single (or very few) "
        "treated unit(s) can be compared against a weighted combination "
        "of untreated donor units that closely tracks its pre-treatment "
        "trajectory.",
    ]
    return MethodScore(
        method="Synthetic Control",
        components=components,
        overall=overall,
        confidence=_confidence_from_score(overall),
        rationale=rationale,
        main_assumption="No interference between the treated unit and donor units; good pre-treatment fit.",
        main_concern="Inference relies on placebo-based permutation tests rather than standard errors.",
    )


def _score_iv(design: ResearchDesignInput, diag: DiagnosisResult) -> MethodScore:
    endogeneity_relevance = 90 if diag.potential_endogeneity == Level.HIGH else 20
    components = {
        "Endogeneity relevance": endogeneity_relevance,
        "Assumed instrument availability": 30,  # cannot be verified without a declared instrument
        "Identification": 100 - _LEVEL_TO_RISK[diag.potential_confounding] * 30,
    }
    overall = sum(components.values()) / len(components)
    rationale = [
        "Instrumental Variables can address endogenous treatment "
        "assignment, but the score here is capped because no valid "
        "instrument has been declared in the current project — "
        "relevance and exclusion restriction cannot be assessed "
        "automatically.",
    ]
    return MethodScore(
        method="Instrumental Variables",
        components=components,
        overall=overall,
        confidence=_confidence_from_score(overall),
        rationale=rationale,
        main_assumption="Instrument relevance and exclusion restriction (no direct effect on the outcome).",
        main_concern="Weak instruments bias estimates toward the OLS estimate.",
    )


def _score_rdd(design: ResearchDesignInput, diag: DiagnosisResult) -> MethodScore:
    threshold_based = 90 if design.assignment_mechanism == "threshold" else 10
    components = {
        "Threshold-based assignment": threshold_based,
        "Data density near cutoff": 50,  # cannot be verified without actual data
    }
    overall = sum(components.values()) / len(components)
    rationale = [
        "Regression Discontinuity is only appropriate when treatment "
        "is assigned by whether a running variable crosses a known "
        "cutoff. This design's assignment mechanism is "
        f"'{design.assignment_mechanism}', which "
        + ("matches this requirement." if design.assignment_mechanism == "threshold"
           else "does not obviously match this requirement."),
    ]
    return MethodScore(
        method="Regression Discontinuity",
        components=components,
        overall=overall,
        confidence=_confidence_from_score(overall),
        rationale=rationale,
        main_assumption="No manipulation of the running variable around the cutoff.",
        main_concern="Local validity only: estimates apply near the cutoff, not to the full population.",
    )


def _score_matching(design: ResearchDesignInput, diag: DiagnosisResult) -> MethodScore:
    selection_on_observables = 100 - _LEVEL_TO_RISK[diag.potential_endogeneity] * 90
    components = {
        "Selection-on-observables plausibility": selection_on_observables,
        "Cross-sectional applicability": 80 if design.data_structure in ("cross_section", "survey") else 50,
    }
    overall = sum(components.values()) / len(components)
    rationale = [
        "Matching / propensity-score methods require that, "
        "conditional on observed covariates, treatment assignment is "
        "as good as random (no unobserved confounding). This is a "
        "strong and untestable assumption.",
    ]
    return MethodScore(
        method="Matching / Propensity Score",
        components=components,
        overall=overall,
        confidence=_confidence_from_score(overall),
        rationale=rationale,
        main_assumption="Conditional independence (selection on observables only).",
        main_concern="Unobserved confounding cannot be ruled out or tested directly.",
    )


def _score_rct(design: ResearchDesignInput, diag: DiagnosisResult) -> MethodScore:
    is_random = design.assignment_mechanism == "random"
    components = {
        "Random assignment": 98 if is_random else 2,
        "Identification": 98 if is_random else 5,
    }
    overall = sum(components.values()) / len(components)
    rationale = [
        "A Randomized Controlled Trial design was "
        + ("declared for this project." if is_random else
           "not declared for this project: treatment assignment is "
           "described as non-random, so an RCT-style analysis is not "
           "applicable retroactively. This score reflects that an RCT "
           "was not the assignment mechanism used."),
    ]
    return MethodScore(
        method="Randomized Controlled Trial",
        components=components,
        overall=overall,
        confidence=_confidence_from_score(overall),
        rationale=rationale,
        main_assumption="Random assignment balances observed and unobserved confounders in expectation.",
        main_concern="External validity beyond the study sample/context.",
    )


_ALL_SCORERS = [
    _score_rct,
    _score_did,
    _score_event_study,
    _score_synthetic_control,
    _score_rdd,
    _score_iv,
    _score_matching,
]


def recommend(design: ResearchDesignInput, diag: DiagnosisResult) -> list[MethodScore]:
    """Score every candidate method in the v0.1 library and return them
    ranked from most to least suitable."""
    scores = [scorer(design, diag) for scorer in _ALL_SCORERS]
    scores.sort(key=lambda s: s.overall, reverse=True)
    return scores
