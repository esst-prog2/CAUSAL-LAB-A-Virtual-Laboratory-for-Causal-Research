"""
Research Question Analysis: the first step of CAUSAL LAB, before any method.

The recommendation must follow from the substance of the research question,
not from superficial features of the design (a panel, a policy). This module
first decides what the question asks (causal, predictive, descriptive, or
ambiguous: see question_reading.py), then lays out its causal structure:

    treatment      what is changed or received
    outcome        what the effect is measured on
    population     for whom
    comparison     against what the treated are compared
    estimand       which causal quantity the question asks for
    assignment     how treatment was assigned
    data           what is observed, and when
    confounding    what could make treated and untreated differ anyway

Each element is labelled with how it is known:

    stated     the question says it clearly, and the words are quoted;
    inferred   it follows from what the question says, and the reasoning is given;
    uncertain  words were extracted, but the wording leaves their role in doubt:
               they are shown "to confirm", never as a fact;
    unknown    the question does not say, and a targeted follow-up question is asked.

The analysis is deterministic and local (no data leave the machine): the
wording is matched against explicit English and French patterns, so every
conclusion can be traced to the words that produced it.

The analysis is an initial methodological assessment. It reads what a question
asks; it does not prove that the effect can be identified. When essential
elements are missing, the recommendation engine holds back its ranking and the
follow-up questions come first.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace

from causal_engine.question_reading import (AMBIGUOUS, CAUSAL, DESCRIPTIVE, PREDICTIVE, THRESHOLD_ASSIGNMENT,
                                             THRESHOLD_UNCLEAR, clean, is_clear_phrase, read_question, threshold_kind)
from utils.i18n import Msg

STATED, INFERRED, UNCERTAIN, UNKNOWN = "stated", "inferred", "uncertain", "unknown"
# The methods that estimate each estimand the analysis can infer: a method outside the
# set answers a different question from the one asked.
ESTIMAND_METHODS = {
    "qa.estimand.local": {"rdd"},
    "qa.estimand.unit": {"synthetic_control", "its"},
    "qa.estimand.late_iv": {"iv"},
    "qa.estimand.late": {"iv", "rdd"},
    "qa.estimand.ate_random": {"rct", "matching"},
}
ELEMENTS = ("treatment", "outcome", "population", "comparison", "estimand", "assignment", "data", "confounding")


@dataclass
class Element:
    name: str
    status: str                       # stated | inferred | uncertain | unknown
    text: str | Msg = ""              # quoted words (stated, uncertain) or the inference (inferred)


@dataclass
class QuestionAnalysis:
    question: str
    intent: str                       # causal | predictive | descriptive | ambiguous
    intent_words: str
    causal_confirmed: bool            # the researcher declared the causal aim the wording leaves open
    elements: dict[str, Element]
    threshold: str | None = None      # assignment | unclear | ordinary
    inferred: dict = field(default_factory=dict)     # ResearchDesignInput field -> value the question implies
    strong: set = field(default_factory=set)         # inferred fields the wording makes unambiguous
    follow_up: list[Msg] = field(default_factory=list)
    blocking: list[Msg] = field(default_factory=list)   # why no method can be ranked yet

    @property
    def causal(self) -> bool:
        return self.intent == CAUSAL or self.causal_confirmed

    def status(self, name: str) -> str:
        return self.elements[name].status

    def intent_messages(self) -> list[Msg]:
        """What the question asks, the words that say so, and the researcher's own statement."""
        messages = [Msg(f"qa.intent.{self.intent}")]
        if self.intent_words:
            messages.append(Msg("qa.intent_words", words=self.intent_words.replace("|", "/")))
        if self.causal_confirmed and self.intent != CAUSAL:
            messages.append(Msg("qa.intent_confirmed"))
        return messages


