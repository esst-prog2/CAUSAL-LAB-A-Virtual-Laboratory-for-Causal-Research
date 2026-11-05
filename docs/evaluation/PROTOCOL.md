# Evaluation protocol: the research-question analyser

Written before any evaluation question was collected or any result was seen. Changes after that point are listed at the end of this file with their date and reason.

## What is evaluated

The analyser in `causal_engine/question_reading.py` and `question_analysis.py`, and the recommendation in `recommendation.py`, at the commit recorded in `results.json`. The question: on research questions it was not developed on, does it read the intent correctly, abstain when it should, and avoid recommending the wrong design?

It does not evaluate whether a recommended design is valid for a given study: a title and a form cannot show that.

## Where the questions come from

Published articles whose **title is itself a question**, retrieved from the OpenAlex catalogue by `spike/fetch_question_candidates.py`. The authors wrote the wording, not the developer of the analyser, and a fixed rule selects them, so the choice cannot favour the analyser.

For each stratum the script runs a fixed query and takes, by descending citation count, the first N works that meet all of these conditions: type article, in English, an abstract is available, a question mark in the title, at most 30 words, and the title is not already in the development tests.

| Stratum | Query (OpenAlex search) | N |
|---|---|---|
| did | abstract: "difference-in-differences" | 7 |
| rdd | abstract: "regression discontinuity" | 7 |
| iv | abstract: "instrumental variable" | 7 |
| rct | abstract: "randomized controlled trial" | 6 |
| synthetic_control | abstract: "synthetic control" | 5 |
| its | abstract: "interrupted time series" | 4 |
| matching | abstract: "propensity score matching" | 4 |
| predictive | title: "predict" | 5 |
| descriptive | title: "how many" or "prevalence" | 5 |
| ambiguous | title: "associated with" or "relationship between" | 6 |

Total: 56. A work is excluded only if its abstract shows that the stratum does not apply (for example, it reviews the method rather than using it, or does not name a design). Each exclusion is recorded with its reason in `question_set.json`, and the next work takes its place.

Event studies are not a separate stratum, because in OpenAlex the phrase mostly retrieves finance event studies, a different design. DiD and event study are counted as the same family.

## Ground truth

Each question is labelled from its **title and abstract**, before the analyser is run on the set. The analyser's output is not consulted. Each record holds:

1. `id`
2. `question`: the title, verbatim
3. `source`: authors, year, journal, DOI or OpenAlex ID
4. `intent`, from the wording of the title, using the rules below
5. `design`: the design the abstract reports, or null
6. `threshold`: whether the *title* describes an assignment threshold (`assignment`, `unclear`, `ordinary`, or null)
7. `clarification`: what a careful reader should ask
8. `explanation`: why the labels are what they are
9. `criterion`: what counts as correct for this question
10. `treatment_word`, `outcome_word`: one word that a correct reading must contain, when the title names them

Rules for `intent`:

- **causal**: the title asks what something does to something else ("does X reduce Y", "effect of X on Y", "is X a cause of Y").
- **predictive**: it asks whether something can be predicted or forecast.
- **descriptive**: it asks how much, how many or what happened, with no cause named.
- **ambiguous**: it asks about an association, a relationship, a difference between groups, or "why" without naming a change.

Labels are those of a **single rater, the agent that also wrote the analyser** (Claude, for the author). This is the main weakness of the design, because knowing the patterns could influence the labels. Reducing it requires a second rater: `rater_sheet.csv` holds the questions with the labels hidden, and agreement (Cohen's kappa) should be computed when a person has filled it in.

## Freezing

The dataset is committed with its SHA-256 in `question_set.sha256` before the evaluation runs, in a commit that precedes the one with the results. `spike/evaluate_question_analysis.py` refuses to run if the hash differs.

## Rules against leakage

- Evaluation questions are not added to the patterns or the tests, and the analyser is not changed to do better on them.
- No question is removed after the run. All failures are listed in the report.
- A correction after this evaluation makes a new version of the analyser, which needs a **new** set of questions to be evaluated. Scores on this set would no longer measure generalisation.

## Metrics

**Intent, question as written, form untouched.** 4 x 4 confusion matrix, accuracy, and precision, recall and F1 for each class.
- *False causal*: labelled predictive, descriptive or ambiguous, read as causal.
- *False non-causal*: labelled causal, read as predictive or descriptive. This is the error the correction aimed at.
- *Abstention on ambiguous questions*: labelled ambiguous, read as ambiguous, and a follow-up question asks for the aim.

**Abstention with no form.** Share of all questions that receive no recommendation with the form untouched. It should be 100%, because a title alone never describes the data.

**Design clue from the question alone**, for each design stratum: whether the analyser infers the mechanism (`rdd`: threshold; `rct`: random; `iv`: an instrument; `did`: policy or staggered; `synthetic_control`/`its`: a single unit). Titles rarely state the design, so low recall is expected. It is reported to show how much the form is needed.

**Method, with the form the design implies**, for each question labelled with a design. The form is fixed in the script, per design, before the run. Outcomes: *correct*, *abstained* (no method; the question or its wording held it back) and *wrong* (another method). DiD and event study count as one family. This is run twice, as written and with the causal aim confirmed.

This metric has a built-in limit: the form already encodes the design, so it mostly measures whether the wording of a real question disturbs a correct form. It does **not** measure whether the app could find the design unaided.

**Threshold.** Recall and false positives of `assignment` against the `threshold` label of the title.

**Clarification.** Share of questions whose labelled clarification corresponds to a follow-up question the analyser asks, judged by the key listed in the record.

**Extraction.** Share of `treatment_word` and `outcome_word` found in the extracted treatment and outcome, and share of errors among elements displayed as "stated".

## Success criteria

Proposed by the agent before the run. The author must review them and may replace them, recording that decision; **replacing them after seeing the results must be declared as such.**

| Criterion | Bar |
|---|---|
| Recall of causal questions | at least 0.70 |
| Precision of causal readings | at least 0.85 |
| False non-causal: causal questions read as predictive or descriptive | at most 5% |
| Abstention on ambiguous questions | at least 0.70 |
| Recommendation with an untouched form | 0 |
| Wrong method given the form, among all questions with a design | at most 5% |
| Threshold false positives on titles without one | at most 2 |

There is no criterion for design clues, which are descriptive.

The bars are judgements, not derived values: they express that a wrong reading is worse than an abstention, because an abstention costs a question and a wrong reading can send the researcher to the wrong design.

## Sampling limits, known in advance

- Question-form titles of highly cited articles are not the questions a student types: they are short, and they often omit the design. The set says nothing about long, multi-sentence questions.
- Citation order favours a few fields, notably medicine.
- All questions are in English, so the French patterns are not evaluated here.
- 56 questions give wide intervals: a proportion near 0.8 on 40 questions has a 95% interval of about ±0.13.
- No question was written by a student or colleague yet. The two-person test (`docs/evaluation/USER_TEST.md`) can provide some, and they would form a **new** set.

## Changes to this protocol

None yet.
