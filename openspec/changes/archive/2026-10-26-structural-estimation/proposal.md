## Why

README section 3's "Not this term" list included structural estimation (MLE/GMM) of the theoretical models. Calibration set each parameter from one explicit moment, with no standard error. On 2026-10-26 the user asked for a broad project.

## What Changes

- **`theory_engine/estimation.py`:**
  - `fit_logit_qre`: maximum likelihood estimate of the logit QRE λ along the principal branch. It reports a curvature standard error, a likelihood-ratio interval, and a test against random play. When the likelihood is flat to the end of the branch, it gives a lower bound only.
  - `gmm_first_order_conditions`: two-step efficient GMM on the equilibrium first-order conditions, with robust sandwich standard errors and Hansen's J test. Input that is under-identified, not identified, or has collinear instruments is refused.
- **`theory_engine/finite_games.py`:** the QRE continuation becomes a branch tracer (`logit_branch`, `qre_profile`), so the likelihood is evaluated in one pass. The module docstring no longer says "support enumeration" (vertex enumeration has been used since the matrix-games change).
- **`ui/estimation_page.py`:**
  - a "Structural estimation" tab on the continuous-model page, where each parameter is fixed, observed in a column, or estimated;
  - an "Estimate λ" section on the matrix-game page, with counts typed or counted in a dataset.
- **References:**
  - `tests/external_reference`: Gambit `logit_estimate` on 40 games;
  - linearmodels `IVGMM` on a new `cournot_markets.csv`;
  - `spike/estimation_calibration.py` for the Monte Carlo coverage.
- Messages in English and French.

## Capabilities

### New Capabilities
- `structural-estimation`

### Modified Capabilities
(none)

## Impact

**Tests:** new `tests/test_estimation.py`. Mutation check: 7 of 7 mutants caught.

**Calibration** (`spike/estimation_calibration.py`, 1000 replications):

| Scenario | Coverage of 95% intervals | Notes |
|---|---|---|
| QRE, inspection game, λ = 1 | LR 95.6%, Wald 95.3% | |
| QRE, inspection game, λ = 3 | LR 94.8%, Wald 93.9% | |
| QRE, stag hunt, λ = 2 | LR 98.4%, Wald 61.7% | 37% of samples give only a lower bound |
| Nonlinear GMM, 300 markets | 93.7–94.3% | J test size 4.9% |
