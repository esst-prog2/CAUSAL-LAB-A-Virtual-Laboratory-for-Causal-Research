## MODIFIED Requirements

### Requirement: Runtime language toggle
The system SHALL let the researcher switch the active language from the sidebar at any time, immediately re-rendering all page text. All page text means every label, button, caption, message box, chart title and axis, table header and option list, and every message produced by the engines.

#### Scenario: Switching language
- **WHEN** the researcher changes the EN/FR radio control in the sidebar
- **THEN** `st.session_state.lang` updates to the new value and the app reruns, so every page's text is redrawn through `t(key, new_lang)`

#### Scenario: French audit of every page
- **WHEN** the interface is in French, with a Virtual World generated, a diagnosis run, each Causal Methods estimator run on its virtual world, and each catalogue model solved (plus one calibrated model with a prediction)
- **THEN** no displayed text outside code blocks is a raw locale key, and none contains an English interface sentence from `en.json` that has a different French translation

## ADDED Requirements

### Requirement: Engine messages are translatable
Every message an engine produces for the researcher SHALL carry a locale key and its parameters, so the interface can render it in the active language. This covers check details, rationales, notes, warnings, model texts, calibration descriptions and user-facing errors. The message's plain string value SHALL be its English text.

#### Scenario: Stress-test detail in French
- **WHEN** a stress-test check result is displayed with the language set to "fr"
- **THEN** its explanation is rendered from the French template of its key, filled with the same numbers as the English version

#### Scenario: Error raised by an estimator
- **WHEN** an estimator rejects its input (for example a non-binary treatment) while the language is "fr"
- **THEN** the page shows the error in French

### Requirement: Identical key sets and placeholders
The English and French dictionaries SHALL contain exactly the same keys, and each French template SHALL use exactly the same placeholders as its English template.

#### Scenario: Coverage test
- **WHEN** `tests/test_i18n_coverage.py` runs
- **THEN** it passes only if both dictionaries have the same keys, the placeholders match, every key referenced in the code exists, and every dynamic key family (methods, options, levels, catalogue entries, parameters, recommendation components, diagnosis dimensions) is present

### Requirement: Deliberate English exceptions
The system SHALL keep the following in English, and SHALL label the technical log as English in the interface:
- generated Python, R and Stata scripts (source code);
- the per-method technical summary log;
- bibliographic references;
- the names of columns from the researcher's own data.

#### Scenario: Technical summary
- **WHEN** a Causal Methods result is shown in French
- **THEN** the technical summary is inside an expander titled "Résumé technique (en anglais)"
