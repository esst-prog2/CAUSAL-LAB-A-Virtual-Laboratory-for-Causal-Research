## Why

HW6 review 5 (error handling) found failures that were hidden, or reported as something else:

- a boolean or text treatment column made `estimate_did` return NaN without an error: `params.get("D", nan)` missed the coefficient `D[T.True]`. An uploaded CSV with `D` = true/false loaded fine, then every DiD showed NaN;
- three stress-test checks caught every exception and returned WARNING, so an internal error counted as a threat. The Serial Correlation fit had no guard at all;
- leave-one-out (robustness) and the matching IPW bootstrap skipped any exception with `except Exception: continue`.

## What Changes

- `estimate_did`: booleans become 0/1; a non-numeric treatment raises a translated error; the coefficient is looked up without a NaN fallback.
- Upload: `D` and `treated_unit` must be 0/1 indicators and `period` and `Y` numeric; accepted indicators are stored as integers.
- Stress test: only `ValueError`, `LinAlgError` and `ZeroDivisionError` are caught, giving N/A with the message; the Serial Correlation fit is guarded the same way.
- Leave-one-out catches only `LocalizedError` (no treatment variation left). The matching bootstrap catches only `PerfectSeparationError` and `LinAlgError`, and reports how many replications were usable.

## Impact

- Code: `estimators/did.py`, `utils/validation.py`, `app.py`, `robustness_engine/stress_test.py`, `robustness_engine/robustness.py`, `estimators/matching.py`, `ui/methods_page.py`, locales.
- Tests: new `test_error_handling.py`; new AppTest for an invalid upload.
