# HW6 review 6 — Dependencies and dead code

- **Date:** 2026-10-16
- **Branch:** `hw6-review`, after review 5 (`c9eae27`)
- **Criteria** (slide points copied by the user): every declared dependency used, every used dependency declared; no new dependency without need; no dead functions, imports, files or translation keys; no stale duplicate documents.

## Scope and method

- **Dependencies:** every top-level `import` in `causal_lab/` (app, tests) and `spike/`, compared with `causal_lab/requirements.txt`. The packages installed in `.venv` were listed with `pip list`.
- **Dead code:**
  - the AST audit from review 2 (unreferenced functions, unused parameters, unread dataclass fields);
  - a scan for unused imports;
  - a scan for locale keys whose literal appears nowhere in the code. Dynamic families such as `check.*`, `nav.*` and `opt.*` were checked by hand against their f-string builders.
- **Files:** `git ls-files`, looking for duplicates, leftovers and generated files.

## Findings

| # | Finding | Severity | Evidence | Action |
|---|---|---|---|---|
| 6.1 | Declared runtime dependencies all used, and all used ones declared: streamlit, numpy, pandas, scipy, statsmodels, linearmodels, plotly, scikit-learn, sympy. | — | import scan vs `requirements.txt` | **No change** |
| 6.2 | **`pytest` had become an undeclared dependency**, through my own review 5 test (`import pytest`, `pytest.raises`, `monkeypatch`). It was the only test file that could not run as a plain script, which the project's tests otherwise all do. | Medium (self-introduced) | `grep -rln "import pytest"` → only `test_error_handling.py` | **Fixed** without adding a dependency: rewritten with `unittest.mock.patch.object` and a small `_raises` helper; it runs as a script |
| 6.3 | **Dead methods since the original upload** (`b435bae`), referenced nowhere: `DiagnosisResult.as_table`, `MethodScore.as_dict`, `StressTestReport.summary_table`. `CheckResult.detail` was used only by `summary_table`. | Low | AST audit (deferred from review 2, finding 2.4); `grep -rn` across code, tests, docs | **Removed** |
| 6.4 | Unused imports: `DiDResult` in `robustness.py`, `LocalizedError` in `rct.py`. | Low | import scan | **Removed** |
| 6.5 | Dead translation keys `home.upload` ("Upload My Dataset") and `settings.local_mode`. The app uses `settings.local_mode_note`, and upload lives on the Virtual Lab page. | Low | literal scan + `grep 'home\.'`, `grep local_mode` | **Removed** from EN and FR (712 keys each); README key count updated (it said 704, stale since review 3) |
| 6.6 | **`causal_lab/causal_lab_README.md` was a byte-identical copy** of `causal_lab/README.md`. Both are the original v0.1 README, which says, for example, that RCT, IV, RDD, synthetic control and DML do not exist yet. | Low (misleading docs) | `cmp` → identical; content vs README §3 | **Deleted the copy.** Kept `causal_lab/README.md`, which the user uploaded, and marked it historical with a link to the current README |
| 6.7 | **The root README had no instructions to run the app or the tests**; they existed only in the stale v0.1 README. | Low | `grep "streamlit run" README.md` → none | **Added** section 6 "Running it" (install, run, tests as scripts or with pytest) |
| 6.8 | Unused parameters (`_score_iv(design)` …, catalogue builders' `n`) and unread result fields. | — | AST audit | **No change**, for the reasons given in review 2 (shared call signatures; public outputs) |

## Tests

- `pytest` (whole repository): **115 passed** (118.4 s).
- Every one of the **26 test files run as a plain script** (`python tests/test_x.py`): **0 failures**. This confirms the README claim of 6.7, and 6.2.
- AST audit after the removals: **no** unreferenced function left.
- `test_i18n_coverage.py` (included above) still finds identical key sets and placeholders in EN and FR after the key removal.

## Remaining risks

- The lower bounds in `requirements.txt` (for example `pandas>=2.2`, `streamlit>=1.50`) were not tested; only the installed versions were (pandas 3.0.6, streamlit 1.64.0, statsmodels 0.15.0, linearmodels 7.0). Checking them needs a second environment, which was not installed.
- The locale-key scan treats any key family built with an f-string as used. A dead member of a live family would not be found.
