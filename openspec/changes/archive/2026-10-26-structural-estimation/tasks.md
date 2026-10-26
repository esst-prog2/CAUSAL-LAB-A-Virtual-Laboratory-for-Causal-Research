## 1. Engine

- [x] 1.1 Logit QRE maximum likelihood along the principal branch, with standard error, LR interval and a lower bound on flat likelihoods; checked against Gambit logit_estimate.
- [x] 1.2 Two-step GMM on first-order conditions, with sandwich standard errors and the J test; checked against linearmodels IVGMM.

## 2. Pages and verification

- [x] 2.1 Structural estimation tab and "Estimate λ" section, with EN and FR messages.
- [x] 2.2 Tests; 7 of 7 mutants caught; Monte Carlo coverage in `spike/estimation_calibration.py`.
- [x] 2.3 Validate with `openspec validate structural-estimation --strict`.
