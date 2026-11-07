## ADDED Requirements

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
