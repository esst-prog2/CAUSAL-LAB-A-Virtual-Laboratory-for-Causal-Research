## ADDED Requirements

### Requirement: Estimator options are validated
The robust estimator SHALL accept only the comparison groups `never_treated` and `not_yet_treated`, and at least 2 bootstrap replications. Any other value SHALL raise an error naming it; it SHALL NOT fall back to another comparison group.

#### Scenario: Misspelt comparison group
- **WHEN** `estimate_staggered_did` is called with `comparison = "never-treated"`
- **THEN** it raises an error naming the value and the allowed comparison groups

#### Scenario: Too few bootstrap replications
- **WHEN** it is called with `n_bootstrap = 1`
- **THEN** it raises an error instead of returning a missing standard error
