## MODIFIED Requirements

### Requirement: Panel generation with known ground truth
The system SHALL generate a synthetic panel dataset from a `VirtualWorldConfig` and return both the dataset and a truth dictionary the estimator is never given.

#### Scenario: Basic generation
- **WHEN** `generate(config)` is called with `n_units`, `n_periods`, `treatment_period`, `share_treated`, and `true_att`
- **THEN** it returns a DataFrame with one row per (unit, period) containing columns `unit`, `period`, `treated_unit`, `post`, `treated_now`, `D`, `X1`, `Y0`, `Y1`, `Y`. It also returns a `truth` dict containing:
  - `true_att`: the mean of Y1 − Y0 over treated unit-periods (D = 1), which equals the mean unit effect among treated units when adoption is not staggered and effects are static;
  - `design_att`: the configured value;
  - `treated_units` and `adoption_period`

#### Scenario: Reproducibility via seed
- **WHEN** `generate(config)` is called twice with the same `seed` and otherwise identical config
- **THEN** it produces identical output, since all randomness is drawn from a `numpy` generator seeded by `config.seed`

## ADDED Requirements

### Requirement: Dynamic treatment effects threat
The system SHALL let treatment effects grow with time since each unit's own adoption.

#### Scenario: Dynamic effects enabled
- **WHEN** `dynamic_effects` is above "none"
- **THEN** a treated unit's effect e periods after its adoption equals its base effect × (1 + 0.25 × intensity_value × e). Combined with staggered adoption, this biases two-way fixed effects
