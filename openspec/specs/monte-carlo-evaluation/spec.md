# monte-carlo-evaluation Specification

## Purpose
Repeatedly draws a fresh synthetic dataset from the Virtual World DGP, applies the DiD estimator, and aggregates bias, RMSE, MAE, confidence-interval coverage, and average CI length across replications — used to see how estimator performance degrades as causal threats are turned on.

## Requirements

### Requirement: Replication and aggregation
The system SHALL run a configurable number of independent replications, each with its own synthetic dataset and DiD estimate, and aggregate their results.

#### Scenario: Running a Monte Carlo simulation
- **WHEN** `run_monte_carlo(config, n_reps, ci_level=0.95, base_seed=0)` is called
- **THEN** it generates `n_reps` synthetic datasets, one per replication, each with `seed = base_seed + replication_index` and otherwise identical config, estimates the DiD ATT on each with `estimate_did`, and returns a `MonteCarloSummary` with `bias` (mean of estimate minus true ATT), `rmse`, `mae`, `coverage` (share of replications whose estimate ± z·SE interval contains the true ATT), `avg_ci_length`, `mean_estimate`, `true_att`, and the full list of point estimates

#### Scenario: Confidence level determines the critical value
- **WHEN** `ci_level` is 0.95
- **THEN** the coverage check uses the two-sided normal critical value z ≈ 1.95996; any other `ci_level` value uses z ≈ 1.64485 (the one other value supported)

### Requirement: Triggering from the app
The system SHALL only offer Monte Carlo simulation when a Virtual World dataset (not an uploaded real-world dataset) is active, since it needs a known ground truth.

#### Scenario: Virtual World active
- **WHEN** a Virtual World dataset has been generated
- **THEN** the Virtual Lab page shows a "Run Monte Carlo" control with a selectable replication count (100/500/1000/5000) and, once run, displays bias, RMSE, 95% CI coverage, average CI length, and a histogram of estimates with the true ATT marked
