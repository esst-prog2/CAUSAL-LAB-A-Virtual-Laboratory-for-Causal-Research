## Why

The single run of version 3 (`docs/evaluation/v3/REPORT.md`) failed the threshold bar with 3 false positives for 2. Two of them are bugs, not judgement: the word "at" was found inside "What" ("What is the threshold…" read as "at the threshold"), and "trigger" made a rule even as the noun "triggering". The same "What" bug caused the only threshold false positive of version 2 (V52). The run also showed an outcome cut at the first comma of a list ("environmental, social, and governance performance").

## What Changes

- Threshold words are matched as whole words: "at", "near", "around" and the sharp-cutoff words need a word boundary.
- "Trigger" counts as a rule word only as a verb ("triggers", "triggered"), not as the noun "triggering".
- A comma inside a short list ("A, B, and C") no longer ends the outcome.
- The third false positive (T10, a title that names "a regression discontinuity design") is not changed: naming the design is a fair clue to an assignment threshold; the label rule counts it as false. The rule is not changed after the run.
- Version 3.1 is not evaluated: the third set revealed these errors, so it cannot measure their correction. The version 3 results stand as reported.

## Capabilities

### Modified Capabilities
- `research-question-analysis`: a threshold clue must be a whole word.

## Impact

- `causal_lab/causal_engine/question_reading.py`, `causal_lab/tests/test_question_reading.py`.
- Regression check, not evidence: 6 of 388 readings change across the three sets and the development set, all in the direction of the labels.
