## Context

Today `estimators/` holds `did.py` and `event_study.py`. Each is one function that takes a DataFrame plus column-name arguments and returns a dataclass with a `summary_text`. `simulation_engine/dgp.py` generates only the DiD panel. `app.py` is a single Streamlit script that routes on `st.radio` page labels. Tests are plain functions with a `__main__` block, run directly with `python tests/test_x.py`; `pytest` is not installed in `.venv`. See proposal.md for motivation, and specs/ for required behavior.

## Goals / Non-Goals

**Goals:**
- One estimator module per method, using the same calling convention as `estimate_did` (DataFrame and column names in, dataclass out), so the estimators work outside the app.
- Every estimator is validated against its own virtual world, where the truth is known, in an automated test.

**Non-Goals:**
- Fuzzy RD, robust bias-corrected RD inference (Calonico–Cattaneo–Titiunik), and covariate-weighted (V-matrix) synthetic control.
- Interactive or other DML model variants, matching with K > 1 neighbours or calipers, LIML or GMM for IV.
- Monte Carlo replications, code generation, stress tests and robustness batteries for the new methods. The existing pages stay DiD-only.
- Feeding the new estimators' results back into the Method Recommendation scores.

## Decisions

**Shared result type.** `estimators/common.py` defines `MethodResult(method, estimand, estimate, se, ci_low, ci_high, p_value, n_obs, details: dict, warnings: list[str], summary_text)`. `se`, `ci_*` and `p_value` are `float | None`, because synthetic control has no standard error. Method-specific tables and paths go in `details`. One result type lets the page render every method with the same metric row and warning list. The alternative, one dataclass per method like `DiDResult`, would need six rendering branches for the common parts.

**RCT.** The difference in means and its HC2 standard error come from OLS of `Y ~ D`. The covariate-adjusted estimate follows Lin (2013): `Y ~ D * (X - mean(X))` with HC2 standard errors, and the coefficient on D is the ATE. Lin is chosen over plain additive adjustment because it is never less precise asymptotically and stays consistent under heterogeneous effects.

**Matching.**
- Propensity scores come from a statsmodels `Logit` model.
- Each treated observation is matched to its 1 nearest control on the propensity score, with replacement, via `np.searchsorted` on sorted control scores. This is O(n log n).
- Standard error: Abadie–Imbens (2006) variance for the ATT, `V = (1/N1²)[Σ_treated (Y_i − Ŷ0_i − τ)² + Σ_controls K_i(K_i − 1) σ̂²_i]`. Here K_i is how many times control i is used as a match. σ̂²_i is estimated by matching each control to its nearest other control: `(Y_i − Y_l)²/2`. The bootstrap is not used, because it is invalid for nearest-neighbour matching (Abadie & Imbens 2008). This variance ignores the estimation error of the propensity score; the design accepts that and says so in the result notes.
- IPW ATT uses normalized (Hájek) weights p/(1−p) on controls. Its standard error comes from 200 bootstrap replications with a fixed seed. The bootstrap is valid for this smooth estimator.

**IV.** `linearmodels.iv.IV2SLS` (already a dependency) with `cov_type="robust"`. The first-stage F is `first_stage.diagnostics["f.stat"]` divided by the number of instruments, since linearmodels reports the robust Wald chi² statistic. OLS uses statsmodels with HC1. Writing 2SLS by hand was rejected: linearmodels gets the second-stage standard errors right, and hand-rolled versions commonly get them wrong.

**RDD.** Weighted least squares on observations with |x − c| < h, using triangular weights `1 − |x − c|/h` and the specification `Y ~ D + (x−c) + D:(x−c)`, with HC1 standard errors. The coefficient on D is the jump.
- Default bandwidth: the Imbens–Kalyanaraman (2012) procedure with the triangular-kernel constant 3.4375. The steps are: a pilot bandwidth of 1.84·sd(x)·n^(−1/5) for the density and the conditional variances; a global cubic with a jump to get the third derivative; quadratic fits on each side for the second derivatives; then the regularization terms. A plain rule-of-thumb bandwidth was rejected because it ignores curvature.
- The manipulation check is a two-sided binomial test, `scipy.stats.binomtest`, on the counts in [c − w, c) and [c, c + w), with w = h/2. It is a simple stand-in for the McCrary density test, and the notes say so.

