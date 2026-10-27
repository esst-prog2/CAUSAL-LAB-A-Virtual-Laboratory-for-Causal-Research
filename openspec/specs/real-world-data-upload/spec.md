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

### Requirement: Bundled real dataset
The system SHALL let the researcher load the public Card & Krueger (1994) New Jersey / Pennsylvania fast-food dataset from the Virtual Lab page. The dataset SHALL ship in the repository with its documented provenance. It SHALL be loaded as uploaded real data: it replaces the active dataset and has no ground truth. Each store SHALL be its own unit: the file's `SHEET` number is not unique (two stores share sheet 407), so the unit is the store's row in the file and `SHEET` is kept as a separate column.

#### Scenario: Loading the Card & Krueger data
- **WHEN** the researcher clicks the "Load real data: Card & Krueger (1994)" button
- **THEN** the store-wave panel (unit, period, D, Y, treated_unit) becomes the active dataset, any Virtual World, its ground truth and its configuration snapshot are cleared, and the Estimation page shows no true-effect comparison

#### Scenario: Reproducing the published effect
- **WHEN** the DiD estimator runs on the loaded data
- **THEN** its estimate is within ±0.1 of the published +2.76 full-time-equivalent employees per store (Card & Krueger 1994, Table 3)

#### Scenario: Reproducing the published standard error
- **WHEN** the DiD estimator runs on the loaded data
- **THEN** its clustered standard error is within ±0.1 of the published 1.36

#### Scenario: One unit per store
- **WHEN** the data are loaded
- **THEN** there are 410 units, none with more than two rows, and the treated indicator is constant within each unit

### Requirement: Required column values are validated at upload time
After the required columns are found, the system SHALL check their values before the upload can become the active dataset: `D` and `treated_unit` SHALL contain only 0/1 values (booleans count as 0/1) and no missing value; `period` and `Y` SHALL be numeric. The indicators of an accepted upload SHALL be stored as integers.

#### Scenario: Text treatment indicator
- **WHEN** an uploaded CSV has the five required columns but `D` contains "yes"/"no"
- **THEN** the app shows an error naming `D` and stating the expected values, and the upload does NOT become the active dataset

#### Scenario: Valid indicators
- **WHEN** `D` and `treated_unit` contain only 0 and 1 and `period` and `Y` are numeric
- **THEN** the upload proceeds to the remaining checks, exactly as before

### Requirement: Incomplete rows are left out at upload
The system SHALL leave out uploaded rows with a missing unit, period or outcome Y, and SHALL tell the researcher how many rows it left out. Missing values in the D and treated_unit indicators SHALL still be refused, as before.

#### Scenario: Some outcomes are empty
- **WHEN** the researcher uploads a panel in which 24 rows have an empty Y
- **THEN** the dataset is loaded without those 24 rows, a message says 24 rows were left out, and every analysis page and the report run on it
