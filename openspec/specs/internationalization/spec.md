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
The system SHALL let the researcher switch the active language from the sidebar at any time, immediately re-rendering all page text.

#### Scenario: Switching language
- **WHEN** the researcher changes the EN/FR radio control in the sidebar
- **THEN** `st.session_state.lang` updates to the new value and the app reruns, so every page's text is redrawn through `t(key, new_lang)`

### Requirement: Two supported languages today
The system SHALL support exactly English and French; no other language dictionary is loaded.

#### Scenario: Supported language set
- **WHEN** the app starts
- **THEN** `SUPPORTED_LANGUAGES` is `("en", "fr")` and `DEFAULT_LANGUAGE` is `"en"`
