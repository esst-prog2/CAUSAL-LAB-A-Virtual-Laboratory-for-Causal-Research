# rdd-estimation Specification

## Purpose
Estimates the effect of a treatment assigned by whether a running variable crosses a known cutoff (sharp regression discontinuity design), at the cutoff, by local linear regression.

## Requirements

### Requirement: Sharp RD local linear estimate
The system SHALL treat observations with running variable at or above the cutoff as treated. It SHALL fit separate linear regressions on each side of the cutoff, using only observations within a bandwidth of the cutoff and weighted by the triangular kernel (1 - |x - c| / h) / h. It SHALL report the jump in the fitted outcome at the cutoff, with an HC1 standard error computed side by side (as rdrobust's vce = "hc1"), a 95% confidence interval and a p-value.

#### Scenario: Estimating the discontinuity
- **WHEN** the RDD estimator is run with an outcome column, a running-variable column and a cutoff value
- **THEN** it reports the estimated jump at the cutoff, its standard error, confidence interval, p-value, the bandwidth used, and the number of observations used on each side

#### Scenario: Reproducing rdrobust
- **WHEN** the estimator and rdrobust (h fixed, triangular kernel, p = 1, vce = "hc1") run on the same data
- **THEN** the conventional estimate and standard error agree to floating-point rounding

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

### Requirement: Robust bias-corrected inference
The system SHALL always compute the robust bias-corrected inference of Calonico, Cattaneo & Titiunik (2014): the leading bias is estimated by a local quadratic fit with bias bandwidth b, which defaults to h as in rdrobust when only h is given. It SHALL report the bias-corrected estimate, its robust standard error, CI and p-value. When the researcher chooses robust inference, the reported standard error, CI and p-value SHALL be the robust ones, while the point estimate stays the conventional one.

#### Scenario: Reproducing rdrobust's robust row
- **WHEN** robust inference is chosen with h fixed
- **THEN** the bias-corrected estimate and the robust standard error equal rdrobust's "Bias-Corrected" coefficient and "Robust" standard error to floating-point rounding

#### Scenario: A wide bandwidth biases the estimate
- **WHEN** the RDD world has curvature 5 and the bandwidth is set to 0.6
- **THEN** the robust CI covers the true effect in more than 90% of 150 Monte Carlo worlds, where the conventional CI covers it in less than 80%

### Requirement: Fuzzy RD
When a treatment-received column is mapped, the system SHALL estimate a fuzzy RD: the jump in the outcome divided by the jump in the treatment at the cutoff (local Wald estimate), with the same kernel and bandwidth. The standard error SHALL come from the delta method, and the robust inference SHALL follow rdrobust's fuzzy formulas. The system SHALL report the first-stage jump with its standard error and F statistic, SHALL warn when F < 10, and SHALL refuse data in which the treatment does not jump at the cutoff.

#### Scenario: Reproducing rdrobust's fuzzy estimate
- **WHEN** the estimator and rdrobust with `fuzzy` run on the same data
- **THEN** the conventional estimate and standard error, the bias-corrected estimate and the robust standard error agree to floating-point rounding

#### Scenario: Fuzzy virtual world
- **WHEN** the RDD world is generated with compliance 0.6 and effect 2
- **THEN** the first-stage jump is about 0.6 and the fuzzy estimate is within three standard errors of 2, while a sharp estimate on the same data recovers about 0.6 × 2
