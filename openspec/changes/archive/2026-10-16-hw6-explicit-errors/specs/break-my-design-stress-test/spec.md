## ADDED Requirements

### Requirement: Computation errors are not threats
When the regression behind a check fails numerically on the data (singular design, a value error from the estimator), the check SHALL return N/A with the error message, and SHALL NOT return WARNING. Any other exception SHALL propagate rather than be hidden in a verdict.

#### Scenario: Singular design
- **WHEN** the regression of the Parallel Trends, Anticipation, Spillovers or Serial Correlation check raises a linear-algebra or value error
- **THEN** that check returns N/A, its message contains the error, and it is not counted in the score

#### Scenario: Programming error
- **WHEN** a check raises an exception of another type
- **THEN** the exception propagates
