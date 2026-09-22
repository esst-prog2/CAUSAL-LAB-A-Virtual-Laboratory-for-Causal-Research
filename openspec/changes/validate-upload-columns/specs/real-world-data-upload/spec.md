## RENAMED Requirements

- FROM: `### Requirement: Required columns are not validated at upload time`
- TO: `### Requirement: Required columns are validated at upload time`

## MODIFIED Requirements

### Requirement: Required columns are validated at upload time
The system SHALL validate that an uploaded CSV contains all five required columns — `unit`, `period`, `Y`, `D`, `treated_unit` — immediately after it is parsed, before it can become the active dataset. Column names stay fixed; no column-mapping UI is offered.

#### Scenario: All required columns present
- **WHEN** an uploaded CSV parses successfully and contains `unit`, `period`, `Y`, `D`, and `treated_unit`
- **THEN** it becomes the active dataset, exactly as before

#### Scenario: Missing a required column
- **WHEN** an uploaded CSV parses successfully but is missing one or more of `unit`, `period`, `Y`, `D`, `treated_unit` (for example the treatment indicator `D`)
- **THEN** the app shows an error naming every missing column, and the upload does NOT become the active dataset — the previously active dataset (if any) is left unchanged
