## MODIFIED Requirements

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
