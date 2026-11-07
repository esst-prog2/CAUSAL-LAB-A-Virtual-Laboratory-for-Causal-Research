## Project facts to keep consistent

- The recommendation covers eight methods (`METHOD_KEYS` in `causal_lab/causal_engine/recommendation.py`). Do not write another number without checking that list. ITS has no estimator in the app; DML has one but is not recommended.
- The question analyser (`causal_engine/question_reading.py`, `question_analysis.py`) gives an initial assessment. Never describe it, or the app, as establishing causal identification.
- No numerical credibility on methods: the order is argued. Do not add scores back. Identification Strength is gone from the app too (`docs/IDENTIFICATION_STRENGTH.md`): the function remains only for the calibration spikes.
- The 10% bias and 90% coverage rule evaluates the DiD simulation study only. It does not control the app or apply to other methods.
- The DiD and the event study share one convention: clustered by unit, unit dummies not counted, Student t with G - 1 degrees of freedom. Any new clustered fit must follow it.
- **Scope:** issue #1 asks for one method, DiD. The wider scope is PENDING PROFESSOR CONFIRMATION (`docs/SCOPE_CLARIFICATION.md`). Do not write that it was approved without written evidence.
- **Evaluation:** `docs/evaluation/question_set.json` and `docs/evaluation/v2/question_set.json` are frozen, and `spike/evaluate_question_analysis.py` refuses to overwrite a result. Never add their questions to patterns or tests, and never change the analyser to score better on them. A corrected analyser needs a new set, with a declared protocol.
- **Do not attribute a threshold to an author** without reading the source. Do not report a kappa from an incomplete sheet (`spike/compute_kappa.py` refuses one).
- **Tests:** from `causal_lab/`, `../.venv/Scripts/python -m pytest` (about 6 minutes). CI also runs `openspec validate --specs`. Do not merge with a failing test, and do not merge without the user's approval.
- **Deployment:** the online app is rebooted by the user at share.streamlit.io. Do not claim it is live until that has been verified.

## Planning log

Whenever we decide something about this project — a requirement, a number, a name, a tool, a scope choice — append one line to `PLANNING_LOG.md` at the repository root: the date, what was decided, and whether the person or the agent decided it. Do this at the moment the decision is made, not in a batch afterward. Never rewrite or delete an earlier line; a correction is a new line, not an edit to an old one.
