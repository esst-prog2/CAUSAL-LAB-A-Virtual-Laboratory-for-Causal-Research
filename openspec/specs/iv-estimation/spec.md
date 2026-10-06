# iv-estimation Specification

## Purpose
Estimates the effect of an endogenous treatment using an instrumental variable, by two-stage least squares, and reports whether the instrument is strong enough to trust the estimate.

## Requirements

### Requirement: Two-stage least squares estimate
The system SHALL estimate the treatment effect by two-stage least squares, with the treatment instrumented by one or more instrument columns and optional exogenous control columns. It SHALL report a heteroskedasticity-robust standard error, a 95% confidence interval and a p-value.

#### Scenario: Estimating with one instrument
- **WHEN** the IV estimator is run with an outcome, a treatment and an instrument column
- **THEN** it reports the 2SLS coefficient on the treatment, with its robust standard error, confidence interval, p-value and number of observations

### Requirement: First-stage strength diagnostic
The system SHALL report the first-stage F statistic of the excluded instruments, and SHALL warn that the estimate is unreliable when that statistic is below 10.

#### Scenario: Weak instrument
- **WHEN** the first-stage F statistic is below 10
- **THEN** the result includes a weak-instrument warning stating the F statistic

### Requirement: Naive OLS comparison
The system SHALL also report the ordinary-least-squares coefficient of the outcome on the treatment (with the same controls), so the researcher can see how far the instrumented estimate moves from the naive one.

#### Scenario: OLS reported next to 2SLS
- **WHEN** the IV estimator is run
- **THEN** the OLS coefficient and its standard error are reported next to the 2SLS estimate
