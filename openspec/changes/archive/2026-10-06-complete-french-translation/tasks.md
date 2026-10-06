## 1. i18n foundation

- [x] 1.1 Add `tf`, `Msg` (a `str` subclass that pickles), `LocalizedError` and `render` to `utils/i18n.py`. Verify that a `Msg` renders in French, keeps `str` behaviour, and survives `pickle`.

## 2. Engines

- [x] 2.1 Convert the messages of the stress test, robustness battery, diagnosis and recommendation to `Msg`. Verify that all existing tests still pass unchanged.
- [x] 2.2 Convert the estimator, virtual-world, column-mapping and theoretical-model messages and errors to `Msg` / `LocalizedError`. Verify that all existing tests still pass unchanged.

## 3. Interface

- [x] 3.1 Rewrite `app.py`, `ui/methods_page.py` and `ui/theory_page.py` so every string goes through `L` / `F` / `R`, with option lists translated through `format_func`. Verify with the two end-to-end smoke scripts (app fixes, CSV uploads), which give the same numbers as before.

## 4. Proof

- [x] 4.1 Add `tests/test_i18n_coverage.py` (same keys and placeholders, static keys, dynamic families, French rendering of engine messages). Verify that it passes. It found two missing keys, which are now added.
- [x] 4.2 Run a scripted French render audit of every page with data, all six methods, all seven catalogue models, plus a calibration and a prediction. Verify that 0 raw keys and 0 untranslated English sentences remain outside code blocks. The audit found and fixed a shadowed `render` import and lazily evaluated language closures.

## 5. Close the loop

- [x] 5.1 Run all tests, add the PLANNING_LOG lines, update README section 4, and verify `openspec validate complete-french-translation --strict`.
