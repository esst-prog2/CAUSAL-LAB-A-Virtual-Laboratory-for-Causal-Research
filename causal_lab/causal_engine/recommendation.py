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

Explanations are translatable `Msg` objects (locale keys rec.*);
`str()` of each gives the English text.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from causal_engine.diagnosis import DiagnosisResult, Level, ResearchDesignInput
from utils.i18n import Msg

_LEVEL_TO_RISK = {Level.LOW: 0.15, Level.MEDIUM: 0.5, Level.HIGH: 0.9, Level.UNKNOWN: 0.5}


def component_slug(name: str) -> str:
    """Locale key suffix of a score component (rec.component.<slug>)."""
    return "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")


@dataclass
class MethodScore:
    method: str
    key: str = ""                                     # locale key suffix: method.<key>
    components: dict = field(default_factory=dict)   # component name -> 0-100
    overall: float = 0.0
    confidence: str = "MEDIUM"
    rationale: list[Msg] = field(default_factory=list)
    main_assumption: Msg | str = ""
    main_concern: Msg | str = ""

    def as_dict(self):
        return {
            "method": self.method,
            "overall": round(self.overall, 1),
            "confidence": self.confidence,
            "components": {k: round(v, 1) for k, v in self.components.items()},
            "rationale": [str(r) for r in self.rationale],
            "main_assumption": str(self.main_assumption),
            "main_concern": str(self.main_concern),
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
        rationale.append(Msg("rec.did.staggered"))
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

    rationale.insert(0, Msg("rec.did.intro"))
    if diag.potential_spillovers == Level.HIGH:
        rationale.append(Msg("rec.did.spillovers"))

    return MethodScore(
        method="Difference-in-Differences", key="did",
        components=components,
        overall=overall,
        confidence=_confidence_from_score(overall),
        rationale=rationale,
        main_assumption=Msg("rec.did.assumption"),
        main_concern=Msg("rec.did.concern_spillovers") if diag.potential_spillovers == Level.HIGH
        else Msg("rec.did.concern_pretrends"),
    )


def _score_event_study(design: ResearchDesignInput, diag: DiagnosisResult) -> MethodScore:
    base = _score_did(design, diag)
    components = dict(base.components)
    components["Pre-period availability"] = 90 if design.n_pre_periods >= 2 else 40
    overall = sum(components.values()) / len(components)
    rationale = [Msg("rec.event_study.intro")]
    if design.n_pre_periods < 2:
        rationale.append(Msg("rec.event_study.few_pre"))
    return MethodScore(
        method="Event Study", key="event_study",
        components=components,
        overall=overall,
        confidence=_confidence_from_score(overall),
        rationale=rationale,
        main_assumption=Msg("rec.event_study.assumption"),
        main_concern=Msg("rec.event_study.concern"),
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
    return MethodScore(
        method="Synthetic Control", key="synthetic_control",
        components=components,
        overall=overall,
        confidence=_confidence_from_score(overall),
        rationale=[Msg("rec.synthetic_control.intro")],
        main_assumption=Msg("rec.synthetic_control.assumption"),
        main_concern=Msg("rec.synthetic_control.concern"),
    )


def _score_iv(design: ResearchDesignInput, diag: DiagnosisResult) -> MethodScore:
    endogeneity_relevance = 90 if diag.potential_endogeneity == Level.HIGH else 20
    components = {
        "Endogeneity relevance": endogeneity_relevance,
        "Assumed instrument availability": 30,  # cannot be verified without a declared instrument
        "Identification": 100 - _LEVEL_TO_RISK[diag.potential_confounding] * 30,
    }
    overall = sum(components.values()) / len(components)
    return MethodScore(
        method="Instrumental Variables", key="iv",
        components=components,
        overall=overall,
        confidence=_confidence_from_score(overall),
        rationale=[Msg("rec.iv.intro")],
        main_assumption=Msg("rec.iv.assumption"),
        main_concern=Msg("rec.iv.concern"),
    )


def _score_rdd(design: ResearchDesignInput, diag: DiagnosisResult) -> MethodScore:
    matches = design.assignment_mechanism == "threshold"
    components = {
        "Threshold-based assignment": 90 if matches else 10,
        "Data density near cutoff": 50,  # cannot be verified without actual data
    }
    overall = sum(components.values()) / len(components)
    return MethodScore(
        method="Regression Discontinuity", key="rdd",
        components=components,
        overall=overall,
        confidence=_confidence_from_score(overall),
        rationale=[Msg("rec.rdd.matches" if matches else "rec.rdd.no_match",
                       mechanism=Msg(f"opt.{design.assignment_mechanism}"))],
        main_assumption=Msg("rec.rdd.assumption"),
        main_concern=Msg("rec.rdd.concern"),
    )


def _score_matching(design: ResearchDesignInput, diag: DiagnosisResult) -> MethodScore:
    selection_on_observables = 100 - _LEVEL_TO_RISK[diag.potential_endogeneity] * 90
    components = {
        "Selection-on-observables plausibility": selection_on_observables,
        "Cross-sectional applicability": 80 if design.data_structure in ("cross_section", "survey") else 50,
    }
    overall = sum(components.values()) / len(components)
    return MethodScore(
        method="Matching / Propensity Score", key="matching",
        components=components,
        overall=overall,
        confidence=_confidence_from_score(overall),
        rationale=[Msg("rec.matching.intro")],
        main_assumption=Msg("rec.matching.assumption"),
        main_concern=Msg("rec.matching.concern"),
    )


def _score_rct(design: ResearchDesignInput, diag: DiagnosisResult) -> MethodScore:
    is_random = design.assignment_mechanism == "random"
    components = {
        "Random assignment": 98 if is_random else 2,
        "Identification": 98 if is_random else 5,
    }
    overall = sum(components.values()) / len(components)
    return MethodScore(
        method="Randomized Controlled Trial", key="rct",
        components=components,
        overall=overall,
        confidence=_confidence_from_score(overall),
        rationale=[Msg("rec.rct.declared" if is_random else "rec.rct.not_declared")],
        main_assumption=Msg("rec.rct.assumption"),
        main_concern=Msg("rec.rct.concern"),
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
