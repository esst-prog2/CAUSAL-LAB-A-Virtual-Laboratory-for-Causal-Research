# internationalization Specification

## Purpose
Every UI string is looked up through a single `t(key, lang)` function backed by JSON translation dictionaries, so no page hard-codes text and the app can be switched between English and French at runtime.

## Requirements

### Requirement: Key lookup with language and English fallback
The system SHALL resolve a translation key against the requested language, falling back to English, then to the raw key, rather than raising or showing a blank string.

#### Scenario: Unsupported language code
- **WHEN** `t(key, lang)` is called with `lang` not in {"en", "fr"}
- **THEN** it looks up the key in the English dictionary instead

#### Scenario: Key missing from the requested language
- **WHEN** the key is not present in the requested (supported) language's dictionary
- **THEN** it falls back to the English dictionary's value for that key

#### Scenario: Key missing everywhere
- **WHEN** the key is present in neither the requested language nor English
- **THEN** `t` returns the raw key string itself, so a missing translation is visible in the UI instead of crashing the app

### Requirement: Runtime language toggle
The system SHALL let the researcher switch the active language from the sidebar at any time, immediately re-rendering all page text. All page text means every label, button, caption, message box, chart title and axis, table header and option list, and every message produced by the engines.

#### Scenario: Switching language
- **WHEN** the researcher changes the EN/FR radio control in the sidebar
- **THEN** `st.session_state.lang` updates to the new value and the app reruns, so every page's text is redrawn through `t(key, new_lang)`

#### Scenario: French audit of every page
- **WHEN** the interface is in French, with a Virtual World generated, a diagnosis run, each Causal Methods estimator run on its virtual world, and each catalogue model solved (plus one calibrated model with a prediction)
- **THEN** no displayed text outside code blocks is a raw locale key, and none contains an English interface sentence from `en.json` that has a different French translation

### Requirement: Two supported languages today
The system SHALL support exactly English and French; no other language dictionary is loaded.

#### Scenario: Supported language set
- **WHEN** the app starts
- **THEN** `SUPPORTED_LANGUAGES` is `("en", "fr")` and `DEFAULT_LANGUAGE` is `"en"`

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
The system SHALL leave untranslated only text that is not interface text:
- bibliographic references (author names, years);
- the names of columns, units and values from the researcher's own data;
- programming-language keywords and function names in generated scripts.

Everything else SHALL follow the interface language, including the comments and printed labels of generated scripts and the per-method technical summary.

#### Scenario: Technical summary
- **WHEN** a Causal Methods result is shown in French
- **THEN** the technical summary is inside an expander titled "Résumé technique", and its lines (headline, inference, method-specific details) are in French

#### Scenario: French audit including code blocks
- **WHEN** the French render audit also inspects code blocks (generated scripts and technical summaries)
- **THEN** it finds no English interface sentence
