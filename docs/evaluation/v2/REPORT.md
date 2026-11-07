# Evaluation report, version 2 of the analyser

**One run, on 2026-11-07, on a new frozen set, at commit `c48bce9`.** Protocol: `PROTOCOL.md`. Every result: `results.json`. The first evaluation stays as it was, in `../REPORT.md`, and describes version 1.

## Result

**One of the seven criteria fails again, and version 2 is not shown to be better than version 1.** Recall of causal questions is 0.60 against a bar of 0.70 (0.64 for version 1 on another set; the difference is well within noise). It remains cautious: 1 causal question of 30 was called non-causal, 1 non-causal reading was called causal, and no method was wrong.

Fixing the wordings seen in development did not raise recall on new titles, because the verb list is closed: "respond", "empower", "discipline" and "deteriorate" are not on it. **This is a structural limit of a pattern reader, not a bug that one more fix removes.** It abstains on what it does not know, and the researcher answers one question.

The labels come from a single rater who also wrote the analyser, so these numbers are provisional.

| Criterion | Bar | Version 2, this set | 95% interval (Wilson) | Verdict | Version 1, first set |
|---|---|---|---|---|---|
| Recall of causal questions | ≥ 0.70 | 0.60 (18/30) | 0.43 to 0.75 | **Fails** | 0.64 (21/33) |
| Precision of causal readings | ≥ 0.85 | 0.95 (18/19) | 0.75 to 0.99 | Passes | 0.95 (21/22) |
| False non-causal | ≤ 5% | 3.3% (1/30) | up to 16% | Passes, interval wider than the bar | 0% (0/33) |
| Abstention on ambiguous | ≥ 0.70 | 0.87 (13/15) | 0.62 to 0.96 | Passes | 0.92 (11/12) |
| Recommendation with an untouched form | 0 | 0 of 58 | | Passes | 0 of 56 |
| Wrong method given the form | ≤ 5% | 0% (0/32) | up to 11% | Passes, interval wider than the bar | 0% (0/40) |
| Threshold false positives | ≤ 2 | 1 | | Passes | 0 |

The two sets differ in composition and were not drawn to be comparable, so do not read the last column as a before and after.

## Dataset

58 published articles whose title is a question: 30 causal, 15 ambiguous, 9 descriptive and 4 predictive by wording; 32 with a reported design. 8 candidates were excluded, each with its reason in `question_set.json`. No work comes from the first set's candidates.

## Intent

Accuracy is 0.66 (38/58), which hides the pattern below.

| Label \ Read | Causal | Predictive | Descriptive | Ambiguous |
|---|---|---|---|---|
| **Causal** (30) | 18 | 0 | 1 | 11 |
| **Predictive** (4) | 0 | 4 | 0 | 0 |
| **Descriptive** (9) | 0 | 1 | 3 | 5 |
| **Ambiguous** (15) | 1 | 1 | 0 | 13 |

| Class | Precision | Recall | F1 |
|---|---|---|---|
| Causal | 0.95 | 0.60 | 0.73 |
| Predictive | 0.67 | 1.00 | 0.80 |
| Descriptive | 0.75 | 0.33 | 0.46 |
| Ambiguous | 0.45 | 0.87 | 0.59 |

**Descriptive recognition is poor (3 of 9).** The first set's 5 of 6 rested on "how many" titles, and this set, which excludes them, shows that this was flattering. Titles naming a prevalence without "what is the" are not recognised. They are read as ambiguous, a safe error.

## Method and design

| Design | n | Clue from the title alone | With the form: correct | Abstained | Wrong |
|---|---|---|---|---|---|
| DiD | 7 | 1 | 5 | 2 | 0 |
| RDD | 5 | 0 | 1 | 4 | 0 |
| IV | 6 | 0 | 2 | 4 | 0 |
| RCT | 6 | 1 | 1 | 5 | 0 |
| Synthetic control | 3 | 0 | 3 | 0 | 0 |
| ITS | 3 | 0 | 0 | 3 | 0 |
| Matching | 2 | 0 | 0 | 2 | 0 |
| **All** | **32** | **2** | **12** | **20** | **0** |

The limits stated in `../REPORT.md` apply. Titles rarely give the design (2 of 32), so the form does the work. The "correct" column shows that wording did not push a correct form to a wrong method; it does not show that the app finds a design.

## Threshold

