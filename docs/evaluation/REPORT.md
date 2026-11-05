# Evaluation report: the research-question analyser

**One run, on 2026-11-05, on the frozen set, at commit `c9be335`.** Protocol: `PROTOCOL.md`. Every result, question by question: `results.json`. Reproduce with `python spike/evaluate_question_analysis.py`.

## Result

**One of the seven success criteria fails: recall of causal questions (0.64 against a bar of 0.70).** The analyser is cautious on this set. It never read a causal question as predictive or descriptive, and it never recommended a wrong method, but it abstained on 12 of the 33 causal questions, a third of them because of one wording it did not recognise.

The labels come from a single rater who also wrote the analyser, so these numbers are provisional until a second rater checks them.

| Criterion | Bar | Result | 95% interval (Wilson) | Verdict |
|---|---|---|---|---|
| Recall of causal questions | ≥ 0.70 | 0.64 (21/33) | 0.47 to 0.78 | **Fails** |
| Precision of causal readings | ≥ 0.85 | 0.95 (21/22) | 0.78 to 0.99 | Passes |
| False non-causal | ≤ 5% | 0% (0/33) | up to 10% | Passes, interval wider than the bar |
| Abstention on ambiguous questions | ≥ 0.70 | 0.92 (11/12) | 0.65 to 0.99 | Passes |
| Recommendation with an untouched form | 0 | 0 of 56 | | Passes |
| Wrong method given the form | ≤ 5% | 0% (0/40) | up to 9% | Passes, interval wider than the bar |
| Threshold false positives | ≤ 2 | 0 | | Passes |

## Dataset

56 published articles whose title is a question, selected from OpenAlex by a fixed rule, by citations. 13 candidates were excluded, each with its reason in `question_set.json`.

| Stratum | n | | Intent (from the wording) | n |
|---|---|---|---|---|
| Difference-in-differences | 7 | | Causal | 33 |
| Regression discontinuity | 7 | | Ambiguous | 12 |
| Instrumental variables | 7 | | Descriptive | 6 |
| Randomised trial | 6 | | Predictive | 5 |
| Synthetic control | 5 | | | |
| Interrupted time series | 4 | | | |
| Matching | 4 | | | |
| Predictive | 5 | | | |
| Descriptive | 5 | | | |
| Ambiguous | 6 | | | |

**Not obtained:** questions written by students or colleagues (0 so far). Published titles are independent of the analyser in wording, but they are not what a student types.

## Intent

Rows are the label, columns the reading. Accuracy is 0.73 (41/56), which hides the pattern below.

| Label \ Read | Causal | Predictive | Descriptive | Ambiguous |
|---|---|---|---|---|
| **Causal** (33) | 21 | 0 | 0 | 12 |
| **Predictive** (5) | 1 | 4 | 0 | 0 |
| **Descriptive** (6) | 0 | 0 | 5 | 1 |
| **Ambiguous** (12) | 0 | 1 | 0 | 11 |

| Class | Precision | Recall | F1 |
|---|---|---|---|
| Causal | 0.95 | 0.64 | 0.76 |
| Predictive | 0.80 | 0.80 | 0.80 |
| Descriptive | 1.00 | 0.83 | 0.91 |
| Ambiguous | 0.46 | 0.92 | 0.61 |

Ambiguous is where the errors collect: precision is 0.46 because 12 causal questions land there. This is the cost of the chosen behaviour. It abstains rather than guesses, and such an error costs the researcher one tick of a box.

Five "descriptive" results are easy: all are "how many" titles, a limit of the selection. They do not show that descriptive wordings are generally recognised.

## Method and design

| Design | n | Design clue from the title alone | With the form: correct | Abstained | Wrong | Aim confirmed: correct |
|---|---|---|---|---|---|---|
| DiD | 7 | 1 | 4 | 3 | 0 | 7 |
| RDD | 7 | 2 | 3 | 4 | 0 | 7 |
| IV | 7 | 0 | 3 | 4 | 0 | 7 |
| RCT | 6 | 0 | 4 | 2 | 0 | 6 |
| Synthetic control | 5 | 0 | 3 | 2 | 0 | 5 |
| ITS | 4 | 0 | 1 | 3 | 0 | 4 |
| Matching | 4 | 0 | 1 | 3 | 0 | 4 |
| **All** | **40** | **3** | **19** | **21** | **0** | **40** |

