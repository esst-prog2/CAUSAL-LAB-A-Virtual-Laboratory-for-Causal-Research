## ADDED Requirements

### Requirement: Required column values are validated at upload time
After the required columns are found, the system SHALL check their values before the upload can become the active dataset: `D` and `treated_unit` SHALL contain only 0/1 values (booleans count as 0/1) and no missing value; `period` and `Y` SHALL be numeric. The indicators of an accepted upload SHALL be stored as integers.

#### Scenario: Text treatment indicator
- **WHEN** an uploaded CSV has the five required columns but `D` contains "yes"/"no"
- **THEN** the app shows an error naming `D` and stating the expected values, and the upload does NOT become the active dataset

#### Scenario: Valid indicators
- **WHEN** `D` and `treated_unit` contain only 0 and 1 and `period` and `Y` are numeric
- **THEN** the upload proceeds to the remaining checks, exactly as before
