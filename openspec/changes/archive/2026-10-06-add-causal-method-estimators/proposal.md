## Why

The Method Recommendation page scores seven identification strategies, but only two of them (Difference-in-Differences and Event Study) can actually be run. When the app recommends a Randomized Controlled Trial, Regression Discontinuity, Instrumental Variables, Matching or Synthetic Control design, the researcher is left with a score and no way to estimate anything. The README lists these methods, plus Double Machine Learning, as "Not this term". The user has now decided to bring all six into this term (PLANNING_LOG, 2026-10-06).

## What Changes

- Add six runnable estimators, each returning an effect estimate together with its uncertainty and method-specific diagnostics:
  - Randomized Controlled Trial (difference in means and covariate-adjusted ATE, plus a covariate balance table)
  - Matching / Propensity Score (nearest-neighbour propensity-score matching ATT and inverse-probability-weighted ATT, plus balance and overlap diagnostics)
  - Instrumental Variables (two-stage least squares, plus first-stage strength and a naive OLS comparison)
  - Regression Discontinuity (sharp design, local linear regression with a data-driven bandwidth, bandwidth sensitivity and a density check at the cutoff)
  - Synthetic Control (donor weights, per-period gaps and placebo-in-space inference)
  - Double Machine Learning (partially linear model with cross-fitted machine-learning nuisance functions, plus a naive OLS comparison)
- Add one synthetic data generator ("virtual world") per method. Each generator has a known true effect, so every estimate can be shown next to its ground truth, as the Virtual Lab already does for DiD.
- Add a new "Causal Methods" page. On it the researcher picks a method, then either generates that method's virtual world or uploads a CSV and maps its columns to the method's roles (outcome, treatment, instrument, running variable, covariates, unit/period...). The page then runs the estimator and shows the result, its diagnostics and a method-specific plot.
- Column mapping is introduced for these new methods only. The existing panel/DiD upload on the Virtual Lab page keeps its five fixed columns.
- New dependency: `scikit-learn`, used for the Double Machine Learning nuisance models.

## Capabilities

### New Capabilities
- `rct-estimation`: average treatment effect under randomized assignment, unadjusted and covariate-adjusted, with balance diagnostics.
- `matching-estimation`: ATT under selection on observables, via propensity-score nearest-neighbour matching and inverse probability weighting, with balance and overlap diagnostics.
- `iv-estimation`: two-stage least squares effect of an endogenous treatment using an instrument, with first-stage strength diagnostics.
- `rdd-estimation`: sharp regression-discontinuity effect at a known cutoff, via local linear regression, with bandwidth selection, bandwidth sensitivity and a manipulation check.
- `synthetic-control-estimation`: effect on a single treated unit from a convex combination of donor units, with placebo-based inference.
- `dml-estimation`: partially linear Double Machine Learning estimate with cross-fitting.
- `causal-methods-lab`: the page, per-method virtual worlds with known truth, and CSV upload with column mapping that tie the six estimators together.

### Modified Capabilities
- `real-world-data-upload`: the requirement "Column names stay fixed; no column-mapping UI is offered" is narrowed to the panel/DiD upload, because the new Causal Methods page does offer column mapping.

## Impact

- New modules: `causal_lab/estimators/{common,rct,matching,iv,rdd,synthetic_control,dml}.py`, `causal_lab/simulation_engine/method_worlds.py` and `causal_lab/utils/column_mapping.py`.
- `causal_lab/app.py`: a new sidebar page (`nav.methods`). Existing pages are unchanged.
- `causal_lab/locales/{en,fr}.json`: new keys for the page.
- `causal_lab/requirements.txt`: adds `scikit-learn`.
- New tests in `causal_lab/tests/`, one per estimator plus the column mapping.
- README.md section 3: the six methods move from "Not this term" to "Delivered".
