## Context

`utils/i18n.t(key, lang)` existed, but only titles and navigation used it. Engine modules returned English f-strings, which the pages displayed as they were. See proposal.md.

## Goals / Non-Goals

**Goals:** a French interface with no English left outside the deliberate exceptions, proved by an automated coverage test and a scripted French render audit.

**Non-Goals:** a third language; translating generated source code or user data; changing any calculation.

## Decisions

- **`Msg` subclasses `str`.** The alternative, a separate message object, would have forced every engine consumer and test to change, along with every string operation and JSON export.
  - The value of a `Msg` is the English text, rendered from `en.json`, so there is a single source of truth for English.
  - `render(lang)` re-renders it in another language.
  - A parameter that is itself a `Msg` is rendered in the same language. This is how, for example, an assignment-mechanism option appears inside a rationale.
  - `__reduce__` keeps the key and parameters through pickling, which `st.cache_data` needs.
- **`LocalizedError(ValueError)`.** Existing `except ValueError` handlers and tests keep working. `CalibrationError` now subclasses it.
- **Identifiers stay stable.** Method names, check names and outcome dict keys keep their English values as identifiers: tests and logic compare them. Only their display goes through keys such as `method.<key>`, `check.<slug>` and the outcome `Msg`.
- **The page language is frozen at render time.** Each page module stores the language when it starts rendering, so the `format_func` closures do not read `session_state` lazily. Streamlit's AppTest evaluates those closures outside a script run, where session state is unavailable. The scripted audit surfaced this.
- **Name clash fixed.** Each page's entry point is `render(L)`, so the i18n helper is imported as `render_message`. Before this, the import was shadowed, and the audit caught it as a crash.

## Risks / Trade-offs

- [Locale files are long (663 keys)] → Keys are namespaced by area (`stress.*`, `rec.*`, `methods.*`, `theory.*`…), and the coverage test catches missing or extra keys.
- [JSON reformatting dropped the blank-line grouping of the original files] → Namespacing replaces the visual grouping.
