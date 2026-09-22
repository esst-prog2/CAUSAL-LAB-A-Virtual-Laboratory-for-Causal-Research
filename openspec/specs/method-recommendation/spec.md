# method-recommendation Specification

## Purpose
Computes a transparent "CAUSAL LAB Method Suitability Score" (0-100) for a fixed library of seven candidate causal-identification methods, from the research design input and its diagnosis. The score is explicitly presented as an explainable heuristic, never as a guarantee of causal identification.

## Requirements

### Requirement: Scored, ranked candidate list
The system SHALL score every candidate method in the fixed library and return them ranked from most to least suitable.

#### Scenario: Recommending methods
- **WHEN** `recommend(design, diagnosis)` is called
- **THEN** it returns a list of 7 `MethodScore` records — Randomized Controlled Trial, Difference-in-Differences, Event Study, Synthetic Control, Regression Discontinuity, Instrumental Variables, Matching / Propensity Score — sorted by `overall` score descending

#### Scenario: Score composition
- **WHEN** a `MethodScore` is produced for any method
- **THEN** it has one or more named components each scored 0-100, an `overall` score equal to the mean of its components, a `confidence` label (HIGH if overall ≥ 75, MEDIUM if ≥ 50, else LOW), a rationale text list, a `main_assumption`, and a `main_concern`

### Requirement: DiD score reflects data structure, timing, and diagnosis
The system SHALL score Difference-in-Differences from data structure fit, pre-treatment-period availability, assignment mechanism, confounding risk, spillover risk, and endogeneity risk.

#### Scenario: Staggered timing penalty
- **WHEN** `treatment_timing` is "staggered"
- **THEN** the DiD "Treatment timing" component score is reduced by 20 points relative to the non-staggered case, and the rationale recommends a heterogeneity-robust estimator (Callaway & Sant'Anna, or de Chaisemartin & D'Haultfoeuille) over the canonical two-way fixed-effects specification

#### Scenario: High spillover risk adds an extension recommendation
- **WHEN** the diagnosis's `potential_spillovers` is HIGH
- **THEN** the DiD "Spatial compatibility" component drops to 40 (from 85), `main_concern` is set to "Spatial spillovers", and the rationale recommends a Spatial Spillover Analysis extension alongside the baseline DiD

### Requirement: Event Study score extends the DiD score
The system SHALL score Event Study as the DiD score plus a pre-period-availability component.

#### Scenario: Sufficient pre-periods
- **WHEN** `n_pre_periods` is 2 or more
- **THEN** the Event Study "Pre-period availability" component is 90

#### Scenario: Insufficient pre-periods
- **WHEN** `n_pre_periods` is fewer than 2
- **THEN** the Event Study "Pre-period availability" component is 40 and the rationale notes the limited ability to assess pre-trends

### Requirement: RCT score reflects the declared assignment mechanism only
The system SHALL score Randomized Controlled Trial almost entirely on whether the assignment mechanism is declared as "random", since it cannot verify randomization after the fact.

#### Scenario: Random assignment declared
- **WHEN** `assignment_mechanism` is "random"
- **THEN** the RCT "Random assignment" and "Identification" components are 98 each

#### Scenario: Non-random assignment declared
- **WHEN** `assignment_mechanism` is not "random"
- **THEN** the RCT "Random assignment" component is 2 and "Identification" is 5, and the rationale states an RCT-style analysis is not applicable retroactively

### Requirement: IV and RDD scores are capped when required design elements are undeclared
The system SHALL cap the Instrumental Variables and Regression Discontinuity scores when the project has not declared an instrument or a threshold-based assignment mechanism, since relevance/exclusion or cutoff validity cannot be assessed automatically.

#### Scenario: No declared instrument
- **WHEN** Instrumental Variables is scored
- **THEN** its "Assumed instrument availability" component is fixed at 30 regardless of design, and the rationale states relevance and the exclusion restriction cannot be assessed automatically because no instrument has been declared

#### Scenario: Non-threshold assignment
- **WHEN** `assignment_mechanism` is not "threshold"
- **THEN** the Regression Discontinuity "Threshold-based assignment" component is 10 (versus 90 when it is "threshold")

### Requirement: Matching score reflects endogeneity risk
The system SHALL score Matching / Propensity Score inversely to the diagnosis's potential-endogeneity risk, since matching only controls for observed confounders.

#### Scenario: High endogeneity risk
- **WHEN** the diagnosis's `potential_endogeneity` is HIGH
- **THEN** the "Selection-on-observables plausibility" component is low (100 minus 90% of the HIGH risk weight), and the rationale states unobserved confounding cannot be ruled out or tested directly
