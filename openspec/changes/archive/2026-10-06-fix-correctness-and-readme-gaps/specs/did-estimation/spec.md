## ADDED Requirements

### Requirement: Treatment must vary
The system SHALL refuse to estimate when the treatment column has a single value, with an error stating that the effect is not identified.

#### Scenario: No treated observations
- **WHEN** `estimate_did` is called on data where `D` is 0 everywhere
- **THEN** it raises a ValueError stating that the treatment column has no variation, and the Estimation page shows that message instead of crashing

### Requirement: Agreement with a reference implementation
The system's DiD estimate SHALL equal the two-way fixed-effects estimate of `linearmodels.PanelOLS` (entity and time effects) on the same data. Its clustered standard error SHALL agree with PanelOLS's entity-clustered standard error to within 2%, the difference coming only from small-sample corrections.

#### Scenario: Comparing with PanelOLS
- **WHEN** both estimators are run on the same Virtual World, including staggered and serially correlated worlds
- **THEN** the point estimates differ by less than 1e-8 and the standard errors by less than 2%
