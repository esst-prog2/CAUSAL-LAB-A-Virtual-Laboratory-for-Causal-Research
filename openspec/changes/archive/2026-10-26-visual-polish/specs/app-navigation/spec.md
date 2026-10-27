## ADDED Requirements

### Requirement: Sidebar pages are grouped by workflow step
The system SHALL show the pages in the sidebar in five sections, in workflow order, with each heading in the interface language:
- Start: Dashboard, Research Question, Causal Diagnosis, Method Recommendation;
- Data: Virtual Lab, External Data;
- Analysis: Estimation, Causal Methods, Theoretical Model;
- Stress test: Break My Design, Robustness;
- Output: Code Generator, Report, Settings.

#### Scenario: Section headings follow the language
- **WHEN** the researcher switches the language to FR
- **THEN** the sidebar section headings are shown in French and the selected page stays the same

### Requirement: Dashboard shows the progress of the workflow
The system SHALL show on the dashboard one card for each of the research question, the diagnosis, the recommendations and the dataset, each marked done or not yet. The recommendations card SHALL give their number.

#### Scenario: After the diagnosis
- **WHEN** the researcher has set a research question and run the diagnosis, and has loaded no data
- **THEN** the question, diagnosis and recommendations cards are marked done, and the dataset card is marked not yet

### Requirement: The appearance loads nothing from the network
The system SHALL style the app with fonts and assets bundled with it, so opening the app sends no request outside the machine.

#### Scenario: Checking the configuration
- **WHEN** the Streamlit configuration is read
- **THEN** no setting points to an http or https URL, no custom font is loaded, and the server and usage-statistics privacy settings are unchanged
