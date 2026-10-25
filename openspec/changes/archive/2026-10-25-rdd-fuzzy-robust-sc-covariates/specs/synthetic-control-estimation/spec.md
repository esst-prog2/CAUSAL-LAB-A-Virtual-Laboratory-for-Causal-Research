## ADDED Requirements

### Requirement: Covariate predictors (ADH 2010)
When covariates are mapped, the system SHALL choose the donor weights to match predictors: the pre-treatment means of the covariates and of the outcome, each standardized by its standard deviation across units. The weights w(V) SHALL minimize the V-weighted predictor distance on the simplex, for a non-negative diagonal V summing to one. V SHALL be searched to minimize the pre-treatment outcome MSPE of w(V), with Nelder-Mead from k + 1 starts (equal V, then each predictor dominant in turn). The system SHALL report each predictor's treated, synthetic and donor-mean values and its importance V, and placebo inference SHALL apply the same procedure to every donor.

#### Scenario: Matching the predictors
- **WHEN** the synthetic control estimator is run with three covariates on a world whose covariates reflect the factor loadings
- **THEN** V and the weights each sum to one; for at least three of the four predictors the synthetic value is at least as close to the treated value as the donor mean is; and the same input gives the same estimate

#### Scenario: Compared with pysyncon
- **WHEN** the estimator and pysyncon (Nelder-Mead from equal V) run on the same covariate data
- **THEN** Causal Lab's pre-treatment outcome MSPE is at most 15% above pysyncon's. The search is local: on 6 worlds Causal Lab's MSPE was lower in 4 and at most 9% higher in 2

#### Scenario: No covariates
- **WHEN** no covariates are mapped
- **THEN** the weights reproduce the pre-treatment outcome path as before, and no predictor table is reported
