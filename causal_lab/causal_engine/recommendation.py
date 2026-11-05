"""
Method Recommendation Engine (CAUSAL LAB spec, Section 11-13).

Recommends the most credible and feasible causal design for the research
question, not the most familiar one. No method is a default: each one is
first checked against the conditions without which it does not identify a
causal effect, and only the methods whose conditions hold are ordered.

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
   the reasons. If no method is supported, the engine says so and lists what
   would make one credible.

2. Order. Supported methods are put in an argued order (`_rank`), not given a
   number: a design whose identifying assumption is created by the assignment
   comes before one whose assumption concerns an unobserved counterfactual,
   which comes before one that relies on measuring every confounder. No number
   is attached, because none has been established empirically. The order holds
   only under the stated conditions and concerns internal validity: each method
   carries its own arguments (`rec.<method>.internal`, `.external`, `.rank`).
   No method is superior in every research context.

Explanations are translatable `Msg` objects (locale keys rec.*);
`str()` of each gives the English text.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from causal_engine.diagnosis import DiagnosisResult, Level, ResearchDesignInput
from causal_engine.question_reading import AMBIGUOUS, DESCRIPTIVE, PREDICTIVE
from utils.i18n import Msg

SUPPORTED, NEEDS_INFO, NOT_SUPPORTED = "supported", "needs_info", "not_supported"
STATUSES = (SUPPORTED, NEEDS_INFO, NOT_SUPPORTED)

# Data in which the same units (or groups) are observed before and after treatment.
LONGITUDINAL = ("panel", "repeated_cross_section", "spatio_temporal_panel", "administrative", "time_series")
UNIT_PANELS = ("panel", "spatio_temporal_panel", "administrative")
MIN_PRE_SYNTHETIC = 5          # pre-treatment periods needed to judge a synthetic control's fit
MIN_PRE_ITS = 3                # pre-treatment points needed to estimate an underlying trend

# The order of the supported methods, strongest identification argument first; see `_rank`.
_ORDER = ("rct", "rdd", "did", "event_study", "synthetic_control", "iv", "its", "matching")
SYNTHETIC_BEFORE_DID_PRE = 10  # with a few treated units, this many pre-periods let a synthetic control's fit be judged


@dataclass
class MethodAssessment:
    method: str
    key: str = ""                                     # locale key suffix: method.<key>
    rationale: list[Msg] = field(default_factory=list)
    main_assumption: Msg | str = ""
    main_concern: Msg | str = ""
    status: str = SUPPORTED
    unmet: list[Msg] = field(default_factory=list)   # failed or unconfirmed conditions

    @property
    def supported(self) -> bool:
        return self.status == SUPPORTED


def _pre(design: ResearchDesignInput) -> int:
    return design.n_pre_periods if design.has_pre_treatment_periods else 0


# --------------------------------------------------------------------------
# Gates: the conditions without which a method does not identify the effect
# --------------------------------------------------------------------------
def _geographic_cutoff(d: ResearchDesignInput, diag: DiagnosisResult) -> bool:
    """Treatment assigned by a geographic boundary: a regression discontinuity in
    distance to the border (Keele & Titiunik 2015; Dell 2010)."""
    return d.assignment_mechanism == "geographic" and "border" in diag.question_signals


def _gates(key: str, d: ResearchDesignInput, diag: DiagnosisResult) -> tuple[list[Msg], list[Msg]]:
    """(failed conditions, unconfirmed conditions) of method `key`."""
    failed, unsure = [], []
    pre = _pre(d)
    if key == "rct":
        if d.assignment_mechanism != "random":
            failed.append(Msg("rec.gate.not_random"))
    elif key == "rdd":
        if d.assignment_mechanism != "threshold" and not _geographic_cutoff(d, diag):
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
# The order of the methods whose conditions hold
# --------------------------------------------------------------------------
def _rank(key: str, d: ResearchDesignInput) -> int:
    """Position among the supported methods; lower comes first. A qualitative order:

    - randomisation and an assignment cutoff create the comparison by design;
    - comparisons over time rest on an untestable counterfactual trend. With a single
      treated unit (or a few and a long pre-period) a synthetic control builds that
      counterfactual explicitly and its fit can be inspected, so it comes first;
    - an instrument rests on an exclusion restriction that the data cannot test;
    - a single series has no comparison group at all;
    - adjustment needs every confounder to be measured.
    """
    order = list(_ORDER)
    if d.n_treated_units == "one" or (d.n_treated_units == "few" and _pre(d) >= SYNTHETIC_BEFORE_DID_PRE):
        order.remove("synthetic_control")
        order.insert(order.index("did"), "synthetic_control")
    return order.index(key)


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
    if key == "rdd" and _geographic_cutoff(d, diag):
        notes.append(Msg("rec.rdd.geographic"))
    # What the wording of the question adds, whichever method answers it.
    signals = diag.question_signals
    if "staggered" in signals and d.treatment_timing != "staggered" and key in ("did", "event_study"):
        notes.append(Msg("rec.note.staggered_text"))
    if "dynamic" in signals and key == "did":
        notes.append(Msg("rec.note.dynamic"))
    if "dose" in signals and d.treatment_type == "binary":
        notes.append(Msg("rec.note.dose"))
    if "heterogeneity" in signals:
        notes.append(Msg("rec.note.heterogeneity"))
    if "mechanism" in signals:
        notes.append(Msg("rec.note.mechanism"))
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


def _assess(key: str, d: ResearchDesignInput, diag: DiagnosisResult) -> MethodAssessment:
    failed, unsure = _gates(key, d, diag)
    status = NOT_SUPPORTED if failed else NEEDS_INFO if unsure else SUPPORTED
    if key == "did":
        concern = "rec.did.concern_spillovers" if diag.potential_spillovers == Level.HIGH else "rec.did.concern_pretrends"
    else:
        concern = f"rec.{key}.concern"
    return MethodAssessment(
        method=_METHODS[key], key=key,
        rationale=_rationale(key, d, diag) if status != NOT_SUPPORTED else [],
        main_assumption=Msg(f"rec.{key}.assumption"), main_concern=Msg(concern),
        status=status, unmet=failed + unsure,
    )


def _ask(method: MethodAssessment, question: Msg) -> None:
    """A method the form supports, held back until the question below is answered."""
    if method.status == SUPPORTED:
        method.status = NEEDS_INFO
    if method.status == NEEDS_INFO:
        method.unmet = method.unmet + [question]


def _reopen(method: MethodAssessment, d: ResearchDesignInput, diag: DiagnosisResult, question: Msg) -> None:
    """A method the form rules out but the question points to: to be confirmed."""
    method.rationale = _rationale(method.key, d, diag)
    method.status, method.unmet = NEEDS_INFO, [question]


_NOT_CAUSAL_ASK = {PREDICTIVE: "rec.ask.predictive", DESCRIPTIVE: "rec.ask.descriptive", AMBIGUOUS: "rec.ask.intent"}


def _check_question(methods: list[MethodAssessment], d: ResearchDesignInput, diag: DiagnosisResult) -> None:
    """The form decides the method only when the wording of the question agrees
    with it. When the question describes a design the form contradicts, the
    engine asks instead of answering a different question."""
    signals = diag.question_signals
    by_key = {method.key: method for method in methods}
    analysis = diag.analysis
    if analysis is not None and not analysis.causal:
        # The question does not (yet) ask for a causal effect: no causal method answers it.
        for method in methods:
            _ask(method, Msg(_NOT_CAUSAL_ASK[analysis.intent]))
        return
    if analysis is not None and analysis.blocking:
        # Essential elements of the question are missing: ask before ranking.
        for method in methods:
            _ask(method, Msg("rec.ask.analysis"))
    if (analysis is not None and "assignment_mechanism" in analysis.strong
            and analysis.inferred["assignment_mechanism"] == "self_selected"
            and d.assignment_mechanism != "self_selected"):
        for method in methods:
            _ask(method, Msg("rec.ask.self_selection"))
    if "cutoff" in signals and d.assignment_mechanism != "threshold" and not _geographic_cutoff(d, diag):
        # The question asks for the effect at a cutoff.
        _reopen(by_key["rdd"], d, diag, Msg("rec.gate.cutoff_unconfirmed"))
        for method in methods:
            if method.key != "rdd":
                _ask(method, Msg("rec.gate.cutoff_estimand"))
    if "threshold_unclear" in signals and d.assignment_mechanism != "threshold":
        # A number that may or may not decide who is treated: ask which.
        _reopen(by_key["rdd"], d, diag, Msg("rec.gate.threshold_unclear"))
        for method in methods:
            if method.key != "rdd":
                _ask(method, Msg("rec.gate.threshold_unclear"))
    if "random" in signals and d.assignment_mechanism != "random" and d.instrument != "available":
        # A lottery or a randomisation in the question; a lottery used as an
        # instrument (declared available) is consistent with the form.
        _reopen(by_key["rct"], d, diag, Msg("rec.ask.random"))
        for method in methods:
            if method.key not in ("rct", "iv"):
                _ask(method, Msg("rec.ask.random_others"))
    if "instrument" in signals and d.instrument == "none":
        _reopen(by_key["iv"], d, diag, Msg("rec.ask.instrument"))
    if "single_unit" in signals and d.n_treated_units == "many":
        # The structure of the units itself is in doubt: every design depends on it.
        for method in methods:
            _ask(method, Msg("rec.ask.single_unit"))


def recommend(design: ResearchDesignInput, diag: DiagnosisResult) -> list[MethodAssessment]:
    """Every candidate method: first those whose conditions hold, in their argued
    order; then those that need information; then those ruled out."""
    methods = [_assess(key, design, diag) for key in _METHODS]
    _check_question(methods, design, diag)
    order = {status: i for i, status in enumerate(STATUSES)}
    methods.sort(key=lambda m: (order[m.status], _rank(m.key, design)))
    return methods


def recommended(methods: list[MethodAssessment]) -> MethodAssessment | None:
    """The recommended method, or None when no credible design is supported."""
    return methods[0] if methods and methods[0].supported else None
