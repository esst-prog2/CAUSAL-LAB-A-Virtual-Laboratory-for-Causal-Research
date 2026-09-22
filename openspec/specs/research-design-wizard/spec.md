# research-design-wizard Specification

## Purpose
Collects structured answers about a research design — research question text, treatment type/timing, assignment mechanism, outcome type, unit of analysis, data structure, and pre/post period counts — into a single `ResearchDesignInput` record that drives the diagnosis and method-recommendation engines.

## Requirements

### Requirement: Structured design input collection
The system SHALL collect research design attributes through a form-based wizard (Streamlit "Research Question" page) and store them in a `ResearchDesignInput` record.

#### Scenario: Default design values
- **WHEN** no design fields have been edited yet
- **THEN** `treatment_type` defaults to "binary", `treatment_timing` to "single_date", `assignment_mechanism` to "policy", `outcome_type` to "continuous", `data_structure` to "panel", `unit_of_analysis` to "individual", `has_pre_treatment_periods` to true, and `n_pre_periods`/`n_post_periods` both default to 1

#### Scenario: Available field choices
- **WHEN** the wizard renders its selectors
- **THEN** `treatment_type` offers binary/continuous/multiple, `treatment_timing` offers single_date/staggered/continuous_time, `assignment_mechanism` offers random/policy/geographic/self_selected/threshold, `outcome_type` offers continuous/binary/count/survival/categorical, and `data_structure` offers cross_section/panel/repeated_cross_section/time_series/spatial/spatio_temporal_panel/experimental/survey/administrative

### Requirement: Diagnosis and recommendation trigger
The system SHALL compute a diagnosis and a ranked method recommendation from the current design input on demand, not automatically on every edit.

#### Scenario: Running the diagnosis
- **WHEN** the researcher clicks "Run Causal Diagnosis" after filling in the wizard
- **THEN** the app computes a `DiagnosisResult` from the current `ResearchDesignInput` and a ranked list of `MethodScore` recommendations from that diagnosis, stores both in session state, and shows a success message pointing to the Diagnosis and Recommendation pages

#### Scenario: Diagnosis page before any run
- **WHEN** the Diagnosis or Recommendation page is opened before "Run Causal Diagnosis" has ever been clicked
- **THEN** the page shows an informational message asking the researcher to fill in the Research Question wizard first, instead of an error
