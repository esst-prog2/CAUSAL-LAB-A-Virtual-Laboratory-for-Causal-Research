## MODIFIED Requirements

### Requirement: Parallel-trends pre-test
The system SHALL test for differential pre-treatment trends between treated and comparison units. It SHALL use a full-rank model: unit and period fixed effects plus one treated-group × pre-period dummy for every pre-treatment period except the last, which is the reference. It SHALL attach a plain-language verdict:
- "plausible" when p ≥ 0.10;
- "questionable" when 0.01 ≤ p < 0.10;
- "violated" when p < 0.01.

#### Scenario: Rejecting equal pre-trends
- **WHEN** the joint Wald test of the treated-group × pre-period dummies on the pre-treatment subsample yields p < 0.10
- **THEN** the "Parallel Trends" check returns WARNING. It reports the p-value and the verdict ("questionable" or "violated"), and states that differential pre-trends threaten the parallel-trends assumption

#### Scenario: Diverging pre-trends in a synthetic world
- **WHEN** the check runs on a Virtual World generated with `differential_trend` = "severe"
- **THEN** the verdict is "questionable" or "violated", not "plausible"

#### Scenario: Not enough pre-treatment data
- **WHEN** the pre-treatment subsample has fewer than 2 distinct periods or fewer than 2 treated/control groups
- **THEN** the "Parallel Trends" check returns WARNING with a message that there is not enough pre-treatment data to test pre-trends

### Requirement: Anticipation check
The system SHALL test whether treated units' outcomes move in the period immediately before treatment. It SHALL compare each unit's change between the last two pre-treatment periods, treated versus control, which removes unit fixed effects.

#### Scenario: Anticipatory jump detected
- **WHEN** the regression of the per-unit change on the treated indicator (HC1 robust SE) gives p < 0.10
- **THEN** the "Anticipation" check returns WARNING, reporting the p-value and noting possible anticipation

### Requirement: Spillover adjacency check
The system SHALL test whether control units adjacent to a treated unit (unit id distance 1) change after treatment differently from the other controls. On control units only, it SHALL use a DiD regression with unit and period fixed effects and SEs clustered by unit. Adjacency alone SHALL NOT trigger a warning.

#### Scenario: Adjacent control units exist
- **WHEN** the adjacent × post coefficient has p < 0.10
- **THEN** the "Spillovers" check returns WARNING, reporting the number of adjacent controls, the estimated shift and the p-value

#### Scenario: No adjacent control units
- **WHEN** no control unit is adjacent to a treated unit, or adjacent controls exist but the adjacent × post coefficient has p ≥ 0.10
- **THEN** the "Spillovers" check returns PASS

#### Scenario: Non-numeric unit ids
- **WHEN** unit identifiers are not numeric
- **THEN** the check returns WARNING, stating that no neighbourhood structure is available to test

### Requirement: Serial correlation check
The system SHALL measure the first-order autocorrelation of the two-way fixed-effects residuals within units. It SHALL never difference consecutive rows that belong to different units. It SHALL correct the residual autocorrelation for the −1/(T−1) bias that unit fixed effects induce.

#### Scenario: Statistic far from 2
- **WHEN** the bias-corrected residual autocorrelation exceeds 0.2
- **THEN** the "Serial Correlation" check returns WARNING. It reports the within-unit Durbin-Watson statistic and the corrected autocorrelation, and recommends unit clustering or a wild-cluster bootstrap

### Requirement: Heterogeneous-effects check
The system SHALL compare the dispersion of unit-level pre/post outcome changes among treated units with that among control units. Under a homogeneous effect both reflect noise only. The comparison SHALL use a one-sided variance-ratio F test.

#### Scenario: High dispersion
- **WHEN** the variance-ratio F test gives p < 0.10
- **THEN** the "Heterogeneous Effects" check returns WARNING, reporting the variance ratio and p-value

#### Scenario: Too few treated units to assess
- **WHEN** fewer than 3 treated or fewer than 3 control units have both pre- and post-treatment observations
- **THEN** the check defaults to PASS with a message that there are too few units to assess heterogeneity

## ADDED Requirements

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
- **THEN** every row of its table satisfies both bounds, and the clean-world mean Identification Strength is at least 85/100
