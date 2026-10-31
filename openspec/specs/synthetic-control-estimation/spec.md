# synthetic-control-estimation Specification

## Purpose
Estimates the effect of an intervention on a single treated unit by building a "synthetic" version of that unit from a weighted combination of untreated donor units, and judges significance with placebo tests.

## Requirements

### Requirement: Convex donor weights fit on pre-treatment outcomes
The system SHALL choose non-negative donor weights summing to one that minimize the squared distance between the treated unit's pre-treatment outcomes and the weighted donor outcomes.

#### Scenario: Computing weights
- **WHEN** the synthetic control estimator is run on a long-format panel (unit, period, outcome) with a treated unit and a treatment period
- **THEN** it returns one weight per donor unit, each between 0 and 1, summing to 1, together with the pre-treatment root mean squared prediction error (RMSPE)

### Requirement: Per-period gaps and average post-treatment effect
The system SHALL report the treated-minus-synthetic gap in every period and, as the headline estimate, the average gap over post-treatment periods.

#### Scenario: Effect path
- **WHEN** the synthetic control estimator is run
- **THEN** it returns the treated and synthetic outcome paths for every period, the gap per period, and the mean post-treatment gap

### Requirement: Placebo-in-space inference
The system SHALL re-run the method with each donor in turn treated as if it were the treated unit, and SHALL report a permutation p-value: the share of units (treated included) whose post/pre RMSPE ratio is at least as large as the treated unit's. No standard error or normal-approximation confidence interval is reported.

#### Scenario: Placebo p-value
- **WHEN** the synthetic control estimator is run with J donor units
- **THEN** it reports a p-value of the form k/(J+1) and the placebo gap paths of all donors

### Requirement: Panel requirements
The system SHALL reject input where the treated unit is absent, where there are fewer than two pre-treatment periods or fewer than two donors, or where the panel is not balanced, with an error naming the problem.

#### Scenario: Unbalanced panel
- **WHEN** some unit is missing an outcome for some period
- **THEN** the estimator raises an error stating that the panel must be balanced

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

### Requirement: Warning when the placebo test cannot reject
The system SHALL warn when the number of donors makes the smallest attainable placebo p-value, 1 / (donors + 1), larger than 0.05. The warning SHALL give that value.

#### Scenario: Eight donors
- **WHEN** synthetic control is estimated with 8 donors
- **THEN** the result warns that no effect can be significant at 5%, because the p-value cannot fall below 1/9
