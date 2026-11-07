# method-recommendation Specification

## Purpose
Checks eight candidate causal-identification methods against the conditions without which they do not identify an effect, from the research design input, its diagnosis and the analysed question. Supported methods are put in an argued, qualitative order; no numerical credibility is attached, and the recommendation is presented as an aid to research design, never as a guarantee of causal identification.

## Requirements

### Requirement: Each method needs its identifying conditions
The system SHALL recommend a method only when its necessary conditions hold:
- RCT: random assignment.
- RDD: an assignment or eligibility cutoff.
- IV: an instrument is declared available. "Not sure" means the method needs information.
- DiD: untreated comparison units, followed before and after treatment, with at least one pre-period and one post-period.
- Event study: the DiD conditions, plus at least two pre-periods.
- Synthetic control: one or a few treated units, a panel of donor units, and at least five pre-treatment periods.
- Interrupted time series: longitudinal data, with at least three pre-treatment observations.
- Matching / regression adjustment: all important confounders measured. "Not sure" means the method needs information, unless assignment is random.

A policy intervention or panel data SHALL NOT by themselves make DiD supported.

#### Scenario: Random assignment
- **WHEN** the assignment mechanism is random
- **THEN** the recommended method is the RCT

#### Scenario: A real cutoff
- **WHEN** the assignment mechanism is a threshold
- **THEN** the recommended method is RDD

#### Scenario: One treated region with a long pre-period
- **WHEN** one unit is treated by a policy in a panel with ten pre-treatment periods
- **THEN** synthetic control is recommended over DiD

#### Scenario: A panel without comparison units
- **WHEN** no untreated comparison units are observed
- **THEN** DiD and the event study are ruled out

### Requirement: No credible design is stated
The system SHALL state explicitly when no method's necessary conditions hold, and SHALL list what would make each method credible.

#### Scenario: Self-selection observed once, with nothing else
- **WHEN** a self-selected treatment is observed in a cross-section, with no instrument and with unmeasured confounders
- **THEN** no method is recommended
- **AND** the Recommendation page and the report say that no credible causal design is supported, with the reasons

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

### Requirement: Every design signal of the question is checked against the form
The system SHALL detect, in English and French, the design features that the wording of the research question describes:
- a cutoff;
- a randomisation or a lottery;
- an instrument;
- a staggered rollout;
- a single unit or a nationwide change;
- a border;
- a prediction or an association;
- heterogeneity;
- a mechanism;
- a dose;
- effects over time.

When the question contradicts the form, the system SHALL recommend no method. It SHALL instead list the method the question points to as needing information, together with the question to answer:
- a lottery or randomisation, while the assignment is not random and no instrument is declared: RCT;
- an instrument, while none is declared: IV;
- a single unit or a nationwide change, while many treated units are declared: every method is held back;
- a prediction or an association, without causal wording: every method is held back, and the researcher is asked to name a treatment and an outcome.

A geographic assignment whose question names a border SHALL support a regression discontinuity.

#### Scenario: Lottery in the question
- **WHEN** the question is "What is the effect of winning a housing lottery on children's outcomes?" and the assignment mechanism is "policy"
- **THEN** no method is recommended, and the RCT is listed first as needing information

#### Scenario: Lottery used as an instrument
- **WHEN** the question mentions the Vietnam draft lottery, the assignment is self-selected and an instrument is declared available
- **THEN** IV is recommended

#### Scenario: Predictive question
- **WHEN** the question is "Which student characteristics predict university dropout?"
- **THEN** no method is recommended, and every method asks for a treatment and an outcome

### Requirement: Caveats from the wording of the question
The system SHALL add to the rationale, without blocking the recommendation:
- the staggered-adoption caveat, when the question describes a staggered rollout but the timing is a single date;
- the event-study suggestion, for effects over time;
- the dose-response caveat, for a dose of a binary treatment;
- conditional effects and causal forests, for heterogeneity;
- the assumptions of mediation analysis, for mechanisms.

#### Scenario: Heterogeneity, mechanism and long-run effects
- **WHEN** the question asks how the long-run effect varies by income and through which mechanism
- **THEN** the recommended method's rationale includes the heterogeneity, mechanism and dynamic caveats

### Requirement: The recommendation shows what it rests on
The Recommendation page SHALL show the design answers the recommendation uses. It SHALL warn when every design answer is still at its default value.

#### Scenario: Only the question typed
- **WHEN** the researcher types a question and runs the diagnosis without changing any other answer
- **THEN** the page shows the answers used and a warning that they are the defaults

### Requirement: Published studies get the design their authors used
The system SHALL recommend, for each study of the benchmark, the design its authors used, given the question and the form as the authors would fill it in.

#### Scenario: Benchmark
- **WHEN** the benchmark of published studies is run
- **THEN** every published study gets the expected design
- **AND** every question that contradicts its form gets no recommendation and a question to answer

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
