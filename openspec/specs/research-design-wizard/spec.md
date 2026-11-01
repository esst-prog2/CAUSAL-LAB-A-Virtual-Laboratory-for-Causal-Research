# research-design-wizard Specification

## Purpose
Collects structured answers about a research design — research question text, treatment type/timing, assignment mechanism, outcome type, unit of analysis, data structure, and pre/post period counts — into a single `ResearchDesignInput` record that drives the diagnosis and method-recommendation engines.

## Requirements

### Requirement: Structured design input collection
The system SHALL collect the research design attributes through a form-based wizard (the Streamlit "Research Question" page) and store them in a `ResearchDesignInput` record. The record SHALL include what identification needs:
- whether untreated comparison units are observed;
- the number of treated units;
- whether an instrument is available;
- whether all important confounders are measured.

#### Scenario: Default design values
- **WHEN** no design field has been edited yet
- **THEN** the fields have these defaults:
  - `treatment_type`: "binary";
  - `treatment_timing`: "single_date";
  - `assignment_mechanism`: "policy";
  - `outcome_type`: "continuous";
  - `data_structure`: "panel";
  - `unit_of_analysis`: "individual";
  - `has_pre_treatment_periods`: true;
  - `n_pre_periods` and `n_post_periods`: 1;
  - `has_control_group`: true;
  - `n_treated_units`: "many";
  - `instrument`: "unsure";
  - `confounders_observed`: "unsure".

#### Scenario: Available field choices
- **WHEN** the wizard renders its selectors
- **THEN** each selector offers these options:
  - `treatment_type`: binary, continuous, multiple;
  - `treatment_timing`: single_date, staggered, continuous_time;
  - `assignment_mechanism`: random, policy, geographic, self_selected, threshold;
  - `outcome_type`: continuous, binary, count, survival, categorical;
  - `data_structure`: cross_section, panel, repeated_cross_section, time_series, spatial, spatio_temporal_panel, experimental, survey, administrative;
  - `n_treated_units`: one, few, many;
  - `instrument`: available, none, unsure;
  - `confounders_observed`: measured, not_measured, unsure.

### Requirement: Diagnosis and recommendation trigger
The system SHALL compute a diagnosis and a ranked method recommendation from the current design input on demand, not automatically on every edit.

#### Scenario: Running the diagnosis
- **WHEN** the researcher clicks "Run Causal Diagnosis" after filling in the wizard
- **THEN** the app computes a `DiagnosisResult` from the current `ResearchDesignInput` and a ranked list of `MethodScore` recommendations from that diagnosis, stores both in session state, and shows a success message pointing to the Diagnosis and Recommendation pages

#### Scenario: Diagnosis page before any run
- **WHEN** the Diagnosis or Recommendation page is opened before "Run Causal Diagnosis" has ever been clicked
- **THEN** the page shows an informational message asking the researcher to fill in the Research Question wizard first, instead of an error
