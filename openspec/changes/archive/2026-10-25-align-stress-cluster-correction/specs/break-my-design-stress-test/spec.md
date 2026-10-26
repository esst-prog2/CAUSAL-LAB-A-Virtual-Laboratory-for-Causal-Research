## MODIFIED Requirements

### Requirement: Parallel-trends pre-test
The system SHALL test for differential pre-treatment trends between treated and comparison units. It SHALL use a full-rank model: unit and period fixed effects plus one treated-group × pre-period dummy for every pre-treatment period except the last, which is the reference. The joint Wald test SHALL use unit-clustered CR1 covariance in which K does not count the unit dummies, as in the DiD estimator, with an F(q, G − 1) reference distribution. It SHALL attach a plain-language verdict:
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
- **THEN** the "Parallel Trends" check returns N/A with a message that there is not enough pre-treatment data to test pre-trends

#### Scenario: Small-sample correction worked out by hand
- **WHEN** the check runs on 4 units and 2 pre-treatment periods whose treated changes are 5 and 7 and control changes are −1 and 1
- **THEN** F = 36 / (28/15) = 135/7 on (1, 3) degrees of freedom, p = 0.0219, and the verdict is "questionable"

### Requirement: Spillover adjacency check
The system SHALL test whether control units adjacent to a treated unit (unit id distance 1) change after treatment differently from the other controls. On control units only, it SHALL use a DiD regression with unit and period fixed effects and SEs clustered by unit, with the same CR1 correction as the DiD estimator (unit dummies not counted in K) and a normal p-value. Adjacency alone SHALL NOT trigger a warning. The caller SHALL state explicitly whether unit ids encode a neighbourhood; the app states it only for a generated Virtual World.

#### Scenario: Adjacent control units exist
- **WHEN** the adjacent × post coefficient has p < 0.10
- **THEN** the "Spillovers" check returns WARNING, reporting the number of adjacent controls, the estimated shift and the p-value

#### Scenario: No adjacent control units
- **WHEN** adjacent controls exist but the adjacent × post coefficient has p ≥ 0.10
- **THEN** the "Spillovers" check returns PASS

#### Scenario: Too few adjacent or non-adjacent controls
- **WHEN** there are not enough adjacent and non-adjacent control units to run the regression
- **THEN** the "Spillovers" check returns N/A

#### Scenario: Non-numeric unit ids
- **WHEN** unit identifiers are not numeric
- **THEN** the check returns N/A, stating that no neighbourhood structure is available to test

#### Scenario: Unit ids without a neighbourhood
- **WHEN** the active data is uploaded or bundled real data
- **THEN** the "Spillovers" check returns N/A, stating that the unit ids do not encode a neighbourhood
