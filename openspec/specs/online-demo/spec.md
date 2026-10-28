# online-demo Specification

## Purpose
TBD - created by archiving change online-demo. Update Purpose after archive.

## Requirements

### Requirement: Privacy notes follow where the app runs
The system SHALL decide from the address the browser used whether it runs on the researcher's own machine (localhost, 127.0.0.1, [::1]) or as an online demo. Locally it SHALL keep its local-data promises. Online it SHALL say instead, in the interface language, that uploaded files are processed on the hosting server, that connector requests (ACLED credentials included) pass through that server, and (on the Settings page) that the host sends Streamlit usage statistics.

#### Scenario: Opened from the public address
- **WHEN** a visitor opens the app at its public address
- **THEN** the sidebar and the Settings page say that uploads are processed on the hosting server, and neither says "no data is sent anywhere"

#### Scenario: Opened on the researcher's machine
- **WHEN** the researcher opens the app at http://localhost:8501
- **THEN** the sidebar says "Your data remain local unless you explicitly enable external processing."

### Requirement: The online demo looks like the local app
The system SHALL give the online demo the same theme and toolbar as the local app, through a repository-root configuration that contains no other setting and no URL.

#### Scenario: Comparing the configurations
- **WHEN** the repository-root and the app-folder Streamlit configurations are read
- **THEN** their client and theme settings are identical, and the root one has no server or browser section
