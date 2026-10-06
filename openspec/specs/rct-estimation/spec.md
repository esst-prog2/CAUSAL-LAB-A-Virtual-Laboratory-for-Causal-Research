# rct-estimation Specification

## Purpose
Estimates the average treatment effect (ATE) of a randomized binary treatment, unadjusted and covariate-adjusted, and reports whether randomization produced balanced groups.

## Requirements

### Requirement: Difference-in-means ATE with robust inference
The system SHALL estimate the ATE of a binary treatment as the difference in mean outcomes between treated and control observations, with a heteroskedasticity-robust standard error, a 95% confidence interval and a p-value.

#### Scenario: No covariates supplied
- **WHEN** the RCT estimator is run with an outcome column and a binary (0/1) treatment column and no covariates
- **THEN** it reports the difference in means as the ATE, with a heteroskedasticity-robust standard error, 95% confidence interval, p-value, and the number of treated and control observations

### Requirement: Covariate-adjusted ATE
The system SHALL, when covariates are supplied, also report a regression-adjusted ATE that uses the covariates (centered and interacted with treatment) to improve precision without changing the estimand.

#### Scenario: Covariates supplied
- **WHEN** the RCT estimator is run with one or more numeric covariates
- **THEN** the headline estimate is the covariate-adjusted ATE, and the unadjusted difference in means is still reported alongside it for comparison

### Requirement: Balance diagnostics
The system SHALL report, for every supplied covariate, the treated and control means and the standardized mean difference, and SHALL flag covariates whose absolute standardized difference exceeds 0.1.

#### Scenario: Imbalanced covariate
- **WHEN** a covariate's absolute standardized mean difference between treated and control exceeds 0.1
- **THEN** that covariate is flagged as imbalanced in the balance table

### Requirement: Treatment must be binary
The system SHALL reject a treatment column that is not coded 0/1 with both values present, with an error naming the problem, instead of producing a number.

#### Scenario: Non-binary treatment
- **WHEN** the treatment column contains values other than 0 and 1, or only one of them
- **THEN** the estimator raises an error stating that the treatment must be binary with both groups present