# --------------------------------------------------------------------------
# Assignment, comparison, data, estimand
# --------------------------------------------------------------------------
_PATTERNS = {
    "random_stated": r"randomi[sz]|random(ly)?\s+assign|\brcts?\b|tirage au sort|al[ée]atoirement|essai contr[ôo]l[ée]",
    # An experiment implies a controlled assignment, but "natural" and "quasi" ones do not.
    "experiment": r"(?<!natural )(?<!quasi-)(?<!quasi )(?<!thought )\bexperiments?\b|\bexp[ée]rimentation\b",
    "lottery": r"\blotter(y|ies)\b|loterie",
    "self_selection": r"\b(join|joining|joined|choos|chose|opt(ed|ing)? (in|for)|decid(e|es|ed|ing) to|"
                      r"enrol(l)?(ing|ed)? in|take[s]? up|taking up|participat|volunteer|self-select|adh[ée]r|choisi|"
                      r"d[ée]cid(e|ent|[ée]) de|s'inscri|particip)",
    "policy": r"\b(polic(y|ies)\b|reforms?\b|laws?\b|acts?\b|program(me)?s?\b|tax(es)?\b|bans?\b|mandates?\b|"
              r"regulations?\b|subsid|expansions?\b|minimum wage|proposition\b|r[ée]formes?\b|lois?\b|"
              r"interdiction|politiques?\b|subvention|construction\b)",
    "border": r"\bborders?\b|boundar|fronti[èe]re",
    "instrument": r"\binstrument|exogenous (shock|variation)|variable instrumentale|choc exog|proximity|distance to|"
                  r"quarter of birth|draft",
    "single_unit": r"nationwide|country-?wide|at the national level|[àa] l'[ée]chelle nationale|"
                   r"\b(one|single) (country|state|region|province|city)\b|\bun seul (pays|[ée]tat)\b",
    "named_region": r"\b(california|basque country|texas|scotland|catalonia|quebec|bavaria|lombardy)\b",
    "staggered": r"stagger|roll-?out|phased[ -]in|in different years|at different (dates|times)|[ée]chelonn|"
                 r"d[ée]ploiement progressif|adopted in different",
    "comparison": r"\b(compared (with|to)|relative to|versus|vs\.?|against|par rapport [àa]|compar[ée]s? [àa])\s+"
                  r"(?P<c>[^,?.;]+)",
    "time": r"\b(19|20)\d{2}\b|before and after|over time|long[- ]run|long[- ]term|years after|trend|"
            r"avant et apr[èe]s|dans le temps|[àa] long terme",
    "att": r"on the treated|for (participants|those who (received|took|were))|among (participants|recipients|"
           r"beneficiaries)|sur les trait[ée]s|pour les b[ée]n[ée]ficiaires",
    "ate": r"average (treatment )?effect|for (everyone|the (whole|entire) population)|effet moyen",
    "late": r"\bcompliers?\b|(?-i:\bLATE\b)",
}


def _has(key: str, text: str) -> re.Match | None:
    return re.search(_PATTERNS[key], text, re.I)


_DOMAINS = (
    ("education", r"school|student|scholarship|education|university|college|class size|test score|enrol|"
                  r"[ée]l[èe]ve|[ée]tudiant|[ée]cole|bourse|universit|scolai"),
    ("labour", r"earning|wage|employment|job|training|labou?r|salaire|emploi|revenu|formation"),
    ("health", r"health|mortality|hospital|disease|medicaid|insurance|smok|cigarette|heart|deworm|"
               r"sant[ée]|mortalit|h[ôo]pital|maladie|tabac"),
    ("politics", r"election|vote|incumben|candidate|[ée]lection|candidat"),
    ("places", r"state|region|country|province|city|municipal|district|r[ée]gion|pays|commune|ville"),
    ("firms", r"\bfirms?\b|compan|business|entreprise"),
)


def _domain(text: str) -> str:
    return next((name for name, pattern in _DOMAINS if re.search(pattern, text, re.I)), "generic")


def form_is_default(design) -> bool:
    """No answer of the form has been given or confirmed: it says nothing about the study."""
    from causal_engine.diagnosis import ResearchDesignInput
    if design.answers_confirmed:
        return False
    return replace(design, research_question="", causal_confirmed=False) == ResearchDesignInput()


def _quoted(name: str, words: str, certain: bool) -> Element:
    """Words taken from the question: stated only when the grammar leaves no doubt."""
    if not words:
        return Element(name, UNKNOWN)
    return Element(name, STATED if certain and is_clear_phrase(words) else UNCERTAIN, words)


