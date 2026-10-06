## 1. Foundations

- [x] 1.1 Add `scikit-learn>=1.4` to `causal_lab/requirements.txt`, install it in `.venv`, and verify that `python -c "import sklearn"` succeeds.
- [x] 1.2 Add `causal_lab/estimators/common.py` with `MethodResult` and helpers for normal-approximation CI and p-value. Verify that it imports cleanly.

## 2. Virtual worlds

- [x] 2.1 Add `causal_lab/simulation_engine/method_worlds.py` with one config dataclass plus generator per method (RCT, Matching, IV, RDD, Synthetic Control, DML), each returning `(df, truth)`. Verify in `tests/test_method_worlds.py` that each generator is reproducible for a fixed seed and returns its documented columns and `truth["true_effect"]`.

## 3. Estimators (each verified against its virtual world)

- [x] 3.1 `estimators/rct.py`: difference in means, Lin-adjusted ATE and balance table, rejecting a non-binary treatment. Verify in `tests/test_rct.py` that the estimate is within 3 SE of the truth, that adjustment shrinks the SE, and that a 3-valued treatment raises `ValueError`.
- [x] 3.2 `estimators/matching.py`: logit propensity score, 1-NN matching ATT with Abadie–Imbens SE, IPW ATT with bootstrap SE, balance before and after, overlap warning. Verify in `tests/test_matching.py` that matching and IPW are each within 3 SE of the true ATT, while the naive difference in means is biased.
- [x] 3.3 `estimators/iv.py`: 2SLS through linearmodels, first-stage F, weak-instrument warning, OLS comparison. Verify in `tests/test_iv.py` that 2SLS is within 3 SE of the truth, that OLS is biased under endogeneity, and that a weak instrument triggers the warning.
- [x] 3.4 `estimators/rdd.py`: triangular-kernel local linear jump, IK bandwidth, 0.5x/1x/2x sensitivity, binomial manipulation check, rejection of a cutoff outside the data. Verify in `tests/test_rdd.py` that the estimate is within 3 SE of the truth and that a cutoff outside the data raises `ValueError`.
- [x] 3.5 `estimators/synthetic_control.py`: SLSQP convex weights, gap path, placebo-in-space p-value, balanced-panel validation. Verify in `tests/test_synthetic_control.py` that the weights are ≥ 0 and sum to 1, that the mean post gap is close to the truth, that the p-value has the form k/(J+1), and that an unbalanced panel raises `ValueError`.
- [x] 3.6 `estimators/dml.py`: cross-fitted partially linear model with random forests, influence-function SE, nuisance R², naive OLS. Verify in `tests/test_dml.py` that DML is within 3 SE of θ, that naive OLS is further from θ than DML on the non-linear world, and that two runs with the same seed give the same estimate.

## 4. Column mapping

- [x] 4.1 `causal_lab/utils/column_mapping.py`: role definitions per method, `validate_mapping` and `prepare_mapped_frame`. Verify in `tests/test_column_mapping.py` that an unmapped required role, a duplicated column and a non-numeric column are each reported by role name, and that NA rows are dropped and counted.

## 5. App page

- [x] 5.1 Add the `nav.methods` and related keys to `locales/en.json` and `locales/fr.json`, and verify that both files parse and have the same key set.
- [x] 5.2 Add the Causal Methods page to `app.py`: method selector, assumption text, a virtual-world/CSV source switch with per-method parameters or column mapping, an estimate button, the metrics row with truth and bias for virtual data, the warnings list and a method-specific plot. Estimator `ValueError`s are shown with `st.error`. Verify with a headless `streamlit.testing.v1.AppTest` run that generates and estimates every method without an exception.
- [ ] 5.3 Manual smoke test with `streamlit run causal_lab/app.py`: run each method on its virtual world, and upload a CSV for one method with a deliberately bad mapping. Verify that the error names the role.

## 6. Close the loop

- [x] 6.1 Run every test file in `causal_lab/tests/` directly (existing and new) and verify that all print OK.
- [x] 6.2 Update README.md section 3 to move the six methods from "Not this term" to "Delivered", add a PLANNING_LOG line, and verify that `openspec validate add-causal-method-estimators --strict` passes.
