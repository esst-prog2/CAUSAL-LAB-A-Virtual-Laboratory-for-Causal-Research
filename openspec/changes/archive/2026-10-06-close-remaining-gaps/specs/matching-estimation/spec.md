## MODIFIED Requirements

### Requirement: Nearest-neighbour matching ATT
The system SHALL estimate the ATT by matching each treated observation, with replacement, to the control observation closest in Mahalanobis distance on the covariates. The bias from inexact matches SHALL be removed with a linear regression of the outcome on the covariates among controls (Abadie & Imbens 2011). The system SHALL report the Abadie-Imbens standard error, which accounts for controls being reused as matches, together with a 95% confidence interval and a p-value.

#### Scenario: Matching estimate
- **WHEN** the matching estimator is run
- **THEN** it reports the bias-corrected ATT, its standard error, confidence interval, p-value and the number of distinct controls used as matches

#### Scenario: Calibrated standard error
- **WHEN** the estimator is run on 60 seeded Matching virtual worlds
- **THEN** the 95% CI covers the true ATT in between 88% and 100% of them, and the mean standard error is within 0.8–1.25 times the sampling standard deviation of the estimates (measured on 200 worlds: 97% coverage, ratio 1.09)
