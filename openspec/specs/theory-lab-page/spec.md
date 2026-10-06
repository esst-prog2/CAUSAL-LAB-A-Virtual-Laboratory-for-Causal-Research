# theory-lab-page Specification

## Purpose
A "Theoretical Model" page that walks the researcher through defining a model, solving its equilibrium on their data, and testing its predictions against causal estimates.

## Requirements

### Requirement: Page with three steps
The system SHALL provide a sidebar page, labelled through the translation system in English and French, organised in three steps:
1. **Model**: catalogue or editor, with equations.
2. **Equilibrium & data**: parameter sources, data source, scope, and the equilibrium table or path.
3. **Predictions**: comparative statics, treatment shift, and comparison with a causal estimate.

#### Scenario: Opening the page with no data
- **WHEN** the researcher opens the page with no dataset loaded
- **THEN** they can still choose a model, see its equations, and solve it with manual parameter values

### Requirement: Data sources
The system SHALL let the researcher calibrate on any of these datasets:
- the active Virtual Lab dataset (generated or uploaded);
- any dataset loaded on the Causal Methods page;
- a CSV uploaded on this page.

#### Scenario: Calibrating on the Virtual Lab panel
- **WHEN** a Virtual World has been generated and the researcher picks it as the data source
- **THEN** its columns are available as parameter sources and the detected structure is "panel"

### Requirement: Visual output
The system SHALL show:
- the equilibrium as a table;
- an equilibrium path chart when the scope is per period, or a per-group bar chart when it is per group;
- a chart of a selected equilibrium outcome as a function of a selected parameter over a range around its current value.

#### Scenario: Outcome curve
- **WHEN** the researcher selects outcome "total effort" and parameter "V" in the Tullock model
- **THEN** the page plots equilibrium total effort for V across a range around its current value

### Requirement: Solver failures are reported, not raised
The system SHALL display parsing, calibration and solver errors as messages on the page without crashing the app.

#### Scenario: Unsolvable custom model
- **WHEN** the solver finds no pure-strategy equilibrium for a custom model
- **THEN** the page shows that message and the rest of the app keeps working
