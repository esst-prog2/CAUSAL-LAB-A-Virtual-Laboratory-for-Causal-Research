# did-estimation Specification

## Purpose
The canonical two-way fixed-effects Difference-in-Differences estimator: `Y_it = alpha_i + gamma_t + beta * D_it + epsilon_it`, fit by OLS with cluster-robust standard errors. This is the estimator every other capability (Monte Carlo, robustness battery, code generator) builds on.

## Requirements

### Requirement: Two-way fixed-effects OLS estimation
The system SHALL estimate the DiD model by OLS with unit and period dummies and cluster-robust standard errors.

#### Scenario: Estimating on panel data
- **WHEN** `estimate_did(df)` is called on panel data with an outcome column, a treatment indicator column, a unit column, and a period column
- **THEN** it fits `outcome ~ treatment + C(unit) + C(period)` by OLS, computes standard errors clustered on the unit column (or on `cluster_col` if one is supplied), and returns the treatment coefficient as `att`, its clustered SE, t-statistic, p-value, and 95% confidence interval, plus `n_obs`, `n_units`, `n_periods`, the model formula string, and a formatted `summary_text`

#### Scenario: Default column names
- **WHEN** `estimate_did` is called without column-name overrides
- **THEN** it assumes the outcome column is `Y`, the treatment column is `D`, the unit column is `unit`, and the period column is `period`

### Requirement: Clustering defaults to the unit column
The system SHALL cluster standard errors on the unit column unless a different clustering variable is explicitly supplied.

#### Scenario: No cluster column supplied
- **WHEN** `cluster_col` is not passed
- **THEN** standard errors are clustered on the same column used as `unit_col`
