# break-my-design-stress-test Specification

## Purpose
Runs a fixed battery of five diagnostic checks against a fitted DiD design on actual (real or simulated) panel data, producing a PASS/WARNING verdict for each threat plus an overall "Identification Strength" score out of 100. This is a diagnostic heuristic, not a statistical proof of causal identification, and is presented as such.

## Requirements

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

### Requirement: Anticipation check
The system SHALL test whether treated units' outcomes move in the period immediately before treatment. It SHALL compare each unit's change between the last two pre-treatment periods, treated versus control, which removes unit fixed effects.

#### Scenario: Anticipatory jump detected
- **WHEN** the regression of the per-unit change on the treated indicator (HC1 robust SE) gives p < 0.10
- **THEN** the "Anticipation" check returns WARNING, reporting the p-value and noting possible anticipation

#### Scenario: Not enough pre-treatment periods
- **WHEN** there are fewer than two pre-treatment periods, or the per-unit changes do not include both treated and control units
- **THEN** the "Anticipation" check returns N/A

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

### Requirement: Serial correlation check
The system SHALL measure the first-order autocorrelation of the two-way fixed-effects residuals within units. It SHALL never difference consecutive rows that belong to different units. It SHALL correct the residual autocorrelation for the −1/(T−1) bias that unit fixed effects induce.

#### Scenario: Statistic far from 2
- **WHEN** the bias-corrected residual autocorrelation exceeds 0.2
- **THEN** the "Serial Correlation" check returns WARNING. It reports the within-unit Durbin-Watson statistic and the corrected autocorrelation, and recommends unit clustering or a wild-cluster bootstrap

#### Scenario: Two periods
- **WHEN** the data have fewer than three distinct periods
- **THEN** the "Serial Correlation" check returns N/A, because the within-unit residuals of a two-period panel are mechanically opposite

### Requirement: Heterogeneous-effects check
The system SHALL compare the dispersion of unit-level pre/post outcome changes among treated units with that among control units. Under a homogeneous effect both reflect noise only. The comparison SHALL use a one-sided variance-ratio F test.

#### Scenario: High dispersion
- **WHEN** the variance-ratio F test gives p < 0.10
- **THEN** the "Heterogeneous Effects" check returns WARNING, reporting the variance ratio and p-value

#### Scenario: Too few treated units to assess
- **WHEN** fewer than 3 treated or fewer than 3 control units have both pre- and post-treatment observations
- **THEN** the check returns N/A with a message that there are too few units to assess heterogeneity

### Requirement: Overall identification strength score
The system SHALL summarize the checks that can be computed as a single 0-100 score. A check returning N/A SHALL be shown as N/A and SHALL NOT count in the score.

#### Scenario: Computing the score
- **WHEN** the five checks have run and k ≥ 1 of them are not N/A
- **THEN** `identification_strength = 100 * (number of PASS checks) / k`, the app states that the score is based on k of 5 checks, and presents it as a diagnostic heuristic, not a formal proof of causal identification

#### Scenario: No computable check
- **WHEN** all five checks return N/A
- **THEN** `identification_strength` is None and the app shows that no score is available

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

### Requirement: Computation errors are not threats
When the regression behind a check fails numerically on the data (singular design, a value error from the estimator), the check SHALL return N/A with the error message, and SHALL NOT return WARNING. Any other exception SHALL propagate rather than be hidden in a verdict.

#### Scenario: Singular design
- **WHEN** the regression of the Parallel Trends, Anticipation, Spillovers or Serial Correlation check raises a linear-algebra or value error
- **THEN** that check returns N/A, its message contains the error, and it is not counted in the score

#### Scenario: Programming error
- **WHEN** a check raises an exception of another type
- **THEN** the exception propagates

### Requirement: Calibration results are never overwritten silently
The calibration spike SHALL write its table only to an output file named explicitly on the command line. It SHALL check the destination before starting the simulation, SHALL refuse an existing file unless `--overwrite` is given, and SHALL report a failed write as an error with a non-zero exit status. The committed result files of 2026-10-03 and 2026-10-06 are historical records.

#### Scenario: No output argument
- **WHEN** `spike/stress_test_calibration.py` is run without an output argument
- **THEN** it exits with an error before simulating anything, and no file is modified

#### Scenario: Existing output file
- **WHEN** it is run with the name of an existing file and without `--overwrite`
- **THEN** it exits with an error before simulating anything, and the file is left byte-for-byte unchanged

#### Scenario: New output file
- **WHEN** it is run with a path that does not exist yet, in an existing folder
- **THEN** it runs the calibration unchanged and writes the table to that path

#### Scenario: Write failure
- **WHEN** the table cannot be written
- **THEN** it exits with an error stating that the results were not saved, and does not report success
