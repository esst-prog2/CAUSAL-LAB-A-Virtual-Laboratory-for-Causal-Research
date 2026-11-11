## MODIFIED Requirements

### Requirement: A threshold is an assignment rule only when the wording says so
The system SHALL distinguish a threshold that assigns treatment (explicit or implicit), a number whose role is unclear, and an ordinary threshold. Only the first SHALL infer a threshold assignment. The second SHALL produce a follow-up question and hold every method back until the researcher answers. A clue SHALL be a whole word: a word found inside another word ("at" in "What") SHALL NOT count, and "trigger" SHALL make a rule only as a verb.

#### Scenario: An implicit rule
- **WHEN** the question is "Does Medicare eligibility at age 65 change health care use?"
- **THEN** a threshold assignment is inferred

#### Scenario: A number of unclear role
- **WHEN** the question is "Does a BMI over 30 raise mortality?"
- **THEN** no threshold assignment is inferred, and a follow-up question asks whether crossing the value decides treatment

#### Scenario: An ordinary threshold
- **WHEN** the question is "Is there a debt threshold above which growth falls?"
- **THEN** no threshold assignment is inferred

#### Scenario: A clue inside another word
- **WHEN** the question is "What is the threshold of blood pressure for starting statins?"
- **THEN** no threshold assignment is inferred, and a follow-up question asks whether crossing the value decides treatment

#### Scenario: Triggering as a phenomenon
- **WHEN** the question is "Landslide triggering: is there a rainfall threshold?"
- **THEN** no threshold assignment is inferred
