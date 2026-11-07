## ADDED Requirements

### Requirement: Prediction and link words are read in context
A prediction SHALL govern what follows it: "predicting the effect of X on Y" SHALL be read as predictive. A loose word for a link ("relationship between", "role of") SHALL give way to an explicit causal clause in the same question, and SHALL stay ambiguous on its own. A conditional SHALL be read as causal with its treatment and outcome labelled "to confirm".

#### Scenario: Predicting an effect
- **WHEN** the question is "Predicting the effect of climate on crop yields with neural networks"
- **THEN** the intent is predictive

#### Scenario: A link and a clause
- **WHEN** the question is "The relationship between sleep and grades: does sleep improve grades?"
- **THEN** the intent is causal

#### Scenario: A conditional
- **WHEN** the question is "If hospitals merged, would prices go up?"
- **THEN** the intent is causal and the treatment is labelled "to confirm"

### Requirement: An experiment implies a randomised assignment, to be confirmed
The word "experiment" SHALL infer a randomised assignment and ask about it, unless the experiment is natural, quasi or a thought experiment.

#### Scenario: A field experiment
- **WHEN** the question ends "Evidence from a field experiment"
- **THEN** a random assignment is inferred, and a follow-up question asks what was randomised
