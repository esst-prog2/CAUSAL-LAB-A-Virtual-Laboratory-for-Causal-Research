# HW6 review 4 — Unnecessary code duplication

- **Date:** 2026-10-16
- **Branch:** `hw6-review`, after review 3 (`fd51a7b`)
- **Criteria** (slide points copied by the user): logic copied rather than shared; copies that can drift apart; constants repeated as literals; merging only where the copies really express one rule.

## Scope and method

- **Searches** over every non-test module of `causal_lab/`:
  - function names defined in more than one module;
  - the literals `1.96` and `norm.ppf(0.975)`;
  - the neighbourhood rule (`c - 1`, `c + 1`, "adjacent");
  - `pivot`/`pivot_table` calls;
  - the error-rendering idioms.
- **Detector:** a script, kept outside the repository, that lists identical windows of 5 non-trivial lines across modules. It was run before the merges, as part of the search, and after them, to confirm.
- **Not merged on purpose:**
  - the `sys.path.insert` header of each test file, which keeps every test runnable as a script, as the README says;
  - the unit bootstraps of `staggered_did.py` and `matching.py`, which resample different objects for different estimators.

## Findings

| # | Duplication | Severity | Evidence | Action |
|---|---|---|---|---|
| 4.1 | **The neighbourhood rule was written twice**, in `stress_test._check_spillovers` and in `robustness.run_robustness_battery`. The copies had already drifted: review 3 limited the first to the Virtual World, while the second still applied it to Card & Krueger's sheet numbers. | Medium (inconsistent results between two pages) | `stress_test.py` (old l.170–172) and `robustness.py` (old l.77–83): same `(c - 1) in treated_ids or (c + 1) in treated_ids` | **Merged** into `robustness_engine/neighbourhood.py::adjacent_control_ids`. `run_robustness_battery` takes a keyword-only `ids_encode_neighbourhood`, and the app decides it in one helper. **User decision** (asked during this review): the robustness row follows the same rule; on real data the row is left out and the page says why. Spec `robustness-battery` updated (archived change `2026-10-16-hw6-deduplication`) |
| 4.2 | **Language helpers copied in two pages** (`_lang`, `F`, `R` in `ui/methods_page.py` and `ui/theory_page.py`, plus `_error_text` in the second). Each copy kept the language in a module-level `_LANG`. Module globals are shared by every session of the Streamlit server process, so one visitor's language could leak into another visitor's page. | Medium (latent cross-session defect) | Identical definitions at `methods_page.py:80–92` and `theory_page.py:39–51` (before); `global _LANG` set at the start of each `render` | **Merged** into `ui/page_text.py`, which reads the language from the visitor's own `st.session_state`. `app.py` uses the same `F`, `R` and `error_text` |
| 4.3 | **95% normal quantile repeated**: `1.96` literal four times (`app.py` ×3, `methods_page.py` ×1), and `stats.norm.ppf(0.975)` recomputed in `did.py` (added in review 3), although `estimators.common.Z_95` exists. | Low | grep | **Replaced** by `Z_95` |
| 4.4 | Two `LocalizedError` display idioms: `exc.render(lang)` and `_error_text(exc)`. | Low | grep | **Merged** into `error_text` (4.2) |
| 4.5 | Page preamble repeated (`df = active_df()`, the "no dataset" message, `treatment_setup`) in the Break My Design and Robustness pages. | Low | duplicate-window detector: `app.py:555`, `app.py:588` | **No change.** Four short lines of Streamlit page flow; a helper would hide the page structure without removing a rule |

## Tests

- **New:**
  - `tests/test_neighbourhood.py` (2 tests): the shared rule on a hand-made table whose expected set {1, 3, 4} is worked out by hand from the rule, and the robustness row present only when ids encode a neighbourhood;
  - `test_pages_with_shared_language_helpers_follow_the_session_language` (AppTest). It checks that, in French, the Theory model selector's labels, rendered by `R()` inside a `format_func` closure, are in French.
- **Mutation check:**
  - a first version of that test only checked the page titles, which come from the app's `L`, not from the shared helpers. With `page_text.lang` forced to `"en"` it still passed (**mutant survived**), so it tested nothing new;
  - it was rewritten to check the selector labels, and the same mutant now makes it fail (**mutant killed**).
- **Changed call:** `test_robustness_handles_string_unit_ids` now passes `ids_encode_neighbourhood=True`; its assertion is unchanged.
- **Results:**
  - `pytest` (whole repository), after the test rewrite: **109 passed** (117.0 s);
  - `openspec validate --specs`: **27 passed**;
  - duplicate-window detector after the merges: only 4.5 and a shared `from __future__` import header remain.

## Remaining risks

- The cross-session language leak (4.2) was found by reading the code. It was not reproduced, because AppTest runs a single session. The fix removes the shared state rather than relying on a test.
- `DiDResult` is imported but unused in `robustness.py`. It is left for review 6 (dead code).
