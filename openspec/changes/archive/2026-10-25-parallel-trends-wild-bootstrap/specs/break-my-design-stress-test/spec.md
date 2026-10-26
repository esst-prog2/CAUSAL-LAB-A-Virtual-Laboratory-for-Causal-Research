## MODIFIED Requirements

### Requirement: Parallel-trends pre-test
The system SHALL test for differential pre-treatment trends between treated and comparison units. It SHALL use a full-rank model: unit and period fixed effects plus one treated-group × pre-period dummy for every pre-treatment period except the last, which is the reference. The p-value of the joint test SHALL come from a wild cluster restricted bootstrap of the unit-clustered Wald statistic, with Rademacher weights:
- all 2^G sign patterns when 2^G ≤ 1,000 (G = number of units);
- otherwise 999 draws with a fixed seed, p = (1 + exceedances) / 1,000.

It SHALL attach a plain-language verdict:
- "plausible" when p ≥ 0.10;
- "questionable" when 0.01 ≤ p < 0.10;
- "violated" when p < 0.01.

#### Scenario: Rejecting equal pre-trends
- **WHEN** the bootstrap test of the treated-group × pre-period dummies on the pre-treatment subsample yields p < 0.10
- **THEN** the "Parallel Trends" check returns WARNING. It reports the p-value and the verdict ("questionable" or "violated"), and states that differential pre-trends threaten the parallel-trends assumption

#### Scenario: Diverging pre-trends in a synthetic world
- **WHEN** the check runs on a Virtual World generated with `differential_trend` = "severe"
- **THEN** the verdict is "questionable" or "violated", not "plausible"

#### Scenario: Not enough pre-treatment data
- **WHEN** the pre-treatment subsample has fewer than 2 distinct periods or fewer than 2 treated/control groups
- **THEN** the "Parallel Trends" check returns N/A with a message that there is not enough pre-treatment data to test pre-trends

#### Scenario: Small-sample correction worked out by hand
- **WHEN** the check runs on 5 units and 2 pre-treatment periods whose treated changes are 19 and 21 and control changes are −1, 0 and 1
- **THEN** only the observed sign pattern and its opposite reach the observed Wald statistic, so p = 2/32 = 0.0625 and the verdict is "questionable"

#### Scenario: Too few units to reach the 10% level
- **WHEN** the pre-treatment subsample has fewer than 5 units, so that no Rademacher p-value can fall below 2/2^4 = 0.125
- **THEN** the "Parallel Trends" check returns N/A, stating the number of units and the minimum, instead of a PASS it could never fail

#### Scenario: Calibrated false-alarm rate
- **WHEN** the check runs on 1,000 default Virtual Worlds without threats
- **THEN** it warns on about 10% of them (10.4% measured on 2026-10-25), not on 18% as the asymptotic F(q, G − 1) test did
