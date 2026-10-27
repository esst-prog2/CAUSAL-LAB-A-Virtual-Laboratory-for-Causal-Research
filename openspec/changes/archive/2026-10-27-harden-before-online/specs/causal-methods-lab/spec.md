## ADDED Requirements

### Requirement: Empty columns and unexpected errors are explained
The system SHALL refuse a mapping in which a chosen column has no values, and SHALL name that column. When an estimator or a check fails for a reason the app does not anticipate, the system SHALL show a message in the interface language with one line of technical detail, and the app SHALL keep working.

#### Scenario: An entirely empty covariate
- **WHEN** the researcher maps a covariate column whose every row is empty
- **THEN** the mapping is refused with a message naming that column as empty, and no estimate is run

#### Scenario: Too few rows for IV
- **WHEN** the researcher runs IV on data with no more complete rows than estimated parameters
- **THEN** the page says how many complete rows were found and how many are needed