Rows are the label, columns the reading.

| Label \ Read | Assignment | Unclear | Ordinary | None |
|---|---|---|---|---|
| **Assignment** (2) | 2 | 0 | 0 | 0 |
| **Unclear** (2) | 0 | 2 | 0 | 0 |
| **Ordinary** (6) | 1 | 3 | 2 | 0 |
| **None** (48) | 0 | 0 | 0 | 48 |

Of 10 titles with a threshold, 6 were read exactly. Ordinary thresholds were mostly read as unclear (3), which only adds a question, and once as an assignment (V52, "the threshold of cost effectiveness": a real error). **There is still no implicit threshold in either set**, such as "eligibility at age 65": question-form titles rarely state one. That behaviour is covered by development tests only.

## Clarification and extraction

| | Result |
|---|---|
| The follow-up a careful reader would ask was among those asked | 46 of 58 |
| Treatment contains the labelled word | 16 of 30 |
| Outcome contains the labelled word | 11 of 20 |
| Errors among elements shown as "stated", by the metric | 1 of 27 |

Most extraction misses are questions read as ambiguous, where nothing is extracted. The metric is lenient. Reading the stated elements after the run shows two that a reader would call wrong:
- V51, treatment "NICE have a cost-effectiveness threshold and what other…";
- V58, treatment "scattered light, spared cortex, and near-threshold vision", which is right in substance but reversed in role, since the label is about what is explained.

V22, treatment "Spanish", was also caught by the metric.

## Failures, all of them

**Causal read as ambiguous (11): the verb is not on the list.**
- V03 respond to, V07 demand, V10 empower, V14 discipline, V17 deteriorate.
- V08 "is X habit forming".
- V19 "how large are X effects".
- V28 "what does X prevent".
- V53 "is X safe".
- V54 "is there an X effect on Y".
- V55 a statement with "potentiate".

**Other errors on intent.**
- V11, causal read as descriptive: "how much does size erode…", the verb "erode" being unknown. This is the kind of error that tells a researcher their question is not causal.
- V51, ambiguous read as causal: "does NICE have a threshold … what other factors influence": a false causal reading.
- V34, ambiguous read as predictive; V35, descriptive read as predictive: the word "forecast" decided.
- V15, V42, V43, V44, descriptive read as ambiguous; V52 too, with the false threshold.

## What this does and does not show

Across two sets of 114 titles, the analyser rarely overclaims (2 false causal readings, 1 false non-causal), has never produced a wrong method given a form, and abstains on about a third of causal questions.

It does not show:
- performance on what students type;
- performance in French: **no French question is in either set**;
- performance on implicit thresholds;
- agreement between raters;
- that version 2 is better than version 1.

## Addendum: the version in the code is 2.1, not the version evaluated

After this run, a second-stage review on new examples found that assignment was being inferred from words in the outcome ("labour force participation" read as self-selection), and that two wordings were misread ("would crime rise without street lighting", "is X responsible for Y"). These were corrected, on examples from neither set, so **the code is version 2.1, which has not been evaluated on a fresh set.**

A regression check, which is **not an evaluation**, compares 2.1 with the stored runs:

**first set, stored run: version 1.** 56 questions. Intent read differently: 11 (Q06: ambiguous -> causal; Q08: ambiguous -> causal; Q10: ambiguous -> causal; Q11: ambiguous -> causal; Q13: ambiguous -> causal; Q18: ambiguous -> causal; Q24: ambiguous -> causal; Q35: ambiguous -> causal; Q41: causal -> predictive; Q51: ambiguous -> causal; Q52: ambiguous -> causal). Inferred fields differ: 7. Method outcome differs: 1 (Q08: abstained -> correct). Wrong methods now: 0.

**second set, stored run: version 2.** 58 questions. Intent read differently: 0 (none). Inferred fields differ: 1. Method outcome differs: 0 (none). Wrong methods now: 0.

So on the second set the intent results above carry over to 2.1 unchanged. The differences on the first set are expected, since version 2 was written after its failures were seen; they are not an improvement in any measured sense.

## What should happen next

1. A second rater fills in `rater_sheet.csv` in this folder (`../RATER_PROCEDURE.md`).
2. The two testers' questions, in English and French, form a third set **only if the analyser is frozen first**.
3. Do not extend the verb list on these failures and report these numbers. Any version 3 needs a new set.
