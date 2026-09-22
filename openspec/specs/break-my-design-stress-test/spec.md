# break-my-design-stress-test Specification

## Purpose
Runs a fixed battery of five diagnostic checks against a fitted DiD design on actual (real or simulated) panel data, producing a PASS/WARNING verdict for each threat plus an overall "Identification Strength" score out of 100. This is a diagnostic heuristic, not a statistical proof of causal identification, and is presented as such.

## Requirements

### Requirement: Parallel-trends pre-test
The system SHALL test for differential pre-treatment trends between treated and comparison units.

#### Scenario: Rejecting equal pre-trends
- **WHEN** a joint Wald test of the treated-group × period interaction terms on the pre-treatment subsample yields p < 0.10
- **THEN** the "Parallel Trends" check returns WARNING, reporting the p-value and stating that differential pre-trends threaten the parallel-trends assumption

#### Scenario: Not enough pre-treatment data
- **WHEN** the pre-treatment subsample has fewer than 2 distinct periods or fewer than 2 treated/control groups
- **THEN** the "Parallel Trends" check returns WARNING with a message that there is not enough pre-treatment data to test pre-trends

### Requirement: Anticipation check
The system SHALL test whether treated units' outcomes jump in the period immediately before treatment.

#### Scenario: Anticipatory jump detected
- **WHEN** the treated-group × immediately-pre-treatment-period interaction (HC1 robust SE, comparing the last two pre-treatment periods) has p < 0.10
- **THEN** the "Anticipation" check returns WARNING, reporting the p-value and noting possible anticipation

### Requirement: Spillover adjacency check
The system SHALL flag control units whose id is directly adjacent to a treated unit's id as a spillover risk.

#### Scenario: Adjacent control units exist
- **WHEN** at least one control unit's id differs by exactly 1 from a treated unit's id
- **THEN** the "Spillovers" check returns WARNING, reporting the count and share of adjacent controls

#### Scenario: No adjacent control units
- **WHEN** no control unit's id is adjacent to any treated unit's id
- **THEN** the "Spillovers" check returns PASS

### Requirement: Serial correlation check
The system SHALL test TWFE residuals for autocorrelation using the Durbin-Watson statistic.

#### Scenario: Statistic far from 2
- **WHEN** the Durbin-Watson statistic on the DiD model's residuals is below 1.5 or above 2.5
- **THEN** the "Serial Correlation" check returns WARNING, reporting the statistic and recommending clustering by unit or a wild-cluster bootstrap

### Requirement: Heterogeneous-effects check
The system SHALL flag high dispersion in post-treatment outcomes across treated units as a sign that a single ATT may mask heterogeneity.

#### Scenario: High dispersion
- **WHEN** there are at least 3 treated units and the coefficient of variation of their post-treatment outcome means exceeds 1.0
- **THEN** the "Heterogeneous Effects" check returns WARNING, reporting the coefficient of variation

#### Scenario: Too few treated units to assess
- **WHEN** fewer than 3 treated units have post-treatment observations
- **THEN** the "Heterogeneous Effects" check defaults to PASS with a message that there are too few treated units to assess heterogeneity

### Requirement: Overall identification strength score
The system SHALL summarize the five checks as a single 0-100 score.

#### Scenario: Computing the score
- **WHEN** all five checks have run
- **THEN** `identification_strength = 100 * (number of PASS checks) / 5`, and the app presents it as a diagnostic heuristic, not a formal proof of causal identification
