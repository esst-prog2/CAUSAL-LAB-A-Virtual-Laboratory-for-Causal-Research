## MODIFIED Requirements

### Requirement: Control units contribute no own coefficient
The system SHALL exclude units that are never treated from the relative-period coefficients while still using them to identify the period fixed effects. They SHALL belong to the reference category, so the model is full-rank.

#### Scenario: Never-treated unit
- **WHEN** a unit's `treated_unit` value is 0
- **THEN** its relative period is undefined, its rows are coded in the reference category (together with the treated units' reference period), and it receives no relative-period coefficient of its own

#### Scenario: Full-rank model
- **WHEN** the event study is fitted on a single-adoption-date Virtual World
- **THEN** no rank-deficiency warning is raised

### Requirement: Adoption period resolution order
The system SHALL resolve each treated unit's adoption period from the most specific source available.

#### Scenario: Per-unit adoption column supplied
- **WHEN** `adoption_period_col` is supplied and present in the data
- **THEN** each unit's own value in that column is used as its adoption period, supporting staggered designs

#### Scenario: Fixed treatment period supplied
- **WHEN** `adoption_period_col` is not supplied but `fixed_treatment_period` is
- **THEN** every treated unit uses that single period as its adoption period

#### Scenario: Neither supplied
- **WHEN** neither `adoption_period_col` nor `fixed_treatment_period` is supplied
- **THEN** each unit's adoption period is inferred as the first period in the data where its treatment indicator (`treated_now`, or `D` if that column is absent) equals 1

#### Scenario: Staggered data in the app
- **WHEN** the active dataset has staggered timing (a staggered Virtual World, or uploaded data whose units first have D = 1 in different periods)
- **THEN** the Estimation page does not pass a fixed treatment period, so each unit's own adoption period is inferred
