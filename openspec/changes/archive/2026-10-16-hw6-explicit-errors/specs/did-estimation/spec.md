## ADDED Requirements

### Requirement: Treatment must be numeric
The system SHALL treat a boolean treatment column as 0/1 and SHALL refuse a non-numeric treatment column with an error naming it. It SHALL never return a missing estimate in place of an error.

#### Scenario: Boolean treatment
- **WHEN** `estimate_did` is called with `D` stored as True/False
- **THEN** the estimate equals the one with `D` stored as 1/0

#### Scenario: Text treatment
- **WHEN** `estimate_did` is called with `D` stored as text (for example "yes"/"no")
- **THEN** it raises a ValueError stating that the treatment column is not numeric and must be a 0/1 indicator
