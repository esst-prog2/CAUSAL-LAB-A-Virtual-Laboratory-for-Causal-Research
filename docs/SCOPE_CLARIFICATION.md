# Academic scope: what is written, what was built, what is unconfirmed

**Status: PENDING PROFESSOR CONFIRMATION.** Nothing in this repository shows that a change of scope was approved. This note states the facts so that the professor can confirm or correct them.

## What is written

- **Issue #1 (2026-09-11).** Status "not yet". "Write the brief about one method, not ten modules": difference-in-differences, a simulated world where the true effect is known, a measurement of under what conditions the estimator goes wrong and by how much, varying confounding, staggered adoption and effect heterogeneity. The hard part is deciding "how much bias is too much" and defending that number in December. The existing code "is not your starting point".
- **Issue #2 (2026-09-26).** Homework 3 accepted, with two small fixes: install the planning-log rule (`AGENTS.md`, `CLAUDE.md`) and record decisions as they happen.
- **README.** Its first sentence describes a tool for one DiD question. Sections 3 and 5 record that more was built, including on 2026-10-25 "knowing that this departs from the scope above and from the advice to stay on one method (issue #1)".
- **PLANNING_LOG.md, 2026-11-03.** "The depth of the question analysis is the project's originality" (the author's statement).

## What was built

| Element | State |
|---|---|
| DiD on simulated worlds, with the true effect known | Built. 4 threats x 5 levels x 1,000 worlds, stored and reproducible |
| "How much bias is too much" | Decided: at most 10% of the effect and at least 90% coverage |
| Confounding, staggered adoption, heterogeneity | Confounding and staggered dynamic effects are in the study. Heterogeneity over time since adoption is in the study, through the staggered threat. Heterogeneity **across units** is in the app's simulator but **not one of the study's four threats**, which also include diverging pre-trends and anticipation |
| Eight methods in the recommendation | Built |
| Six more estimators (RCT, matching, IV, RDD, synthetic control, DML) | Built, beyond the brief |
| Question analysis | Built, stated by the author as the principal contribution |
| Game-theory module, data connectors, report export | Built, beyond the brief |

## Where they conflict

1. **One method or several.** Issue #1 asks for one. The app covers eight in its recommendation.
2. **What the contribution is.** Issue #1 centres on measuring when an estimator fails. The author now presents the analysis of research questions as the original contribution.
3. **The starting point.** Issue #1 says the existing code is not the starting point. The project extended it.
4. **Effect heterogeneity.** Issue #1 asks to vary it. The stored study varies effects that grow with time since adoption, but not effects that differ across units (`treatment_heterogeneity`). Whether that satisfies the request is the professor's call. Adding it would take a new threat in `simulation_engine/demo_study.py` and about 30 minutes of computing, and has not been done.

## A possible reading, to be confirmed

This is a proposal, not an agreement:

- **DiD and its simulation study remain the validated core**: the only method measured under the decision rule.
- **The question analysis is the principal contribution**: it decides whether DiD, or another design, should be used at all.
- **The other methods are the context the analysis needs**: to say "not DiD here" credibly, the app must know the alternatives. They are validated against reference packages, not under the decision rule.
- **The theory module is an extension**, not part of the claim.

## What the professor needs to confirm

- Whether this reading of the scope is acceptable.
- Whether the question analysis may be presented as the principal contribution.
- Whether effect heterogeneity must be added to the simulation study.
- What is assessed in December.
- Whether issue #2 can be closed.

## Proposed line for PLANNING_LOG.md

To be added by the author once the email is sent, and corrected by a new line when the answer arrives:

```
- 2026-11-05: Project scope: PENDING PROFESSOR CONFIRMATION. The written instruction (issue #1) is one method, DiD; the app covers eight in its recommendation and the author presents the question analysis as the principal contribution. The author reports having discussed this with the professor, but no written confirmation exists yet; asked for it by email on [date]. Until it arrives, no document states that the change was approved.
```
