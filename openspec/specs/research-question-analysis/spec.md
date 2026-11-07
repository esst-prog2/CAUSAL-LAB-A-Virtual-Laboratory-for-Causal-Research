# research-question-analysis Specification

## Purpose
Lays out the causal structure of the research question before any method is recommended: treatment, outcome, population, comparison, estimand, assignment, data and confounding, each stated, inferred or unknown, with targeted follow-up questions. The recommendation follows from this analysis, not from superficial features of the design.

## Requirements

### Requirement: The question's causal structure is laid out before any method
The system SHALL analyse the research question before recommending any method. The analysis SHALL cover eight elements: treatment, outcome, population, comparison, estimand, assignment, data and timing, confounding and selection.

Each element SHALL be labelled with one status:
- stated: the question says it, with the words quoted;
- inferred: it follows from the wording, with the reasoning given;
- unknown: the question does not say it.

The analysis SHALL be deterministic and local.

#### Scenario: Scholarship near an eligibility cutoff
- **WHEN** the question is "What is the causal effect of receiving a scholarship on university enrollment among students whose entrance exam scores are near the scholarship eligibility cutoff?"
- **THEN** the treatment "receiving a scholarship", the outcome "university enrollment" and the population of students near the cutoff are stated
- **AND** the assignment by a cutoff and the local estimand at the cutoff are inferred
- **AND** the data are unknown
- **AND** the confounding is reasoned for an education question

#### Scenario: A lottery as treatment or as instrument
- **WHEN** the treatment is winning a lottery
- **THEN** assignment is inferred as random
- **WHEN** the question instead uses a lottery that shifts the chance of treatment (the Vietnam draft lottery)
- **THEN** an instrument is inferred, with a LATE for compliers

#### Scenario: A weak preposition does not open a population
- **WHEN** the question is about "hospital admissions for heart attacks"
- **THEN** the whole phrase is the outcome and no population is stated

### Requirement: Unknown elements get targeted follow-up questions
The system SHALL ask a follow-up question for each unknown element, and for each inference that must be confirmed. Examples of inferences to confirm are a sharp or fuzzy cutoff, compliance with a lottery, and who a policy reached.

#### Scenario: Class size, nothing on assignment
- **WHEN** the question is "How does class size affect test scores among third graders?"
- **THEN** the follow-up questions ask how treatment was assigned, which estimand is wanted, and what data are available
- **AND** no question asks for the population, which is stated

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

### Requirement: The analysis is shown first
The system SHALL show the analysis under the question on the Research Question form, as the question is written. The system SHALL offer to carry what the question implies into the form. Where the question and the form disagree, the system SHALL show both answers. The analysis SHALL come first on the Recommendation page and in the report.

#### Scenario: Carrying the question into the form
- **WHEN** the researcher writes the scholarship question and clicks "Use what the question implies in the form"
- **THEN** the assignment mechanism becomes "threshold"
- **AND** the diagnosis recommends RDD

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
