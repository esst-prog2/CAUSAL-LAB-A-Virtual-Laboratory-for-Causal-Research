# dml-estimation Specification

## Purpose
Estimates a treatment effect while controlling for many covariates whose influence on treatment and outcome may be non-linear, using Double/Debiased Machine Learning in the partially linear model with cross-fitting.

## Requirements

### Requirement: Cross-fitted partially linear estimate
The system SHALL estimate theta in Y = theta*D + g(X) + e, as follows. It SHALL split the sample into K folds (default 5). It SHALL predict E[Y|X] and E[D|X] for each fold with machine-learning models trained on the other folds. It SHALL regress the outcome residuals on the treatment residuals. It SHALL report theta with a standard error based on the influence function, a 95% confidence interval and a p-value.

#### Scenario: Estimating theta
- **WHEN** the DML estimator is run with an outcome, a treatment (binary or continuous) and at least one numeric covariate
- **THEN** it reports theta, its standard error, confidence interval, p-value, the number of folds, and the out-of-fold R-squared of both nuisance models

#### Scenario: Reproducibility
- **WHEN** the DML estimator is run twice on the same data with the same random seed
- **THEN** it returns the same estimate both times

### Requirement: Naive OLS comparison
The system SHALL also report the coefficient on the treatment from an OLS regression of the outcome on the treatment and the covariates entered linearly.

#### Scenario: Non-linear confounding
- **WHEN** the covariates affect treatment and outcome non-linearly
- **THEN** the naive OLS coefficient is reported next to the DML estimate so the difference is visible
