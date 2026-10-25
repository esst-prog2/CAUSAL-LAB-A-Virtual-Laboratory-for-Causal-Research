# code-generation Specification

## Purpose
Produces ready-to-run R, Python, and Stata scripts that reproduce the DiD analysis configured in the app, so the researcher can leave CAUSAL LAB and keep working in their own environment with full reproducibility.

## Requirements

### Requirement: Three-language script export
The system SHALL generate equivalent Python, R, and Stata scripts fitting the same two-way fixed-effects DiD model. Each script SHALL use the declared column names directly, without re-encoding them. Comments and printed labels SHALL be written in the interface language, while the executable code SHALL be identical across languages. The Python script SHALL apply the app's small-sample correction (unit dummies nested in the clusters not counted), so that it prints the app's standard error.

#### Scenario: Generating all three
- **WHEN** `generate_all(params, lang)` is called with a data file path, outcome/treatment/unit/time column names, an optional cluster column, and a language
- **THEN** it returns a dict with three keys, each a complete script string using the same outcome, treatment, unit, and time column names:
  - `"python"`: pandas + `statsmodels.formula.api.ols` with `cov_type="cluster"`;
  - `"r"`: `fixest::feols` with unit/period fixed effects and clustered SEs;
  - `"stata"`: `reghdfe` with `absorb(unit period)` and `vce(cluster ...)`, preceded by a comment on how to install `reghdfe`

#### Scenario: Numeric unit identifiers in Stata
- **WHEN** the unit column is numeric (as in every Virtual World)
- **THEN** the Stata script contains no `encode` step, which would fail on a numeric variable, and absorbs the unit column as is

#### Scenario: French scripts
- **WHEN** the scripts are generated with `lang = "fr"`
- **THEN** their comments and printed labels are in French, and the lines that differ from the English scripts are only comments, headers and printed labels

#### Scenario: Python reproduces the app's standard error
- **WHEN** the Python script runs on the Card & Krueger data
- **THEN** it prints the app's ATT and standard error (1.34), not the 1.91 of statsmodels' default correction

### Requirement: Clustering defaults to the unit column
The system SHALL cluster standard errors on the unit column in all three generated scripts unless a different cluster column is specified.

#### Scenario: No cluster column supplied
- **WHEN** `CodeGenParams.cluster_col` is not set
- **THEN** all three generated scripts cluster standard errors on `unit_col`

### Requirement: Scripts are downloadable from the app
The system SHALL let the researcher download each generated script directly from the Code page.

#### Scenario: Viewing and downloading
- **WHEN** the Code page is open
- **THEN** it shows the Python, R, and Stata scripts in separate tabs with syntax highlighting, each with its own download button (`causal_lab_did.py`, `causal_lab_did.R`, `causal_lab_did.do`)
