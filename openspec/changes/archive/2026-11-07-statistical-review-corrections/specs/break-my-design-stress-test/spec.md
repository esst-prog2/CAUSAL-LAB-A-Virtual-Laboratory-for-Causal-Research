## ADDED Requirements

### Requirement: A qualitative summary of the checks
The system SHALL summarize the checks aimed at the DiD's identifying assumption (parallel trends, anticipation, spillovers) in one of three categories, and SHALL NOT show a numerical score or call a design valid:
- warning: at least one such check warned;
- no warning: at least one was computed and none warned, stated as not being evidence of validity;
- insufficient: none could be computed.

Serial correlation and heterogeneous effects SHALL NOT enter the summary. A check returning N/A SHALL be shown as N/A.

#### Scenario: No identifying check computed
- **WHEN** the checks run on Card & Krueger, where only Heterogeneous Effects can be computed
- **THEN** the summary is "insufficient"

#### Scenario: A warning
- **WHEN** Parallel Trends warns
- **THEN** the summary is "warning"

## REMOVED Requirements

### Requirement: Overall identification strength score
**Reason**: Measured against the true bias, it does not track identification, and it counted checks unrelated to it (`docs/IDENTIFICATION_STRENGTH.md`).
**Migration**: Replaced by "A qualitative summary of the checks".

## MODIFIED Requirements

### Requirement: Checks are calibrated on the Virtual World
Each check SHALL fire rarely on a threat-free Virtual World and reliably on a world where its own threat is set to "severe". Measured over 200 seeded replications of the default Virtual World:
- each check's false-alarm rate in the clean world SHALL be at most 20%;
- each check's detection rate for its own threat SHALL be at least 80%.

The threat for each check is:
- Parallel Trends: `differential_trend`
- Anticipation: `anticipation`
- Spillovers: `spillovers`
- Serial Correlation: `serial_correlation`
- Heterogeneous Effects: `treatment_heterogeneity`

#### Scenario: Re-running the calibration spike
- **WHEN** `spike/stress_test_calibration.py` is run
- **THEN** every row of its table satisfies both bounds, and at least 65% of clean worlds raise no warning on the checks aimed at the identifying assumption
