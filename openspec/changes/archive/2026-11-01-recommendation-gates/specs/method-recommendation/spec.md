## MODIFIED Requirements

### Requirement: Scored, ranked candidate list
The system SHALL check every candidate method against the conditions without which it does not identify a causal effect, and score only the methods whose conditions hold. Methods SHALL be ranked in this order:
- supported methods, by score;
- methods that need information;
- methods ruled out.

#### Scenario: Recommending methods
- **WHEN** `recommend(design, diagnosis)` is called
- **THEN** it returns 8 `MethodScore` records, in the order above: Randomized Controlled Trial, Regression Discontinuity, Difference-in-Differences, Event Study, Synthetic Control, Instrumental Variables, Interrupted Time Series, and Matching / Propensity Score

#### Scenario: Score composition
- **WHEN** a supported method is scored
- **THEN** its score has three components, each from 0 to 100: design credibility, assumption plausibility and data adequacy
- **AND** its `overall` is their mean
- **AND** its `confidence` is HIGH if overall ≥ 75, MEDIUM if overall ≥ 50, and LOW otherwise
- **AND** it carries a rationale, a `main_assumption` and a `main_concern`

#### Scenario: Ruled-out method
- **WHEN** a method's necessary condition fails
- **THEN** its status is `not_supported`, its overall is 0, and `unmet` lists the failed conditions

## REMOVED Requirements

### Requirement: DiD score reflects data structure, timing, and diagnosis
**Reason**: DiD is no longer scored when its conditions fail. Its data structure and pre-periods are conditions, not score components.
**Migration**: see "Each method needs its identifying conditions" and the staggered-adoption note.

### Requirement: Event Study score extends the DiD score
**Reason**: The event study now has its own condition (two or more pre-treatment periods) and is scored with the same three components as DiD.
**Migration**: see "Each method needs its identifying conditions".

### Requirement: RCT score reflects the declared assignment mechanism only
**Reason**: A non-random assignment now rules RCT out instead of scoring it low.
**Migration**: see "Each method needs its identifying conditions".

### Requirement: IV and RDD scores are capped when required design elements are undeclared
**Reason**: The wizard now asks about an instrument. IV and RDD are ruled out, or flagged as needing information, instead of being scored with a fixed cap.
**Migration**: see "Each method needs its identifying conditions".

### Requirement: Matching score reflects endogeneity risk
**Reason**: Matching now requires the researcher to state that all important confounders are measured. Endogeneity risk still lowers its plausibility component.
**Migration**: see "Each method needs its identifying conditions".

## ADDED Requirements

### Requirement: Each method needs its identifying conditions
The system SHALL recommend a method only when its necessary conditions hold:
- RCT: random assignment.
- RDD: an assignment or eligibility cutoff.
- IV: an instrument is declared available. "Not sure" means the method needs information.
- DiD: untreated comparison units, followed before and after treatment, with at least one pre-period and one post-period.
- Event study: the DiD conditions, plus at least two pre-periods.
- Synthetic control: one or a few treated units, a panel of donor units, and at least five pre-treatment periods.
- Interrupted time series: longitudinal data, with at least three pre-treatment observations.
- Matching / regression adjustment: all important confounders measured. "Not sure" means the method needs information, unless assignment is random.

A policy intervention or panel data SHALL NOT by themselves make DiD supported.

#### Scenario: Random assignment
- **WHEN** the assignment mechanism is random
- **THEN** the recommended method is the RCT

#### Scenario: A real cutoff
- **WHEN** the assignment mechanism is a threshold
- **THEN** the recommended method is RDD

#### Scenario: One treated region with a long pre-period
- **WHEN** one unit is treated by a policy in a panel with ten pre-treatment periods
- **THEN** synthetic control is recommended over DiD

#### Scenario: A panel without comparison units
- **WHEN** no untreated comparison units are observed
- **THEN** DiD and the event study are ruled out

### Requirement: No credible design is stated
The system SHALL state explicitly when no method's necessary conditions hold, and SHALL list what would make each method credible.

#### Scenario: Self-selection observed once, with nothing else
- **WHEN** a self-selected treatment is observed in a cross-section, with no instrument and with unmeasured confounders
- **THEN** no method is recommended
- **AND** the Recommendation page and the report say that no credible causal design is supported, with the reasons

### Requirement: Structured recommendation
For the recommended method, the system SHALL give:
- the causal estimand;
- why the method fits;
- the identification strategy;
- the key assumptions;
- the threats and diagnostics;
- the alternative methods, with when each is preferable;
- the additional details needed (the questions behind each method that needs information).

#### Scenario: Default design
- **WHEN** the researcher runs the diagnosis on a policy evaluated in a panel with a pre-period, with the instrument and the confounders answered "not sure"
- **THEN** DiD is recommended, with the ATT as estimand
- **AND** IV and matching are listed as possible with more information
- **AND** each of the two questions to answer is shown
