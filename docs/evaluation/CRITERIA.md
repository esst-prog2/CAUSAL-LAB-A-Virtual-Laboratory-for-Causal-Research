# Success criteria of the analyser's evaluation: for the author's review

**Status: proposed by the agent before the first run, not yet adopted by the author.** They were not changed after the results were seen. If you change them now, the change is **post-hoc**: record it as such in `PLANNING_LOG.md`, and keep the original verdicts next to the new ones. Do not choose bars by looking at which ones the results pass.

## The principle behind them

A wrong reading costs more than an abstention. An abstention costs the researcher one click. A wrong reading can send them to the wrong design without warning. So the bars are strict on errors and lenient on abstention.

None of the bars is derived from a theorem or a published standard. They are judgements, and "statistical justification" below means what the sample size can and cannot support.

## What the sample can support

With the number of questions available, the 95% interval (Wilson) around a proportion is wide:

| Observed | n | Interval |
|---|---|---|
| 0.80 | 30 | 0.63 to 0.90 |
| 0.80 | 50 | 0.67 to 0.89 |
| 0.95 | 20 | 0.76 to 0.99 |
| 0 errors | 40 | up to 0.09 |

So a pass or fail near a bar is weak evidence. A bar at 5% errors cannot be confirmed with 40 questions and no error: the interval still reaches 9%. Roughly 75 questions with no error would be needed for an upper limit of 5%.

## Criterion by criterion

| Criterion | Proposed | Why | In practice | Alternatives | Risk if too permissive |
|---|---|---|---|---|---|
| Recall of causal questions | ≥ 0.70 | Some abstention is acceptable, since it asks rather than guesses | Up to 3 in 10 causal questions need one extra click | 0.60 tolerates a shy tool; 0.80 demands wider vocabulary | A tool that asks about almost everything looks safe and helps nobody |
| Precision of causal readings | ≥ 0.85 | Being called causal opens the method workflow | At most about 1 in 7 causal readings is wrong | 0.90 is stricter, and 22 readings cannot distinguish it well | Predictions or associations get causal treatment |
| False non-causal | ≤ 5% | The error found in the first test: a causal question told it is not causal | About 1 in 20 at most | 0%, unprovable on this sample | Researchers are told their question is not causal, and may believe it |
| Abstention on ambiguous | ≥ 0.70 | Association wordings should not be decided for the researcher | Up to 3 in 10 are decided anyway | 0.80 | Associations get causal language |
| Recommendation from untouched form | 0 | A rule, not a statistic: DiD by default is the error being removed | None | No alternative is defensible | Default method returns |
| Wrong method given the form | ≤ 5% | The most costly error | About 1 in 20 at most | 0 of n, with its interval reported | Wrong design, without warning |
| Threshold false positives | ≤ 2 | Each one suggests an RDD with no rule | | A rate, once the set has more thresholds | RDD suggested from any number |

**Note on recall and abstention.** They trade off. Accepting more questions as causal raises recall and lowers abstention, so read them together and never alone.

**Note on the method metric.** Whatever bar is chosen, it does not show that the app finds a design, because the form already encodes the design. It shows that the wording does not disturb a correct form. Consider presenting it as a safety check rather than an accuracy.

## Bars that do not exist yet, and might

- **French.** No criterion, because no French question has been evaluated.
- **Stated readings.** The share of "stated" readings that are wrong (2 of 39 in the first run, plus 2 the metric missed) has no bar. If it matters to you, set one for the next set.
- **Rater agreement.** You may want a minimum raw agreement for the labels to be used at all, to be fixed before the second rater returns the sheet.

## Your decision

For each criterion, keep or replace it, and add one line to `PLANNING_LOG.md`, with the date and the words "post-hoc: results seen" if you change anything. The bars apply to the next evaluation as they stand unless you change them first.
