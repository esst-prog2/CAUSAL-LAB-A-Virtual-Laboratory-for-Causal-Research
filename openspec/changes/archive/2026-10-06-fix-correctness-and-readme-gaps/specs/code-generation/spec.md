## MODIFIED Requirements

### Requirement: Three-language script export
The system SHALL generate equivalent Python, R, and Stata scripts fitting the same two-way fixed-effects DiD model. Each script SHALL use the declared column names directly, without re-encoding them.

#### Scenario: Generating all three
- **WHEN** `generate_all(params)` is called with a data file path, outcome/treatment/unit/time column names, and an optional cluster column
- **THEN** it returns a dict with three keys, each a complete script string using the same outcome, treatment, unit, and time column names:
  - `"python"`: pandas + `statsmodels.formula.api.ols` with `cov_type="cluster"`;
  - `"r"`: `fixest::feols` with unit/period fixed effects and clustered SEs;
  - `"stata"`: `reghdfe` with `absorb(unit period)` and `vce(cluster ...)`, preceded by a comment on how to install `reghdfe`

#### Scenario: Numeric unit identifiers in Stata
- **WHEN** the unit column is numeric (as in every Virtual World)
- **THEN** the Stata script contains no `encode` step, which would fail on a numeric variable, and absorbs the unit column as is
