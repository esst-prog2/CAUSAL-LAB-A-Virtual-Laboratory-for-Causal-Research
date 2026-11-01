"""
Method Recommendation Engine (CAUSAL LAB spec, Section 11-13).

Recommends the most credible and feasible causal design for the research
question, not the most familiar one. No method is a default: each one is
first checked against the conditions without which it does not identify a
causal effect, and only the methods whose conditions hold are scored.

1. Gate. Each method's necessary conditions are checked against the
   structured design input:

     RCT                 treatment randomly assigned
     RDD                 a real assignment or eligibility cutoff
     IV                  an instrument the researcher can defend
     DiD / event study   treated and untreated units, observed before and
                         after (an event study needs >= 2 pre-periods)
     Synthetic control   one or a few treated units, a donor pool, and
                         enough pre-treatment periods to judge the fit (>= 5)
     ITS                 a long enough series before and after treatment
     Matching / adjust.  all important confounders measured

   A method is "supported", "needs_info" (a condition the researcher
   answered "not sure" about) or "not_supported" (a condition fails), with
   the reasons.

2. Score. Supported methods get a transparent score, the mean of:
     design credibility       how strong the identifying assumption is when
                              its conditions hold (randomisation > cutoff >
                              comparison over time > instrument > ...);
     assumption plausibility  how this design's diagnosed threats
                              (confounding, endogeneity, spillovers) weaken it;
     data adequacy            whether the data are rich enough to check it.

   The score is NOT ground truth (spec Section 12). If no method is
   supported, the engine says so and lists what would make one credible.

Explanations are translatable `Msg` objects (locale keys rec.*);
`str()` of each gives the English text.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from causal_engine.diagnosis import DiagnosisResult, Level, ResearchDesignInput
from utils.i18n import Msg

_LEVEL_TO_RISK = {Level.LOW: 0.15, Level.MEDIUM: 0.5, Level.HIGH: 0.9, Level.UNKNOWN: 0.5}

SUPPORTED, NEEDS_INFO, NOT_SUPPORTED = "supported", "needs_info", "not_supported"
STATUSES = (SUPPORTED, NEEDS_INFO, NOT_SUPPORTED)

# Data in which the same units (or groups) are observed before and after treatment.
LONGITUDINAL = ("panel", "repeated_cross_section", "spatio_temporal_panel", "administrative", "time_series")
UNIT_PANELS = ("panel", "spatio_temporal_panel", "administrative")
MIN_PRE_SYNTHETIC = 5          # pre-treatment periods needed to judge a synthetic control's fit
MIN_PRE_ITS = 3                # pre-treatment points needed to estimate an underlying trend

# How strong each identifying assumption is when its conditions hold.
_CREDIBILITY = {"rct": 98, "rdd": 88, "did": 75, "event_study": 75, "synthetic_control": 75, "iv": 70,
                "its": 55, "matching": 50}


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
    status: str = SUPPORTED
    unmet: list[Msg] = field(default_factory=list)   # failed or unconfirmed conditions

    @property
    def supported(self) -> bool:
        return self.status == SUPPORTED


def _confidence_from_score(score: float) -> str:
    if score >= 75:
        return "HIGH"
    if score >= 50:
        return "MEDIUM"
    return "LOW"


def _pre(design: ResearchDesignInput) -> int:
    return design.n_pre_periods if design.has_pre_treatment_periods else 0


def _risk(level: Level, weight: float) -> float:
    return 100 - _LEVEL_TO_RISK[level] * weight


# --------------------------------------------------------------------------
# Gates: the conditions without which a method does not identify the effect
# --------------------------------------------------------------------------
def _gates(key: str, d: ResearchDesignInput) -> tuple[list[Msg], list[Msg]]:
    """(failed conditions, unconfirmed conditions) of method `key`."""
    failed, unsure = [], []
    pre = _pre(d)
    if key == "rct":
        if d.assignment_mechanism != "random":
            failed.append(Msg("rec.gate.not_random"))
    elif key == "rdd":
        if d.assignment_mechanism != "threshold":
            failed.append(Msg("rec.gate.no_cutoff"))
    elif key == "iv":
        if d.instrument == "none":
            failed.append(Msg("rec.gate.no_instrument"))
        elif d.instrument == "unsure":
            unsure.append(Msg("rec.gate.instrument_unsure"))
    elif key in ("did", "event_study"):
        if not d.has_control_group:
            failed.append(Msg("rec.gate.no_control_group"))
        if d.data_structure not in LONGITUDINAL or d.data_structure == "time_series":
            failed.append(Msg("rec.gate.not_before_after"))
        if pre < 1 or d.n_post_periods < 1:
            failed.append(Msg("rec.gate.no_pre_post"))
        elif key == "event_study" and pre < 2:
            failed.append(Msg("rec.gate.event_study_pre"))
    elif key == "synthetic_control":
        if d.n_treated_units == "many":
            failed.append(Msg("rec.gate.many_treated"))
        if not d.has_control_group or d.data_structure not in UNIT_PANELS:
            failed.append(Msg("rec.gate.no_donor_panel"))
        if pre < MIN_PRE_SYNTHETIC:
            failed.append(Msg("rec.gate.synthetic_pre", n=MIN_PRE_SYNTHETIC))
    elif key == "its":
        if d.data_structure not in LONGITUDINAL:
            failed.append(Msg("rec.gate.not_before_after"))
        if pre < MIN_PRE_ITS or d.n_post_periods < 1:
            failed.append(Msg("rec.gate.its_pre", n=MIN_PRE_ITS))
    elif key == "matching":
        if d.confounders_observed == "not_measured":
            failed.append(Msg("rec.gate.confounders_unmeasured"))
        elif d.confounders_observed == "unsure" and d.assignment_mechanism != "random":
            unsure.append(Msg("rec.gate.confounders_unsure"))
    return failed, unsure


# --------------------------------------------------------------------------
# Scores of the methods whose conditions hold
# --------------------------------------------------------------------------
def _components(key: str, d: ResearchDesignInput, diag: DiagnosisResult) -> dict:
    pre = _pre(d)
    spill = diag.potential_spillovers
    if key == "rct":
        plausibility = _risk(spill, 30)
        data = 90
    elif key == "rdd":
        plausibility = 85                       # treatment set by a known rule; manipulation still to be checked
        data = 80                               # the running variable is recorded; density near the cutoff is not yet known
    elif key == "iv":
        plausibility = 60                       # the exclusion restriction is untestable
        data = 65
    elif key in ("did", "event_study"):
        plausibility = (_risk(diag.potential_confounding, 60) + _risk(spill, 40)) / 2   # parallel trends are untestable
        if d.n_treated_units == "one":
            plausibility -= 15                  # inference with one treated unit is fragile
        data = 90 if pre >= (3 if key == "did" else 4) else 65
        if key == "event_study":
            data -= 1                           # the dynamic version of the same design: ranked just after DiD
    elif key == "synthetic_control":
        plausibility = _risk(spill, 40)
        data = 90 if pre >= 10 else 70
    elif key == "its":
        plausibility = 55 if d.has_control_group else 65   # with a control group a comparative design is better
        plausibility -= 20 if diag.potential_confounding == Level.HIGH else 0
        data = 85 if pre >= 8 else 60
    else:                                       # matching / regression adjustment
        plausibility = 85 if d.assignment_mechanism == "random" else _risk(diag.potential_endogeneity, 70)
        plausibility = min(plausibility, _risk(spill, 40))
        data = 80 if d.data_structure in ("cross_section", "survey", "experimental", "administrative") else 65
    return {"Design credibility": _CREDIBILITY[key], "Assumption plausibility": round(plausibility),
            "Data adequacy": data}


def _rationale(key: str, d: ResearchDesignInput, diag: DiagnosisResult) -> list[Msg]:
    notes = [Msg(f"rec.{key}.intro")]
    if key in ("did", "event_study") and d.treatment_timing == "staggered":
        notes.append(Msg("rec.did.staggered"))
    if key in ("did", "event_study") and d.n_treated_units == "one":
        notes.append(Msg("rec.did.one_treated"))
    if key in ("did", "event_study", "matching") and d.treatment_type == "continuous":
        notes.append(Msg("rec.note.continuous_treatment"))
    if key in ("did", "event_study", "synthetic_control", "matching") and diag.potential_spillovers == Level.HIGH:
        notes.append(Msg("rec.note.spillovers"))
    if key == "its" and d.has_control_group:
        notes.append(Msg("rec.its.has_controls"))
    if key == "matching" and d.assignment_mechanism == "random":
        notes.append(Msg("rec.matching.random"))
    return notes


_METHODS = {
    "rct": "Randomized Controlled Trial",
    "rdd": "Regression Discontinuity",
    "did": "Difference-in-Differences",
    "event_study": "Event Study",
    "synthetic_control": "Synthetic Control",
    "iv": "Instrumental Variables",
    "its": "Interrupted Time Series",
    "matching": "Matching / Propensity Score",
}
METHOD_KEYS = tuple(_METHODS)


def _score(key: str, d: ResearchDesignInput, diag: DiagnosisResult) -> MethodScore:
    failed, unsure = _gates(key, d)
    status = NOT_SUPPORTED if failed else NEEDS_INFO if unsure else SUPPORTED
    components = _components(key, d, diag) if status != NOT_SUPPORTED else {}
    overall = sum(components.values()) / len(components) if components else 0.0
    if key == "did":
        concern = "rec.did.concern_spillovers" if diag.potential_spillovers == Level.HIGH else "rec.did.concern_pretrends"
    else:
        concern = f"rec.{key}.concern"
    return MethodScore(
        method=_METHODS[key], key=key, components=components, overall=overall,
        confidence=_confidence_from_score(overall) if status == SUPPORTED else "LOW",
        rationale=_rationale(key, d, diag) if status != NOT_SUPPORTED else [],
        main_assumption=Msg(f"rec.{key}.assumption"), main_concern=Msg(concern),
        status=status, unmet=failed + unsure,
    )


def recommend(design: ResearchDesignInput, diag: DiagnosisResult) -> list[MethodScore]:
    """Every candidate method: first those whose conditions hold, ranked by
    score; then those that need information; then those ruled out."""
    scores = [_score(key, design, diag) for key in _METHODS]
    order = {status: i for i, status in enumerate(STATUSES)}
    scores.sort(key=lambda s: (order[s.status], -s.overall))
    return scores


def recommended(scores: list[MethodScore]) -> MethodScore | None:
    """The recommended method, or None when no credible design is supported."""
    return scores[0] if scores and scores[0].supported else None
