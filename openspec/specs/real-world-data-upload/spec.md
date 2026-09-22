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

### Requirement: Required columns are not validated at upload time
The system SHALL accept any CSV that pandas can parse at upload time, without checking for the columns downstream analysis pages require.

#### Scenario: Missing a required column
- **WHEN** an uploaded CSV parses successfully but is missing a column a downstream page needs (for example the treatment indicator `D`, or `unit`/`period`/`Y`)
- **THEN** the upload itself succeeds with no error shown, and the missing-column failure only surfaces later, as a runtime error from the page that first accesses that column (there is no upload-time check that names the missing column)
