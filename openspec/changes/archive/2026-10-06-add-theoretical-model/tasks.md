## 1. Setup

- [x] 1.1 Add `sympy>=1.12` to `causal_lab/requirements.txt`, install it in `.venv`, and verify that `import sympy` succeeds.

## 2. Game engine

- [x] 2.1 `causal_lab/theory_engine/game.py`: `Agent`, `Game`, FOC and best-response derivation, and the safe editor parser `build_custom_game`. Verify in `tests/test_theory_game.py` that the Cournot best response matches the textbook form, that an undeclared name and the inputs `__import__`, `x.real` and `a[0]` are rejected, and that a valid custom Tullock model is built.
- [x] 2.2 Numerical solver `solve_equilibrium` (multi-start best response, deviation verification, dedupe) and `comparative_statics`. Verify in `tests/test_theory_game.py` that a custom symmetric Tullock model gives V/4, that a corner public-good contribution is 0 and verified, that a game with no pure equilibrium reports none. The test uses a pursuit game on [0,1], with U1 = -(x1-x2)^2 and U2 = (x1-x2)^2. Continuous matching pennies is not used because it has a pure equilibrium at (1/2, 1/2). and that the comparative-statics signs are correct for Cournot.

## 3. Catalogue

- [x] 3.1 `causal_lab/theory_engine/catalogue.py` with the seven models (N-agent builders where applicable), descriptions, references, outcomes and closed forms. Verify in `tests/test_theory_catalogue.py` that every smooth model's numeric equilibrium matches its closed form within 1e-3 relative, and that Downs and Niskanen closed-form equilibria pass verification.

## 4. Calibration and predictions

- [x] 4.1 `causal_lab/theory_engine/calibration.py`: `ParameterSource`, `compute_parameter`, `detect_structure`, `solve_by_scope`. Verify in `tests/test_theory_calibration.py` that a filtered mean is correct, that a missing column raises an error naming the parameter, that the Virtual Lab panel is detected as panel, and that per-period scope returns one ordered row per period.
- [x] 4.2 `causal_lab/theory_engine/predictions.py`: treatment shift (manual or treated − control), predicted effects and the verdict rule. Verify in `tests/test_theory_predictions.py` that a Tullock prize shift Δ gives a total-effort effect of Δ/2, and that the three verdict cases are correct.

## 5. Page

- [x] 5.1 Locale keys `nav.theory` and `theory.*` in `en.json`/`fr.json`. Verify that both parse and have identical key sets.
- [x] 5.2 `causal_lab/ui/theory_page.py` plus the sidebar entry in `app.py`: Model / Equilibrium & data / Predictions tabs, equations through `st.latex`, data sources (Virtual Lab, Causal Methods, CSV upload), equilibrium table and path chart, outcome-vs-parameter curve, and the comparison with a causal estimate. Verify with a headless `AppTest` run that solves every catalogue model with manual parameters, calibrates one model per period on a generated Virtual World, builds and solves a custom model, and shows an editor error, all without an exception.
- [x] 5.3 Manual smoke test in the browser: calibrate the Tullock model on an uploaded CSV, and compare a prediction with a Causal Methods estimate.

## 6. Close the loop

- [x] 6.1 Run every test file in `causal_lab/tests/` directly and verify that all print OK.
- [x] 6.2 Update README.md section 3 and PLANNING_LOG, and verify that `openspec validate add-theoretical-model --strict` passes.
