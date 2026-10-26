## Why

The post-hw6 review (PR #9) found that Parallel Trends and Spillovers still count the unit dummies in the CR1 small-sample correction of their unit-clustered regressions. hw6 review 3 had removed that convention from the DiD estimator, so the app used two conventions for the same kind of regression. On 2026-10-25 the user decided to align the two checks with the DiD.

## What Changes

- Parallel Trends: the joint Wald test uses the cluster covariance with the unit dummies left out of K (F reference distribution unchanged: F(q, G − 1)).
- Spillovers: the adjacent × post SE uses the same correction; the p-value stays normal.
- Both reuse `estimators.did.nested_fe_factor` (previously the private `_nested_fe_factor`).

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `break-my-design-stress-test`: the parallel-trends and spillover requirements state the small-sample correction.

## Impact

- Code: `causal_lab/robustness_engine/stress_test.py`, `causal_lab/estimators/did.py` (rename only).
- Tests: `causal_lab/tests/test_stress_hand_computed_regressions.py`, new hand values (cluster factor 28/15 instead of 14/3).
- Verdicts: both checks warn more often. Calibration spike re-run on the same 1,200 worlds (`spike/stress_test_calibration_results_2026-10-25.md`): Parallel Trends false alarms 14% → 20%, Spillovers 8% → 9%, detection unchanged at 100%, clean-world score 92.2 → 90.8.
- Card & Krueger: unchanged (both checks are N/A on those data).
