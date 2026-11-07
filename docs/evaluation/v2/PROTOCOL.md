# Evaluation protocol, version 2

Written on 2026-11-07, before this set was collected and before version 2 was run on it. **It adds to the first evaluation and replaces nothing:** `../PROTOCOL.md`, `../REPORT.md` and `../results.json` stay as they are, and describe version 1 at commit `c9be335`.

## Why a second set

Version 2 of the analyser was corrected after a new check on 49 wordings. The first evaluation's failures, which I had read, pointed in part at the same fixes. That set therefore cannot test version 2.

## What stays the same

The metrics, the rules for labelling intent, the rules against leakage and the single run are those of `../PROTOCOL.md`. So are the **success bars**, unchanged and still not reviewed by the author: they were written before the first run, and they are not moved here.

## What is different

**New works only.** Every OpenAlex ID already in `../candidates.json` is excluded, so no question from the first set returns, nor any candidate seen while labelling it.

**Strata.** Selection by descending citations, under the same conditions as before.

| Stratum | Query | N |
|---|---|---|
| did | abstract: "difference-in-differences" | 6 |
| rdd | abstract: "regression discontinuity" | 5 |
| iv | abstract: "instrumental variable" | 6 |
| rct | abstract: "randomly assigned" or "randomized field experiment" | 6 |
| synthetic_control | abstract: "synthetic control" | 3 |
| its | abstract: "interrupted time series" | 3 |
| matching | abstract: "propensity score matching" | 3 |
| predictive | title: "predict" or "forecast" | 6 |
| descriptive | title: "prevalence", "what proportion" or "how common"; not "how many" | 6 |
| ambiguous | title: "associated with", "correlated", "relationship between" | 6 |
| threshold | title: "eligibility", "threshold", "cutoff" or "cut-off" | 8 |

Total: 58. The last stratum answers a gap in the first set, which held only 2 thresholds. Its titles are labelled `assignment`, `unclear`, `ordinary` or null from the title's wording.

**A rule for mixed titles, written now.** When a title has both a link word and an explicit causal clause, the clause decides the intent. In the first set this case was labelled by judgement. The rule also matches what version 2 does, and that is a known dependence: a label rule chosen by the author of the analyser favours it.

## Added metric

A confusion table of threshold kinds (`assignment`, `unclear`, `ordinary`, none), in place of recall alone.

## Limits, known in advance

The limits of `../PROTOCOL.md` apply, and in particular the single rater who also wrote the analyser. Implicit thresholds are only as represented as they are in question-form titles, which may be few. Question-form titles are not what students type. All are in English: **French is still only covered by development tests**, and the students' questions could fill this gap.

## Changes to this protocol

None yet.
