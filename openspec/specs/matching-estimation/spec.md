# matching-estimation Specification

## Purpose
Estimates the average treatment effect on the treated (ATT) when treatment is non-random but assumed to depend only on observed covariates (selection on observables), via propensity-score matching and inverse probability weighting.

## Requirements

### Requirement: Propensity-score estimation
The system SHALL estimate each observation's propensity score, the probability of treatment given the supplied covariates, with a logistic regression.

#### Scenario: Estimating propensity scores
- **WHEN** the matching estimator is run with an outcome, a binary treatment and at least one numeric covariate
- **THEN** every observation receives a propensity score strictly between 0 and 1

### Requirement: Nearest-neighbour matching ATT
The system SHALL estimate the ATT by matching each treated observation, with replacement, to the control observation closest in Mahalanobis distance on the covariates. The bias from inexact matches SHALL be removed with a linear regression of the outcome on the covariates among controls (Abadie & Imbens 2011). The system SHALL report the Abadie-Imbens standard error, which accounts for controls being reused as matches, together with a 95% confidence interval and a p-value.

#### Scenario: Matching estimate
- **WHEN** the matching estimator is run
- **THEN** it reports the bias-corrected ATT, its standard error, confidence interval, p-value and the number of distinct controls used as matches

#### Scenario: Calibrated standard error
- **WHEN** the estimator is run on 60 seeded Matching virtual worlds
- **THEN** the 95% CI covers the true ATT in between 88% and 100% of them, and the mean standard error is within 0.8–1.25 times the sampling standard deviation of the estimates (measured on 200 worlds: 97% coverage, ratio 1.09)

### Requirement: Inverse-probability-weighted ATT
The system SHALL also report an inverse-probability-weighted ATT, in which control observations are weighted by p/(1-p), as a second estimate under the same assumption.

#### Scenario: IPW estimate reported alongside matching
- **WHEN** the matching estimator is run
- **THEN** the IPW ATT and its standard error are reported next to the matching ATT

### Requirement: Balance and overlap diagnostics
The system SHALL report the standardized mean difference of every covariate before and after matching, and SHALL warn when treated propensity scores fall outside the range of control propensity scores (lack of overlap).

#### Scenario: Matching improves balance
- **WHEN** treatment depends on the covariates
- **THEN** the balance table shows each covariate's standardized difference both in the raw sample and in the matched sample

#### Scenario: Poor overlap
- **WHEN** some treated observations have a propensity score above the largest control propensity score
- **THEN** the result includes an overlap warning stating how many treated observations are outside the control range
