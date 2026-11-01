## MODIFIED Requirements

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

### Requirement: Warning when cohorts are small
The system SHALL report the number of units in the smallest adoption cohort. When it is below 5, the Estimation page and the report SHALL say that the estimates rest on few units and that the interval accounts for it with a Student t on the stated degrees of freedom.

#### Scenario: Cohorts of three units
- **WHEN** Callaway & Sant'Anna is estimated on a panel whose smallest cohort has 3 units
- **THEN** the page and the report explain that the interval is wide because it uses a t distribution with few degrees of freedom
