## Why

On 2026-11-01 the user asked the app: "What is the causal effect of receiving a scholarship on university enrollment among students whose entrance exam scores are near the scholarship eligibility cutoff?". The form was left at its defaults (policy assignment, panel, one pre-period), and the Method Recommendation Engine answered Difference-in-Differences.

The engine trusted the form and never read the question. But the question's estimand is the effect at the cutoff, which only a regression discontinuity identifies; DiD would estimate a different effect. The method-selection discipline says: when the design cannot be assessed reliably, ask, rather than recommend prematurely.

## What Changes

- The diagnosis detects a cutoff described in the question: cutoff, cut-off, threshold, discontinuity, seuil. "Eligibility" alone does not count, because an eligibility expansion over time is a DiD design.
- When the question describes a cutoff but the assignment mechanism is not "threshold":
  - the diagnosis adds a note;
  - RDD becomes "needs information", with the question to answer (does crossing the cutoff decide treatment?);
  - every other supported method becomes "needs information", because it estimates a different effect;
  - no method is recommended.
- When no method is recommended but some need information, the page and the report say "More information is needed before a method can be recommended" and list the questions. "No credible causal design" is kept for the case where every method is ruled out.
- With the assignment mechanism set to "threshold", the scholarship question gets RDD.

## Capabilities

### Modified Capabilities
- `method-recommendation`: the question's estimand is checked against the form; missing information leads to a request for it, not to a recommendation.

## Impact

- Code: `causal_engine/diagnosis.py`, `causal_engine/recommendation.py`, `app.py`, `report_engine/builder.py`, and the EN and FR texts.
- New tests:
  - the scholarship question asks before answering;
  - it gets RDD with a threshold;
  - an eligibility expansion is not mistaken for a cutoff.
