# robustness-battery Specification

## Purpose
Re-runs the actual DiD estimator (never an approximation) on a fixed set of alternative, well-defined subsamples and specifications, so the researcher can see how sensitive the ATT estimate is to reasonable variations in the sample.

## Requirements

### Requirement: Baseline row always included
The system SHALL always report the full-sample baseline estimate first.

#### Scenario: Running the battery
- **WHEN** `run_robustness_battery(df, treatment_period)` is called
- **THEN** the first row is "Baseline (full sample)" with the ATT, SE, and n_obs from `estimate_did` on the unmodified data

### Requirement: Alternative pre-treatment windows
The system SHALL re-estimate on samples restricted to narrower windows around the treatment period.

#### Scenario: Restricted windows
- **WHEN** the battery runs
- **THEN** it re-estimates on the subsample with `period >= treatment_period - 3` (labeled "Restricted window (±3 periods)") and on `period >= treatment_period - 5` (labeled "±5 periods"), skipping either window if it would leave fewer than 2 distinct periods

### Requirement: Leave-one-treated-unit-out
The system SHALL re-estimate with each treated unit dropped one at a time, up to a performance cap.

#### Scenario: Dropping treated units
- **WHEN** the battery runs and treated units exist
- **THEN** it re-estimates once per treated unit, for at most the first 10 treated units (sorted), dropping that unit's rows each time, and reports one summary row "Leave-one-treated-unit-out (range)" whose ATT is the mean of the per-drop ATTs, whose SE is their standard deviation, and whose note gives the min/max ATT across drops

### Requirement: Excluding spillover-adjacent controls
The system SHALL re-estimate after excluding control units whose id is adjacent to a treated unit's id, when any exist.

#### Scenario: Adjacent controls present
- **WHEN** at least one control unit's id differs by exactly 1 from a treated unit's id
- **THEN** the battery re-estimates on the subsample excluding those control units and reports a row "Excluding spillover-adjacent controls" noting how many were excluded

#### Scenario: No adjacent controls
- **WHEN** no control unit's id is adjacent to any treated unit's id
- **THEN** no "Excluding spillover-adjacent controls" row is added
