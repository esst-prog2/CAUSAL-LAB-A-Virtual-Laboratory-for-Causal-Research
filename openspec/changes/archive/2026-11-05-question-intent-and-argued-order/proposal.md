## Why

A test on 16 new wordings (2026-11-05) found that the question analysis called 6 clearly possible causal questions "not causal", missed implicit cutoffs, and displayed garbled readings as "stated". A failed pattern match was being reported as a finding about the question.

The ranking rested on hand-set numbers (RCT 98, RDD 88, ...). They suggest a precision nobody has established and cannot be defended. The user asked to remove them.

Any question with the form at its defaults also received a recommendation, usually DiD, on data the researcher never described. That contradicts the rule that no method is a default.

## What Changes

- **Intent.** `causal_engine/question_reading.py` reads a question as causal, predictive, descriptive or ambiguous. Only explicit predictive or descriptive wording is non-causal. Associations, comparisons of groups and unrecognised wordings are ambiguous, and the analysis abstains and asks. The researcher can state a causal aim; that changes the reading of the words, never the conditions of the methods.
- **Wordings.** Reusable families cover "is X a cause of Y", "what happens to Y when X", "would Y be different in the absence of X", "does X make Y increase", passives, perfects, negation and modal verbs, in English and French.
- **Uncertainty.** A new status, "to confirm", marks words extracted from a doubtful structure. Such words are never shown as stated, and the recommendation does not quote them back as fact.
- **Thresholds.** An assignment rule (explicit or implicit), an unclear number and an ordinary threshold are told apart. Only the first infers a threshold assignment; the second asks.
- **No recommendation from defaults.** With the form untouched, no method is recommended until the researcher changes an answer or confirms that the answers describe the study.
- **No numerical credibility.** Scores, components, confidence levels and the score chart are removed from the engine, the page and the report. Supported methods keep an argued order, and each method states its internal validity, its external validity and why it sits where it does.
- **Relative bias.** `Summary.bias_share` no longer divides by zero. At a zero true effect the 10% rule does not apply and says so.

## Capabilities

### Modified Capabilities
- `research-question-analysis`: intent, the "to confirm" status, thresholds, what blocks a ranking.
- `method-recommendation`: argued order instead of scores.

## Impact

Over a grid of 25,920 designs without a question, the first choice changes in 610 (2.4%). The largest groups are ITS to IV when both hold (270) and DiD to synthetic control with one treated unit and at least 5 pre-periods (162). In 54 designs a declared threshold now gives RDD instead of synthetic control.
