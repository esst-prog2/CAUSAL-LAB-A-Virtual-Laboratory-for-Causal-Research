# Evaluation report, version 3 of the analyser

**One run, on 2026-11-11, on a new frozen set of 58 titles, at commit `a91c43e`** (the analyser frozen at `20b4b8f`, before the test titles were read). Protocol: `PROTOCOL.md`. Every result: `results.json`. The first two reports stay as they were.

## Result

**Recall of causal questions passes its bar on this set: 0.83 (25/30), with no false causal reading (25/25).** One other criterion fails: 3 threshold false positives for a bar of 2, from the threshold reader, which version 3 did not change.

**Most of the rise is the set, not the code.** Run on this same set, the frozen version 2 reads 24 of the 30 causal titles (0.80). Version 3 adds one (T14, "Does firm investment respond to peers' investment?"). So the gap between 0.60 on the second set and 0.83 here mostly says how much recall moves from one set of 30 titles to another. The honest summary is:

- version 3 does not fail the recall bar on new titles, and it read no non-causal title as causal;
- this set does not show that version 3 is better than version 2: +1 title is within noise;
- across the three sets, recall is 0.64, 0.60 and 0.83 for versions 1, 2 and 3, each on its own set. The intervals overlap.

The labels come from a single rater who also wrote the analyser, so these numbers are provisional.

| Criterion | Bar | Version 3, this set | 95% interval (Wilson) | Verdict | Version 2 on this set, for comparison |
|---|---|---|---|---|---|
| Recall of causal questions | ≥ 0.70 | 0.83 (25/30) | 0.66 to 0.93 | Passes, interval wider than the bar | 0.80 (24/30) |
| Precision of causal readings | ≥ 0.85 | 1.00 (25/25) | 0.87 to 1.00 | Passes | 1.00 (24/24) |
| False non-causal | ≤ 5% | 0% (0/30) | up to 11% | Passes, interval wider than the bar | |
| Abstention on ambiguous | ≥ 0.70 | 0.94 (16/17) | 0.73 to 0.99 | Passes | |
| Recommendation with an untouched form | 0 | 0 of 58 | | Passes | |
| Wrong method given the form | ≤ 5% | 0% (0/32) | up to 11% | Passes, interval wider than the bar | |
| Threshold false positives | ≤ 2 | 3 | | **Fails** | |

The comparison column is the frozen version 2 (commit `c48bce9`) run on this set after the evaluation, to read the result. It is not a second evaluation of version 2.

## Dataset

58 titles: 30 causal, 17 ambiguous, 6 predictive and 5 descriptive by wording; 32 with a reported design. 6 candidates excluded, each with its reason in `question_set.json`: two DiD papers where DiD is only a robustness check, two IV papers that discuss the method rather than use it, a methods paper on matching, and one title whose "?" is an encoded prime. No work comes from the earlier sets or from the development half.

## Intent

Accuracy is 0.84 (49/58).

| Label \ Read | Causal | Predictive | Descriptive | Ambiguous |
|---|---|---|---|---|
| **Causal** (30) | 25 | 0 | 0 | 5 |
| **Predictive** (6) | 0 | 6 | 0 | 0 |
| **Descriptive** (5) | 0 | 0 | 2 | 3 |
| **Ambiguous** (17) | 0 | 1 | 0 | 16 |

## Method and design

| Design | n | Clue from the title alone | With the form: correct | Abstained | Wrong |
|---|---|---|---|---|---|
| DiD | 6 | 0 | 4 | 2 | 0 |
| RDD | 5 | 1 | 2 | 3 | 0 |
| IV | 6 | 1 | 3 | 3 | 0 |
| RCT | 6 | 1 | 2 | 4 | 0 |
| Synthetic control | 3 | 0 | 2 | 1 | 0 |
| ITS | 3 | 1 | 3 | 0 | 0 |
| Matching | 3 | 0 | 1 | 2 | 0 |
| **All** | **32** | **4** | **17** | **15** | **0** |

With the causal aim confirmed, all 32 are correct. The limits of `../REPORT.md` apply: the form encodes the design.

## Threshold

| Label \ Read | Assignment | Unclear | Ordinary | None |
|---|---|---|---|---|
| **Unclear** (1) | 0 | 0 | 0 | 1 |
| **Ordinary** (7) | 2 | 5 | 0 | 0 |
| **None** (50) | 1 | 0 | 0 | 49 |

