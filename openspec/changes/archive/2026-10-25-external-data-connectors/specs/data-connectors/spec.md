## ADDED Requirements

### Requirement: Connectors are off until enabled
The system SHALL send no network request to external data services unless the researcher has turned the data connectors on in Settings. The setting SHALL default to off and SHALL persist while the researcher moves between pages. The External Data page SHALL state what the connectors send: query parameters only (country codes, indicator ids, boundaries, years, and ACLED credentials to ACLED alone, never stored). It SHALL not send any dataset loaded in Causal Lab.

#### Scenario: Default session
- **WHEN** the app opens and the External Data, Settings and dashboard pages are shown
- **THEN** no network session is opened, and the External Data page says the connectors are off and shows no fetch button

#### Scenario: Turning the connectors on
- **WHEN** the researcher turns the connectors on in Settings and opens the External Data page
- **THEN** the page offers DHS, WorldPop and ACLED, and the setting is still on when Settings is shown again

### Requirement: DHS indicators
The system SHALL fetch DHS Program indicators from the public API for chosen countries and indicator ids, nationally or by region, following every page of results. It SHALL return a panel with one row per country (or region) and survey year and one column per indicator, keeping only each survey's preferred estimate.

#### Scenario: Preferred estimate
- **WHEN** the API returns a ten-year and a preferred five-year under-five mortality rate for a survey
- **THEN** the panel holds the preferred value, whatever the order of the rows

### Requirement: WorldPop population by administrative unit
The system SHALL fetch administrative boundaries from geoBoundaries and, for each unit and chosen year from 2000 to 2020, the WorldPop zonal total population. The polygon SHALL be sent with POST. The system SHALL read replies that are preceded by PHP notices, and SHALL refuse years or levels the services do not have.

#### Scenario: Rwanda provinces
- **WHEN** the population of Rwanda's five provinces is fetched for 2010 and 2015
- **THEN** the panel has 10 rows whose populations equal the WorldPop totals for each polygon

### Requirement: ACLED events
The system SHALL exchange the researcher's ACLED e-mail and password for an access token, fetch events page by page for a country and years, and aggregate them to events and fatalities per country or admin1 and per year or month. Unit-periods without events SHALL be filled with zeros. The page SHALL state that the connector follows ACLED's documented API and was not tried against the live service.

#### Scenario: Paging and aggregation
- **WHEN** ACLED returns 3 events in 2019 and 1 in 2020, over two pages
- **THEN** both pages are read, and the panel has every unit-year with 3 events and 9 fatalities for the 2019 unit and zeros elsewhere

### Requirement: Using a fetched dataset
The system SHALL let the researcher download a fetched dataset as CSV, or send it to a chosen Causal Methods page as if it had been uploaded there, where its columns are mapped as usual.

#### Scenario: Sending to a method
- **WHEN** the researcher sends a fetched DHS panel to the DML page
- **THEN** the app opens the Causal Methods page with that method's upload source holding the dataset
