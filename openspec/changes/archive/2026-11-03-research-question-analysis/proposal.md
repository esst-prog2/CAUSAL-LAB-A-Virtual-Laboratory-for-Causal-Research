## Why

On 2026-11-03 the user stated the core originality of CAUSAL LAB. The application must analyse the research question in depth before it recommends any method: the treatment, the outcome, the population, the estimand, the assignment mechanism, the data, and the plausible sources of confounding and selection. It must keep apart what the question states, what can reasonably be inferred, and what remains unknown. It must ask targeted follow-up questions instead of ranking methods prematurely, and explain why the recommended method fits this question and why competing methods are less appropriate.

Until now the question was read only for keywords that checked the form. Its causal structure was never laid out. The user chose a local, deterministic analyser: no data leave the machine, and every conclusion can be traced back to the words that produced it.

## What Changes

- **Research Question Analysis** (`causal_engine/question_analysis.py`).
  - **Elements.** For each of eight elements, the analyser records its status (stated, inferred or unknown) with either the quoted words or the reasoning. The elements are: treatment, outcome, population, comparison, estimand, assignment, data and timing, confounding and selection.
  - **Treatment, outcome and population** are quoted from the question's "effect of X on Y among Z" structure and its variants, in English and French. Variants include "does X raise Y", "the cost of X in Z" and "la réforme a-t-elle réduit Y". A weak preposition ("for", "in") opens a population only when it names people, units or a place: "admissions for heart attacks" is an outcome.
  - **Assignment.** It is either stated ("randomly assigned") or inferred:
    - a named cutoff: assignment by a threshold;
    - winning a lottery: random assignment;
    - a lottery that only shifts the chance of treatment: an instrument (Angrist 1990);
    - a border: geographic assignment;
    - choice verbs: self-selection;
    - a policy word: a policy, weakly.
  - **Estimand.** It is either stated (ATT, ATE or LATE wording) or inferred from the assignment:
    - local at the cutoff;
    - the effect on a single treated unit;
    - the ATE under randomisation;
    - the LATE with an instrument;
    - the ATT for a policy.
  - **Confounding** is reasoned from the assignment and from the subject domain: education, labour, health, politics, places or firms.
  - **Follow-up questions** target each unknown element and each inference that needs confirmation, such as a sharp or fuzzy cutoff, compliance, or who the policy reached.
  - **Blocking.** The ranking is held back when:
    - the question is not causal (predictive or descriptive);
    - no outcome can be identified;
    - neither the question nor the form says how treatment was assigned.
- **The recommendation follows from the analysis.**
  - Essential elements missing: methods "need information" and the follow-up questions come first.
  - The question describes self-selection but the form does not: the recommendation is held back.
  - Once a method is recommended, it is explained against the question: "for this question, the effect of X on Y for Z", tied to the inferred assignment.
  - Each competing method is listed with why it is less appropriate. It may estimate a different quantity from the one the question asks for, be weaker on named components, lack information, or fail a condition.
- **Interface.**
  - The analysis appears live under the question on the Research Question form, with a button that carries what the question implies into the form. Where the question and the form disagree, both answers are shown.
  - The analysis comes first on the Recommendation page and in the report.

## Capabilities

### New Capabilities
- `research-question-analysis`: the analysis of the question's causal structure.

### Modified Capabilities
- `method-recommendation`: ranking held back by the analysis; explanations against the question.

## Impact

- **New files:** `causal_engine/question_analysis.py` and `ui/question_panel.py`.
- **Modified files:**
  - `causal_engine/diagnosis.py` (the analysis is part of the diagnosis);
  - `causal_engine/recommendation.py`;
  - `app.py`;
  - `report_engine/builder.py`;
  - the EN and FR texts.
- **Tests:**
  - `tests/test_question_analysis.py` (new);
  - an end-to-end app test (question, analysis, carry into the form, RDD with explanations);
  - the 23-case benchmark still passes.
