# real-world-data-upload Specification

## Purpose
Lets a researcher upload their own panel CSV instead of using the synthetic Virtual World, so the same diagnosis, estimation, stress-test, and robustness pages work on real data.

## Requirements

### Requirement: CSV upload replaces the active dataset
The system SHALL parse an uploaded CSV with pandas and make it the active dataset, clearing any previously generated Virtual World dataset and its ground truth. Each uploaded file SHALL be loaded only once, so a later Virtual World generation is not overridden by the same upload on the next rerun.

#### Scenario: Successful upload
- **WHEN** a CSV file is uploaded on the Virtual Lab page
- **THEN** it is parsed with `pandas.read_csv` and stored as the uploaded dataset. The previously generated Virtual World dataset, its ground truth and its configuration snapshot are cleared from session state, and a success message reports the row count and detected column names

#### Scenario: Generating after an upload
- **WHEN** a Virtual World is generated while the uploader still holds an earlier file
- **THEN** the generated world becomes the active dataset and stays active on every following rerun

#### Scenario: Unparsable file
- **WHEN** the uploaded file cannot be parsed as CSV by pandas
- **THEN** the app shows an error containing the exception message and does not change the active dataset

### Requirement: Uploaded data takes priority over generated data
The system SHALL prefer an uploaded dataset over a generated Virtual World dataset whenever both exist.

#### Scenario: Both datasets present
- **WHEN** an uploaded dataset exists in session state
- **THEN** the Diagnosis, Estimation, Break My Design, and Robustness pages all use the uploaded dataset rather than any previously generated Virtual World dataset

### Requirement: No ground-truth comparison for uploaded data
The system SHALL only show an Estimated-vs-True-ATT comparison when the active dataset came from the Virtual World generator, since uploaded data has no known ground truth.

#### Scenario: Uploaded dataset active
- **WHEN** the active dataset is an uploaded CSV (not a generated Virtual World)
- **THEN** the Estimation page shows the DiD estimate, standard error, and confidence interval, but does not show a "Ground truth comparison" section

### Requirement: Required columns are validated at upload time
The system SHALL validate that an uploaded CSV contains all five required columns — `unit`, `period`, `Y`, `D`, `treated_unit` — immediately after it is parsed, before it can become the active dataset. Column names stay fixed for this panel/DiD upload on the Virtual Lab page; no column-mapping UI is offered there. Column mapping exists only on the separate Causal Methods page, for the methods it hosts.

#### Scenario: All required columns present
- **WHEN** an uploaded CSV parses successfully and contains `unit`, `period`, `Y`, `D`, and `treated_unit`
- **THEN** it becomes the active dataset, exactly as before

#### Scenario: Missing a required column
- **WHEN** an uploaded CSV parses successfully but is missing one or more of `unit`, `period`, `Y`, `D`, `treated_unit` (for example the treatment indicator `D`)
- **THEN** the app shows an error naming every missing column, and the upload does NOT become the active dataset — the previously active dataset (if any) is left unchanged

### Requirement: Treatment timing inferred for uploaded data
The system SHALL infer the treatment date of uploaded data from the treatment column instead of assuming the median period. The treatment date SHALL be the first period in which any unit has D = 1. Timing SHALL be considered staggered when units first have D = 1 in different periods.

#### Scenario: Uploaded panel with treatment starting in period 6
- **WHEN** the uploaded data's treated units first have D = 1 in period 6
- **THEN** the Estimation, Break My Design and Robustness pages use 6 as the treatment period

#### Scenario: Treatment without variation
- **WHEN** an uploaded CSV has the five required columns but `D` takes a single value
- **THEN** the upload is rejected with an error explaining that some observations must be treated and some untreated
