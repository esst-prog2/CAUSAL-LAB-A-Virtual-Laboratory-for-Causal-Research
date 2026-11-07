## Why

A check on 49 new wordings on 2026-11-07 found 13 mismatches. Two were serious: a conditional question was read as descriptive, and "predicting the effect of X" was read as causal. Bare "does X matter" and "do X work" were not recognised, French negation was missed, and close elections were not treated as a threshold clue. The frozen evaluation of version 1 had pointed at several of these too.

## What Changes

Version 2 of the question reading in `causal_engine/question_reading.py`: prediction governs what follows it; loose link words give way to an explicit causal clause; bare effect verbs; conditionals, shown "to confirm"; French negation; experiment words infer a randomised assignment unless natural or quasi; more threshold forms.

The version 1 evaluation stays as it was (`docs/evaluation/REPORT.md`, commit c9be335). Version 2 is evaluated on a new set.

## Capabilities

### Modified Capabilities
- `research-question-analysis`: more wordings; prediction, link words and experiments as above.
