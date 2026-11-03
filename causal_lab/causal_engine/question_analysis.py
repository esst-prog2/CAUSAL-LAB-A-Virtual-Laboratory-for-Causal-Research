"""
Research Question Analysis: the first step of CAUSAL LAB, before any method.

The recommendation must follow from the substance of the research question,
not from superficial features of the design (a panel, a policy). This module
reads the question and lays out its causal structure, element by element:

    treatment      what is changed or received
    outcome        what the effect is measured on
    population     for whom
    comparison     against what the treated are compared
    estimand       which causal quantity the question asks for
    assignment     how treatment was assigned
    data           what is observed, and when
    confounding    what could make treated and untreated differ anyway

Each element is labelled with how it is known:

    stated     the question says it, and the words are quoted;
    inferred   it follows from what the question says, and the reasoning is given;
    unknown    the question does not say, and a targeted follow-up question is asked.

The analysis is deterministic and local (no data leave the machine): the
wording is matched against explicit English and French patterns, so every
conclusion can be traced to the words that produced it. A wording the patterns
do not recognise is reported as unknown and asked about, never guessed.

When essential elements are missing (the question is not causal, the treatment
or the outcome cannot be identified, or nothing says how treatment was
assigned), the recommendation engine holds back its ranking and the follow-up
questions come first.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from utils.i18n import Msg

STATED, INFERRED, UNKNOWN = "stated", "inferred", "unknown"
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
    status: str                       # stated | inferred | unknown
    text: str | Msg = ""              # quoted words (stated) or the inference (inferred)


@dataclass
class QuestionAnalysis:
    question: str
    causal: bool
    elements: dict[str, Element]
    inferred: dict = field(default_factory=dict)     # ResearchDesignInput field -> value the question implies
    strong: set = field(default_factory=set)         # inferred fields the wording makes unambiguous
    follow_up: list[Msg] = field(default_factory=list)
    blocking: list[Msg] = field(default_factory=list)   # why no method can be ranked yet

    def status(self, name: str) -> str:
        return self.elements[name].status


# --------------------------------------------------------------------------
# Treatment, outcome and population: "effect of X on Y among Z" and variants
# --------------------------------------------------------------------------
_HARD_STOPS = r"\?|\.(?:\s|$)|;|,?\s+(?:compared|comparing|relative to|versus|vs\.?|using|given|when|whereby|including|" \
              r"across|vary|varies|differ|differs|par rapport|en utilisant|compar|lorsque|quand|varie|gr[âa]ce [àa])\b"
_POPULATION = r"\s+(?:among|for|in|within|chez|parmi|pour|dans|aupr[èe]s d(?:es|u|e la|e l'))\s+"
_STRONG_POPULATION = re.compile(r"^\s*(?:among|within|chez|parmi|aupr[èe]s)", re.I)
# After a weak preposition (for, in, pour, dans) the words are a population only if
# they name people, units or a place: "admissions for heart attacks" is an outcome.
_POPULATION_NOUN = re.compile(
    r"^(?:the\s+|les?\s+|la\s+|l')?(?:[A-ZÉ]|(?:[\w'-]+\s+){0,3}(?:students?|pupils?|children|kids|women|men|"
    r"workers|employees|people|persons|individuals|households|families|firms|companies|patients|adults|youths?|"
    r"graders|voters|candidates|countries|states|regions|cities|municipalities|districts|schools|villages|"
    r"teenagers|[ée]l[èe]ves|[ée]tudiants|enfants|femmes|hommes|travailleurs|salari[ée]s|personnes|m[ée]nages|"
    r"familles|entreprises|jeunes|pays|[ée]tats|r[ée]gions|villes|communes|[ée]coles)\b)")
_EFFECT_EN = re.compile(r"\b(?:causal\s+)?(?:effects?|impacts?|consequences?|influence)\s+(?:of|from)\s+(?P<rest>.+)",
                        re.I | re.S)
_EFFECT_FR = re.compile(r"\b(?:effets?|impacts?|cons[ée]quences?|influence)\s+(?:causal\s+)?(?:de la|de l'|du|des|de|d')\s*"
                        r"(?P<rest>.+)", re.I | re.S)
_VERB = (r"affects?|affected|increases?|increased|reduces?|reduced|raises?|raised|lowers?|lowered|improves?|improved|"
         r"decreases?|decreased|causes?|caused|changes?|changed|boosts?|boosted|hurts?|harms?|harmed|worsens?|worsened")
_DOES = re.compile(rf"\b(?:does|did|do|can|could|will|would|how does|how did|how do)\s+(?P<t>.+?)\s+(?:{_VERB}|affect|"
                   rf"increase|reduce|raise|lower|improve|decrease|cause|change|boost|hurt|harm|worsen)\s+(?P<rest>.+)",
                   re.I | re.S)
_DOES_FR = re.compile(r"\b(?P<t>(?:la|le|les|l'|un|une)\s.+?)\s+(?:a-t-il|a-t-elle|ont-ils|ont-elles|"
                      r"augmente-t-il|augmente-t-elle|r[ée]duit-il|r[ée]duit-elle|affecte-t-il|affecte-t-elle)\s+"
                      r"(?:(?:un effet|une influence|augment[ée]|r[ée]duit|am[ée]lior[ée]|diminu[ée])\s+(?:sur\s+)?)?"
                      r"(?P<rest>.+)", re.I | re.S)
_COST = re.compile(r"\b(?P<o>(?:[\w-]+\s+)?costs?)\s+of\s+(?P<rest>.+)", re.I | re.S)
_PREDICT = re.compile(r"\b(?:what|which)\s+(?:[\w-]+\s+)?(?:factors|characteristics|variables)\s+(?:predict|explain|are associated with|"
                      r"influence)\s+(?P<o>.+?)(?:\?|$)", re.I | re.S)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" ,;:.?!\"'«»").strip()


def _cut(text: str, pattern: str) -> tuple[str, str]:
    m = re.search(pattern, text, re.I)
    return (text[:m.start()], text[m.end():]) if m else (text, "")


def _split_on(rest: str, word: str) -> tuple[str, str] | None:
    """Treatment and the text after it: the last `word` before the first hard stop."""
    head, _ = _cut(rest, _HARD_STOPS)
    positions = [m.start() for m in re.finditer(rf"\s{word}\s", head, re.I)]
    if not positions:
        return None
    pos = positions[-1]
    return head[:pos], rest[pos + len(word) + 2:]


def _outcome_and_population(after: str) -> tuple[str, str]:
    after, _ = _cut(after, _HARD_STOPS)
    for m in re.finditer(_POPULATION, after, re.I):
        rest = after[m.end():]
        if _STRONG_POPULATION.match(m.group(0)) or _POPULATION_NOUN.match(rest):
            outcome, _ = _cut(after[:m.start()], r",")
            return _clean(outcome), _clean(rest)
    outcome, _ = _cut(after, r",")
    return _clean(outcome), ""


def _parse(question: str) -> tuple[str, str, str]:
    """(treatment, outcome, population) quoted from the question; '' when not found."""
    for pattern, word in ((_EFFECT_EN, "on"), (_EFFECT_FR, "sur")):
        m = pattern.search(question)
        if m:
            split = _split_on(m.group("rest"), word)
            if split:
                treatment, after = split
                outcome, population = _outcome_and_population(after)
                return _clean(treatment), outcome, population
    m = _COST.search(question)
    if m:
        rest, _ = _cut(m.group("rest"), _HARD_STOPS)
        treatment, population = _cut(rest, _POPULATION)
        return _clean(treatment), _clean(m.group("o")), _clean(population)
    for pattern in (_DOES, _DOES_FR):
        m = pattern.search(question)
        if m:
            outcome, population = _outcome_and_population(m.group("rest"))
            return _clean(m.group("t")), outcome, population
    m = _PREDICT.search(question)
    if m:
        return "", _clean(m.group("o")), ""
    return "", "", ""


# --------------------------------------------------------------------------
# Assignment, comparison, data, estimand
# --------------------------------------------------------------------------
_PATTERNS = {
    "random_stated": r"randomi[sz]|random(ly)?\s+assign|\brcts?\b|tirage au sort|al[ée]atoirement|essai contr[ôo]l[ée]",
    "lottery": r"\blotter(y|ies)\b|loterie",
    "cutoff": r"cut-?\s?offs?\b|threshold|discontinuit|\bseuils?\b|barely (won|lost|passed|failed)|"
              r"just (above|below)|de justesse",
    "self_selection": r"\b(join|joining|joined|choos|chose|opt(ed|ing)? (in|for)|decid|enrol(l)?(ing|ed)? in|"
                      r"take[s]? up|taking up|participat|volunteer|self-select|adh[ée]r|choisi|d[ée]cid|s'inscri|"
                      r"particip)",
    "policy": r"\b(polic(y|ies)\b|reforms?\b|laws?\b|acts?\b|program(me)?s?\b|tax(es)?\b|bans?\b|mandates?\b|"
              r"regulations?\b|subsid|expansions?\b|minimum wage|proposition\b|r[ée]formes?\b|lois?\b|"
              r"interdiction|politiques?\b|subvention|construction\b)",
    "border": r"\bborders?\b|boundar|fronti[èe]re",
    "instrument": r"\binstrument|exogenous (shock|variation)|variable instrumentale|choc exog|proximity|distance to|"
                  r"quarter of birth|draft",
    "single_unit": r"nationwide|country-?wide|at the national level|[àa] l'[ée]chelle nationale|"
                   r"\b(a|one|single) (country|state|region|province|city)\b|\bun seul (pays|[ée]tat)\b",
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
    "late": r"\bcompliers?\b|\blate\b",
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


def _form_is_default(design) -> bool:
    from dataclasses import replace
    from causal_engine.diagnosis import ResearchDesignInput
    return replace(design, research_question="") == ResearchDesignInput()


def analyze(design) -> QuestionAnalysis | None:
    """Analysis of `design.research_question`; None when there is no question."""
    q = (design.research_question or "").strip()
    if not q:
        return None
    treatment, outcome, population = _parse(q)
    predictive = bool(re.search(r"\bpredict|forecast|associated with|correlat|pr[ée]di|pr[ée]voir|facteurs associ", q,
                                re.I))
    causal_words = bool(re.search(r"effect|impact|\bcaus|influence|effet|affect|\bcost", q, re.I))
    causal = bool(treatment) and not (predictive and not causal_words)
    domain = _domain(q)
    e: dict[str, Element] = {}
    inferred, strong, follow = {}, set(), []

    # Treatment, outcome, population
    e["treatment"] = Element("treatment", STATED, treatment) if treatment else Element("treatment", UNKNOWN)
    e["outcome"] = Element("outcome", STATED, outcome) if outcome else Element("outcome", UNKNOWN)
    if population:
        e["population"] = Element("population", STATED, population)
    else:
        e["population"] = Element("population", UNKNOWN)
        follow.append(Msg("qa.ask.population"))

    # Assignment: stated words first, then inferences from the wording
    if _has("random_stated", q):
        e["assignment"] = Element("assignment", STATED, _has("random_stated", q).group(0))
        inferred["assignment_mechanism"] = "random"
        strong.add("assignment_mechanism")
        follow.append(Msg("qa.ask.random"))
    elif _has("cutoff", q):
        e["assignment"] = Element("assignment", INFERRED, Msg("qa.infer.cutoff", words=_has("cutoff", q).group(0)))
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
    elif _has("self_selection", q):
        e["assignment"] = Element("assignment", INFERRED,
                                  Msg("qa.infer.self_selection", words=_has("self_selection", q).group(0)))
        inferred["assignment_mechanism"] = "self_selected"
        strong.add("assignment_mechanism")
        follow.append(Msg("qa.ask.self_selection"))
    elif _has("policy", q):
        e["assignment"] = Element("assignment", INFERRED, Msg("qa.infer.policy", words=_has("policy", q).group(0)))
        inferred["assignment_mechanism"] = "policy"
        follow.append(Msg("qa.ask.policy"))
    else:
        e["assignment"] = Element("assignment", UNKNOWN)
        follow.append(Msg("qa.ask.assignment"))
    if _has("instrument", q) and inferred.get("assignment_mechanism") != "random":
        inferred["instrument"] = "available"
        follow.append(Msg("qa.ask.instrument", words=_has("instrument", q).group(0)))
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
    mechanism = inferred.get("assignment_mechanism") if _form_is_default(design) else design.assignment_mechanism

    # Comparison
    m = _has("comparison", q)
    if m:
        e["comparison"] = Element("comparison", STATED, _clean(m.group("c")))
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

    # Data
    m = _has("time", q)
    if m:
        e["data"] = Element("data", STATED, Msg("qa.data.time", words=m.group(0)))
    else:
        e["data"] = Element("data", UNKNOWN)
        follow.append(Msg("qa.ask.data"))
    if inferred.get("treatment_timing") == "staggered":
        e["data"] = Element("data", STATED, Msg("qa.data.staggered", words=_has("staggered", q).group(0)))

    # Confounding: what could make treated and untreated differ, given the assignment
    e["confounding"] = Element("confounding", INFERRED,
                               Msg(f"qa.confounding.{mechanism or 'unknown'}", domain=Msg(f"qa.domain.{domain}")))

    # What blocks a ranking
    blocking = []
    if not causal:
        blocking.append(Msg("qa.block.not_causal"))
    elif not outcome:
        blocking.append(Msg("qa.block.no_outcome"))
    if causal and e["assignment"].status == UNKNOWN and _form_is_default(design):
        blocking.append(Msg("qa.block.no_assignment"))
    return QuestionAnalysis(question=q, causal=causal, elements=e, inferred=inferred, strong=strong,
                            follow_up=follow, blocking=blocking)
