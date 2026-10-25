## Why

Closing the app lost every question, setting and dataset. README section 3 had listed "Project persistence / saved sessions" under "Not this term". On 2026-10-25 the user decided to build it anyway, together with the other excluded features, knowing that this departs from the scope decision and from the professor's advice to stay on one method (issue #1).

## What Changes

- New module `causal_lab/utils/project_file.py` with:
  - `save_project`, which returns the bytes of a `.causallab` zip: `manifest.json` plus Parquet datasets;
  - `load_project`, which validates the file and returns the session values;
  - `apply_project`, which replaces the project in the session and recomputes the diagnosis.
- Settings page: a "Save project" download button and an "Open a project" uploader. A dashboard shortcut leads there, and the page title becomes "Settings".
- New messages in English and French.
- No new dependency: Parquet uses pyarrow, which Streamlit requires.

## Capabilities

### New Capabilities
- `project-persistence`: saving a project to a local file and opening it again.

### Modified Capabilities
(none)

## Impact

- **Privacy:** the file only travels from the browser to the same computer, so "your data remain local" still holds. Nothing is pickled, so opening a file cannot run code.
- **Not saved in version 1:** the Theoretical Model page and estimation results (re-run with one click).
- **Tests:** new `tests/test_project_file.py`:
  - round trips (Virtual World, Card & Krueger, Causal Methods data);
  - every refusal reason;
  - forward compatibility;
  - opening a project in the running app.
