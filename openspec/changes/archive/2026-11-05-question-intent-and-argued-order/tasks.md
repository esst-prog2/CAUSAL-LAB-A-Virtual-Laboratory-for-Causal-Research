## 1. Reading the question

- [x] 1.1 Classify intent as causal, predictive, descriptive or ambiguous, keeping the words that decided it (EN, FR).
- [x] 1.2 Add the new causal wordings as reusable families of verbs, auxiliaries and connectors.
- [x] 1.3 Tell an assignment threshold from an unclear number and an ordinary threshold.
- [x] 1.4 Add the "to confirm" status and the researcher's confirmation of a causal aim.

## 2. Recommendation

- [x] 2.1 Replace the scores with an argued order and per-method arguments (EN, FR).
- [x] 2.2 Hold back every method when the question is not causal, when a threshold is unclear, or when the form is untouched.
- [x] 2.3 Remove the scores from the page and the report.

## 3. Tests and checks

- [x] 3.1 `tests/test_question_reading.py` covers every new wording, ambiguous case and threshold kind.
- [x] 3.2 Compare the old and new first choices over the design grid.
- [x] 3.3 Relative bias at a zero true effect (`tests/test_demo_study.py`).
