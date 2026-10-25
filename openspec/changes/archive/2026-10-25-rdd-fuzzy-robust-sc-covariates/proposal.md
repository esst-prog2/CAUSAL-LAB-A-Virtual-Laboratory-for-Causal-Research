## Why

README section 3 listed fuzzy RD, robust bias-corrected RD inference and covariate-weighted synthetic control under "Not this term". On 2026-10-25 the user decided to build them anyway, with the other excluded features.

## What Changes

**RDD.** `estimators/rdd.py` is rewritten around one side-by-side local polynomial core that follows rdrobust (CCT 2014). It gives:
- the conventional estimate, with a side-by-side HC1 SE (the old pooled-HC1 SE differed from rdrobust by 2.6e-5);
- the bias-corrected estimate and the robust SE;
- the fuzzy design: local Wald estimate, delta-method SE, and a first stage with its F statistic.

New options: `treatment_col` (fuzzy) and `inference = "conventional" | "robust"`, with conventional as the default. The RDD world gets `compliance` (default 1, which leaves sharp worlds unchanged bit for bit). The page gets an inference choice and an optional "treatment received" role.

**Synthetic control.** `covariate_cols` adds ADH predictors with a searched V. The inner problem is NNLS with a sum-to-one row; the outer problem is Nelder-Mead from k + 1 starts. The SC world gets `n_covariates` (default 0, which leaves worlds unchanged). The page gets an optional predictors role and a predictor-balance table, and the stress checks pass the covariates on.

**Code.** Fuzzy and robust RDD in all three languages; covariate SC in all three, labelled "close, not identical" because V is searched. The RDD scripts are now exact, SE included.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `rdd-estimation`: side-by-side HC1, robust bias-corrected inference, fuzzy RD.
- `synthetic-control-estimation`: covariate predictors.

## Impact

**Validated against rdrobust:**
- sharp and fuzzy, conventional and robust: estimates and SEs to 1e-14;
- stored in `tests/external_reference`.

**Measured:**
- with the IK bandwidth, conventional and robust CIs both cover 93–95% on the RDD worlds (the robust CI is 45% longer);
- with a hand-set wide bandwidth (curvature 5): h = 0.6 gives 69% vs 95%, and h = 0.9 gives 0% vs 85%;
- covariate SC is a local search: its pre-MSPE vs pysyncon was better in 4 of 6 worlds and up to 9% worse in 2. In the default worlds covariates do not reliably improve on outcome-only SC, as Kaul et al. (2022) explain.

**Tests:**
- 7 mutants: 6 caught. The 7th (unstandardized predictors) is equivalent, because V absorbs predictor scale.