The three false positives:
- T52, "earthquake triggering: no lower threshold": "triggering" is a word for a rule that assigns treatment. A real error.
- T51, "what is the threshold for symptomatic response and remission": an outcome level read as an assignment rule. A real error.
- T10, "Does the one-child policy improve children's human capital? A regression discontinuity design": read from "discontinuity". The title names the design, not a threshold, so by the label rule it is a false positive; a reader could argue it is not.

No ordinary threshold was read as ordinary: 5 of 7 were read as unclear, which only adds a question. There is again no assignment threshold among these titles, so threshold recall is not measured.

## Clarification and extraction

| | Result |
|---|---|
| The follow-up a careful reader would ask was among those asked | 48 of 58 |
| Treatment contains the labelled word | 24 of 29 |
| Outcome contains the labelled word | 17 of 24 |
| Errors among elements shown as "stated", by the metric | 1 of 42 |

The stated error is T02: outcome "corporate environmental", cut at the first comma of "environmental, social, and governance performance".

## Failures, all of them

**Causal read as ambiguous (5).** None has the shape the open verb class reads:
- T05 "is there a health penalty of X";
- T07 "what's X got to do with it";
- T17 "X: an information superhighway to Y", a metaphor;
- T18 "who may benefit", with no subject before the verb;
- T45 "are there causal relationships between", read as a relationship.

**Other errors on intent.**
- T37, ambiguous read as predictive: "predictive variables" decided.
- T41, T51, T58, descriptive read as ambiguous: "who has diabetes", "what is the threshold", "what percent would be covered". A safe error.

## What version 3's rules did here

Only T14 was read through the open verb class; the 24 others use verbs that were already on the list. The rule produced no false causal reading on these 58 titles. The progressive and "what works" rules were not triggered. So this set tests the new rules very little; it mainly shows they did not harm precision.

## Regression check on the earlier sets, not evidence

Version 3's rules were written knowing why version 2 failed, so the earlier sets cannot evaluate it. For the record:
- **first set** (56 titles): 13 readings change; causal titles read as causal 31/33, false causal 2;
- **second set** (58 titles): 6 readings change, all from ambiguous to causal on titles labelled causal; 24/30, false causal 1.

## What this does and does not show

It shows that, on a third set of new titles, version 3 reads 25 of 30 causal questions as causal and calls no other question causal, and that no wrong method was given with a form.

It does not show:
- that version 3 is better than version 2 (one title on this set);
- performance on what students type, or in French;
- that the true recall is above 0.70: the interval runs from 0.66;
- agreement between raters.

## What should happen next

1. A second rater fills in `rater_sheet.csv` in this folder (`../RATER_PROCEDURE.md`).
2. The threshold reader needs its own correction ("triggering", an outcome level), and then a new set: not this one. The correction is version 3.1 (addendum below); the new set is still to do.
3. Report all three evaluations together, never this one alone.

## Addendum: the version in the code is 3.1, not the version evaluated

Reading the three threshold false positives after the run showed that two were bugs, not judgement:
- T51: the word "at" was found inside "What" ("What Is the Threshold…" read as "at the threshold"). The same bug made V52, the only threshold false positive of the second set.
- T52: "trigger" made a rule even as the noun "triggering".

The run also showed T02's outcome cut at the first comma of a list. Version 3.1 matches threshold words as whole words, counts "trigger" only as a verb, and keeps the commas of a short list ("A, B, and C") in the outcome. The tests use invented examples, not titles from any set. T10 is not changed: naming "a regression discontinuity design" is a fair clue to an assignment threshold, and the label rule that counts it as false is not changed after the run.

**This set revealed these errors, so it cannot measure their correction: version 3.1 is not evaluated, and the results above stand as version 3's.** A regression check, which is not evidence, compares 3.1 with 3 on all 388 titles (the three sets and the development set). 6 readings change, and no other:

| Title | Version 3 | Version 3.1 |
|---|---|---|
| T51, "What Is the Threshold for Symptomatic Response…" | threshold: assignment | unclear |
| T52, "…earthquake triggering: No lower threshold in sight?" | threshold: assignment | unclear |
| T02, outcome | "corporate environmental" | "corporate environmental, social, and governance performance" |
| V52 (second set), "…what is the threshold of cost…" | threshold: assignment | unclear |
| D199 (development), "What Threshold for Adjuvant Therapy…" | threshold: assignment | unclear |
| D081 (development), outcome | "Poverty" | "Poverty, Health, and Education" |

Rescored on this set, 3.1 would have 1 threshold false positive (T10), but that is a corrected run on the set that showed the errors, not an evaluation. Whether 3.1 passes the threshold bar needs a fourth set.
