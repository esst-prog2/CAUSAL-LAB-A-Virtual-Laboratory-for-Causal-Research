# app-navigation Specification

## Purpose
Lets the researcher move between the app's pages from the sidebar and from the dashboard shortcuts, without losing their place when the interface language changes.

## Requirements

### Requirement: Dashboard shortcuts open their pages
The system SHALL make each dashboard shortcut button open its page:
- "Start a New Research Project" opens Research Question;
- "Start a Virtual Experiment" opens Virtual Lab;
- "Diagnose My Research Design" opens Break My Design.

#### Scenario: Starting a virtual experiment
- **WHEN** the researcher clicks "Start a Virtual Experiment" on the dashboard
- **THEN** the Virtual Lab page is shown and selected in the sidebar

### Requirement: Page selection survives a language switch
The system SHALL identify pages by a language-independent id, so switching the language keeps the current page.

#### Scenario: Switching to French on a page
- **WHEN** the researcher is on Break My Design and switches the language from EN to FR
- **THEN** Break My Design is still shown, now labelled in French
