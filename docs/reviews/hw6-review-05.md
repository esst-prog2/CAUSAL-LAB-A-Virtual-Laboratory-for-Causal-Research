# HW6 review 5 — Explicit and reliable error handling

- **Date:** 2026-10-16
- **Branch:** `hw6-review`, after review 4 (`8aba484`)
- **Criteria** (slide points copied by the user): no silent failures; no catch-all handlers that hide bugs; no fallback values passed off as results; errors reported where the user can act on them.

## Scope and method

- **Every `except` clause** outside the tests (`grep -rn except`), plus lookups with a default value (`.get(…, nan)`). Each handler was checked for three things: what it catches, what it does instead, and whether the user can see it.
- **Probes on degenerate inputs:**
  - treatment column stored as booleans or text;
  - non-numeric outcome;
  - missing indicator values;
  - a forced singular design in the stress test (monkeypatched).
- **Files examined:** `app.py`, `estimators/{did,event_study,matching,rdd}.py`, `robustness_engine/{robustness,stress_test}.py`, `theory_engine/{calibration,game}.py`, `ui/{methods_page,theory_page}.py`, `utils/{i18n,validation}.py`.

## Findings

| # | Finding | Severity | Evidence | Action |
|---|---|---|---|---|
| 5.1 | **Silent NaN estimate.** `estimate_did` read the coefficient with `fitted.params.get(treatment_col, np.nan)`. A boolean or text `D` enters the formula as a category (`D[T.True]`), so the lookup missed and ATT, SE, CI were all NaN, with no error. An uploaded CSV with `D` = true/false passed every upload check. | High | Probe: `D.astype(bool)` → `att = nan, se = nan`; `D` = "yes"/"no" → `nan` | **Fixed.** Booleans are cast to 0/1; a non-numeric treatment raises `err.did_non_numeric`; the coefficient is read without a fallback, so any future mismatch fails loudly |
| 5.2 | **Upload accepted unusable values.** Only column names and variation in `D` were checked. | Medium | `app.py` upload block | **Fixed.** `utils/validation.invalid_required_columns`: `D` and `treated_unit` must be 0/1 with no missing value, `period` and `Y` numeric (spec: D is the "treatment indicator", treated when D = 1). Accepted indicators are stored as `int` |
| 5.3 | **Computation errors counted as threats.** Parallel Trends, Anticipation and Spillovers caught `Exception` and returned WARNING with the message "Test could not be computed". That is a contradiction, and it lowered the score. Serial Correlation had no guard: a singular fit there crashed the page. | Medium | `stress_test.py` (old l.101, 157, 188; `# pragma: no cover`, i.e. never tested); `smf.ols(...)` unguarded in `_check_serial_correlation` | **Fixed.** `NUMERICAL_ERRORS = (ValueError, LinAlgError, ZeroDivisionError)` → N/A with the message, consistent with review 3's N/A decision (user). Other exceptions propagate |
| 5.4 | **Leave-one-out skipped any failure** (`except Exception: continue`). The only expected failure is "no treatment variation left". | Low | `robustness.py` (old l.66) | **Fixed.** Catches `LocalizedError` only. The note still reports how many units were used |
| 5.5 | **Matching bootstrap skipped any failure, without saying so.** The SE could rest on a few replications and nobody would know. | Low | `matching.py` (old l.112) | **Fixed.** Catches `PerfectSeparationError` and `LinAlgError` only; `details["ipw_bootstrap_used"]` is shown next to the SE ("n usable replications") |
| 5.6 | Handlers kept as they are, each explicit and visible to the user. | — | — | **No change:** |

The handlers in 5.6:
- upload `read_csv` (`except Exception`): any parse failure of an arbitrary file is shown as a read error;
- `game.py:332`: re-raised as a translated `err.expr_parse`;
- `event_study.py:92`: skips non-numeric bucket names by design;
- `rdd.py:114`: a bandwidth with too few points shows NaN in the sensitivity table, labelled by bandwidth;
- the theory curve, where unsolved points are gaps;
- `i18n.tf` falling back to English when formatting fails, which is guarded by `test_same_keys_and_placeholders`.

## Tests

- **New:**
  - `tests/test_error_handling.py` (5 tests): text/boolean treatment; upload value checks; N/A on a numerical failure and propagation of a programming error; leave-one-out does not hide a programming error; matching bootstrap count;
  - AppTest `test_upload_with_a_text_treatment_is_rejected`.
- **Mutation checks:**
  - catch-all restored in the stress test (`NUMERICAL_ERRORS = (Exception,)`) → **killed**;
  - type check removed from `estimate_did` → **killed** (fails with `KeyError`; thanks to the removed fallback it is no longer a silent NaN).
- **Results:**
  - `pytest` (whole repository): **115 passed** (118.3 s);
  - `openspec validate --specs`: **27 passed**; change `2026-10-16-hw6-explicit-errors` validated `--strict` and archived.

## Remaining risks

- `NUMERICAL_ERRORS` is a judgement about which exceptions statsmodels raises on degenerate data. A numerical failure of another type would now crash the Break My Design page instead of showing a verdict. That is visible, not silent, but less graceful.
- Upload validation does not check that `D` is consistent with `treated_unit` and `period` (for example, D = 1 for a control unit). That would be a new data rule; none is specified.
