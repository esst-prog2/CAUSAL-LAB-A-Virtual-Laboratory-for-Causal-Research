## MODIFIED Requirements

### Requirement: Dashboard shortcuts open their pages
The system SHALL make each dashboard shortcut button open its page:
- "Open the guided demo", the primary action, opens Guided Demo;
- "Start a New Research Project" opens Research Question;
- "Start a Virtual Experiment" opens Virtual Lab;
- "Stress-test My Design" opens Break My Design;
- "Save or Open a Project" opens Settings.

#### Scenario: Starting a virtual experiment
- **WHEN** the researcher clicks "Start a Virtual Experiment" on the dashboard
- **THEN** the Virtual Lab page is shown and selected in the sidebar

### Requirement: Sidebar pages are grouped by workflow step
The system SHALL show the sidebar pages in six sections, in workflow order:
- Start: Dashboard, Guided Demo;
- Research design: Research Question, Causal Diagnosis, Method Recommendation;
- Data: Virtual Lab, External Data;
- Analysis: Estimation, Causal Methods, Theoretical Model;
- Stress test: Break My Design, Robustness;
- Output: Code Generator, Report, Settings.

No section SHALL hold more than four pages. Each section heading SHALL be in the interface language. Each page SHALL have an icon from the icon font bundled with Streamlit.

#### Scenario: Section headings follow the language
- **WHEN** the researcher switches the language to FR
- **THEN** the sidebar section headings are shown in French and the selected page stays the same

## ADDED Requirements

### Requirement: Pages are titled with their sidebar name
The system SHALL title every page except the dashboard with its sidebar name, in the interface language.

#### Scenario: Opening the Virtual Lab
- **WHEN** the researcher selects "Virtual Lab" in the sidebar
- **THEN** the page title is "Virtual Lab"

### Requirement: Empty pages offer a way out
When a page cannot show results yet, the system SHALL state the reason and offer buttons that remove it:
- with no dataset (Estimation, Break My Design, Robustness): open the Virtual Lab, or load the Card & Krueger (1994) data;
- with no diagnosis (Causal Diagnosis, Method Recommendation): open the Research Question form.

#### Scenario: Estimation without data
- **WHEN** the researcher opens Estimation with no dataset and clicks "Load the Card & Krueger (1994) data"
- **THEN** the Card & Krueger data become the active dataset and the estimates are shown

### Requirement: Dashboard states the guided demo's main finding
The system SHALL show the guided demo's main finding on the dashboard, computed from the stored simulation study. The finding SHALL take the level of diverging pre-trends at which the most worlds pass the pre-trend test, and state:
- how many worlds pass the test at that level;
- how often the DiD interval of those worlds covers the true effect.

#### Scenario: Stored study available
- **WHEN** the dashboard is opened and the stored simulation study is present
- **THEN** the finding is shown with the study's numbers, followed by a button that opens the guided demo

### Requirement: Text contrast and keyboard focus
The system SHALL keep the following at a contrast of at least 4.5:1, in both the light and the dark theme:
- captions;
- inline code in captions;
- sidebar labels;
- the selected tab.

The system SHALL show which sidebar page has the keyboard focus.

#### Scenario: Navigating the sidebar with the keyboard
- **WHEN** the researcher moves through the sidebar pages with the arrow keys
- **THEN** the focused page is outlined
