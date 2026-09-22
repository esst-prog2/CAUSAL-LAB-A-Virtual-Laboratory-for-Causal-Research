# real-world-data-upload Specification

## Purpose
Lets a researcher upload their own panel CSV instead of using the synthetic Virtual World, so the same diagnosis, estimation, stress-test, and robustness pages work on real data.

## Requirements

### Requirement: CSV upload replaces the active dataset
The system SHALL parse an uploaded CSV with pandas and make it the active dataset, clearing any previously generated Virtual World dataset and its ground truth.

#### Scenario: Successful upload
- **WHEN** a CSV file is uploaded on the Virtual Lab page
- **THEN** it is parsed with `pandas.read_csv`, stored as the uploaded dataset, the previously generated Virtual World dataset is cleared from session state, and a success message reports the row count and detected column names

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
The system SHALL validate that an uploaded CSV contains all five required columns — `unit`, `period`, `Y`, `D`, `treated_unit` — immediately after it is parsed, before it can become the active dataset. Column names stay fixed; no column-mapping UI is offered.

#### Scenario: All required columns present
- **WHEN** an uploaded CSV parses successfully and contains `unit`, `period`, `Y`, `D`, and `treated_unit`
- **THEN** it becomes the active dataset, exactly as before

#### Scenario: Missing a required column
- **WHEN** an uploaded CSV parses successfully but is missing one or more of `unit`, `period`, `Y`, `D`, `treated_unit` (for example the treatment indicator `D`)
- **THEN** the app shows an error naming every missing column, and the upload does NOT become the active dataset — the previously active dataset (if any) is left unchanged
