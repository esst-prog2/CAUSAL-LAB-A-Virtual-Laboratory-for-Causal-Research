## ADDED Requirements

### Requirement: An argued order, not a numerical score
The system SHALL check every candidate method against the conditions without which it does not identify a causal effect. Methods SHALL be listed in this order:
- supported methods, in an argued order;
- methods that need information;
- methods ruled out.

The system SHALL NOT attach a numerical credibility to a method. For each method it SHALL state its internal validity, its external validity and the argument for its position, and it SHALL say that the order is qualitative, holds under the stated conditions, and does not make any method superior in every research context.

#### Scenario: Recommending methods
- **WHEN** `recommend(design, diagnosis)` is called
- **THEN** it returns 8 `MethodAssessment` records, in the order above: Randomized Controlled Trial, Regression Discontinuity, Difference-in-Differences, Event Study, Synthetic Control, Instrumental Variables, Interrupted Time Series, and Matching / Propensity Score

#### Scenario: One treated unit
- **WHEN** one unit is treated and a synthetic control's conditions hold
- **THEN** synthetic control comes before DiD, because the counterfactual is built explicitly and its fit can be inspected

#### Scenario: Ruled-out method
- **WHEN** a method's necessary condition fails
- **THEN** its status is `not_supported` and `unmet` lists the failed conditions

## REMOVED Requirements

### Requirement: Scored, ranked candidate list
**Reason**: The hand-set numbers suggested a precision that was never established.
**Migration**: Replaced by "An argued order, not a numerical score".

## MODIFIED Requirements

### Requirement: Structured recommendation
For the recommended method, the system SHALL give:
- the causal estimand;
- why the method fits;
- the identification strategy;
- the key assumptions;
- the threats and diagnostics;
- its internal and external validity;
- the alternative methods, with when each is preferable;
- the additional details needed (the questions behind each method that needs information).

#### Scenario: Default design
- **WHEN** the researcher confirms a policy evaluated in a panel with a pre-period, with the instrument and the confounders answered "not sure"
- **THEN** DiD is recommended, with the ATT as estimand
- **AND** IV and matching are listed as possible with more information
- **AND** each of the two questions to answer is shown

### Requirement: The recommendation follows from the analysed question
The system SHALL hold back every method when the analysis of the research question finds an essential gap. It SHALL also hold back every method when the question describes self-selection but the form does not.

Once a method is recommended, the system SHALL explain it against the question: the effect of the stated treatment on the stated outcome for the stated population, and the inferred assignment. It SHALL do so only when the treatment and the outcome are labelled stated.

For each competing method, the system SHALL say why it is less appropriate. The reasons are:
- it estimates a different quantity from the one the question asks for;
- the argument for its position is weaker here;
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
