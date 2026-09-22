# virtual-world-generation Specification

## Purpose
Generates a synthetic panel dataset with an explicitly known ground truth (potential outcomes Y(0), Y(1), and a true Average Treatment Effect on the Treated), with a configurable "Causal Threats Generator" (confounding, spillovers, serial correlation, staggered adoption, treatment-effect heterogeneity). This lets the app show Estimated ATT vs. True ATT vs. Bias, which is the pedagogical core of the Virtual Lab.

## Requirements

### Requirement: Panel generation with known ground truth
The system SHALL generate a synthetic panel dataset from a `VirtualWorldConfig` and return both the dataset and a truth dictionary the estimator is never given.

#### Scenario: Basic generation
- **WHEN** `generate(config)` is called with `n_units`, `n_periods`, `treatment_period`, `share_treated`, and `true_att`
- **THEN** it returns a DataFrame with one row per (unit, period) containing columns `unit`, `period`, `treated_unit`, `post`, `treated_now`, `D`, `X1`, `Y0`, `Y1`, `Y`, and a `truth` dict containing `true_att` (the realized mean effect among treated units), `design_att` (the configured value), `treated_units`, and `adoption_period`

#### Scenario: Reproducibility via seed
- **WHEN** `generate(config)` is called twice with the same `seed` and otherwise identical config
- **THEN** it produces identical output, since all randomness is drawn from a `numpy` generator seeded by `config.seed`

### Requirement: Confounding threat
The system SHALL let the researcher introduce selection-on-a-covariate confounding at five intensity levels.

#### Scenario: Confounding enabled
- **WHEN** `confounding` is "low", "medium", "high", or "severe" (any level above "none")
- **THEN** treated-unit selection is biased toward units with higher values of a time-invariant covariate `X1` via a logistic propensity function, and `X1` also enters the outcome's trend term, so a naive comparison of treated vs. untreated units (without controlling for the confounder) would be biased

#### Scenario: Confounding disabled
- **WHEN** `confounding` is "none"
- **THEN** treated units are selected by simple random sampling, independent of `X1`

### Requirement: Staggered adoption threat
The system SHALL let treated units begin treatment at different times instead of all on the same date.

#### Scenario: Staggered adoption enabled
- **WHEN** `staggered_adoption` is true
- **THEN** each treated unit is independently assigned an adoption period drawn uniformly from `[treatment_period, treatment_period + n_periods // 3)`, instead of every treated unit sharing `treatment_period`

### Requirement: Spillover threat
The system SHALL let a currently-treated unit's effect partially leak to control units adjacent to it.

#### Scenario: Spillovers enabled
- **WHEN** `spillovers` is above "none" and a control unit's id is directly adjacent (distance 1) to a currently-treated unit's id
- **THEN** that control unit's observed outcome receives an additive spill bonus equal to `spill_strength * neighbor's individual treatment effect * 0.5`

### Requirement: Serial correlation and treatment-effect heterogeneity threats
The system SHALL let the researcher introduce AR(1) serially correlated errors and cross-unit treatment-effect heterogeneity independently of each other.

#### Scenario: Serial correlation enabled
- **WHEN** `serial_correlation` is above "none"
- **THEN** the idiosyncratic error term follows an AR(1) process with persistence `rho = min(0.95, intensity_value / 2.2)` instead of being independent across periods

#### Scenario: Treatment heterogeneity enabled
- **WHEN** `treatment_heterogeneity` is above "none"
- **THEN** each unit's individual treatment effect is drawn from `Normal(true_att, het_strength)` instead of every treated unit sharing exactly `true_att`, and the realized `true_att` returned in the truth dict is the mean of these unit-level effects among treated units
