## ADDED Requirements

### Requirement: Incomplete rows are left out at upload
The system SHALL leave out uploaded rows with a missing unit, period or outcome Y, and SHALL tell the researcher how many rows it left out. Missing values in the D and treated_unit indicators SHALL still be refused, as before.

#### Scenario: Some outcomes are empty
- **WHEN** the researcher uploads a panel in which 24 rows have an empty Y
- **THEN** the dataset is loaded without those 24 rows, a message says 24 rows were left out, and every analysis page and the report run on it
