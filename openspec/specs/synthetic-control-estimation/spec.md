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
