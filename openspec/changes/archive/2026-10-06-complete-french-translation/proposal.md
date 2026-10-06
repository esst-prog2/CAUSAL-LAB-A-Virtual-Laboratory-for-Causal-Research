## Why

README section 4 sets this bar: "Switching the sidebar language toggle from EN to FR redraws every page's text in French." Only page titles and navigation went through the i18n layer. About 280 interface strings, and every message produced by the engines, were hard-coded English. Those messages are the stress-test details, recommendation rationales, diagnosis notes, estimator warnings and errors, and theoretical-model texts. The French interface was therefore mostly English. The user asked on 2026-10-06 to make everything perfect.

## What Changes

- **Messages from the engines.** Engines return translatable messages instead of English strings: a locale key plus parameters. A `Msg` *is* a `str` whose value is the English text, so engine code, tests and string operations work unchanged. The interface renders the message in the active language. Errors raised for the user are `LocalizedError`, a `ValueError` subclass.
- **Interface strings.** Every interface string in `app.py`, `ui/methods_page.py` and `ui/theory_page.py` goes through the i18n layer. This covers:
  - labels, buttons, captions, info and warning boxes;
  - chart titles and axes;
  - table headers;
  - option lists, through `format_func`.
- **Locale files.** `en.json` and `fr.json` grow from 77 to 663 keys, with identical key sets and identical placeholders.
- **Deliberate English exceptions**, labelled as such in the interface:
  - the generated Python/R/Stata scripts, which are source code;
  - the per-method "Technical summary (English)" log;
  - bibliographic references;
  - the names of columns from the user's own data.
- **Automated coverage.** `tests/test_i18n_coverage.py` checks that:
  - EN and FR have the same keys and the same placeholders;
  - every key used in the code exists;
  - every dynamic key family exists (methods, options, levels, catalogue, parameters, components…);
  - engine messages render differently in French.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `internationalization`: the runtime-toggle requirement now covers engine-generated messages and every interface string. New requirements: translatable engine messages, a single source for the English text, identical key sets, and the explicit English exceptions.

## Impact

- **Engines (messages only, no calculation change):**
  - `utils/i18n.py`: adds `tf`, `Msg`, `LocalizedError` and `render`;
  - `robustness_engine/{stress_test,robustness}.py`, `causal_engine/{diagnosis,recommendation}.py`;
  - `estimators/{common,did,rct,matching,iv,rdd,synthetic_control,dml}.py`;
  - `simulation_engine/{dgp,method_worlds}.py`;
  - `theory_engine/{game,calibration,predictions,catalogue}.py`, `utils/column_mapping.py`.
- **Interface:** `app.py` and `ui/*.py`.
- **Locales:** `locales/{en,fr}.json` are rewritten as plain sorted-insertion JSON; the blank-line grouping is dropped.
