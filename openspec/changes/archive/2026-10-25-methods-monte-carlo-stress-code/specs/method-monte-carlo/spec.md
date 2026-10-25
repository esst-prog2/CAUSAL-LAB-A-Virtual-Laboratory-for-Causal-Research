## ADDED Requirements

### Requirement: Monte Carlo for the six Causal Methods
For a Causal Methods estimate on a virtual world, the system SHALL let the researcher run a Monte Carlo with a chosen number of replications. Replication r SHALL draw the world with the same settings and seed s + r, where s is the world's seed, and run the method exactly as the page does. The system SHALL report:
- bias, RMSE and MAE against each replication's true effect;
- the 95% CI coverage, mean CI length and mean SE over the sampling SD of the estimates;
- the share of replications that reject "no effect" at 5%;
- the number of replications the estimator refused;
- a histogram of the estimates.

For synthetic control, which has no standard error, coverage, CI length and the SE ratio SHALL be shown as unavailable, and rejections SHALL use the placebo p-value.

#### Scenario: Calibrated RCT
- **WHEN** the Monte Carlo runs 150 replications of the default RCT world
- **THEN** the bias is within three Monte Carlo standard errors of zero, the coverage is between 90% and 99%, and the SE ratio is between 0.8 and 1.25

#### Scenario: Weak instrument
- **WHEN** the IV world's instrument strength is lowered from 1.0 to 0.05
- **THEN** the absolute bias grows and the RMSE is more than three times larger

#### Scenario: Uploaded data
- **WHEN** the method's data were uploaded
- **THEN** the Monte Carlo tab states that it needs a virtual world