**How to read this.**

- **The form does the work.** Titles gave a design clue in only 3 of 40 cases. The analyser does not find the design in a title, and the app could not choose a method without the form.
- **The "correct" column is not evidence that the app can find a design.** The form already encodes it. It shows that the wording of a real question did not push a correct form to a wrong method.
- **"Confirmed" (40/40) follows almost by construction**, since a confirmed aim and a correct form leave nothing else to decide. Do not cite it as accuracy.

## Threshold

Both titles naming a discontinuity were recognised (2/2), with 0 false positives among the other 54. Only 2 labelled cases cannot measure recall: the set contains **no implicit threshold in a title** of the kind "eligibility at age 65". Implicit thresholds are covered by development tests only, and are **not validated here**.

## Clarification

In 44 of 56 questions the follow-up that a careful reader would ask was among those the analyser asked. Most misses are of two kinds: "field experiment" or "experiment" in a title does not trigger the question about randomisation (4), and policy-like treatments such as lockdowns or a medical scheme do not trigger the question about who was reached.

## Extraction

| | Correct | Checked |
|---|---|---|
| Treatment contains the labelled word | 22 | 34 |
| Outcome contains the labelled word | 21 | 25 |
| Errors among elements shown as "stated" | 2 | 39 |

The two "stated" errors are both on Q31, which took the treatment and outcome from the subtitle (Mohamed Salah), a defensible reading that differs from the label.

**This check is lenient, and the bar was not designed to catch garbled phrases.** A review of the output after the run found two more readings shown as "stated" that a reader would call wrong, though they contain the labelled word:

- Q02: outcome "or Impede Firm Innovation";
- Q38: treatment "Client Characteristics Really".

So the "to confirm" status does not catch everything. These two were found by reading the results, not by the metric.

## Failures, all of them

**False causal (1).** Q41, "Predicting the impacts of climate change on the distribution of species: are bioclimate envelope models useful?": "impacts of X on Y" won over "predicting". This is the most serious kind of error in the set, because the app then treats a prediction question as a causal one.

**Causal read as ambiguous (12).**

| Cause | Questions |
|---|---|
| "Does X matter?" with no "for" | Q10, Q11, Q18, Q35 |
| "Does X work?" | Q06, Q24 |
| "Role of" or "relationship" elsewhere in the title overrides a clear causal clause | Q08, Q51 |
| "Are X effective?" with no object | Q13 |
| "Is X good or bad for Y?" treated as a comparison, against a title saying "causality" | Q19 |
| "Does X mean Y" | Q04 |
| "Can government regulate safety", a verb outside the list | Q36 |

Q08 and Q51 are a defect of order, not of vocabulary: an association word later in a title should not defeat an explicit causal clause.

**Others (2).** Q34 (descriptive, read as ambiguous). Q43 (ambiguous, read as predictive: "motivational synergy in predicting").

## Examples

| Question | Reading | Good because |
|---|---|---|
| Does Pollution Increase School Absences? | Causal; Pollution; School Absences | Clean extraction; no method without a form |
| Is Earnings Quality Associated with Corporate Social Responsibility? | Ambiguous; both "to confirm"; asks for the aim | Not called causal or non-causal |
| How Many Species Are There on Earth and in the Ocean? | Descriptive | No causal method |
| Do Parties Matter for Economic Outcomes? A Regression-Discontinuity Approach | Causal; assignment threshold | Clue from the title |

## What this does and does not show

It shows that, on highly cited question-form titles, the analyser rarely overclaims and often abstains, and that wording did not produce a wrong method here.

It does not show:

- how the app performs on what students type (long questions, poor wording);
- performance in French;
- performance on implicit thresholds;
- that a recommended design is valid for a study;
- agreement between raters.

## What should happen next

1. **Second rater.** A person fills in `rater_sheet.csv`, and Cohen's kappa is computed. Labels may change; the report then needs correcting, and the change must be declared.
2. **Decide about a new version.** The failures above point to fixes (the order of rules, "matter", "work", "effective", experiment words, predictive words taking precedence over "impacts"). This set can **no longer test them**: its failures are now known. A new version needs a new set, ideally written by students. No fix has been made.
3. **Author's review of the bars.** The bars were proposed by the agent. If you change them now, say that it is after seeing the results.
