# Evaluation protocol, version 4

Written on 2026-11-12, before the test titles were read and before version 3.1 was run on them. **It adds to the first three evaluations and replaces nothing.**

## Why a version 4

Version 3 failed one bar on the third set: threshold false positives (3 for a bar of 2). Two of the three were bugs, corrected in version 3.1 (`../v3/REPORT.md`, addendum): "at" found inside "What", and the noun "triggering" read as a rule. The set that showed them cannot measure their correction. Version 3.1 is therefore run on a fourth set, as is, **with no development step**: the code is the commit named below, frozen before the pool was fetched.

| Frozen | Commit |
|---|---|
| Version 3.1 of the analyser | `8033035` |

## The pool, fetched before it is read

`spike/fetch_question_candidates_v4.py` takes, for each stratum of `../v2/PROTOCOL.md`, up to 20 qualifying works by descending citations, under the same conditions, with no work from the candidates of the three earlier sets nor from the third set's development titles. The pool is written outside the repository, and its SHA-256 is recorded below before any title is read:

| File | SHA-256 |
|---|---|
| test pool (`eval_v4_private/test_pool.json`, outside the repository, fetched 2026-11-12) | `85a88a74811601725c5e01149ceafcdc49508d43b065a2657ffed0ea89d1444d` |

## The test set

The strata and sizes of `../v2/PROTOCOL.md` (58 titles), taken in pool order. Titles are labelled by the rules of `../PROTOCOL.md` and the mixed-title rule of `../v2/PROTOCOL.md`, **without running the analyser on them**. Exclusions as before, each with its reason, replaced by the next title of the stratum. If a stratum runs short, the shortfall is reported, not filled. The labelled set is committed with its hash, then run once by `spike/evaluate_question_analysis.py`.

## What stays the same

Metrics, label rules, leakage rules, the single run and **every success bar**, unchanged. In particular a title that only names a design ("a regression discontinuity design") is labelled by the wording rule, as T10 was: no threshold is described, so reading one is a false positive. This rule is kept although it costs version 3.1 a point; changing it after seeing T10 would be choosing the rule by its result.

## What it can and cannot show

It can show whether version 3.1 passes the threshold bar (≤ 2 false positives) on new titles, and give a fourth independent reading of every other bar. As before, about 30 causal titles give a 95% interval of about ±0.17 on recall, and the labels come from one rater who wrote the analyser. Earlier sets showed recall moving by 0.20 between sets for the same code: a single run is never reported alone.

## Changes to this protocol

None yet.