def _not_causal_analysis(q: str, reading, threshold: str | None) -> QuestionAnalysis:
    """A question that explicitly predicts or describes: no causal structure to lay out."""
    e = {name: Element(name, UNKNOWN) for name in ELEMENTS}
    if reading.outcome:
        e["outcome"] = Element("outcome", UNCERTAIN, reading.outcome)
    return QuestionAnalysis(question=q, intent=reading.intent, intent_words=reading.evidence, causal_confirmed=False,
                            elements=e, threshold=threshold, follow_up=[Msg("qa.ask.rephrase")],
                            blocking=[Msg(f"qa.block.{reading.intent}")])


def analyze(design) -> QuestionAnalysis | None:
    """Analysis of `design.research_question`; None when there is no question."""
    q = (design.research_question or "").strip()
    if not q:
        return None
    reading = read_question(q)
    threshold, threshold_words = threshold_kind(q)
    confirmed = bool(design.causal_confirmed)
    if reading.intent in (PREDICTIVE, DESCRIPTIVE) and not confirmed:
        return _not_causal_analysis(q, reading, threshold)
    treatment, outcome, population = reading.treatment, reading.outcome, reading.population
    domain = _domain(q)
    # How treatment was assigned is read from the treatment, when it can be told apart:
    # "the effect of a tax credit on labour force participation" is not self-selection,
    # and "the effect of schooling on tax compliance" is not a tax policy.
    about_treatment = treatment or q
    e: dict[str, Element] = {}
    inferred, strong, follow = {}, set(), []
    if reading.intent == AMBIGUOUS and not confirmed:
        follow.append(Msg("qa.ask.intent"))

    # Treatment, outcome, population
    e["treatment"] = _quoted("treatment", treatment, reading.certain)
    e["outcome"] = _quoted("outcome", outcome, reading.certain)
    if UNCERTAIN in (e["treatment"].status, e["outcome"].status):
        follow.append(Msg("qa.ask.confirm_reading"))
    if population:
        e["population"] = Element("population", STATED if reading.certain else UNCERTAIN, population)
    else:
        e["population"] = Element("population", UNKNOWN)
        follow.append(Msg("qa.ask.population"))

    # Assignment: stated words first, then inferences from the wording
    if _has("random_stated", q):
        e["assignment"] = Element("assignment", STATED, _has("random_stated", q).group(0))
        inferred["assignment_mechanism"] = "random"
        strong.add("assignment_mechanism")
        follow.append(Msg("qa.ask.random"))
    elif _has("experiment", q):
        e["assignment"] = Element("assignment", INFERRED, Msg("qa.infer.experiment", words=_has("experiment", q).group(0)))
        inferred["assignment_mechanism"] = "random"
        follow.append(Msg("qa.ask.random"))
    elif threshold == THRESHOLD_ASSIGNMENT:
        e["assignment"] = Element("assignment", INFERRED, Msg("qa.infer.cutoff", words=threshold_words))
        inferred["assignment_mechanism"] = "threshold"
        strong.add("assignment_mechanism")
        follow.append(Msg("qa.ask.cutoff"))
    elif _has("lottery", treatment):          # winning the lottery is itself the treatment
        e["assignment"] = Element("assignment", INFERRED, Msg("qa.infer.lottery", words=_has("lottery", q).group(0)))
        inferred["assignment_mechanism"] = "random"
        follow.append(Msg("qa.ask.lottery"))
    elif _has("border", q) and _has("policy", q) is None and _has("self_selection", q) is None:
        e["assignment"] = Element("assignment", INFERRED, Msg("qa.infer.border", words=_has("border", q).group(0)))
        inferred["assignment_mechanism"] = "geographic"
        follow.append(Msg("qa.ask.border"))
    elif _has("self_selection", about_treatment):
        e["assignment"] = Element("assignment", INFERRED,
                                  Msg("qa.infer.self_selection", words=_has("self_selection", about_treatment).group(0)))
        inferred["assignment_mechanism"] = "self_selected"
        strong.add("assignment_mechanism")
        follow.append(Msg("qa.ask.self_selection"))
    elif _has("policy", about_treatment):
        e["assignment"] = Element("assignment", INFERRED, Msg("qa.infer.policy", words=_has("policy", about_treatment).group(0)))
        inferred["assignment_mechanism"] = "policy"
        follow.append(Msg("qa.ask.policy"))
    else:
        e["assignment"] = Element("assignment", UNKNOWN)
        follow.append(Msg("qa.ask.assignment"))
    if threshold == THRESHOLD_UNCLEAR:
        follow.insert(0, Msg("qa.ask.threshold_role", words=threshold_words))
    # A distance or a draft is an instrument only as a source of variation, not as the treatment itself.
    outside_treatment = q.replace(treatment, " ") if treatment else q
    instrument = _has("instrument", outside_treatment)
    if instrument and inferred.get("assignment_mechanism") != "random":
        inferred["instrument"] = "available"
        follow.append(Msg("qa.ask.instrument", words=instrument.group(0)))
    if _has("lottery", q) and not _has("lottery", treatment):
        inferred["instrument"] = "available"       # a lottery that shifts the chance of treatment (Angrist 1990)
        follow.append(Msg("qa.ask.lottery_instrument"))
    if _has("single_unit", q) or _has("named_region", q):
        inferred["n_treated_units"] = "one"
        follow.append(Msg("qa.ask.single_unit"))
    if _has("staggered", q):
        inferred["treatment_timing"] = "staggered"
    # The estimand and the confounders depend on the assignment: the form's answer when
    # the researcher has filled it in, otherwise what the question implies.
    default_form = form_is_default(design)
    mechanism = inferred.get("assignment_mechanism") if default_form else design.assignment_mechanism

    # Comparison
    m = _has("comparison", q)
    if m:
        e["comparison"] = Element("comparison", STATED, clean(m.group("c")))
    elif mechanism:
        e["comparison"] = Element("comparison", INFERRED, Msg(f"qa.comparison.{mechanism}"))
    else:
        e["comparison"] = Element("comparison", UNKNOWN)
        follow.append(Msg("qa.ask.comparison"))

    # Estimand
    for key in ("late", "att", "ate"):
        m = _has(key, q)
        if m:
            e["estimand"] = Element("estimand", STATED, Msg(f"qa.estimand.{key}", words=m.group(0)))
            break
    else:
        if mechanism == "threshold":
            e["estimand"] = Element("estimand", INFERRED, Msg("qa.estimand.local"))
        elif inferred.get("n_treated_units") == "one":
            e["estimand"] = Element("estimand", INFERRED, Msg("qa.estimand.unit"))
        elif mechanism == "random":
            e["estimand"] = Element("estimand", INFERRED, Msg("qa.estimand.ate_random"))
        elif inferred.get("instrument") == "available":
            e["estimand"] = Element("estimand", INFERRED, Msg("qa.estimand.late_iv"))
        elif mechanism in ("policy", "geographic", "self_selected"):
            e["estimand"] = Element("estimand", INFERRED, Msg("qa.estimand.att_policy"))
        else:
            e["estimand"] = Element("estimand", UNKNOWN)
            follow.append(Msg("qa.ask.estimand"))

    # Data: a reference to time implies observations over time; it does not state what is observed.
    m = _has("time", q)
    if m:
        e["data"] = Element("data", INFERRED, Msg("qa.data.time", words=m.group(0)))
    else:
        e["data"] = Element("data", UNKNOWN)
        follow.append(Msg("qa.ask.data"))
    if inferred.get("treatment_timing") == "staggered":
        e["data"] = Element("data", STATED, Msg("qa.data.staggered", words=_has("staggered", q).group(0)))

    # Confounding: what could make treated and untreated differ, given the assignment
    e["confounding"] = Element("confounding", INFERRED if mechanism else UNKNOWN,
                               Msg(f"qa.confounding.{mechanism or 'unknown'}", domain=Msg(f"qa.domain.{domain}")))

    # What blocks a ranking. The researcher's confirmation overrides the reading of the
    # words, never the conditions of the methods, which the recommendation engine checks.
    blocking = []
    if reading.intent == AMBIGUOUS and not confirmed:
        blocking.append(Msg("qa.block.ambiguous"))
    elif not confirmed:
        if not treatment:
            blocking.append(Msg("qa.block.no_treatment"))
        if not outcome:
            blocking.append(Msg("qa.block.no_outcome"))
    if default_form:
        blocking.append(Msg("qa.block.no_assignment" if e["assignment"].status == UNKNOWN else "qa.block.default_form"))
    return QuestionAnalysis(question=q, intent=reading.intent, intent_words=reading.evidence, causal_confirmed=confirmed,
                            elements=e, threshold=threshold, inferred=inferred, strong=strong, follow_up=follow,
                            blocking=blocking)
