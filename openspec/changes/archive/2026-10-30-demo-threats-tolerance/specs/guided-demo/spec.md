## MODIFIED Requirements

### Requirement: The demo reports a simulation study, not a single draw
The system SHALL show, for each of four threats (diverging pre-trends, confounding, staggered adoption with growing effects, anticipation) at five levels, the performance of the DiD estimator over at least 1,000 simulated worlds:
- bias, RMSE, the empirical SE against the mean model SE, coverage of the 95% confidence interval, rejection of H0: ATT = 0, and the rate at which the pre-trend test warns, with Monte Carlo standard errors;
- the coverage among the worlds in which the pre-trend test does not warn;
- the distribution of the bias over the worlds.

#### Scenario: Reading the study
- **WHEN** the researcher opens the Guided Demo page
- **THEN** one tab per threat gives these statistics for the levels none, low, medium, high and severe, with a figure of the bias distribution

## ADDED Requirements

### Requirement: The demo judges each scenario by a stated decision rule
The system SHALL state the author's decision rule on how much bias is too much: |bias| ≤ 10% of the true effect and coverage of the 95% CI ≥ 90%. It SHALL also state when the rule was fixed. It SHALL mark each scenario as within or beyond the rule, and SHALL give, for each threat, the highest level up to which the DiD is acceptable.

#### Scenario: Overview of the threats
- **WHEN** the researcher reads the simulation study
- **THEN** an overview table names, for each threat, the level up to which the DiD meets the rule and the bias and coverage at the first level beyond it
