# causal-diagnosis Specification

## Purpose
A transparent, rule-based heuristic layer that turns a `ResearchDesignInput` (plus free-text keywords found in the research question) into qualitative risk flags — LOW / MEDIUM / HIGH / UNKNOWN — across eight dimensions, orienting the researcher toward the right causal-identification questions before any data is collected or analyzed. It is explicitly not a statistical test; actual hypothesis tests run later, on data, in the stress-test module.

## Requirements

### Requirement: Eight-dimension diagnosis output
The system SHALL produce a `DiagnosisResult` with a risk level for treatment_type, treatment_timing, outcome_type, data_structure, potential_endogeneity, potential_confounding, treatment_heterogeneity, and potential_spillovers, plus a list of free-text explanatory notes.

#### Scenario: Diagnosis is derived, not entered
- **WHEN** `diagnose(design)` is called with a `ResearchDesignInput`
- **THEN** every one of the eight dimensions is set to LOW, MEDIUM, or HIGH by rule (never left UNKNOWN, since every input field has a default)

### Requirement: Treatment timing risk flag
The system SHALL flag staggered treatment timing as a higher identification risk than a single treatment date.

#### Scenario: Staggered adoption
- **WHEN** `treatment_timing` is "staggered"
- **THEN** `treatment_timing` risk is HIGH and a note is added warning that standard two-way fixed-effects DiD can be biased under treatment-effect heterogeneity (citing Goodman-Bacon 2021 and de Chaisemartin & D'Haultfoeuille 2020), recommending a heterogeneity-robust DiD estimator

#### Scenario: Single treatment date
- **WHEN** `treatment_timing` is "single_date"
- **THEN** `treatment_timing` risk is LOW

#### Scenario: Continuous treatment timing
- **WHEN** `treatment_timing` is "continuous_time"
- **THEN** `treatment_timing` risk is MEDIUM

### Requirement: Endogeneity risk from assignment mechanism and language
The system SHALL derive potential-endogeneity risk from the declared assignment mechanism, then escalate it if the research question text uses self-selection or reverse-causality language.

#### Scenario: Random assignment
- **WHEN** `assignment_mechanism` is "random"
- **THEN** `potential_endogeneity` is LOW

#### Scenario: Threshold or policy assignment
- **WHEN** `assignment_mechanism` is "threshold" or "policy"
- **THEN** `potential_endogeneity` is MEDIUM

#### Scenario: Self-selection language overrides the mechanism-based level
- **WHEN** the research question text contains a keyword such as "self-select", "chose", "choice", "endogenous", "reverse", or "demand"
- **THEN** `potential_endogeneity` is forced to HIGH regardless of the assignment mechanism, and a note is added flagging the design as potentially endogenous

### Requirement: Confounding risk from assignment mechanism and pre-period availability
The system SHALL flag potential confounding as HIGH when no pre-treatment periods are available and assignment is not random, as LOW under random assignment, and MEDIUM otherwise.

#### Scenario: No pre-treatment periods
- **WHEN** `assignment_mechanism` is not "random" and `has_pre_treatment_periods` is false
- **THEN** `potential_confounding` is HIGH and a note is added stating pre-trends and time-invariant confounding cannot be assessed directly

#### Scenario: Random assignment
- **WHEN** `assignment_mechanism` is "random"
- **THEN** `potential_confounding` is LOW

### Requirement: Treatment heterogeneity risk from keywords or staggered timing
The system SHALL flag treatment-effect heterogeneity as HIGH when the research question mentions subgroup-differencing language or when timing is staggered, and MEDIUM otherwise.

#### Scenario: Heterogeneity keyword
- **WHEN** the research question text contains a keyword such as "gender", "income", "age", "heterogene", "differ by", or "vary by"
- **THEN** `treatment_heterogeneity` is HIGH

#### Scenario: No heterogeneity signal and non-staggered timing
- **WHEN** neither a heterogeneity keyword is present nor `treatment_timing` is "staggered"
- **THEN** `treatment_heterogeneity` is MEDIUM

### Requirement: Spillover risk from spatial component or keywords
The system SHALL flag potential spillovers as HIGH when the design declares a spatial component or the research question uses spatial/network language, and LOW otherwise.

#### Scenario: Spatial or diffusion language
- **WHEN** `has_spatial_component` is true, or the research question text contains a keyword such as "neighbor", "nearby", "spatial", "adjacent", "surrounding", "diffusion", "spread", "region", or "territories"
- **THEN** `potential_spillovers` is HIGH and a note is added warning of a possible SUTVA violation and recommending a spillover / spatial-DiD analysis

#### Scenario: No spatial signal
- **WHEN** neither condition above holds
- **THEN** `potential_spillovers` is LOW

### Requirement: Data structure risk
The system SHALL rank data-structure risk from LOW (panel-like structures) to HIGH (anything not otherwise classified).

#### Scenario: Panel-like structure
- **WHEN** `data_structure` is "panel", "spatio_temporal_panel", or "experimental"
- **THEN** `data_structure` risk is LOW

#### Scenario: Repeated cross-section or administrative data
- **WHEN** `data_structure` is "repeated_cross_section", "survey", or "administrative"
- **THEN** `data_structure` risk is MEDIUM

#### Scenario: Any other structure
- **WHEN** `data_structure` is not one of the structures listed above
- **THEN** `data_structure` risk is HIGH
