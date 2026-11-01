## ADDED Requirements

### Requirement: Weak-instrument-robust confidence set
The system SHALL report, with every IV estimate, the heteroskedasticity-robust Anderson-Rubin 95% confidence set for the effect and the Anderson-Rubin p-value of no effect. The set SHALL be shown as an interval, as two unbounded rays, as every value, or as empty, whichever it is. The weak-instrument warning SHALL point to the set.

#### Scenario: Useless instrument
- **WHEN** the first-stage F is far below 10
- **THEN** the result warns of a weak instrument, and the Anderson-Rubin set is unbounded rather than a misleadingly short interval
