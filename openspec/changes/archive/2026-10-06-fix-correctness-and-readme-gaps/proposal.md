## Why

The README's own bar for "it works" (section 4) is not met, and some numbers the app shows are wrong.

- **Stress tests.** The hw4 spike measured three of the five "Break My Design" checks as useless. Spillovers fires on 100% of clean worlds, Heterogeneous Effects on 94%, and Serial Correlation never fires. As a result the Identification Strength score barely moves (57.6 → 58.0) whatever the threat.
- **Simulation and estimation engines:**
  - Under staggered adoption, many "treated" units are never treated, yet they still count in the true ATT.
  - The Monte Carlo compares every replication with the last replication's truth.
  - The event study fits a rank-deficient model.
  - The generated Stata script fails on numeric ids.
- **App state:**
  - The dashboard shortcuts do nothing.
  - A stale CSV upload silently overrides a newly generated Virtual World.
  - Ground truth is shown for uploaded data, which violates the real-world-data-upload spec.
  - Editing a widget after generation changes the treatment period used to analyse already-generated data.
- **README promises not delivered.** Section 3 promises a treated-vs-untreated trend plot and a "plausible / questionable / violated" parallel-trends verdict. Section 4 promises that diverging pre-trends are flagged. Section 5 promises that DiD is validated against a reference package. None of these exist.

The user asked on 2026-10-06 to fix everything (PLANNING_LOG). This reverses the 2026-10-03 deferral of the recalibration.

## What Changes

- **Stress tests**, recalibrated so that each check measures its threat:
  - Parallel Trends: full-rank lead test, plus a plain-language verdict — plausible (p ≥ 0.10), questionable (0.01 ≤ p < 0.10), violated (p < 0.01).
  - Spillovers: a real test that adjacent controls shift after treatment relative to other controls (instead of counting neighbours).
  - Serial Correlation: within-unit residual autocorrelation, corrected for the fixed-effects (Nickell) bias.
  - Heterogeneous Effects: variance-ratio F test of the pre/post changes of treated units vs control units.
- **Virtual World generator:**
  - confounded selection draws exactly the requested number of treated units;
  - staggered adoption dates stay inside the panel;
  - the AR(1) errors are stationary from the first period;
  - generation is vectorized (it was O(N²·T) with spillovers);
  - two new threat levers that the stress tests can be checked against: `differential_trend` (diverging pre-trends) and `anticipation` (effect starting k periods early).
- **Monte Carlo:** each estimate is compared with its own replication's truth, and any confidence level is supported.
- **Event study:** control units sit in the reference category, so the model is full-rank.
- **Robustness battery:**
  - the windows are symmetric around the treatment date;
  - the leave-one-out row reports the range of estimates, not a pseudo standard error;
  - adjacency is only used for numeric ids.
- **Code generation:** the Stata script no longer `encode`s columns.
- **Diagnosis keywords:** short keywords match whole words only, so "age" no longer matches "average".
- **DiD:**
  - a clear error when the treatment has no variation;
  - an automated check against `linearmodels.PanelOLS` with two-way effects and clustered SEs.
- **App:**
  - dashboard shortcuts open their pages, and the selected page survives a language switch;
  - an upload is loaded once per file, and loading it clears the old ground truth;
  - the analysis pages use the configuration snapshot that generated the data;
  - for uploaded data, the treatment date is inferred from `D`, and staggered timing is detected;
  - estimates are cached;
  - the deprecated `use_container_width` is replaced by `width=`, and `streamlit>=1.50` is required;
  - new Estimation-page plot: treated vs untreated mean outcome over time, with the treatment date marked.

## Capabilities

### New Capabilities
- `app-navigation`: dashboard shortcuts, and page selection that survives a language switch.
- `trend-plot`: the treated vs untreated average outcome plot.

### Modified Capabilities
- `break-my-design-stress-test`: the parallel-trends, spillover, serial-correlation and heterogeneity requirements change; a calibration requirement is added.
- `virtual-world-generation`: confounding, staggered adoption and serial-correlation requirements change; differential-trend, anticipation and configuration-snapshot requirements are added.
- `monte-carlo-evaluation`: replication truth and the confidence level change.
- `robustness-battery`: windows, leave-one-out and adjacency change.
- `event-study-estimation`: control units are coded in the reference category.
- `code-generation`: the Stata script no longer re-encodes columns.
- `causal-diagnosis`: whole-word keyword matching.
- `did-estimation`: no-variation error and reference-package agreement.
- `real-world-data-upload`: an upload is loaded once, it clears the ground truth, and the treatment timing is inferred from `D`.

## Impact

- **Code:** `robustness_engine/{stress_test,robustness}.py`, `simulation_engine/{dgp,monte_carlo}.py`, `estimators/{did,event_study}.py`, `code_generator/generator.py`, `causal_engine/diagnosis.py`, `app.py` and `ui/*.py` (`width=`).
- **Requirements:** `streamlit>=1.50`.
- **Tests:** new `tests/test_stress_and_engine_fixes.py` and `tests/test_did_reference.py`.
- **Spike:** `spike/stress_test_calibration.py` is extended with the two new levers and re-run; its results file records the before/after numbers.
- **README:** sections 3–5 are updated with the new behaviour and measured numbers.
