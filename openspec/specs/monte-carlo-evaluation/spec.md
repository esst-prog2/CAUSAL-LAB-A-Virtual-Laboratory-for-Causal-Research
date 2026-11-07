# monte-carlo-evaluation Specification

## Purpose
Repeatedly draws a fresh synthetic dataset from the Virtual World DGP, applies the DiD estimator, and aggregates bias, RMSE, MAE, confidence-interval coverage, and average CI length across replications — used to see how estimator performance degrades as causal threats are turned on.

## Requirements

### Requirement: Replication and aggregation
The system SHALL run a configurable number of independent replications, each with its own synthetic dataset and DiD estimate, and aggregate their results. Each estimate SHALL be compared with the true ATT of its own replication.

#### Scenario: Running a Monte Carlo simulation
- **WHEN** `run_monte_carlo(config, n_reps, ci_level=0.95, base_seed=0)` is called
- **THEN** it generates `n_reps` synthetic datasets, one per replication, each with `seed = base_seed + replication_index` and otherwise identical config, and estimates the DiD ATT on each with `estimate_did`. It returns a `MonteCarloSummary` with:
  - `bias`: mean over replications of (estimate − that replication's true ATT);
  - `rmse` and `mae`;
  - `coverage`: the share of replications whose estimate ± t·SE interval contains that replication's true ATT;
  - `avg_ci_length` and `mean_estimate`;
  - `true_att`: the mean of the per-replication true ATTs;
  - the full list of point estimates

#### Scenario: Confidence level determines the critical value
- **WHEN** `ci_level` is any value in (0, 1)
- **THEN** the coverage check uses the two-sided Student t critical value with n_units - 1 degrees of freedom, the interval the app reports

### Requirement: Triggering from the app
The system SHALL only offer Monte Carlo simulation when a Virtual World dataset (not an uploaded real-world dataset) is active, since it needs a known ground truth.

#### Scenario: Virtual World active
- **WHEN** a Virtual World dataset has been generated
- **THEN** the Virtual Lab page shows a "Run Monte Carlo" control with a selectable replication count (100/500/1000/5000) and, once run, displays bias, RMSE, 95% CI coverage, average CI length, and a histogram of estimates with the true ATT marked
