# theory-data-calibration Specification

## Purpose
Ties a theoretical model to the data the researcher is using. Model parameters are computed from the dataset, and the model is solved once for every group or period the data structure supports.

## Requirements

### Requirement: Parameter sources
Each model parameter SHALL be set from exactly one source:
- **manual**: a fixed value.
- **statistic**: the mean, median, standard deviation, minimum, maximum, sum or count of a column, optionally restricted to rows where another column equals a given value.
- **regression**: the slope or intercept of an OLS regression of one column on another.

#### Scenario: Parameter from a filtered statistic
- **WHEN** a parameter is set to the mean of column `income` restricted to rows where `group == "A"`
- **THEN** its calibrated value equals that subgroup mean

#### Scenario: Unusable source
- **WHEN** a source refers to a missing or non-numeric column, or its filter selects no rows
- **THEN** calibration reports an error naming the parameter, and no equilibrium is computed for that unit

### Requirement: Data-structure detection
The system SHALL classify the dataset from its unit and period columns (either may be absent):
- **panel**: each unit observed in several periods.
- **repeated cross-section**: several periods, with units not repeated.
- **time series**: one unit over periods.
- **cross-section**: no period column.

It SHALL propose the matching default scope of computation: per period for panel, repeated cross-section and time series; pooled for cross-section.

#### Scenario: Panel dataset
- **WHEN** the active dataset is the Virtual Lab panel (unit, period)
- **THEN** it is classified as panel and the proposed scope is "per period"

### Requirement: Equilibrium per unit of computation
The system SHALL calibrate the parameters and solve the equilibrium separately for each unit of the chosen scope (the whole sample, each value of a group column, or each period). It SHALL return one row per unit with the calibrated parameters, equilibrium strategies, outcomes and verification status. When the scope is per period, the rows SHALL be ordered by period, forming an equilibrium path.

#### Scenario: Equilibrium path
- **WHEN** the scope is per period on a dataset with 20 periods
- **THEN** 20 equilibria are reported, one per period, in period order