**Synthetic control.**
- Outcome-only weights: minimize ‖y1_pre − Y0_pre·w‖² subject to w ≥ 0 and Σw = 1, solved with `scipy.optimize.minimize(method="SLSQP")` starting from uniform weights.
- Placebos re-run the same solver with each donor as the treated unit and the remaining donors (excluding the real treated unit) as the pool.
- The p-value is the rank of the treated unit's post/pre RMSPE ratio among all J+1 ratios, following Abadie, Diamond & Hainmueller (2010).
- A dedicated quadratic-programming library was rejected: SLSQP is in scipy and sufficient for a few dozen donors.

**DML.** Partially linear model with K=5 folds (`sklearn.model_selection.KFold(shuffle=True, random_state=seed)`).
- Both nuisance models are `RandomForestRegressor(n_estimators=200, min_samples_leaf=5, random_state=seed)`. A regressor is also used for binary D, so m(X) is a probability estimate. Random forests need no tuning and handle non-linearity, which is why they are preferred to lasso here.
- θ = Σ ṽ·ũ / Σ ṽ². The standard error comes from the influence function ψ = (ũ − θ·ṽ)·ṽ, as `sqrt(mean(ψ²) / mean(ṽ²)² / n)` (Chernozhukov et al. 2018).

**Virtual worlds.** `simulation_engine/method_worlds.py` has one generator per method. Each takes a frozen dataclass of parameters with a `seed` and returns `(df, truth)` in the same shape as `generate()`.
- RCT: the truth is the sample ATE, the mean of τ_i.
- Matching: the treated units' τ_i depends on X1, so ATE ≠ ATT; the truth is the sample ATT.
- IV: a constant effect, so 2SLS targets it directly.
- RDD: the jump of a cubic conditional mean at c.
- Synthetic control: a factor model in which the treated unit's loadings are a convex combination of the donors' loadings; the truth is the mean post-treatment effect.
- DML: non-linear m(X) and g(X); the truth is θ.

**Column mapping.** `utils/column_mapping.py` declares each method's roles. Each role has a name, a kind (single or multi), whether it is required, and whether it must be numeric. `validate_mapping(df, method, mapping)` returns a list of error strings, following the same "return problems, don't raise" style as `utils/validation.missing_required_columns`. `prepare_mapped_frame` drops NA rows and reports how many it dropped. The existing five-column panel upload is untouched (see the delta spec).

**App wiring.** A new `elif page == L("nav.methods")` branch is added, plus its label in the sidebar list.
- Session state keeps one entry per method: `method_data[method] = {"df", "truth", "mapping", "source"}`. Switching methods therefore does not discard the work done on another method.
- Estimator calls are wrapped in `try/except ValueError` and shown with `st.error`.
- Plots use plotly, as the rest of the app does.

## Risks / Trade-offs

- [Abadie–Imbens SE ignores propensity-score estimation error] → Measured on the Matching virtual world over 200 replications, the SE is conservative: it averages 0.151 against a true sampling SD of 0.116, and CI coverage is 100%. This is stated in the result notes, and the IPW estimate with a bootstrap SE is reported alongside.
- Measured CI coverage over 200 replications (60 for DML) on each method's default virtual world:
  - RCT 94%
  - IV 94%
  - RDD 94%
  - DML 93%
  - Matching 100% (conservative, see above)
  
  Bias is below 0.03 in absolute value for every method.
- [The IK bandwidth can be unstable in small samples, or degenerate when the estimated curvature difference is near zero] → The regularization terms keep it finite. The bandwidth is clipped to the data range. Bandwidth sensitivity at 0.5x and 2x is always shown.
- [SLSQP may stop at a slightly suboptimal point] → The convex problem has a unique optimum in fit. The optimizer's success flag is checked and a warning is added if it fails.
- [DML with random forests adds a few seconds per run and a new dependency] → 200 trees and 5 folds keep a run on n ≈ 1,000 under ~5 s. `scikit-learn` is a standard, widely installed package.
- [Scope creep: the README's section 5 warns about it] → Non-goals are listed above, the decision is logged in PLANNING_LOG, and nothing in the existing DiD path changes.
