## ADDED Requirements

### Requirement: Logit QRE by maximum likelihood
For a matrix game and observed counts of each player's choices, the system SHALL estimate the logit QRE precision λ by maximum likelihood along the principal branch. The counts are either typed or counted in a dataset's columns.

It SHALL report:
- the curvature standard error;
- a 95% interval that inverts the likelihood-ratio test;
- the fitted against the observed frequencies;
- a likelihood-ratio test against random play.

When the likelihood is flat or rising to the end of the traced branch, the system SHALL report λ only as a lower bound.

#### Scenario: Gambit
- **WHEN** 40 random games with counts drawn from a QRE are estimated
- **THEN** λ equals Gambit's logit_estimate to 1e-4 relative and the log-likelihood to 2e-6, except on the plateau of choices that all fall on a pure equilibrium, where only the lower bound is reported and Gambit's value lies above it

#### Scenario: Interval
- **WHEN** the counts are proportional to a QRE at λ = 2
- **THEN** the estimate is 2 to 1e-6, and at each end of the interval twice the drop in log-likelihood is χ²₁(0.95) to 1e-6

### Requirement: GMM on first-order conditions
For a smooth continuous game and a dataset with one observed equilibrium per row, the system SHALL estimate the chosen parameters by two-step efficient GMM. The moments are the chosen agents' first-order conditions times a constant and the chosen instruments. Each other parameter is fixed or observed in a column.

It SHALL report:
- heteroskedasticity-robust standard errors and 95% intervals;
- the rows used and dropped;
- Hansen's J test when there are more moments than parameters.

It SHALL refuse, with a translated error, input that is under-identified, has collinear instruments, is not identified (a combination of parameters that does not move the moments), assigns two roles to one parameter, or comes from a non-smooth model.

#### Scenario: linearmodels
- **WHEN** firm 1's first-order condition of a Cournot dataset is linear in the parameters
- **THEN** the estimates, standard errors and J statistic equal linearmodels' IVGMM to 1e-8 relative

#### Scenario: Nonlinear model
- **WHEN** constant-elasticity Cournot data are generated from the closed-form equilibrium
- **THEN** the estimates are within 3 standard errors of the true values
