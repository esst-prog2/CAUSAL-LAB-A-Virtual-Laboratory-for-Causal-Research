"""
How a research question is read: its intent, its treatment and outcome, and
whether it describes an assignment cutoff.

The reading is deterministic and local. It is built from reusable grammatical
families (a verb list with its inflections, auxiliaries, connectors), in English
and French, and every conclusion keeps the words that produced it. Four intents
are distinguished:

    causal       the question explicitly asks what a change does to an outcome
    predictive   it explicitly asks to predict or forecast
    descriptive  it explicitly asks how much, how many, or what happened over time
    ambiguous    anything else: an association, a comparison of groups, an
                 unrecognised wording. The reader abstains and asks.

A question is never called non-causal because a pattern failed to match: only
explicit predictive or descriptive wording does that. Causal *intent* is not
causal *identification*: the wording says what is asked, not whether the data
can answer it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

CAUSAL, PREDICTIVE, DESCRIPTIVE, AMBIGUOUS = "causal", "predictive", "descriptive", "ambiguous"
THRESHOLD_ASSIGNMENT, THRESHOLD_UNCLEAR, THRESHOLD_ORDINARY = "assignment", "unclear", "ordinary"


@dataclass(frozen=True)
class Reading:
    intent: str
    evidence: str = ""                # the words that decided the intent
    treatment: str = ""
    outcome: str = ""
    population: str = ""
    certain: bool = True              # the grammar was clear enough to quote treatment and outcome as stated


# --------------------------------------------------------------------------
# Verbs and their forms
# --------------------------------------------------------------------------
_IRREGULAR = {"make": ("makes", "made", "making"), "lead": ("leads", "led", "leading"),
              "drive": ("drives", "drove|driven", "driving"), "cut": ("cuts", "cut", "cutting"),
              "hurt": ("hurts", "hurt", "hurting"), "spur": ("spurs", "spurred", "spurring"),
              "shift": ("shifts", "shifted", "shifting"), "lift": ("lifts", "lifted", "lifting")}
# Verbs that take the outcome as their object (or a fixed preposition).
_CAUSAL_VERBS = ("affect", "alter", "benefit", "boost", "cause", "change", "close", "contribute to", "create",
                 "crowd out", "curb", "cut", "decrease", "destroy", "deter", "diminish", "discourage", "drive",
                 "encourage", "enhance", "foster", "harm", "help", "hinder", "hurt", "impact", "improve", "increase",
                 "induce", "influence", "kill", "lead to", "lessen", "lift", "lower", "make", "matter for", "matter to",
                 "matter in", "mitigate", "narrow", "prevent", "promote", "raise", "reduce", "result in", "save",
                 "shape", "shift", "spur", "stimulate", "strengthen", "undermine", "weaken", "widen", "worsen")
# Verbs that also describe a change with no cause: "did Y increase in 2020?"
_CHANGE_VERBS = ("change", "decrease", "increase", "improve", "lower", "shift", "worsen", "narrow", "widen")
_INTRANSITIVE = ("rise", "fall", "grow", "decline", "drop", "go up", "go down", "shrink", "stagnate")
_INTRANSITIVE_PAST = ("risen", "rose", "fallen", "fell", "grown", "grew", "declined", "dropped", "gone up", "gone down",
                      "shrunk", "shrank", "stagnated")


def _forms(verb: str) -> tuple[str, str]:
    """(third person, past and participle) of a possibly two-word verb, as regex alternatives."""
    head, _, tail = verb.partition(" ")
    tail = f" {tail}" if tail else ""
    if head in _IRREGULAR:
        third, past, _ = _IRREGULAR[head]
    elif head.endswith(("sh", "ch", "ss")):
        third, past = head + "es", head + "ed"
    elif head.endswith("e"):
        third, past = head + "s", head + "d"
    else:
        third, past = head + "s", head + "ed"
    return f"{third}{tail}", "|".join(f"{p}{tail}" for p in past.split("|"))


_BASE = "|".join(_CAUSAL_VERBS)
_THIRD = "|".join(_forms(v)[0] for v in _CAUSAL_VERBS)
_PAST = "|".join(_forms(v)[1] for v in _CAUSAL_VERBS)
_AUX = r"(?:does|do|did|can|could|will|would|might|may|should)(?:n['’]t)?"
_NOT = r"(?:\s+not)?"
_PREP_AFTER_NOUN = re.compile(r"^(?:in|of|on|for|to)\b", re.I)
_DETERMINER = re.compile(r"\b(?:the|a|an|this|that|these|those|any|such)$", re.I)
_TIME_PREP = re.compile(r"^(?:in|over|since|during|between|across|from|by|at|through|throughout)\b", re.I)
_EVENT_PREP = re.compile(r"^(?:after|following|once|when|as)\b", re.I)
_WITH_PREP = re.compile(r"^with\b", re.I)
_YEAR_AFTER_SINCE = re.compile(r"^since\s+(?:the\s+)?(?:(?:19|20)\d{2}|\d+s)\b", re.I)

# --------------------------------------------------------------------------
# Phrases around the treatment and the outcome
# --------------------------------------------------------------------------
_HARD_STOPS = (r"\?|\.(?:\s|$)|;|:|,?\s+(?:compared|comparing|relative to|versus|vs\.?|using|given|when|whereby|including|"
               r"across|vary|varies|differ|differs|instrumenting|exploiting|evidence from|in an? (?:randomi[sz]ed|"
               r"natural|field|quasi|controlled)\w*|par rapport|en utilisant|compar|lorsque|quand|varie|"
               r"gr[âa]ce [àa])\b")
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
_NOT_A_NOUN_PHRASE = re.compile(r"^(?:on|of|to|in|for|at|by|with|from|sur|de|du|des|what|which|who|how|why|when|does|do|"
                                r"did|is|are|was|were|be|has|have|had|can|could|will|would|reduce|increase|raise|lower|"
                                r"affect|improve|que|qui|quel|quelle)\b", re.I)
_RELATIVE = re.compile(r"\b(?:who|whom|that|which|whose|qui|que)\b", re.I)
_MAX_WORDS = 14


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" ,;:.?!\"'«»").strip()


def is_clear_phrase(text: str) -> bool:
    """Words that can be quoted as a treatment or an outcome: a short noun phrase."""
    return bool(text) and len(text.split()) <= _MAX_WORDS and not _NOT_A_NOUN_PHRASE.match(text) \
        and not _RELATIVE.search(text)


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
    after = re.sub(r"^\s*(?:on|upon|sur)\s+", "", after, flags=re.I)
    for m in re.finditer(_POPULATION, after, re.I):
        rest = after[m.end():]
        if _STRONG_POPULATION.match(m.group(0)) or _POPULATION_NOUN.match(rest):
            outcome, _ = _cut(after[:m.start()], r",")
            return clean(outcome), clean(rest)
    outcome, _ = _cut(after, r",")
    return clean(outcome), ""


def _treatment_part(text: str) -> str:
    return clean(_cut(text, _HARD_STOPS)[0])


# --------------------------------------------------------------------------
# Explicitly causal structures, in the order they are tried
# --------------------------------------------------------------------------
# Words that contain "effect" or "impact" without asking for a causal effect.
_NOT_AN_EFFECT = re.compile(r"\b(?:side|fixed|random|main|interaction|placebo)[- ]effects?\b|\beffect sizes?\b|"
                            r"\bimpact factors?\b|\beffets? (?:secondaires?|fixes?|al[ée]atoires?)\b", re.I)
_EFFECT_NOUN = r"(?:effects?|impacts?|consequences?|influence|effectiveness|efficacy|benefits?)"
_EFFECT_EN = re.compile(rf"\b(?:[\w-]+\s+)?{_EFFECT_NOUN}\s+(?:of|from)\s+(?P<rest>.+)", re.I | re.S)
_ANY_EFFECT_WORD = re.compile(r"\b(?:effects?|impacts?|consequences?|effets?|cons[ée]quences?|incidence)\b", re.I)
_EFFECT_FR = re.compile(r"\b(?:effets?|impacts?|cons[ée]quences?|influence|efficacit[ée]|incidence|r[ée]percussions?)\s+(?:causal\s+)?"
                        r"(?:de la|de l'|du|des|de|d')\s*(?P<rest>.+)", re.I | re.S)
_QUEL_EFFET_FR = re.compile(r"\bquel(?:le)?s?\s+(?:effets?|impacts?|influence|cons[ée]quences?)\s+(?P<t>.+?)\s+"
                            r"(?:a|ont)-(?:t-)?(?:il|elle|ils|elles)\s+(?:eu\s+)?sur\s+(?P<rest>.+)", re.I | re.S)
_HAS_EFFECT = re.compile(rf"\b(?:{_AUX}|has|have|had){_NOT}\s+(?P<t>.+?)\s+(?:have|has|had)\s+(?:an?\s+|any\s+|no\s+)?"
                         r"(?:[\w-]+\s+)?(?:effects?|impacts?|influence)\s+(?:on|upon)\s+(?P<rest>.+)", re.I | re.S)
_CAUSE_NOUN = re.compile(r"\b(?:is|are|was|were)\s+(?P<t>.+?)\s+(?:an?\s+|the\s+|one of the\s+)?(?:[\w-]+\s+)?causes?\s+of\s+"
                         r"(?P<rest>.+)", re.I | re.S)
_CAUSE_NOUN_FR = re.compile(r"\b(?P<t>(?:la|le|les|l['’]|un|une)\s*.+?)\s+(?:est|sont)(?:-(?:il|elle|ils|elles))?\s+"
                            r"(?:une|la|l['’]une des)\s+causes?\s+(?:de la|de l'|du|des|de|d')\s*(?P<rest>.+)", re.I | re.S)
_WHAT_HAPPENS = re.compile(r"\bwhat\s+(?:happens|happened|would happen|will happen|could happen|might happen)\s+"
                           r"(?:to\s+(?P<o>.+?)\s+)?(?:when|if|after|once|as)\s+(?P<t>.+)", re.I | re.S)
_WHAT_HAPPENS_FR = re.compile(r"\bque se passe-t-il\s+(?:(?:pour|sur)\s+(?P<o>.+?)\s+)?(?:quand|si|lorsque|apr[èe]s)\s+"
                              r"(?P<t>.+)", re.I | re.S)
_ABSENCE = re.compile(r"\bwould\s+(?P<o>.+?)\s+(?:be|have been)\s+(?:[\w-]+\s+){0,2}?(?:in the absence of|absent|without|"
                      r"if not for|but for|had\b|if\b)\s*(?P<t>.+)", re.I | re.S)
_ABSENCE_FR = re.compile(r"\b(?P<o>(?:la|le|les|l['’])\s*.+?)\s+(?:serait|seraient|aurait|auraient)-(?:il|elle|ils|elles)\s+"
                         r"(?:[\w-]+\s+){0,2}?(?:sans|en l['’]absence d(?:e|u|es|['’]))\s*(?P<t>.+)", re.I | re.S)
_IF_WOULD = re.compile(r"\bif\s+(?P<t>.+?),?\s+(?:would|will)\s+(?P<o>.+)", re.I | re.S)
_WOULD_HAD = re.compile(r"\bwould\s+(?P<o>.+?)\s+(?:have\s+)?\w+\s+had\s+(?P<t>.+)", re.I | re.S)
_EFFECTIVE = re.compile(r"\b(?:how\s+effective\s+)?(?:is|are|was|were)\s+(?P<t>.+?)\s+(?:(?:cost-)?effective)\s*"
                        r"(?:(?:at|in|for|on)\s+(?P<o>.+))?(?:\?|$)|\bhow\s+effective\s+(?:is|are|was|were)\s+(?P<t2>.+?)"
                        r"(?:\s+(?:at|in|for|on)\s+(?P<o2>.+))?(?:\?|$)", re.I | re.S)
_HOW_MANY_CAUSAL = re.compile(rf"\bhow\s+(?:many|much)\s+(?P<o>.+?)\s+{_AUX}\s+(?P<t>.+?)\s+(?:{_BASE})\s*\??\s*$", re.I | re.S)
_WHAT_CAUSES = re.compile(r"^\s*what\s+(?:causes|caused|drives|drove|is causing|is driving)\s+(?P<o>.+)", re.I | re.S)
_SOCIAL_COST = re.compile(r"\b(?P<o>(?:economic|social|welfare|human|fiscal|health)\s+costs?)\s+of\s+(?P<rest>.+)", re.I | re.S)
_COST_FR = re.compile(r"\b(?P<o>co[ûu]ts?\s+(?:[ée]conomiques?|sociaux|social|humains?))\s+(?:de la|de l'|du|des|de|d')\s*"
                      r"(?P<rest>.+)", re.I | re.S)
_RETURNS = re.compile(r"\b(?P<o>(?:[\w-]+\s+)?returns?)\s+to\s+(?P<t>.+)", re.I | re.S)
# "Does X reduce Y?" and its negative, past and modal variants.
_AUX_CLAUSE = re.compile(rf"\b{_AUX}{_NOT}\s+(?P<tail>.+)", re.I | re.S)
_VERB_IN_TAIL = re.compile(rf"\b(?P<v>{_BASE})\b", re.I)
# "Does X matter?", "do programs work?": asks for an effect and names no outcome.
_BARE_EFFECT = re.compile(rf"^(?P<t>.+?)\s+(?:not\s+)?(?P<v>matter|work|succeed|pay off)\s*(?:\?.*)?$", re.I | re.S)
_ADVERB_AT_END = re.compile(r"\s+(?:really|actually|truly|indeed|always|also|in fact|necessarily)$", re.I)
_INTRANSITIVE_IN_TAIL = re.compile(rf"\b(?P<v>{'|'.join(_INTRANSITIVE)})\b", re.I)
_PERFECT = re.compile(rf"\b(?:has|have|had)(?:n['’]t)?{_NOT}\s+(?P<t>.+?)\s+(?P<v>{_PAST})\b\s*(?P<rest>.*)", re.I | re.S)
_PERFECT_INTRANSITIVE = re.compile(rf"\b(?:has|have|had)(?:n['’]t)?{_NOT}\s+(?P<t>.+?)\s+(?P<v>{'|'.join(_INTRANSITIVE_PAST)})\b"
                                   r"\s*(?P<rest>.*)", re.I | re.S)
_PASSIVE = re.compile(r"\b(?:is|are|was|were|has been|have been)\s+(?P<o>.+?)\s+(?:affected|influenced|caused|driven|shaped|"
                      r"altered|impacted|harmed|improved|reduced|increased)\s+by\s+(?P<t>.+)", re.I | re.S)
_CLAUSE = re.compile(rf"^\s*(?:how|whether|if|to what extent)?\s*(?P<t>[^?]+?)\s+(?P<v>{_THIRD}|{_PAST})\s+(?P<rest>.+)", re.I | re.S)

_FR_ARTICLE = r"(?:la|le|les|l['’]|un|une|ce|cet|cette|ces|son|sa|ses|leur|leurs)"
_FR_VERB = (r"augment|r[ée]du|am[ée]lior|diminu|affect|influenc|caus|provoqu|entra[îi]n|baiss|accro[îi]t|favoris|nui|"
            r"renforc|affaibl|modifi|stimul|chang")
_DOES_FR = re.compile(rf"\b(?P<t>{_FR_ARTICLE}\s*.+?)\s+(?:n['’]|ne\s+)?(?:a|ont)-(?:t-)?(?:il|elle|ils|elles)\s+(?:pas\s+)?"
                      rf"(?:(?:un effet|une influence|un impact|des effets)\s+(?:sur\s+)?|(?:{_FR_VERB})\w*\s+)(?P<rest>.+)",
                      re.I | re.S)
_VERB_FR = re.compile(rf"\b(?P<t>{_FR_ARTICLE}\s*.+?)\s+(?:ne\s+)?(?:{_FR_VERB})\w*-(?:t-)?(?:il|elle|ils|elles)\s+(?:pas\s+)?(?P<rest>.+)", re.I | re.S)
_EST_CE_FR = re.compile(rf"\best-ce qu(?:e\s+|['’])(?P<t>.+?)\s+(?:{_FR_VERB})\w*\s+(?P<rest>.+)", re.I | re.S)

# --------------------------------------------------------------------------
# Explicitly predictive or descriptive, and associations
# --------------------------------------------------------------------------
_PREDICTIVE = re.compile(r"\b(?:predict\w*|forecast\w*|pr[ée]di(?:re|sent|t|ction|ctions|ctif|ctive|ctifs)|pr[ée]voir|"
                         r"pr[ée]vision\w*|classif(?:y|ier|ication)\b)", re.I)
_PREDICTING_FIRST = re.compile(r"\b(?:predicting|forecasting|to (?:predict|forecast)|pr[ée]dire|pr[ée]voir)\b", re.I)
_PREDICT_OBJECT = re.compile(r"\b(?:predict|forecast)\s+(?P<o>.+?)(?:\s+(?:using|with|from|based on)\b.*)?(?:\?|$)", re.I | re.S)
_DESCRIPTIVE = re.compile(
    r"\bhow (?:many|common|prevalent|frequent|widespread|often)\b|\bhow much\b|\bwhat (?:share|proportion|percentage|fraction)\b|"
    r"\bwhat (?:is|was|are|were) the (?:[\w-]+\s+)?(?:prevalence|incidence|share|proportion|percentage|number|"
    r"average|mean|median|level|distribution|trend|rate|size|extent)\b|"
    r"\bhow (?:has|have|did|do|does)\b.+\b(?:changed?|evolved?|developed?|varied?|vary)\b|"
    r"\b(?:describe|characteri[sz]e)\b|\bwhat are the characteristics\b|\bwho (?:are|uses?|used)\b|"
    r"\bcombien\b|\bquell?e?s? (?:est|sont|[ée]tait) (?:la|le|les) (?:part|proportion|pr[ée]valence|moyenne|nombre|"
    r"niveau|taux|[ée]volution|distribution)\b|\bcomment (?:a|ont)\s+[ée]volu|\bd[ée]crire\b", re.I | re.S)
_WEAK_ASSOCIATION = re.compile(
    r"\b(?:relationships?|relations?|associations?|correlations?|links?|connections?|liens?)\s+(?:between|entre)\b|"
    r"\b(?:the\s+)?role\s+of\b|\ble r[ôo]le d", re.I)
_ASSOCIATION = re.compile(
    r"\b(?:associated|correlated|linked|related|connected|associ[ée]e?s?|corr[ée]l[ée]e?s?|li[ée]e?s?)\s+(?:with|to|[àa]|avec)\b|"
    r"\bcorrelat\w*|\bwhat (?:explains?|accounts? for)\b|\bwhat (?:factors|variables|characteristics|determinants)\b|"
    r"\bwhich (?:factors|variables|characteristics|determinants)\b|\bdeterminants?\s+of\b|\bwhy\s+(?:do|does|did|are|is|were|was)\b|"
    r"\bwhat determines?\b|\bqu['’]est-ce qui explique\b|\bquels? facteurs\b|\bquelles? variables\b|"
    r"\bd[ée]terminants? d|\bpourquoi\b", re.I)
_BETWEEN = re.compile(r"\b(?:between|entre)\s+(?P<t>.+?)\s+(?:and|et)\s+(?P<o>.+)", re.I | re.S)
_ASSOCIATED = re.compile(r"\b(?:is|are|was|were|does|do|did)\s+(?P<t>.+?)\s+(?:(?:associated|correlated|linked|related|"
                         r"connected)\s+(?:with|to)|correlate\s+with)\s+(?P<o>.+)", re.I | re.S)
_ASSOCIATED_FR = re.compile(rf"\b(?P<t>{_FR_ARTICLE}\s*.+?)\s+(?:est|sont)(?:-(?:il|elle|ils|elles))?\s+"
                            r"(?:associ[ée]e?s?|corr[ée]l[ée]e?s?|li[ée]e?s?)\s+(?:[àa]\s+|au\s+|aux\s+|avec\s+)(?P<o>.+)", re.I | re.S)
_EXPLAINS = re.compile(r"\b(?:explains?|accounts? for|factors?\s+(?:predict|explain|influence|affect)|determinants?\s+of|"
                       r"qui explique)\s+(?P<o>.+)", re.I | re.S)
_DESCRIBED_OUTCOME = re.compile(r"\b(?:prevalence|incidence|share|proportion|percentage|number|average|mean|median|level|"
                                r"distribution|trend|rate)\s+of\s+(?P<o>.+)", re.I | re.S)
# Comparisons of groups: possibly causal, but the wording does not say so.
_LIKELY = re.compile(r"\b(?:are|is|were|was)\s+(?P<t>.+?)\s+(?:less|more)\s+likely\s+(?:to\s+(?:be\s+)?)?(?P<o>.+)", re.I | re.S)
_COMPARE = re.compile(r"\b(?:less|more)\s+likely\b|\b(?:higher|lower|better|worse|greater|fewer|longer|shorter|faster|slower|"
                      r"richer|poorer|healthier|more|less)\b.*\bthan\b|\b(?:plus|moins|mieux|davantage)\b.*\bque\b|"
                      r"\b(?:plus|moins) susceptibles?\b", re.I | re.S)
_SUBJECT_VERB_COMPARE = re.compile(rf"\b{_AUX}{_NOT}\s+(?P<t>.+?\b(?:who|that|with|qui)\b.+?)\s+(?P<o>[a-z]+\s+(?:higher|lower|better|"
                                   r"worse|longer|more|less)\b.*)", re.I | re.S)
_GOOD_FOR = re.compile(r"\b(?:is|are|was|were)\s+(?P<t>.+?)\s+(?:good|bad|beneficial|harmful|better|worse)\s+for\s+(?P<o>.+)", re.I | re.S)


def _evidence(words: str, limit: int = 60) -> str:
    """The words behind a reading, cut on a word boundary."""
    words = clean(words)
    return words if len(words) <= limit else words[:limit].rsplit(" ", 1)[0] + "…"


def _causal(treatment: str, after: str, evidence: str, certain: bool = True) -> Reading:
    outcome, population = _outcome_and_population(after) if after else ("", "")
    return Reading(CAUSAL, evidence, _treatment_part(treatment), outcome, population, certain)


def _ambiguous(evidence: str, treatment: str = "", outcome: str = "") -> Reading:
    return Reading(AMBIGUOUS, evidence, _treatment_part(treatment), _treatment_part(outcome), "", certain=False)


def _strong_causal(q: str) -> Reading | None:
    """Structures that ask for an effect whatever the verb."""
    for pattern in (_ABSENCE, _ABSENCE_FR):
        m = pattern.search(q)
        if m:
            return _causal(m.group("t"), m.group("o"), _evidence(m.group(0)))
    for pattern in (_IF_WOULD, _WOULD_HAD):       # counterfactual, with roles too loose to quote as stated
        m = pattern.search(q)
        if m:
            return Reading(CAUSAL, _evidence(m.group(0)), _treatment_part(m.group("t")), _treatment_part(m.group("o")), "",
                           certain=False)
    for pattern in (_WHAT_HAPPENS, _WHAT_HAPPENS_FR):
        m = pattern.search(q)
        if m:
            return _causal(m.group("t"), m.group("o") or "", _evidence(m.group(0)))
    for pattern in (_CAUSE_NOUN, _CAUSE_NOUN_FR):
        m = pattern.search(q)
        if m:
            return _causal(m.group("t"), m.group("rest"), _evidence(m.group(0)))
    m = _HAS_EFFECT.search(q)
    if m:
        return _causal(m.group("t"), m.group("rest"), _evidence(m.group(0)))
    m = _QUEL_EFFET_FR.search(q)
    if m:
        return _causal(m.group("t"), m.group("rest"), _evidence(m.group(0)))
    for pattern, word in ((_EFFECT_EN, "on"), (_EFFECT_FR, "sur")):
        m = pattern.search(q)
        if m:
            split = _split_on(m.group("rest"), word) or (_split_on(m.group("rest"), "upon") if word == "on" else None)
            words = _evidence(m.group(0))
            if split:
                return _causal(split[0], split[1], words)
            treatment, population = _cut(_treatment_part(m.group("rest")), _POPULATION)
            return Reading(CAUSAL, words, clean(treatment), "", clean(population))
    for pattern in (_SOCIAL_COST, _COST_FR):
        m = pattern.search(q)
        if m:
            treatment, population = _cut(_treatment_part(m.group("rest")), _POPULATION)
            return Reading(CAUSAL, _evidence(m.group(0)), clean(treatment), clean(m.group("o")), clean(population))
    m = _EFFECTIVE.search(q)
    if m:
        treatment, outcome = m.group("t") or m.group("t2"), m.group("o") or m.group("o2") or ""
        return _causal(treatment, outcome, _evidence(m.group(0)))
    m = _HOW_MANY_CAUSAL.search(q)
    if m:
        return _causal(m.group("t"), m.group("o"), _evidence(m.group(0)))
    m = _WHAT_CAUSES.search(q)
    if m:
        return _causal("", m.group("o"), _evidence(m.group(0)))
    m = _RETURNS.search(q)
    if m:
        return Reading(CAUSAL, _evidence(m.group(0)), _treatment_part(m.group("t")), clean(m.group("o")))
    return None


def _predictive(q: str) -> Reading | None:
    m = _PREDICTIVE.search(q)
    if not m:
        return None
    obj = _PREDICT_OBJECT.search(q)
    return Reading(PREDICTIVE, m.group(0), "", _treatment_part(obj.group("o")) if obj else "", "", certain=False)


def _descriptive(q: str) -> Reading | None:
    m = _DESCRIPTIVE.search(q)
    if not m:
        return None
    obj = _DESCRIBED_OUTCOME.search(q)
    return Reading(DESCRIPTIVE, _evidence(m.group(0)), "", _treatment_part(obj.group("o")) if obj else "", "", certain=False)


def _association(q: str) -> Reading | None:
    m = _ASSOCIATION.search(q)
    if not m:
        return None
    words = m.group(0)
    for pattern in (_ASSOCIATED, _ASSOCIATED_FR):
        pair = pattern.search(q)
        if pair:
            return _ambiguous(words, pair.group("t"), pair.group("o"))
    pair = _BETWEEN.search(q)
    if pair:
        return _ambiguous(words, pair.group("t"), pair.group("o"))
    explained = _EXPLAINS.search(q)
    return _ambiguous(words, "", explained.group("o") if explained else "")


def _weak_association(q: str) -> Reading | None:
    m = _WEAK_ASSOCIATION.search(q)
    if not m:
        return None
    pair = _BETWEEN.search(q)
    return _ambiguous(m.group(0), pair.group("t"), pair.group("o")) if pair else _ambiguous(m.group(0))


def _change_without_cause(treatment: str, rest: str, words: str) -> Reading:
    """A change with no named cause: "did Y rise in 2020?" is descriptive, "did Y rise after the reform?" may be causal."""
    rest = rest.strip()
    if _EVENT_PREP.match(rest) or _WITH_PREP.match(rest) or (rest.lower().startswith("since")
                                                               and not _YEAR_AFTER_SINCE.match(rest)):
        return _ambiguous(_evidence(f"{words} {rest}"), re.sub(r"^\S+\s+", "", rest), treatment)
    return Reading(DESCRIPTIVE, words, "", _treatment_part(treatment), "", certain=False)


def _verb_clause(q: str) -> Reading | None:
    """Aux + subject + base verb + object, with the first verb form that is really the verb:
    in "does the increase in taxes reduce spending", "increase" is a noun."""
    for clause in _AUX_CLAUSE.finditer(q):
        tail = clause.group("tail").split("?")[0]        # a subtitle is not part of the clause
        bare = _BARE_EFFECT.match(tail.strip())
        if bare and not re.fullmatch(r"(?:it|this|that|they|we|you)", bare.group("t").strip(), re.I):
            return _causal(_ADVERB_AT_END.sub("", bare.group("t").strip()), "", _evidence(clause.group(0)))
        verbs = list(_VERB_IN_TAIL.finditer(tail))
        for i, m in enumerate(verbs):
            subject, verb, rest = tail[:m.start()], m.group("v").lower(), tail[m.end():].strip()
            if not subject.strip() or _DETERMINER.search(subject.strip()):
                continue
            if _PREP_AFTER_NOUN.match(rest) and " " not in verb and i < len(verbs) - 1:
                continue                       # a noun followed by the real verb
            words = _evidence(clause.group(0))
            subject = _ADVERB_AT_END.sub("", re.sub(r"\s+not$", "", subject.strip(), flags=re.I))
            rest = re.sub(r"^or\s+\w+\s+", "", rest, flags=re.I)        # "enhance or impede Y": the outcome is Y
            if verb in _CHANGE_VERBS and (not clean(rest) or _TIME_PREP.match(rest) or _EVENT_PREP.match(rest)
                                          or _WITH_PREP.match(rest)):
                return _change_without_cause(subject, rest, words)
            if verb == "make":      # "does X make Y increase": the outcome is Y
                rest = re.sub(r"\s+(?:increase|decrease|rise|fall|grow|decline|go up|go down)\s*\??\s*$", "", rest, flags=re.I)
            return _causal(subject, rest, words)
        m = _INTRANSITIVE_IN_TAIL.search(tail)
        if m and tail[:m.start()].strip():
            return _change_without_cause(tail[:m.start()].strip(), tail[m.end():], _evidence(clause.group(0)))
    return None


def _perfect_or_passive(q: str) -> Reading | None:
    m = _PERFECT.search(q)
    if m:
        rest = m.group("rest").strip()
        verb = m.group("v").lower()
        if not clean(rest) or _TIME_PREP.match(rest) or _EVENT_PREP.match(rest) or _WITH_PREP.match(rest):
            if any(verb.startswith(v[:-1]) for v in _CHANGE_VERBS):
                return _change_without_cause(m.group("t"), rest, _evidence(m.group(0)))
        return _causal(m.group("t"), rest, _evidence(m.group(0)))
    m = _PERFECT_INTRANSITIVE.search(q)
    if m:
        return _change_without_cause(m.group("t"), m.group("rest"), _evidence(m.group(0)))
    m = _PASSIVE.search(q)
    if m:
        return _causal(m.group("t"), m.group("o"), _evidence(m.group(0)))
    return None


def _french_clause(q: str) -> Reading | None:
    for pattern in (_DOES_FR, _VERB_FR, _EST_CE_FR):
        m = pattern.search(q)
        if m:
            return _causal(m.group("t"), m.group("rest"), _evidence(m.group(0)))
    return None


def _comparison(q: str) -> Reading | None:
    for pattern in (_LIKELY, _GOOD_FOR, _SUBJECT_VERB_COMPARE):
        m = pattern.search(q)
        if m:
            return _ambiguous(_evidence(m.group(0)), m.group("t"), m.group("o"))
    m = _COMPARE.search(q)
    return _ambiguous(_evidence(m.group(0))) if m else None


def read_question(question: str) -> Reading:
    """The intent of the question, with the treatment and outcome it names."""
    q = _NOT_AN_EFFECT.sub("", question)
    predicting = _PREDICTING_FIRST.search(q)
    effect = _ANY_EFFECT_WORD.search(q)
    if predicting and (effect is None or predicting.start() < effect.start()):
        return _predictive(q) or Reading(PREDICTIVE, _evidence(predicting.group(0)), certain=False)
    strong = _strong_causal(q)
    if strong is not None:
        return strong
    for rule in (_predictive, _association):
        reading = rule(q)
        if reading is not None:
            return reading
    clause = _verb_clause(q) or _perfect_or_passive(q) or _french_clause(q)
    if clause is not None and clause.intent == CAUSAL:
        return clause
    # A loose word for a link gives way to an explicit causal clause, as in
    # "the relationship between X and Y: does X reduce Y?"; on its own it stays ambiguous.
    weak = _weak_association(q)
    if weak is not None:
        return weak
    descriptive = _descriptive(q)
    if descriptive is not None:
        return descriptive
    if clause is not None:
        return clause
    comparison = _comparison(q)
    if comparison is not None:
        return comparison
    m = _CLAUSE.search(q)            # a statement: "the reform reduces employment", "whether X affects Y"
    if m and not re.match(r"\s*(?:what|which|who|when|where|is|are|was|were)\b", q, re.I):
        return _causal(m.group("t"), m.group("rest"), _evidence(m.group(0)), certain=False)
    return Reading(AMBIGUOUS, "", certain=False)


# --------------------------------------------------------------------------
# Thresholds: an assignment rule, an ordinary number, or unclear
# --------------------------------------------------------------------------
_CUTOFF_WORD = re.compile(r"cut-?\s?offs?\b|\bthresholds?\b|\bseuils?\b", re.I)
_SHARP = re.compile(r"barely (?:won|lost|passed|failed|above|below|qualified)|just (?:above|below|over|under)|de justesse|"
                    r"discontinuit\w*|by a (?:narrow|slim|small) margin|narrowly (?:won|lost|elected|defeated)|"
                    r"close (?:elections?|races?)|juste (?:au[- ]dessus|au[- ]dessous|en[- ]dessous)", re.I)
_NEAR_CUTOFF = re.compile(r"(?:near|close to|around|at|proches? d[ue]|autour d[ue])\s+(?:(?:the|a|an|le|la|ce)\s+)?(?:[\w-]+\s+){0,3}?"
                          r"(?:cut-?\s?offs?\b|thresholds?\b|seuils?\b)", re.I)
_ORDINARY = re.compile(r"threshold (?:effects?|models?|regressions?)|\b(?:above|below|beyond) which\b|significance (?:level|threshold)|"
                       r"poverty (?:line|threshold)|seuils? de (?:pauvret[ée]|significativit[ée])|effets? de seuil", re.I)
# Words that make a rule decide who is treated.
_RULE = re.compile(r"\beligib\w*|[ée]ligib\w*|\bqualif\w*|\badmi(?:t|ss)\w*|\bentitl\w*|\bexempt\w*|\bactivat\w*|\btrigger\w*|"
                   r"d[ée]clench\w*|\badmissib\w*|\bdetermined by\b|\bbased on\b|\bassign\w*|\bsplit\w*|\baward\w*|\bgrant\w*|"
                   r"\bcross\w*", re.I)
_GETS = r"(?:receives?|gets?|are (?:awarded|assigned|granted|given|eligible)|is (?:awarded|assigned|granted|given|eligible)|obtiennent|re[çc]oivent)"
_COMPARATOR = (r"\b(?:above|below|over|under|at least|at most|more than|less than|fewer than|greater than|exceed\w*|au[- ]dessus d[eu]|"
               r"en[- ]dessous d[eu]|au moins|plus de|moins de|[àa] partir de)\s+(?:an?\s+|the\s+)?(?:[\w-]+\s+){0,2}?\d[\d.,]*\b"
               r"(?!\s*(?:years?|months?|weeks?|days?|ans|mois|semaines|jours)\b)|"
               r"\bat (?:the )?age (?:of )?\d+|[àa] l['’][âa]ge de \d+|[àa] partir de \d+ ans\b|\b\d+ years? (?:or older|and over|of age)\b|\b(?:minimum|passing) (?:grade|score|age|mark|income)\b|"
               r"\bnote minimale\b|\b[âa]ge minimum\b")


def threshold_kind(question: str) -> tuple[str | None, str]:
    """(kind, words): a threshold that assigns treatment, one whose role is unclear, an
    ordinary one that says nothing about assignment, or None."""
    rule = _RULE.search(question)
    ordinary = _ORDINARY.search(question)
    if ordinary and not re.search(r"eligib|[ée]ligib", question, re.I):
        return THRESHOLD_ORDINARY, ordinary.group(0)
    for pattern in (_SHARP, _NEAR_CUTOFF):
        m = pattern.search(question)
        if m:
            return THRESHOLD_ASSIGNMENT, m.group(0)
    word = _CUTOFF_WORD.search(question)
    if word:
        return (THRESHOLD_ASSIGNMENT if rule else THRESHOLD_UNCLEAR), word.group(0)
    comparator = re.search(_COMPARATOR, question, re.I)
    if comparator:
        # "students scoring above 70 receive tutoring" is a rule; "patients who receive more
        # than 3 doses" is a dose: the number must come before the verb that gives treatment.
        rule_after = re.search(rf"(?:{_COMPARATOR}).*\b{_GETS}\b", question, re.I | re.S)
        return (THRESHOLD_ASSIGNMENT if rule or rule_after else THRESHOLD_UNCLEAR), comparator.group(0)
    return None, ""
