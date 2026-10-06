## Purpose

Shows, before any estimate, how the average outcome of treated and untreated units evolves over time, which is the first visual check of a difference-in-differences design.

## ADDED Requirements

### Requirement: Treated vs untreated average outcome plot
The system SHALL show on the Estimation page a line chart of the mean outcome per period for treated units and for untreated units. The treatment date SHALL be marked; with staggered timing, the mark SHALL be at the first adoption.

#### Scenario: Viewing the plot
- **WHEN** a Virtual World or an uploaded panel is active and the Estimation page is opened
- **THEN** the chart shows one line for treated and one for untreated units across all periods, with a vertical line just before the treatment period

#### Scenario: Diverging pre-trends are visible
- **WHEN** the active Virtual World was generated with `differential_trend` above "none"
- **THEN** the two lines visibly diverge before the treatment date in the chart
