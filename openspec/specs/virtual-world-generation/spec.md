# virtual-world-generation Specification

## Purpose
Generates a synthetic panel dataset with an explicitly known ground truth (potential outcomes Y(0), Y(1), and a true Average Treatment Effect on the Treated), with a configurable "Causal Threats Generator" (confounding, spillovers, serial correlation, staggered adoption, treatment-effect heterogeneity). This lets the app show Estimated ATT vs. True ATT vs. Bias, which is the pedagogical core of the Virtual Lab.

## Requirements

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

### Requirement: Confounding threat
The system SHALL let the researcher introduce selection-on-a-covariate confounding at five intensity levels.

#### Scenario: Confounding enabled
- **WHEN** `confounding` is "low", "medium", "high", or "severe" (any level above "none")
- **THEN** exactly `round(n_units * share_treated)` units are drawn without replacement, each with probability proportional to a logistic propensity in a time-invariant covariate `X1`. `X1` also enters the outcome's trend term, so a naive comparison of treated vs. untreated units (without controlling for the confounder) would be biased

#### Scenario: Confounding disabled
- **WHEN** `confounding` is "none"
- **THEN** treated units are selected by simple random sampling, independent of `X1`

### Requirement: Staggered adoption threat
The system SHALL let treated units begin treatment at different times instead of all on the same date. Every treated unit SHALL actually be treated within the observed panel.

#### Scenario: Staggered adoption enabled
- **WHEN** `staggered_adoption` is true
- **THEN** each treated unit is independently assigned an adoption period drawn uniformly from `[treatment_period, min(n_periods - 1, treatment_period + max(1, n_periods // 3) - 1)]`, so every treated unit has D = 1 in at least one observed period

### Requirement: Spillover threat
The system SHALL let a currently-treated unit's effect partially leak to control units adjacent to it.

#### Scenario: Spillovers enabled
- **WHEN** `spillovers` is above "none" and a control unit's id is directly adjacent (distance 1) to a currently-treated unit's id
- **THEN** that control unit's observed outcome receives an additive spill bonus equal to `spill_strength * neighbor's individual treatment effect * 0.5`

### Requirement: Serial correlation and treatment-effect heterogeneity threats
The system SHALL let the researcher introduce AR(1) serially correlated errors and cross-unit treatment-effect heterogeneity independently of each other.

#### Scenario: Serial correlation enabled
- **WHEN** `serial_correlation` is above "none"
- **THEN** the idiosyncratic error follows a stationary AR(1) process with persistence `rho = min(0.95, intensity_value / 2.2)`. Its marginal standard deviation equals `noise_sd` in every period, including the first

#### Scenario: Treatment heterogeneity enabled
- **WHEN** `treatment_heterogeneity` is above "none"
- **THEN** each unit's individual treatment effect is drawn from `Normal(true_att, het_strength)` instead of every treated unit sharing exactly `true_att`, and the realized `true_att` returned in the truth dict is the mean of these unit-level effects among treated units

### Requirement: Diverging pre-trends threat
The system SHALL let the researcher make treated units' untreated outcomes drift away from controls, which violates parallel trends.

#### Scenario: Differential trend enabled
- **WHEN** `differential_trend` is above "none"
- **THEN** every treated unit's untreated outcome gains `0.08 * intensity_value * noise_sd * (period - treatment_period)`, so treated and control trends diverge before and after treatment

### Requirement: Anticipation threat
The system SHALL let treated units react one period before their own adoption, while D is still 0.

#### Scenario: Anticipation enabled
- **WHEN** `anticipation` is above "none"
- **THEN** in the period just before each treated unit's adoption, its observed outcome shifts by `0.5 * intensity_value * noise_sd` in the direction of `true_att`, and no other period changes

### Requirement: Analyses use the generating configuration
The system SHALL keep a snapshot of the configuration that generated the active Virtual World, and the analysis pages SHALL read the treatment period and timing from that snapshot.

#### Scenario: Editing a setting after generation
- **WHEN** the researcher changes the treatment-period widget after generating a Virtual World
- **THEN** the Estimation, Break My Design and Robustness pages keep using the treatment period the data was generated with, until a new world is generated

### Requirement: Dynamic treatment effects threat
The system SHALL let treatment effects grow with time since each unit's own adoption.

#### Scenario: Dynamic effects enabled
- **WHEN** `dynamic_effects` is above "none"
- **THEN** a treated unit's effect e periods after its adoption equals its base effect × (1 + 0.25 × intensity_value × e). Combined with staggered adoption, this biases two-way fixed effects
