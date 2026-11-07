## ADDED Requirements

### Requirement: The recommendation follows from the analysed question
The system SHALL hold back every method when the analysis of the research question finds an essential gap. It SHALL also hold back every method when the question describes self-selection but the form does not.

Once a method is recommended, the system SHALL explain it against the question: the effect of the stated treatment on the stated outcome for the stated population, and the inferred assignment.

For each competing method, the system SHALL say why it is less appropriate. The reasons are:
- it estimates a different quantity from the one the question asks for;
- it is weaker on named score components;
- information is missing;
- one of its conditions fails.

#### Scenario: Why not DiD for the scholarship question
- **WHEN** the scholarship question with a threshold assignment recommends RDD
- **THEN** DiD is listed among the competing methods
- **AND** the reason given is that it estimates a different quantity (the ATT) from the local effect at the cutoff the question asks for

#### Scenario: Self-selection against a policy form
- **WHEN** the question is "Does joining a gym improve health?" and the assignment mechanism is "policy"
- **THEN** no method is recommended
- **AND** the methods ask whether the units select themselves
