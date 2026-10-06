## MODIFIED Requirements

### Requirement: Replication and aggregation
The system SHALL run a configurable number of independent replications, each with its own synthetic dataset and DiD estimate, and aggregate their results. Each estimate SHALL be compared with the true ATT of its own replication.

#### Scenario: Running a Monte Carlo simulation
- **WHEN** `run_monte_carlo(config, n_reps, ci_level=0.95, base_seed=0)` is called
- **THEN** it generates `n_reps` synthetic datasets, one per replication, each with `seed = base_seed + replication_index` and otherwise identical config, and estimates the DiD ATT on each with `estimate_did`. It returns a `MonteCarloSummary` with:
  - `bias`: mean over replications of (estimate − that replication's true ATT);
  - `rmse` and `mae`;
  - `coverage`: the share of replications whose estimate ± z·SE interval contains that replication's true ATT;
  - `avg_ci_length` and `mean_estimate`;
  - `true_att`: the mean of the per-replication true ATTs;
  - the full list of point estimates

#### Scenario: Confidence level determines the critical value
- **WHEN** `ci_level` is any value in (0, 1)
- **THEN** the coverage check uses the two-sided normal critical value `z = Φ⁻¹(0.5 + ci_level / 2)`, e.g. ≈ 1.95996 for 0.95
