## MODIFIED Requirements

### Requirement: Clustering defaults to the unit column
The system SHALL cluster standard errors on the unit column unless a different clustering variable is explicitly supplied. The small-sample correction SHALL be CR1, G/(G−1)·(N−1)/(N−K), where K SHALL NOT count the unit dummies when every unit lies in a single cluster (Stata xtreg, fe / reghdfe convention).

#### Scenario: No cluster column supplied
- **WHEN** `cluster_col` is not passed
- **THEN** standard errors are clustered on the same column used as `unit_col`

#### Scenario: Unit fixed effects nested in the clusters
- **WHEN** the standard error is clustered by unit
- **THEN** it equals a CR1 sandwich written out by hand with K excluding the unit dummies, to within 1e-8 relative, and the CI and p-value use the normal distribution

### Requirement: Agreement with a reference implementation
The system's DiD estimate SHALL equal the two-way fixed-effects estimate of `linearmodels.PanelOLS` (entity and time effects) on the same data. Its clustered standard error SHALL agree to within 2% with PanelOLS's entity-clustered standard error computed with G/(G−1) and without counting effects (`group_debias=True`, `debiased=True`, `auto_df=False`, `count_effects=False`), the difference coming only from the period dummies, which PanelOLS does not count.

#### Scenario: Comparing with PanelOLS
- **WHEN** both estimators are run on the same Virtual World, including staggered and serially correlated worlds
- **THEN** the point estimates differ by less than 1e-8 and the standard errors by less than 2%
