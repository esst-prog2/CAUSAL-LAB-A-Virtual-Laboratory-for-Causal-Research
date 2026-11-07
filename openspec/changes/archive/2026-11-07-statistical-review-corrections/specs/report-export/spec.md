## MODIFIED Requirements

### Requirement: Project report
The system SHALL offer a Report page that generates, on request, a report of the current project in the interface language. The report SHALL contain:
- the research question and design;
- the diagnosis and recommendation when they were run;
- a description of the active data;
- the DiD estimate with its standard error, CI, p-value and N, and, for a Virtual World, the true ATT and the bias;
- the event-study coefficients, and the Callaway & Sant'Anna estimate when adoption is staggered;
- every stress-test check with its verdict and the qualitative summary of the checks;
- the robustness battery;
- the Causal Methods results already computed;
- the generated Python, R and Stata code.

Every number in it SHALL come from the same engines as the app pages, run on the active data.

#### Scenario: Report on a Virtual World
- **WHEN** the researcher generates a report after creating a staggered Virtual World and running the diagnosis and a Causal Methods estimate
- **THEN** the report holds every section above, and its estimated ATT, true ATT, summary of the checks and method estimate equal what the engines return

#### Scenario: Report on real data
- **WHEN** the active data are uploaded or bundled real data
- **THEN** the report describes their source and shows no true effect or bias

#### Scenario: Report without data
- **WHEN** no dataset is loaded
- **THEN** the report states that no research question or dataset is available, leaves out the estimation sections and still includes the generated code
