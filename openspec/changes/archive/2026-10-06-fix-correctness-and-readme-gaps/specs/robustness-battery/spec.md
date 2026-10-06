## MODIFIED Requirements

### Requirement: Alternative pre-treatment windows
The system SHALL re-estimate on samples restricted to windows symmetric around the treatment period.

#### Scenario: Restricted windows
- **WHEN** the battery runs
- **THEN** it re-estimates on `treatment_period - w <= period < treatment_period + w` for w = 3 and w = 5, labelled "Restricted window (±3 periods)" and "(±5 periods)". It skips a window that would leave fewer than 2 distinct periods or no treatment variation

### Requirement: Leave-one-treated-unit-out
The system SHALL re-estimate with each treated unit dropped one at a time, up to a performance cap. It SHALL report the spread of the resulting estimates, not a sampling standard error.

#### Scenario: Dropping treated units
- **WHEN** the battery runs and treated units exist
- **THEN** it re-estimates once per treated unit, for at most the first 10 treated units (sorted), dropping that unit's rows each time. It reports one summary row "Leave-one-treated-unit-out (range)" whose ATT is the mean of the per-drop ATTs, whose SE is empty (not applicable), and whose note gives the min/max ATT across drops

### Requirement: Excluding spillover-adjacent controls
The system SHALL re-estimate after excluding control units whose id is adjacent to a treated unit's id, when unit ids are numeric and such controls exist.

#### Scenario: Adjacent controls present
- **WHEN** unit ids are numeric and at least one control unit's id differs by exactly 1 from a treated unit's id
- **THEN** the battery re-estimates on the subsample excluding those control units and reports a row "Excluding spillover-adjacent controls" noting how many were excluded

#### Scenario: No adjacent controls
- **WHEN** no control unit's id is adjacent to any treated unit's id
- **THEN** no "Excluding spillover-adjacent controls" row is added

#### Scenario: Non-numeric unit ids
- **WHEN** unit ids are not numeric
- **THEN** no "Excluding spillover-adjacent controls" row is added, and the battery does not fail
