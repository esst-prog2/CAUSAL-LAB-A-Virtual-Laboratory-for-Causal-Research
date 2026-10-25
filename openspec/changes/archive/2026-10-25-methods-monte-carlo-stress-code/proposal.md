## Why

README section 3 listed "Monte Carlo / stress-test / code-generation support for the six additional methods" under "Not this term": those pages were DiD-only. On 2026-10-25 the user decided to build it anyway, with the other excluded features.

## What Changes

- **`estimators/registry.py`:** the six methods' worlds and estimator calls in one place, shared by the page, the Monte Carlo, the checks and the code. The page's private copies are removed.
- **`simulation_engine/method_monte_carlo.py`:** a Monte Carlo per method. Matching skips its IPW bootstrap there (new `n_bootstrap` argument), which cuts 0.94 s to 0.02 s per replication.
- **`robustness_engine/method_stress.py`:** Break My Design per method, calibrated before release. Four first-draft rules had false-alarm rates of 26–94% and were replaced:
  - RCT |SMD| > 0.1: 55%;
  - matching "any unit outside support": 94%;
  - RDD "shift > 1 SE": 55%;
  - SC in-time gap > 2 RMSPE: 26%.
- **`code_generator/methods.py`:** Python, R and Stata scripts per method. Every Python and R script was run and its agreement with Causal Lab measured; each header states that agreement.
- **Causal Methods page:** Break My Design, Monte Carlo and Code tabs under each result. The world's configuration is stored, also in project files, so the Monte Carlo can redraw it.
- **Fix:** the DiD Python script now applies the app's nested-fixed-effects correction. It printed 1.91 instead of 1.34 on Card & Krueger.

## Capabilities

### New Capabilities
- `method-monte-carlo`
- `method-stress-test`
- `method-code-generation`

### Modified Capabilities
- `code-generation`: the Python DiD script reproduces the app's standard error.

## Impact

- **Monte Carlo on the default worlds** (200 replications, 30 for DML; `spike/method_calibration_results.md`): every method has 93–96% CI coverage and a bias below 0.03. A first 30-replication run had suggested an IV bias of 0.16 and 87% RDD coverage; both were Monte Carlo noise.
- **Findings:**
  - the synthetic-control permutation test of the default world is anti-conservative: p = 1/21 occurs 9.5% of the time instead of 4.8%;
  - the RCT balance test warns on 23% of randomized worlds with only 40 observations (HC1 over-rejects in very small samples);
  - R DoubleML differs from Causal Lab by about 1.4 SE on the test world.
- **Tests:** new `test_method_monte_carlo.py`, `test_method_stress.py`, `test_method_code.py` and `test_methods_page_tools.py`. 9 of 9 mutants are caught; two first survived, which led to the F = 4.4 case and to pinning the robust overidentification test.
