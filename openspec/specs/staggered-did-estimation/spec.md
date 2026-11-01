# staggered-did-estimation Specification

## Purpose
Estimates the average treatment effect on the treated under staggered adoption without the bias of two-way fixed effects, by comparing each adoption cohort only with units that are not (yet) treated (Callaway & Sant'Anna 2021).

## Requirements

### Requirement: Group-time effects with a clean comparison group
The system SHALL estimate, for every adoption cohort g and period t, ATT(g, t) as the cohort's mean outcome change between g-1 and t minus the same change in the comparison group. The comparison group SHALL be the never-treated units. When no unit is never treated, it SHALL instead be the units not yet treated by both t and g-1.

#### Scenario: Never-treated units exist
- **WHEN** the estimator runs on a staggered Virtual World with untreated units
- **THEN** every ATT(g, t) uses the never-treated units as comparison, and the result reports `comparison = "never_treated"`

#### Scenario: Everyone is eventually treated
- **WHEN** every unit is treated by the last period
- **THEN** the result reports `comparison = "not_yet_treated"` and still returns an estimate

### Requirement: Aggregation and inference
The system SHALL report:
- the overall ATT, the cohort-size-weighted mean of post-treatment ATT(g, t) cells;
- an event study ATT(e), aggregated by time since adoption e;
- analytic standard errors and 95% confidence intervals, from the unit contributions to each aggregate. The variance SHALL use unbiased within-cohort variances (a one-unit cohort borrows the variance of the same combination of outcome changes among the comparison units), and the critical value and p-value SHALL use a Student t with Welch–Satterthwaite degrees of freedom. A seeded unit bootstrap SHALL be used only when no such variance can be formed.

#### Scenario: Recovering the truth where TWFE fails
- **WHEN** both estimators are run on staggered Virtual Worlds with `dynamic_effects = "severe"`
- **THEN** the Callaway & Sant'Anna estimate shows no detectable bias against the true ATT, while the TWFE estimate is clearly biased

#### Scenario: Two groups, two periods
- **WHEN** one cohort and the never-treated units are observed in two periods
- **THEN** the estimate, its degrees of freedom and its p-value are those of Welch's t test on the outcome changes

### Requirement: Estimation-page tab
The system SHALL show a "Robust DiD (Callaway & Sant'Anna)" tab on the Estimation page with:
- the robust ATT, its analytic SE (with its degrees of freedom) and CI;
- a table comparing TWFE, Callaway & Sant'Anna and, for Virtual Worlds, the true ATT;
- the robust event study plot, with the t intervals.

The robust estimator SHALL use only units observed in every period, as the R package `did` does by default (`allow_unbalanced_panel = FALSE`), and SHALL report how many units it left out.

#### Scenario: Staggered dataset
- **WHEN** the active dataset has staggered timing
- **THEN** the DiD tab's warning points to the robust tab, and the robust tab shows the three-way comparison

#### Scenario: Unbalanced panel
- **WHEN** some unit lacks an outcome in some period
- **THEN** that unit is left out, the estimate equals the one on the panel balanced beforehand, and the tab states how many units were left out

#### Scenario: No complete unit
- **WHEN** no unit is observed in every period
- **THEN** the tab shows an error instead of crashing

### Requirement: Estimator options are validated
The robust estimator SHALL accept only the comparison groups `never_treated` and `not_yet_treated`, and at least 2 bootstrap replications. Any other value SHALL raise an error naming it; it SHALL NOT fall back to another comparison group.

#### Scenario: Misspelt comparison group
- **WHEN** `estimate_staggered_did` is called with `comparison = "never-treated"`
- **THEN** it raises an error naming the value and the allowed comparison groups

#### Scenario: Too few bootstrap replications
- **WHEN** it is called with `n_bootstrap = 1`
- **THEN** it raises an error instead of returning a missing standard error

### Requirement: Warning when cohorts are small
The system SHALL report the number of units in the smallest adoption cohort. When it is below 5, the Estimation page and the report SHALL say that the estimates rest on few units and that the interval accounts for it with a Student t on the stated degrees of freedom.

#### Scenario: Cohorts of three units
- **WHEN** Callaway & Sant'Anna is estimated on a panel whose smallest cohort has 3 units
- **THEN** the page and the report explain that the interval is wide because it uses a t distribution with few degrees of freedom
