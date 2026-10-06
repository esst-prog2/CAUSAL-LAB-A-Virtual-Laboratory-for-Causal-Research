## Purpose

Estimates the effect of a treatment assigned by whether a running variable crosses a known cutoff (sharp regression discontinuity design), at the cutoff, by local linear regression.

## ADDED Requirements

### Requirement: Sharp RD local linear estimate
The system SHALL treat observations with running variable at or above the cutoff as treated. It SHALL fit separate linear regressions on each side of the cutoff, using only observations within a bandwidth of the cutoff and weighted by a triangular kernel, and SHALL report the jump in the fitted outcome at the cutoff, with a heteroskedasticity-robust standard error, a 95% confidence interval and a p-value.

#### Scenario: Estimating the discontinuity
- **WHEN** the RDD estimator is run with an outcome column, a running-variable column and a cutoff value
- **THEN** it reports the estimated jump at the cutoff, its standard error, confidence interval, p-value, the bandwidth used, and the number of observations used on each side

### Requirement: Data-driven default bandwidth
The system SHALL compute a mean-squared-error-optimal bandwidth from the data (Imbens–Kalyanaraman) when no bandwidth is supplied, and SHALL use a user-supplied bandwidth when one is given.

#### Scenario: No bandwidth supplied
- **WHEN** the RDD estimator is run without a bandwidth
- **THEN** the bandwidth used is computed from the data and reported

#### Scenario: Bandwidth supplied
- **WHEN** the RDD estimator is run with a positive bandwidth h
- **THEN** only observations with |running - cutoff| < h are used

### Requirement: Bandwidth sensitivity
The system SHALL report the estimate re-computed at half and at double the chosen bandwidth.

#### Scenario: Sensitivity table
- **WHEN** the RDD estimator is run
- **THEN** the result contains the estimates and standard errors at 0.5x, 1x and 2x the bandwidth

### Requirement: Manipulation check at the cutoff
The system SHALL test whether observations bunch on one side of the cutoff, by comparing the number of observations in equal-width windows just below and just above it, and SHALL warn when the imbalance is significant at the 5% level.

#### Scenario: Bunching above the cutoff
- **WHEN** significantly more observations lie just above the cutoff than just below it
- **THEN** the result includes a possible-manipulation warning with the counts and p-value

### Requirement: Cutoff must split the sample
The system SHALL reject a cutoff that leaves fewer than 10 observations within the bandwidth on either side, with an error stating the counts.

#### Scenario: Cutoff outside the data
- **WHEN** the cutoff lies outside (or at the edge of) the range of the running variable
- **THEN** the estimator raises an error instead of producing a number
