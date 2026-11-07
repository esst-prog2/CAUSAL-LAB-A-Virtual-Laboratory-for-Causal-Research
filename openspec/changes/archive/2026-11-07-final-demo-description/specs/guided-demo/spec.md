## ADDED Requirements

### Requirement: README section 1 describes the demo's path
Section 1 of the README SHALL describe the December demo in three to six present-tense sentences, naming real screens, a real file and real numbers. Each number SHALL be the one the app shows.

#### Scenario: Reading section 1
- **WHEN** someone reads section 1 of the README
- **THEN** they find the path from the Research Question screen through Method Recommendation to the Guided Demo
- **AND** its figures match the Guided Demo: bias +0.236, 47% of the effect, coverage 31.3%, pre-trend test warning in 14.2% of the worlds

### Requirement: A second edit of a form field is kept
A form field on the Research Question or Virtual Lab page SHALL keep every edit, however many times it is changed, and SHALL show a value changed from outside it.

#### Scenario: Typing a second question
- **WHEN** the researcher types a question and then replaces it with another
- **THEN** the second question stays in the field and is the one analysed
