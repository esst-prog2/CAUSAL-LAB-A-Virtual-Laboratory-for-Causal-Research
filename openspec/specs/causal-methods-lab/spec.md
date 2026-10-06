# causal-methods-lab Specification

## Purpose
A single "Causal Methods" page where a researcher picks one of the six additional identification methods, feeds it either a synthetic world with a known true effect or their own CSV with mapped columns, and sees the estimate, its diagnostics and a method-specific plot.

## Requirements

### Requirement: Method selection page
The system SHALL provide a sidebar page, labelled through the translation system in English and French, on which the researcher selects one of: Randomized Controlled Trial, Matching / Propensity Score, Instrumental Variables, Regression Discontinuity, Synthetic Control, Double Machine Learning.

#### Scenario: Opening the page
- **WHEN** the researcher opens the Causal Methods page
- **THEN** they can choose any of the six methods, and the page shows that method's identifying assumption before any data is loaded

### Requirement: Per-method virtual world with known truth
The system SHALL offer, for every method, a synthetic data generator whose data satisfies that method's identifying assumption and whose true effect is known. The generator SHALL be reproducible from a random seed and SHALL expose the parameters that make the method succeed or fail (for example instrument strength, confounding strength, non-linearity).

#### Scenario: Generating and estimating on a virtual world
- **WHEN** the researcher generates a method's virtual world and runs the estimator
- **THEN** the page shows the estimate next to the true effect and the bias (estimate minus truth)

#### Scenario: Same seed, same data
- **WHEN** a method's virtual world is generated twice with the same parameters and seed
- **THEN** the two datasets are identical

### Requirement: CSV upload with column mapping
The system SHALL let the researcher upload a CSV for the selected method and map its columns to that method's roles:
- RCT: outcome, binary treatment, optional covariates
- Matching: outcome, binary treatment, one or more covariates
- IV: outcome, treatment, one or more instruments, optional controls
- RDD: outcome, running variable, cutoff value
- Synthetic Control: unit, period, outcome, treated unit, first treated period
- DML: outcome, treatment, one or more covariates

#### Scenario: Valid mapping
- **WHEN** every required role is mapped to a distinct numeric column (unit identifiers may be non-numeric)
- **THEN** the estimator runs on the uploaded data, and no true-effect comparison is shown

#### Scenario: Invalid mapping
- **WHEN** a required role is unmapped, two roles share a column, or a role that must be numeric is mapped to a non-numeric column
- **THEN** the page shows an error naming the offending role(s) and does not run the estimator

#### Scenario: Missing values
- **WHEN** mapped columns contain missing values
- **THEN** rows with missing values in any mapped column are dropped before estimation, and the number of dropped rows is reported

### Requirement: Estimator errors are shown, not raised
The system SHALL display an estimator's validation error (for example non-binary treatment, cutoff outside the data, unbalanced panel) as an error message on the page instead of crashing the app.

#### Scenario: Estimator rejects the data
- **WHEN** the selected estimator raises a validation error on the mapped data
- **THEN** the page shows the error text and the rest of the app keeps working

### Requirement: Method-specific visual
The system SHALL show, for each method, the plot that best supports its identifying assumption:
- RCT and Matching: covariate balance
- Matching: propensity-score overlap
- IV: first-stage relationship
- RDD: binned outcome against the running variable, with the fitted lines on each side of the cutoff
- Synthetic Control: treated vs synthetic paths and the placebo gaps
- DML: DML vs naive OLS estimates

#### Scenario: RDD plot
- **WHEN** an RDD estimate has been computed
- **THEN** the page shows binned outcome means against the running variable, with the cutoff marked and the two local linear fits drawn
