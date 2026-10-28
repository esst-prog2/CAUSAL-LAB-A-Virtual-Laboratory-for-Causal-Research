# method-stress-test Specification

## Purpose
TBD - created by archiving change methods-monte-carlo-stress-code. Update Purpose after archive.

## Requirements

### Requirement: Break My Design for the six Causal Methods
For a Causal Methods estimate, the system SHALL run, on request, checks aimed at the method's identifying assumption. Each check returns PASS, WARNING or N/A with a translated message, and the result is summarized by the same Identification Strength score as the DiD stress test. The checks are:
- **RCT:** a joint HC1 Wald test that the covariates do not predict treatment, and a minimum arm size of 30.
- **Matching:** at most 5% of treated units outside the control propensity range; no standardized difference above 0.1 after matching; at most 5% of propensity scores beyond 0.95 or below 0.05; and agreement of matching and IPW at 10%.
- **IV:** first-stage F of at least 10, and, with more than one instrument, the robust Wooldridge overidentification test at 10%.
- **RDD:** the manipulation test at 10%; a Hausman-type comparison of the estimates at h/2, h and 2h (Bonferroni, 10%); and placebo cutoffs at the median of the running variable on each side, each estimated with that side's data only (Bonferroni, 10%).
- **Synthetic control:**
  - a pre-treatment RMSPE of at most half the outcome's standard deviation;
  - leave-one-out of the main donor moving the estimate by at most 2 pre-treatment RMSPE;
  - an in-time placebo halfway through the pre-period, with a placebo p-value of at least 0.05.
- **DML:** the covariates explain at most 95% of the treatment's variance, and another sample split moves the estimate by at most 0.75 SE.

#### Scenario: Threats turned on in the worlds
- **WHEN** the checks run on worlds with instrument strength 0.05 or 0.3 (IV, F = 4.4), 40 observations (RCT), confounding strength 3 (Matching) or noise 3 (Synthetic control)
- **THEN** the weak-instrument, arm-size, balance-after-matching and extreme-propensity, and pre-fit checks warn respectively

#### Scenario: Calibrated false alarms
- **WHEN** each check runs on 200 default worlds of its method (20 for DML)
- **THEN** its warning rate is at most 14%, as measured in `spike/method_calibration_results.md`

#### Scenario: Not applicable
- **WHEN** an RCT has no covariates, or an IV has one instrument
- **THEN** the balance check, respectively the overidentification check, is N/A and left out of the score

### Requirement: A non-rejection is reported as absence of evidence
The system SHALL word a check that passes because a test did not reject as an absence of evidence ("no significant difference", "no evidence against"), never as a proof that the property holds. A passing overidentification test SHALL also say that it cannot establish the validity of the instruments.

#### Scenario: Overidentification test not rejected
- **WHEN** the IV overidentification test does not reject
- **THEN** the message says there is no evidence against the overidentifying restrictions, and that this cannot show the instruments are valid
