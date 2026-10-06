## Context

See proposal.md. These were the remaining known limits, after the stress-test recalibration and the translation work.

## Goals / Non-Goals

**Goals:** each fix is validated by Monte Carlo or by an automated test, not by assumption.

**Non-Goals:**
- Covariate-adjusted Callaway & Sant'Anna (doubly-robust or outcome-regression versions) and its analytic influence-function SEs.
- The Abadie-Imbens (2016) propensity-score adjustment, which becomes unnecessary once matching is on the covariates.

## Decisions

- **Callaway & Sant'Anna without covariates, base period g−1, unit bootstrap.**
  - This is the unconditional version, which matches the Virtual World's unconditional parallel trends.
  - The unit-level bootstrap is valid for this smooth estimator and is simple to implement. 199 replications take about 2 s on a 100×20 panel.
  - The overall ATT weights post cells by cohort size, which is exactly the mean effect over treated unit-periods. The Virtual World's `true_att` is redefined to that quantity, so the two are comparable.
  - Rejected alternative: the de Chaisemartin & D'Haultfoeuille estimator, which targets switchers. Callaway & Sant'Anna is the more common reference and fits the event-study display.
- **Dynamic-effects lever.** The effect is multiplied by (1 + 0.25·v·e), where v is the intensity value and e the number of periods since adoption. This is the textbook case of the Goodman-Bacon decomposition: early-treated units act as controls for later ones while their own effects are still growing.
- **Covariate matching with bias correction.**
  - Matching uses Mahalanobis distance via a Cholesky whitening, then a scikit-learn KD-tree, which avoids the n1×n0 distance matrix.
  - Bias correction uses a linear μ0 fitted on controls.
  - Measured on the Matching world over 200 replications: SD of estimates 0.092 (versus 0.116 with propensity-score matching), mean SE 0.100, coverage 97%.
- **Summary lines as `Msg`.** `format_summary` stores translatable lines on the result, and `summary_text` stays their English join. The method headline uses `method.<key>`.
- **Generated scripts.** A `lang` argument switches only comments and printed labels. A test asserts that every line differing between the EN and FR scripts is a comment, header or label.

## Risks / Trade-offs

- [Bootstrap SEs are random] → They use a fixed seed, so they are reproducible.
- [Covariate matching degrades with many covariates (curse of dimensionality)] → The bias correction removes the first-order bias. The propensity-score overlap diagnostic is still shown.
