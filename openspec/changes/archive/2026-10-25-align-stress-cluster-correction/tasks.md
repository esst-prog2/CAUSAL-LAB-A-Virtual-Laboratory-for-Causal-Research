## 1. Implementation

- [x] 1.1 Make the DiD's nested fixed-effects factor public (`estimators.did.nested_fe_factor`) and use it in the Parallel Trends Wald test and the Spillovers SE.
- [x] 1.2 Replace the hand values in `tests/test_stress_hand_computed_regressions.py` (cluster factor 28/15), keeping a case between 5% and 10% for each check that pins the 10% threshold. Verify the values independently (explicit-dummy sandwich with numpy, scipy F and normal tails).

## 2. Calibration

- [x] 2.1 Re-run `spike/stress_test_calibration.py` on the old and new code with the same seeds and record the new results in `spike/stress_test_calibration_results_2026-10-25.md` and the README.

## 3. Specification

- [x] 3.1 State the correction in the parallel-trends and spillover requirements of `break-my-design-stress-test`. Verify with `openspec validate align-stress-cluster-correction --strict`.
