## ADDED Requirements

### Requirement: Opened panels are checked like uploads
The system SHALL check the panel datasets of an opened project file as it checks an uploaded CSV. A panel that lacks a required column, or whose indicators are not 0/1, SHALL make the file be refused with the reason. Rows with a missing unit, period or outcome SHALL be left out.

#### Scenario: A hand-edited project without treated_unit
- **WHEN** the researcher opens a project file whose uploaded panel has no treated_unit column
- **THEN** the file is refused, the message names the column, and the current project is kept
