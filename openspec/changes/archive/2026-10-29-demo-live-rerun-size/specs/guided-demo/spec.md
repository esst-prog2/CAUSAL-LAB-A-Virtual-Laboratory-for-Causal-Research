## MODIFIED Requirements

### Requirement: The study is reproducible
The system SHALL store every replication of the study with its seed. It SHALL let the researcher re-run the first 20, 50 or 100 worlds of any level (20 by default) and compare them, value by value, with the stored ones. The page SHALL say about how long each world takes.

#### Scenario: Live re-run
- **WHEN** the researcher re-runs 20 worlds of the severe level
- **THEN** the page says whether they are identical to the stored replications
