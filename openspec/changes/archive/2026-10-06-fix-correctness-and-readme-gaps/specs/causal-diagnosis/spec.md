## MODIFIED Requirements

### Requirement: Treatment heterogeneity risk from keywords or staggered timing
The system SHALL flag treatment-effect heterogeneity as HIGH when the research question mentions subgroup-differencing language or when timing is staggered, and MEDIUM otherwise. Keywords SHALL match at the start of a word. The short keywords "age", "chose", "choice", "demand" and "spread" SHALL match only as whole words (optionally plural), so that "average", "village" or "wage" do not trigger them.

#### Scenario: Heterogeneity keyword
- **WHEN** the research question text contains a keyword such as "gender", "income", "age", "heterogene", "differ by", or "vary by"
- **THEN** `treatment_heterogeneity` is HIGH

#### Scenario: Keyword only inside another word
- **WHEN** the research question is "Effect of a wage subsidy on average village output"
- **THEN** no heterogeneity keyword is detected and, with non-staggered timing, `treatment_heterogeneity` is MEDIUM

#### Scenario: No heterogeneity signal and non-staggered timing
- **WHEN** neither a heterogeneity keyword is present nor `treatment_timing` is "staggered"
- **THEN** `treatment_heterogeneity` is MEDIUM
