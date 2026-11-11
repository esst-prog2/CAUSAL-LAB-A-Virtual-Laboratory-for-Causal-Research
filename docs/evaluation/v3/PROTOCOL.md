# Evaluation protocol, version 3

Written on 2026-11-07 and completed on 2026-11-11, before the test titles were read and before version 3 was run on them. **It adds to the first two evaluations and replaces nothing:** `../REPORT.md` and `../v2/REPORT.md` stay as they are.

## Why a version 3

Version 2 failed one bar, recall of causal questions (0.60 for a bar of 0.70). Its report names the cause: causal verbs are a closed list, and new titles use verbs that are not on it. It also says that extending the list on those failures would not be an evaluation, and that any version 3 needs a new set.

Version 3 changes the rule, not the list:

1. **An open verb class (English).** A question built as auxiliary + subject + verb + object ("Do minimum wages discipline firms?") is read as causal whatever the verb, unless the verb only describes (know, use, prefer, differ…; a closed list in `question_reading.py`). Treatment and outcome are then never shown as stated, only "to confirm"; when the verb takes a preposition ("respond to"), no role is guessed.
2. **A named effect.** "Is there an X effect on Y?" and a question naming an effect without "of" ("how large are peer effects?") are read as causal, with roles to confirm.

**What this costs, known in advance.** The cause of version 2's failures was read in its report, so **neither earlier set can evaluate version 3**: the regression check on them is reported, not used as evidence. The rule also matches the labelling rule for `causal` ("asks what something does to something else") more closely than before, and the labeller wrote the rule: the main weakness, as before.

## Development and test, split before either was seen

`spike/fetch_question_candidates_v3.py` takes, for each stratum of `../v2/PROTOCOL.md`, a pool of up to 40 qualifying works by descending citations, further down the order, with no work from the candidates of either earlier set. **Works at even ranks go to development, at odd ranks to the test set.** The test pool is written outside the repository, and its SHA-256 is recorded below before version 3 is developed:

| File | SHA-256 |
|---|---|
| test pool (`eval_v3_private/test_pool.json`, outside the repository, fetched 2026-11-11) | `547285ce70a14961339f510205e0e13f05833bc620f2c6cb92e995e7b09a233b` |

Development: the analyser is changed and checked on the development titles only. They are committed in `dev_set.json` with their labels.

Freezing: version 3 is committed. **Only after that commit** are the test titles read and labelled, by the rules of `../PROTOCOL.md` and the mixed-title rule of `../v2/PROTOCOL.md`. The labelled set is committed with its hash, then run once by `spike/evaluate_question_analysis.py`.

## The test set

The strata and sizes of `../v2/PROTOCOL.md` (58 titles), taken in pool order (by citations) from the test half. Exclusions as before, each with its reason. If a stratum's half has too few qualifying titles, the shortfall is reported, not filled from the development half.

## What stays the same

Metrics, label rules, leakage rules, the single run and **the success bars**, unchanged. The bar that failed (recall ≥ 0.70) is not moved. Precision of causal readings (≥ 0.85) is the bar version 3 puts at risk, and it is reported with the same weight.

## Limits, known in advance

Those of the earlier protocols: one rater who wrote the analyser, question-form titles of cited articles rather than what students type, English only, about 30 causal titles, so a 95% interval of about ±0.17 on recall. **A recall above 0.70 on this set would not show that the true recall is above 0.70**; it would show that version 3 does not fail the bar on new titles.

## Changes to this protocol

- **2026-11-11, the ITS stratum.** Its pool holds 31 qualifying works, not 40: 16 for development, 15 for test. The test needs 3.
- **2026-11-11, the fetch.** OpenAlex sent truncated pages twice; the script now retries and caches pages. The selection rule did not change.
