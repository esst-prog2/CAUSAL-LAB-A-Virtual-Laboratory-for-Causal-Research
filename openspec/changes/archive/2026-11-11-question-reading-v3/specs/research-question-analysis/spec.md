## MODIFIED Requirements

### Requirement: The intent of the question is read before its structure
The system SHALL classify each research question as causal, predictive, descriptive or ambiguous, and SHALL show the words that decided it. A question SHALL be non-causal only when its wording is explicitly predictive or descriptive. An association, a comparison of groups or an unrecognised wording SHALL be ambiguous: the system abstains and asks. In English, a question built as auxiliary, subject, verb and object SHALL be read as causal whatever the verb, with its treatment and outcome "to confirm", unless the verb only describes, the subject is the units themselves and the verb is not a reaction, or the question compares groups. The researcher MAY state a causal aim, which changes the reading of the words and not the conditions of the methods.

#### Scenario: An explicit cause
- **WHEN** the question is "Is smoking a cause of lung cancer?"
- **THEN** the intent is causal, with treatment "smoking" and outcome "lung cancer"

#### Scenario: An association
- **WHEN** the question is "Is smoking associated with lung cancer?"
- **THEN** the intent is ambiguous, and a follow-up question asks whether a causal effect is wanted

#### Scenario: An explicit prediction
- **WHEN** the question is "Can we predict dropout using grades?"
- **THEN** the intent is predictive and no causal method is recommended

#### Scenario: A verb on no list
- **WHEN** the question is "Does job insecurity erode trust?"
- **THEN** the intent is causal, with treatment "job insecurity" and outcome "trust" labelled "to confirm"

#### Scenario: A verb that only describes
- **WHEN** the question is "Do physicians follow clinical guidelines?"
- **THEN** the intent is ambiguous
