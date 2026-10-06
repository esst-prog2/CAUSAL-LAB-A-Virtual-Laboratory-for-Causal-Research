## 1. Engines

- [x] 1.1 Port the reviewed fixes into `dgp.py`, `monte_carlo.py`, `did.py`, `event_study.py`, `robustness.py`, `stress_test.py`, `generator.py` and `diagnosis.py`. Verify that every existing test file still prints OK.
- [x] 1.2 Add the `differential_trend` and `anticipation` levers to `VirtualWorldConfig`/`generate`. Verify in `tests/test_stress_and_engine_fixes.py` that the anticipation shift only touches the period before adoption, with D = 0.
- [x] 1.3 Add the plain-language parallel-trends verdict and the first-difference anticipation test. Verify that the diverging-pre-trends world is "questionable"/"violated", that the clean world is "plausible", and that severe anticipation is detected.
- [x] 1.4 Make DML predictions single-threaded. Verify with three consecutive runs of `tests/test_dml.py`.

## 2. Reference validation

- [x] 2.1 Add `tests/test_did_reference.py`. Verify that the estimate equals PanelOLS within 1e-8 and the SE within 2% on three worlds, that a true effect of 2.0 is recovered, and that the no-variation error is raised.

## 3. Calibration

- [x] 3.1 Extend `spike/stress_test_calibration.py` with the new levers and an output-name argument. Re-run it into `spike/stress_test_calibration_results_after_fix.md`, and verify that every row meets the spec bounds (false alarm ≤ 20%, detection ≥ 80%, clean score ≥ 85).

## 4. App

- [x] 4.1 `app.py`: page ids with working shortcuts, upload loaded once (with ground truth cleared and D variation checked), configuration snapshot, treatment timing inferred for uploads, staggered-aware event study, cached estimators, the treated-vs-untreated trend plot, the parallel-trends verdict banner, the two new threat sliders, and `width="stretch"` in `app.py` and `ui/*.py` with `streamlit>=1.50`. Verify with a scripted AppTest run that checks the shortcut, upload-then-generate, no truth for uploaded data, the configuration snapshot, the verdict banner, the page kept on a language switch, and all 12 pages rendering.

## 5. Close the loop

- [x] 5.1 Update README sections 3–5 with the new behaviour and measured numbers, add the PLANNING_LOG lines, run all tests, and verify `openspec validate fix-correctness-and-readme-gaps --strict`.
