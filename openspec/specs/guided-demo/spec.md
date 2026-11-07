# guided-demo Specification

## Purpose
TBD - created by archiving change guided-demo. Update Purpose after archive.

## Requirements

### Requirement: The demo reports a simulation study, not a single draw
The system SHALL show, for each of four threats (diverging pre-trends, confounding, staggered adoption with growing effects, anticipation) at five levels, the performance of the DiD estimator over at least 1,000 simulated worlds:
- bias, RMSE, the empirical SE against the mean model SE, coverage of the 95% confidence interval, rejection of H0: ATT = 0, and the rate at which the pre-trend test warns, with Monte Carlo standard errors;
- the coverage among the worlds in which the pre-trend test does not warn;
- the distribution of the bias over the worlds.

#### Scenario: Reading the study
- **WHEN** the researcher opens the Guided Demo page
- **THEN** one tab per threat gives these statistics for the levels none, low, medium, high and severe, with a figure of the bias distribution

### Requirement: The study is reproducible
The system SHALL store every replication of the study with its seed. It SHALL let the researcher re-run the first 20, 50 or 100 worlds of any level (20 by default) and compare them, value by value, with the stored ones. The page SHALL say about how long each world takes.

#### Scenario: Live re-run
- **WHEN** the researcher re-runs 20 worlds of the severe level
- **THEN** the page says whether they are identical to the stored replications

### Requirement: The published Card & Krueger table is replicated cell by cell
The system SHALL recompute rows 1, 2 and 4 of Card & Krueger (1994), Table 3, from the raw data, and show each published value next to the recomputed one. It SHALL state how many cells agree to two decimals, and explain any that do not.

#### Scenario: Replication
- **WHEN** the researcher opens the replication section
- **THEN** 17 of the 18 published numbers agree to two decimals, the difference-in-differences is 2.75 (1.34) in both, and the remaining standard error is explained by rounding

### Requirement: The demo judges each scenario by a stated decision rule
The system SHALL state the author's decision rule on how much bias is too much: |bias| ≤ 10% of the true effect and coverage of the 95% CI ≥ 90%. It SHALL also state when the rule was fixed. It SHALL mark each scenario as within or beyond the rule, and SHALL give, for each threat, the highest level up to which the DiD is acceptable.

#### Scenario: Overview of the threats
- **WHEN** the researcher reads the simulation study
- **THEN** an overview table names, for each threat, the level up to which the DiD meets the rule and the bias and coverage at the first level beyond it

### Requirement: README section 1 describes the demo's path
Section 1 of the README SHALL describe the December demo in three to six present-tense sentences, naming real screens, a real file and real numbers. Each number SHALL be the one the app shows.

#### Scenario: Reading section 1
- **WHEN** someone reads section 1 of the README
- **THEN** they find the path from the Research Question screen through Method Recommendation to the Guided Demo
- **AND** its figures match the Guided Demo: bias +0.236, 47% of the effect, coverage 31.3%, pre-trend test warning in 14.2% of the worlds

### Requirement: A second edit of a form field is kept
A form field on the Research Question or Virtual Lab page SHALL keep every edit, however many times it is changed, and SHALL show a value changed from outside it.

#### Scenario: Typing a second question
- **WHEN** the researcher types a question and then replaces it with another
- **THEN** the second question stays in the field and is the one analysed
