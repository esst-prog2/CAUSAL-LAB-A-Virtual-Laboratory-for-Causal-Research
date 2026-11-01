## ADDED Requirements

### Requirement: The question's estimand is checked against the form
The system SHALL detect a cutoff or threshold described in the research question. The words "cutoff", "cut-off", "threshold", "discontinuity" and "seuil" count. "Eligibility" alone SHALL NOT count, since an eligibility expansion over time is a DiD design.

When the question describes a cutoff but the assignment mechanism is not "threshold", the system SHALL:
- add a diagnosis note;
- mark Regression Discontinuity as needing information, with the question to answer;
- mark every other supported method as needing information, because it estimates a different effect;
- recommend no method.

When no method is recommended but some need information, the system SHALL say that more information is needed, and list the questions.

#### Scenario: Scholarship near an eligibility cutoff, form left at its defaults
- **WHEN** the question is "What is the causal effect of receiving a scholarship on university enrollment among students whose entrance exam scores are near the scholarship eligibility cutoff?" and the assignment mechanism is "policy"
- **THEN** no method is recommended
- **AND** Regression Discontinuity is listed first, as needing information, with the question whether crossing the cutoff decides treatment
- **AND** DiD is not recommended

#### Scenario: The same question with a threshold assignment
- **WHEN** the assignment mechanism is "threshold"
- **THEN** Regression Discontinuity is recommended

#### Scenario: An eligibility expansion over time
- **WHEN** the question is "Did the 2014 Medicaid eligibility expansion raise coverage?" and the data are a panel with pre-periods
- **THEN** no cutoff is detected and DiD or the event study is recommended
