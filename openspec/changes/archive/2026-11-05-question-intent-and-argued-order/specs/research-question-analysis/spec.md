## ADDED Requirements

### Requirement: The intent of the question is read before its structure
The system SHALL classify each research question as causal, predictive, descriptive or ambiguous, and SHALL show the words that decided it. A question SHALL be non-causal only when its wording is explicitly predictive or descriptive. An association, a comparison of groups or an unrecognised wording SHALL be ambiguous: the system abstains and asks. The researcher MAY state a causal aim, which changes the reading of the words and not the conditions of the methods.

#### Scenario: An explicit cause
- **WHEN** the question is "Is smoking a cause of lung cancer?"
- **THEN** the intent is causal, with treatment "smoking" and outcome "lung cancer"

#### Scenario: An association
- **WHEN** the question is "Is smoking associated with lung cancer?"
- **THEN** the intent is ambiguous, and a follow-up question asks whether a causal effect is wanted

#### Scenario: An explicit prediction
- **WHEN** the question is "Can we predict dropout using grades?"
- **THEN** the intent is predictive and no causal method is recommended

### Requirement: Doubtful readings are not shown as stated
The system SHALL label words extracted from a doubtful structure "to confirm", and SHALL ask the researcher to confirm them. Such words SHALL NOT be quoted back in the recommendation as the treatment or the outcome.

#### Scenario: A comparison of groups
- **WHEN** the question is "Are vaccinated people less likely to be hospitalized?"
- **THEN** the treatment and the outcome are labelled "to confirm"

### Requirement: A threshold is an assignment rule only when the wording says so
The system SHALL distinguish a threshold that assigns treatment (explicit or implicit), a number whose role is unclear, and an ordinary threshold. Only the first SHALL infer a threshold assignment. The second SHALL produce a follow-up question and hold every method back until the researcher answers.

#### Scenario: An implicit rule
- **WHEN** the question is "Does Medicare eligibility at age 65 change health care use?"
- **THEN** a threshold assignment is inferred

#### Scenario: A number of unclear role
- **WHEN** the question is "Does a BMI over 30 raise mortality?"
- **THEN** no threshold assignment is inferred, and a follow-up question asks whether crossing the value decides treatment

#### Scenario: An ordinary threshold
- **WHEN** the question is "Is there a debt threshold above which growth falls?"
- **THEN** no threshold assignment is inferred

## MODIFIED Requirements

### Requirement: Essential gaps hold the ranking back
The system SHALL hold back the ranking of methods when any of these holds:
- the question is predictive, descriptive or ambiguous, and the researcher has not stated a causal aim;
- the treatment or the outcome cannot be identified, and the researcher has not stated a causal aim;
- the form is untouched: no answer has been changed or confirmed.

#### Scenario: Ranking after the gap is filled
- **WHEN** the class-size question is analysed with the form at its defaults
- **THEN** no method is recommended
- **WHEN** the researcher then declares a threshold assignment and cross-sectional data
- **THEN** RDD is recommended

#### Scenario: Default answers that do describe the study
- **WHEN** the researcher confirms that the default answers describe the study
- **THEN** the conditions of the methods decide, and DiD can be recommended
