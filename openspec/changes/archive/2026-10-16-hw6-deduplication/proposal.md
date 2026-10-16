## Why

HW6 review 4 (code duplication) found the same logic written in several places, where the copies could drift apart:

- the neighbourhood rule (unit ids differing by 1) in the Spillovers check and in the robustness battery. Review 3 restricted only the first to the Virtual World;
- the language helpers (`_lang`, `F`, `R`, error text) copied in the two page modules, each keeping the language in a module-level global that all Streamlit sessions share;
- the 95% normal quantile written as `1.96` in four places and recomputed in `did.py`, although `estimators.common.Z_95` exists.

The user decided that the robustness battery follows the same rule as the Spillovers check (PLANNING_LOG.md, 2026-10-16).

## What Changes

- One neighbourhood function, `robustness_engine/neighbourhood.py`, used by both features; `run_robustness_battery` takes an explicit keyword-only `ids_encode_neighbourhood`.
- One `ui/page_text.py` for the page language helpers, reading the language from the visitor's session.
- `Z_95` everywhere.

## Impact

- Code: `stress_test.py`, `robustness.py`, `app.py`, `ui/methods_page.py`, `ui/theory_page.py`, `estimators/did.py`; new `neighbourhood.py`, `page_text.py`.
- Tests: new `test_neighbourhood.py`; new AppTest in `test_app_flows.py`.
