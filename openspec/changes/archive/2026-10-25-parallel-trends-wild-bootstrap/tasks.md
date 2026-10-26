## 1. Diagnosis

- [x] 1.1 Compare variants of the Parallel Trends test on the same clean Virtual Worlds:
  - classical F;
  - CR1 with F(q, G − 1);
  - Hotelling F(q, G − q), with G the units and with G the treated units;
  - CR2 + Hotelling;
  - wild cluster restricted bootstrap.

## 2. Implementation

- [x] 2.1 Replace the asymptotic F test with the wild cluster restricted bootstrap in `robustness_engine/stress_test.py`:
  - exhaustive enumeration for G ≤ 9, otherwise 999 seeded draws;
  - fixed effects removed by alternating projections, so unbalanced panels are exact;
  - N/A below 5 units.
- [x] 2.2 Add the `stress.pt.too_few_units` message in English and French.
- [x] 2.3 Verify independently:
  - the Wald statistic equals statsmodels' cluster Wald times its CR1 factor;
  - the p-value equals a first-difference enumeration;
  - the within residuals equal explicit dummies on an unbalanced panel.

## 3. Tests

- [x] 3.1 Rewrite the Parallel Trends cases of `tests/test_stress_hand_computed_regressions.py`:
  - p = 1 for equal trends;
  - the 2/2^G floor in the 5–10% band;
  - "questionable" and "violated" against first differences;
  - an ordinary design with a mid-range p;
  - seeded random draws;
  - N/A for 4 units.

  Check with mutants: 5 of 5 caught.
- [x] 3.2 Adapt `tests/test_error_handling.py`, which simulated a singular regression through `smf.ols`.

## 4. Calibration and specification

- [x] 4.1 Re-run the calibration spike and record it in `spike/` and the README.
- [x] 4.2 Update the parallel-trends requirement. Verify with `openspec validate parallel-trends-wild-bootstrap --strict`.
