## ADDED Requirements

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
- the question is not causal;
- the question has no identifiable outcome;
- neither the question nor the form says how treatment was assigned.

#### Scenario: Ranking after the gap is filled
- **WHEN** the class-size question is analysed with the form at its defaults
- **THEN** no method is recommended
- **WHEN** the researcher then declares a threshold assignment and cross-sectional data
- **THEN** RDD is recommended

### Requirement: The analysis is shown first
The system SHALL show the analysis under the question on the Research Question form, as the question is written. The system SHALL offer to carry what the question implies into the form. Where the question and the form disagree, the system SHALL show both answers. The analysis SHALL come first on the Recommendation page and in the report.

#### Scenario: Carrying the question into the form
- **WHEN** the researcher writes the scholarship question and clicks "Use what the question implies in the form"
- **THEN** the assignment mechanism becomes "threshold"
- **AND** the diagnosis recommends RDD
