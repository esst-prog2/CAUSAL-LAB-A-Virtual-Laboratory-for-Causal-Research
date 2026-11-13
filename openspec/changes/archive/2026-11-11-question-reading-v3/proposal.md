## Why

Version 2 of the question reader failed its recall bar (0.60 for 0.70, `docs/evaluation/v2/REPORT.md`) because causal verbs were a closed list: every new verb ("respond", "empower", "discipline") made it abstain. The professor's feedback (2026-11-09) presents the analyser as an extension with that number stated; the author asked to improve it.

## What Changes

- In English, a question built as auxiliary + subject + verb + object is read as causal whatever the verb, with treatment and outcome "to confirm". It stays ambiguous when the verb only describes (a closed list: know, use, prefer, differ…), when the subject is the units themselves and the verb is not a reaction ("do firms export to China?"), or when the question compares groups.
- The progressive ("is X helping Y?"), "what works" heading a question, and "is there an X effect on Y?" are read as causal, with roles to confirm.
- French keeps the closed list.
- Evaluated once on a third frozen set (`docs/evaluation/v3/`): recall 0.83, precision 1.00; the frozen version 2 scores 0.80 on that set, so most of the rise is the set. The threshold reader, unchanged, fails its bar there (3 false positives).

## Capabilities

### Modified Capabilities
- `research-question-analysis`: the intent of the question is read with an open verb class in English.
