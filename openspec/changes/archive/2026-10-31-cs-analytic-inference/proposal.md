## Why

The estimator validation study (2026-10-31) found that Callaway & Sant'Anna's unit-bootstrap intervals were too short with small adoption cohorts (about 3 units): coverage 91.4%, size 8.6%. A warning was added, but on 2026-10-31 the user asked to correct the problem rather than only warn about it. A jackknife was tried and was not significantly better.

## What Changes

- **Analytic inference.** Every aggregate (the overall ATT and each event-study ATT(e)) is a sum of one contribution per unit. The variance sums, over adoption cohorts and the never-treated group, n_s times the unbiased (n_s − 1) variance of the contributions. The interval and the p-value use a Student t with Welch–Satterthwaite degrees of freedom.
- **One-unit cohorts** borrow the variance of the same combination of outcome changes among the never-treated units (else the not-yet-treated).
- **The unit bootstrap** remains only as a fallback, used when no variance can be borrowed.
- **Validation (1,000 worlds):** coverage 95.0% (0.7), size 5.0% (0.7). It is about 40 times faster than the bootstrap.
- **Against R `did`:** the SE is 3.5% above `did`'s analytic one, by design: `did` divides by n where Causal Lab uses n − 1.
- **In the two-group, two-period case,** the result is exactly Welch's t test (checked against scipy).
- **The small-cohort message** now explains the wide interval instead of saying it is too narrow, and the SE label states the degrees of freedom.
- **Bibliography:** Welch (1947) and Satterthwaite (1946), checked against Crossref.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `staggered-did-estimation`: analytic inference, the tab content, and the small-cohort message.

## Impact

- `estimators/staggered_did.py`, the Estimation page, the report, and the texts (EN, FR).
- The R `did` reference test is tightened from within 15% to between 0% and 5%.
- New tests: the Welch equivalence and the one-unit cohort.
