## ADDED Requirements

### Requirement: Warning when cohorts are small
The system SHALL report the number of units in the smallest adoption cohort. When it is below 5, the Estimation page and the report SHALL warn that the 95% interval is too narrow, and SHALL quote the coverage and the size measured in the validation study.

#### Scenario: Cohorts of three units
- **WHEN** Callaway & Sant'Anna is estimated on a panel whose smallest cohort has 3 units
- **THEN** the page and the report warn that the interval is too narrow and should be read as a lower bound on the uncertainty
