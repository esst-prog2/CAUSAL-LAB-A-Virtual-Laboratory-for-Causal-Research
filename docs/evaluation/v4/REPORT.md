# Evaluation report, version 3.1 of the analyser

**One run, on 2026-11-12, on a new frozen set of 58 titles, at commit `b74f165`** (the analyser frozen at `8033035`, before the pool was fetched; the pool's hash committed at `c59cdaf`, before any title was read). Protocol: `PROTOCOL.md`. Every result: `results.json`. The first three reports stay as they were.

## Result

**Every bar passes on this set**, including the one version 3 failed on the third set: no threshold false positive (bar ≤ 2).

**But this set does not show that the 3.1 correction works.** Run on this same set, the frozen version 3 (`20b4b8f`) gives the same counts: 24 of 28 causal titles, one false causal reading, no threshold false positive. No title here has the wordings that caused version 3's errors ("What is the threshold…", "triggering"). The frozen version 2 (`c48bce9`) reads 22 of 28 (0.79).

The honest summary is:
- version 3.1 passes every bar on titles it has never seen;
- the threshold bar passes because this set holds no trap of the kind that failed before, not because the correction was tested; the correction is covered by tests on invented examples only;
- across the four sets, recall is 0.64, 0.60, 0.83 and 0.86 for versions 1, 2, 3 and 3.1, each on its own set. Version 2 scores 0.80 and 0.79 on the last two sets: the open verb class adds one or two titles per set, within noise.

The labels come from a single rater who also wrote the analyser, so these numbers are provisional.

| Criterion | Bar | Version 3.1, this set | 95% interval (Wilson) | Verdict | Version 2 on this set, for comparison |
|---|---|---|---|---|---|
| Recall of causal questions | ≥ 0.70 | 0.86 (24/28) | 0.69 to 0.94 | Passes, interval wider than the bar | 0.79 (22/28) |
| Precision of causal readings | ≥ 0.85 | 0.96 (24/25) | 0.80 to 0.99 | Passes, interval wider than the bar | 0.96 (22/23) |
| False non-causal | ≤ 5% | 3.6% (1/28) | up to 18% | Passes, interval wider than the bar | |
| Abstention on ambiguous | ≥ 0.70 | 0.91 (21/23) | 0.73 to 0.98 | Passes | |
| Recommendation with an untouched form | 0 | 0 of 58 | | Passes | |
| Wrong method given the form | ≤ 5% | 0% (0/32) | up to 11% | Passes, interval wider than the bar | |
| Threshold false positives | ≤ 2 | 0 | | Passes | 0 |

The comparison column is the frozen version 2 run on this set after the evaluation, to read the result. It is not a second evaluation of version 2.

## Dataset

58 titles: 28 causal, 23 ambiguous, 4 predictive and 3 descriptive by wording; 32 with a reported design. 8 candidates excluded, each with its reason in `question_set.json`: designs used only as robustness checks (5), a main design other than the stratum's (2), and a methods paper on IV. No work comes from the earlier sets or from the third set's development half. Fewer predictive and descriptive labels than before: many titles of those strata ask "why", "does X matter" or "does Z explain differences", which the label rules do not count as prediction or description.

## Intent

Accuracy is 0.88 (51/58).

| Label \ Read | Causal | Predictive | Descriptive | Ambiguous |
|---|---|---|---|---|
| **Causal** (28) | 24 | 1 | 0 | 3 |
| **Predictive** (4) | 0 | 4 | 0 | 0 |
| **Descriptive** (3) | 0 | 0 | 2 | 1 |
| **Ambiguous** (23) | 1 | 1 | 0 | 21 |

## Method and design

| Design | n | Clue from the title alone | With the form: correct | Abstained | Wrong |
|---|---|---|---|---|---|
| DiD | 6 | 0 | 5 | 1 | 0 |
| RDD | 5 | 0 | 3 | 2 | 0 |
| IV | 6 | 0 | 5 | 1 | 0 |
| RCT | 6 | 1 | 4 | 2 | 0 |
| Synthetic control | 3 | 0 | 1 | 2 | 0 |
| ITS | 3 | 2 | 1 | 2 | 0 |
| Matching | 3 | 0 | 2 | 1 | 0 |
| **All** | **32** | **3** | **21** | **11** | **0** |

With the causal aim confirmed, all 32 are correct. The limits of `../REPORT.md` apply: the form encodes the design.

## Threshold

| Label \ Read | Assignment | Unclear | Ordinary | None |
|---|---|---|---|---|
| **Ordinary** (8) | 0 | 7 | 1 | 0 |
| **None** (50) | 0 | 0 | 0 | 50 |

No false positive. 7 of 8 ordinary thresholds were read as unclear, which only adds a question. **For the fourth time there is no assignment threshold among the titles**, so threshold recall is still not measured: question-form titles of cited articles almost never state one. That behaviour is covered by development tests only.

## Clarification and extraction

| | Result |
|---|---|
| The follow-up a careful reader would ask was among those asked | 52 of 58 |
| Treatment contains the labelled word | 23 of 28 |
| Outcome contains the labelled word | 19 of 22 |
| Errors among elements shown as "stated", by the metric | 0 of 38 |

## Failures, all of them

**Causal read as ambiguous (3).**
- F26 "How small- and medium-sized enterprises respond to responsible investment": no auxiliary, so the open verb class does not apply.
- F28 "Has the Texas Closing the Gaps plan been successful?": "been successful" is not a verb with an object.
- F53 "Estradiol-Induced Sex Reversal…: How Little Is Too Much?": the cause is inside a noun phrase. A label a reader could dispute.

**Causal read as predictive (1), the false non-causal.** F33 "Does Forecast Accuracy Matter to Security Analysts?": "Forecast" decided, although the question asks what accuracy does to analysts. A real error: the word is the subject, not the aim.

**Other errors on intent.**
- F54, ambiguous read as causal, the false causal: "How can urban green spaces be planned to mitigate urban heat island effect?" A design question read through "mitigate". A reader could argue it asks what green spaces do to heat.
- F37, ambiguous read as predictive: "Can Predicted Protein 3D Structures Provide…": "Predicted" decided.
- F42, descriptive read as ambiguous: "Prevalence Rates of…" after a figurative question. A safe error.

Two of these (F33, F37) are the same kind: a word of prediction used as a noun or an adjective, not as the question's aim. They are listed for a later version, which would need a fifth set.

## What this does and does not show

It shows that version 3.1, frozen before the pool was fetched, passes every bar on 58 new titles, and gave no wrong method with a form.

It does not show:
- that the 3.1 correction works on real titles: version 3 does the same here;
- that version 3 or 3.1 is better than version 2 by more than noise (+2 titles here, +1 on the third set);
- threshold recall (no assignment threshold in any set);
- performance on what students type, or in French;
- agreement between raters.

## What should happen next

1. A second rater fills in `rater_sheet.csv` in this folder (`../RATER_PROCEDURE.md`).
2. Report the four evaluations together, never this one alone.
