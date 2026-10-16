## MODIFIED Requirements

### Requirement: Excluding spillover-adjacent controls
The system SHALL re-estimate after excluding control units whose id is adjacent to a treated unit's id, when the caller states that unit ids encode a neighbourhood, unit ids are numeric, and such controls exist. Adjacency SHALL use the same definition as the Spillovers check (one shared function). The app SHALL state that ids encode a neighbourhood only for a generated Virtual World.

#### Scenario: Adjacent controls present
- **WHEN** unit ids encode a neighbourhood, are numeric, and at least one control unit's id differs by exactly 1 from a treated unit's id
- **THEN** the battery re-estimates on the subsample excluding those control units and reports a row "Excluding spillover-adjacent controls" noting how many were excluded

#### Scenario: No adjacent controls
- **WHEN** no control unit's id is adjacent to any treated unit's id
- **THEN** no "Excluding spillover-adjacent controls" row is added

#### Scenario: Non-numeric unit ids
- **WHEN** unit ids are not numeric
- **THEN** no "Excluding spillover-adjacent controls" row is added, and the battery does not fail

#### Scenario: Uploaded or real data
- **WHEN** the active data is uploaded or bundled real data
- **THEN** no "Excluding spillover-adjacent controls" row is added, and the Robustness page states that these unit ids do not encode a neighbourhood
