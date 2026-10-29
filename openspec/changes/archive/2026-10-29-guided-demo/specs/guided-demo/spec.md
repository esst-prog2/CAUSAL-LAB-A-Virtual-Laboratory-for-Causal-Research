## ADDED Requirements

### Requirement: The demo reports a simulation study, not a single draw
The system SHALL show, for each level of diverging pre-trends, the performance of the DiD estimator over at least 1,000 simulated worlds:
- bias, RMSE, the empirical SE against the mean model SE, coverage of the 95% confidence interval, rejection of H0: ATT = 0, and the rate at which the pre-trend test warns, with Monte Carlo standard errors;
- the coverage among the worlds in which the pre-trend test does not warn.

#### Scenario: Reading the study
- **WHEN** the researcher opens the Guided Demo page
- **THEN** a table gives these statistics for the levels none, low, medium, high and severe, and the text states the coverage under parallel trends and under severe violation, each taken from that table

### Requirement: The study is reproducible
The system SHALL store every replication of the study with its seed, and SHALL let the researcher re-run the first 100 worlds of any level and compare them, value by value, with the stored ones.

#### Scenario: Live re-run
- **WHEN** the researcher re-runs 100 worlds of the severe level
- **THEN** the page says whether they are identical to the stored replications

### Requirement: The published Card & Krueger table is replicated cell by cell
The system SHALL recompute rows 1, 2 and 4 of Card & Krueger (1994), Table 3, from the raw data, and show each published value next to the recomputed one. It SHALL state how many cells agree to two decimals, and explain any that do not.

#### Scenario: Replication
- **WHEN** the researcher opens the replication section
- **THEN** 17 of the 18 published numbers agree to two decimals, the difference-in-differences is 2.75 (1.34) in both, and the remaining standard error is explained by rounding
