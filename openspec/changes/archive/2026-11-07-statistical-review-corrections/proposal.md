## Why

A statistical review on 2026-11-07 probed every estimator and diagnostic. It found:

- the DiD crashed on an empty outcome cell;
- the event study's standard errors bypassed the DiD's correction (0.402 against 0.284 on the same two-period model);
- Callaway & Sant'Anna failed on non-consecutive periods, accepted a treatment that switches off, and ignored always-treated units in silence;
- the normal DiD interval covered 87.8% with 10 units, and nothing warned about few clusters;
- a passed pre-trend test was called "plausible", where the study shows it can pass at a bias of 47%.

Identification Strength was measured against the true bias: 91.7 at a bias of 21%, against 91.5 with no threat, and 72.5 at 320%. It also counted serial correlation and heterogeneity, which are not threats to identification. The user asked to keep it only if defensible.

## What Changes

- **DiD.** Complete rows only; Student t with G - 1 degrees of freedom; warnings for few clusters, a non-binary treatment and a treatment that switches off.
- **Event study.** Same standard errors and interval as the DiD.
- **Callaway & Sant'Anna.** The base period is the last observed before adoption; a treatment that switches off is refused; always-treated units are counted and reported.
- **Stored study.** Intervals and p-values recomputed with Student t, without re-simulation. Verdicts do not change.
- **Break My Design.** No score. A qualitative summary of the checks aimed at the identifying assumption, which never calls a design valid.
- **Wording.** A passed pre-trend test reads "not rejected". DiD under self-selection says why parallel trends are doubtful.

## Capabilities

### Modified Capabilities
- `break-my-design-stress-test`, `method-stress-test`, `report-export`, `monte-carlo-evaluation`, `did-estimation`.
