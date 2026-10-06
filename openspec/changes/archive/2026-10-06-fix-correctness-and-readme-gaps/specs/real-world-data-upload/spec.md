## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Treatment timing inferred for uploaded data
The system SHALL infer the treatment date of uploaded data from the treatment column instead of assuming the median period. The treatment date SHALL be the first period in which any unit has D = 1. Timing SHALL be considered staggered when units first have D = 1 in different periods.

#### Scenario: Uploaded panel with treatment starting in period 6
- **WHEN** the uploaded data's treated units first have D = 1 in period 6
- **THEN** the Estimation, Break My Design and Robustness pages use 6 as the treatment period

#### Scenario: Treatment without variation
- **WHEN** an uploaded CSV has the five required columns but `D` takes a single value
- **THEN** the upload is rejected with an error explaining that some observations must be treated and some untreated
