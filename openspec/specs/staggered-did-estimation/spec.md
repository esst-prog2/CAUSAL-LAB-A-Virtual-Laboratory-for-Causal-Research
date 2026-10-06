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
- standard errors from a seeded unit-level bootstrap, with 95% confidence intervals.

#### Scenario: Recovering the truth where TWFE fails
- **WHEN** both estimators are run on staggered Virtual Worlds with `dynamic_effects = "severe"`
- **THEN** the Callaway & Sant'Anna estimate shows no detectable bias against the true ATT, while the TWFE estimate is clearly biased. Measured on 60 worlds: TWFE bias +0.21 with 38% CI coverage; Callaway & Sant'Anna bias +0.006 with 93% coverage

### Requirement: Estimation-page tab
The system SHALL show a "Robust DiD (Callaway & Sant'Anna)" tab on the Estimation page with:
- the robust ATT, its bootstrap SE and CI;
- a table comparing TWFE, Callaway & Sant'Anna and, for Virtual Worlds, the true ATT;
- the robust event study plot.

#### Scenario: Staggered dataset
- **WHEN** the active dataset has staggered timing
- **THEN** the DiD tab's warning points to the robust tab, and the robust tab shows the three-way comparison

#### Scenario: Unbalanced panel
- **WHEN** some unit lacks an outcome in some period
- **THEN** the tab shows an error asking for a balanced panel instead of crashing
