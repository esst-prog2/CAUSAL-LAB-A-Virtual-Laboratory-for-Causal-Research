"""
Causal Diagnosis Engine (CAUSAL LAB spec, Section 9).

This module turns the structured answers collected in the Research
Question wizard (treatment type/timing, outcome type, unit of
analysis, data structure, plus free-text keywords found in the
research question) into a set of qualitative diagnostic flags:

    LOW / MEDIUM / HIGH / UNKNOWN

This is a transparent, rule-based heuristic layer, NOT a statistical
test. It is meant to orient the researcher toward the right questions
before any data is collected or analyzed, exactly as described in the
project's core principle:

    "Never start by choosing an estimator. Start by understanding the
    causal problem."

Nothing here invents a statistical result. Actual hypothesis tests
(parallel trends, serial correlation, etc.) are computed later, on
real or simulated data, by the robustness_engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Level(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


@dataclass
class ResearchDesignInput:
    """Structured input collected from the Research Question wizard."""

    research_question: str = ""
    treatment_type: str = "binary"            # binary | continuous | multiple
    treatment_timing: str = "single_date"      # single_date | staggered | continuous_time
    assignment_mechanism: str = "policy"       # random | policy | geographic | self_selected | threshold
    outcome_type: str = "continuous"           # continuous | binary | count | survival | categorical
    unit_of_analysis: str = "individual"
    data_structure: str = "panel"              # cross_section | panel | repeated_cross_section
                                                # | time_series | spatial | spatio_temporal_panel
                                                # | experimental | survey | administrative
    has_spatial_component: bool = False
    has_pre_treatment_periods: bool = True
    n_pre_periods: int = 1
    n_post_periods: int = 1


@dataclass
class DiagnosisResult:
    treatment_type: Level = Level.UNKNOWN
    treatment_timing: Level = Level.UNKNOWN
    outcome_type: Level = Level.UNKNOWN
    data_structure: Level = Level.UNKNOWN
    potential_endogeneity: Level = Level.UNKNOWN
    potential_confounding: Level = Level.UNKNOWN
    treatment_heterogeneity: Level = Level.UNKNOWN
    potential_spillovers: Level = Level.UNKNOWN
    notes: list[str] = field(default_factory=list)

    def as_table(self) -> list[tuple[str, str]]:
        return [
            ("Treatment type", self.treatment_type.value),
            ("Treatment timing", self.treatment_timing.value),
            ("Outcome type", self.outcome_type.value),
            ("Data structure", self.data_structure.value),
            ("Potential endogeneity", self.potential_endogeneity.value),
            ("Potential confounding", self.potential_confounding.value),
            ("Treatment heterogeneity", self.treatment_heterogeneity.value),
            ("Potential spillovers", self.potential_spillovers.value),
        ]


_SPILLOVER_KEYWORDS = (
    "neighbor", "neighbour", "nearby", "spatial", "adjacent",
    "surrounding", "diffusion", "spread", "region", "territories",
)
_ENDOGENEITY_KEYWORDS = (
    "self-select", "chose", "choice", "endogenous", "reverse", "demand",
)
_HETEROGENEITY_KEYWORDS = (
    "gender", "income", "age", "heterogene", "differ by", "vary by",
)


def _keyword_flag(text: str, keywords: tuple[str, ...]) -> bool:
    text_low = text.lower()
    return any(k in text_low for k in keywords)


def diagnose(design: ResearchDesignInput) -> DiagnosisResult:
    """Produce a DiagnosisResult from a ResearchDesignInput.

    The logic here is intentionally simple and explainable: each rule
    is a direct, documented mapping from a design feature to a risk
    level, so the researcher can see exactly why a flag was raised.
    """
    result = DiagnosisResult()

    # --- Treatment type -------------------------------------------------
    result.treatment_type = Level.LOW if design.treatment_type in (
        "binary", "continuous") else Level.MEDIUM

    # --- Treatment timing ------------------------------------------------
    if design.treatment_timing == "single_date":
        result.treatment_timing = Level.LOW
    elif design.treatment_timing == "staggered":
        result.treatment_timing = Level.HIGH
        result.notes.append(
            "Staggered treatment timing detected: standard two-way "
            "fixed-effects DiD can be biased under treatment-effect "
            "heterogeneity (Goodman-Bacon 2021; de Chaisemartin & "
            "D'Haultfoeuille 2020). Consider heterogeneity-robust "
            "DiD estimators."
        )
    else:
        result.treatment_timing = Level.MEDIUM

    # --- Outcome type ------------------------------------------------
    result.outcome_type = Level.LOW if design.outcome_type == "continuous" else Level.MEDIUM

    # --- Data structure ------------------------------------------------
    if design.data_structure in ("panel", "spatio_temporal_panel", "experimental"):
        result.data_structure = Level.LOW
    elif design.data_structure in ("repeated_cross_section", "survey", "administrative"):
        result.data_structure = Level.MEDIUM
    else:
        result.data_structure = Level.HIGH

    # --- Potential endogeneity ------------------------------------------------
    if design.assignment_mechanism == "random":
        result.potential_endogeneity = Level.LOW
    elif design.assignment_mechanism in ("threshold", "policy"):
        result.potential_endogeneity = Level.MEDIUM
    else:
        result.potential_endogeneity = Level.HIGH
    if _keyword_flag(design.research_question, _ENDOGENEITY_KEYWORDS):
        result.potential_endogeneity = Level.HIGH
        result.notes.append(
            "The research question mentions self-selection or reverse "
            "causality language; treat the assignment mechanism as "
            "potentially endogenous."
        )

    # --- Potential confounding ------------------------------------------------
    if design.assignment_mechanism == "random":
        result.potential_confounding = Level.LOW
    elif not design.has_pre_treatment_periods:
        result.potential_confounding = Level.HIGH
        result.notes.append(
            "No pre-treatment periods are available: pre-trends and "
            "time-invariant confounding cannot be assessed directly."
        )
    else:
        result.potential_confounding = Level.MEDIUM

    # --- Treatment heterogeneity ------------------------------------------------
    result.treatment_heterogeneity = (
        Level.HIGH if _keyword_flag(design.research_question, _HETEROGENEITY_KEYWORDS)
        or design.treatment_timing == "staggered"
        else Level.MEDIUM
    )

    # --- Potential spillovers ------------------------------------------------
    if design.has_spatial_component or _keyword_flag(design.research_question, _SPILLOVER_KEYWORDS):
        result.potential_spillovers = Level.HIGH
        result.notes.append(
            "Spatial or network language detected: treated and "
            "comparison units may not be independent (SUTVA "
            "violation). Consider a spillover / spatial-DiD analysis."
        )
    else:
        result.potential_spillovers = Level.LOW

    return result
