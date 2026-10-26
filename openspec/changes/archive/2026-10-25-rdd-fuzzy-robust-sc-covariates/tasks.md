## 1. RDD

- [x] 1.1 Rewrite the estimation core side by side, following rdrobust: conventional, bias-corrected, robust, fuzzy.
- [x] 1.2 Check it against rdrobust (sharp and fuzzy, conventional and robust; gaps below 1e-14).
- [x] 1.3 Add a compliance parameter to the RDD world, the optional treatment role, the inference choice on the page, and the scripts.

## 2. Synthetic control

- [x] 2.1 Add covariate predictors with a searched V; add covariates to the SC world; show the predictor table; pass the covariates to the stress checks; update the scripts.
- [x] 2.2 Compare with pysyncon on 6 worlds; store a reference and the tolerance.

## 3. Verification

- [x] 3.1 Tests for RD, SC, the page and the scripts; mutation check; EN and FR messages.
- [x] 3.2 Validate with `openspec validate rdd-fuzzy-robust-sc-covariates --strict`.
