# code-generation Specification

## Purpose
Produces ready-to-run R, Python, and Stata scripts that reproduce the DiD analysis configured in the app, so the researcher can leave CAUSAL LAB and keep working in their own environment with full reproducibility.

## Requirements

### Requirement: Three-language script export
The system SHALL generate equivalent Python, R, and Stata scripts fitting the same two-way fixed-effects DiD model.

#### Scenario: Generating all three
- **WHEN** `generate_all(params)` is called with a data file path, outcome/treatment/unit/time column names, and an optional cluster column
- **THEN** it returns a dict with `"python"` (pandas + `statsmodels.formula.api.ols` with `cov_type="cluster"`), `"r"` (`fixest::feols` with unit/period fixed effects and clustered SEs), and `"stata"` (`reghdfe` with `absorb()` and `vce(cluster ...)`) keys, each a complete script string using the same outcome, treatment, unit, and time column names

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
