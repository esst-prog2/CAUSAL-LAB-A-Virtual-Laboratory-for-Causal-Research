## ADDED Requirements

### Requirement: Warning when the placebo test cannot reject
The system SHALL warn when the number of donors makes the smallest attainable placebo p-value, 1 / (donors + 1), larger than 0.05. The warning SHALL give that value.

#### Scenario: Eight donors
- **WHEN** synthetic control is estimated with 8 donors
- **THEN** the result warns that no effect can be significant at 5%, because the p-value cannot fall below 1/9
