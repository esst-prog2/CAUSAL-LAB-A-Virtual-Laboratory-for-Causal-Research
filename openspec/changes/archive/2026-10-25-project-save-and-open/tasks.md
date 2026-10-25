## 1. Implementation

- [x] 1.1 Write `utils/project_file.py`:
  - zip archive with a manifest and Parquet datasets;
  - JSON encoding of Msg and of unit-keyed dicts;
  - validation;
  - `apply_project`.
- [x] 1.2 Add the save and open controls to the Settings page (the open action runs as an uploader callback, before the sidebar widgets are drawn), plus the dashboard shortcut.
- [x] 1.3 Add the EN and FR messages.

## 2. Tests and specification

- [x] 2.1 Write `tests/test_project_file.py`: round trips, refusals, forward compatibility, file name, `apply_project`, and an opened project rendering in the app.
- [x] 2.2 Add the `project-persistence` spec. Verify with `openspec validate project-save-and-open --strict`.
