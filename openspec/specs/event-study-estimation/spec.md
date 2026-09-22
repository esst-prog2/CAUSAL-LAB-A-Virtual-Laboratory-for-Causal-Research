# event-study-estimation Specification

## Purpose
A leads-and-lags estimator that produces one treatment-effect coefficient per period relative to treatment, with the period immediately before treatment (k = -1) as the reference category, so pre-treatment coefficients can be inspected as an informal visual test of parallel trends.

## Requirements

### Requirement: Per-relative-period coefficients
The system SHALL estimate a separate coefficient for each period relative to a unit's treatment adoption, omitting the reference period.

#### Scenario: Estimating dynamic effects
- **WHEN** `estimate_event_study(df, ...)` is called
- **THEN** it computes each treated unit's relative period as `period - adoption_period`, clips it to `[-window, window]` (default window = 6), fits `outcome ~ C(rel_bucket, Treatment('ref')) + C(unit) + C(period)` by OLS with cluster-robust SEs by unit, and returns a coefficient table with one row per relative period (including the reference period fixed at estimate 0, SE 0) plus the total observation count

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

### Requirement: Control units contribute no own coefficient
The system SHALL exclude units that are never treated from the relative-period coefficients while still using them to identify the period fixed effects.

#### Scenario: Never-treated unit
- **WHEN** a unit's `treated_unit` value is 0
- **THEN** its relative period is undefined (bucketed as "control") and it receives no relative-period coefficient of its own
