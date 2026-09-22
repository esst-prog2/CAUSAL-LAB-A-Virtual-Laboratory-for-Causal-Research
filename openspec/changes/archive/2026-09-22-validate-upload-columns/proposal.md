## Why

Uploading a CSV missing a required column (e.g. no `D`) currently succeeds silently; the failure only surfaces later as a raw `KeyError`/formula error on whichever analysis page touches that column first. The project's own README already promises the opposite as a v1 acceptance criterion: "Given a panel CSV missing the treatment indicator column, the app reports an error naming that column instead of running." This closes that gap.

## What Changes

- Validate an uploaded CSV against the five fixed, required column names — `unit`, `period`, `Y`, `D`, `treated_unit` — immediately at upload time, before it becomes the active dataset.
- If any are missing, show an error naming the missing column(s) and leave the previously active dataset (if any) untouched instead of switching to the invalid upload.
- No column-mapping UI is introduced; column names stay fixed, matching every other part of the app (estimators, stress test, robustness battery all assume these exact names already).

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `real-world-data-upload`: the "Required columns are not validated at upload time" requirement is replaced by upload-time validation that names missing columns and blocks the switch to the invalid dataset.

## Impact

- `causal_lab/app.py` — the CSV upload handler on the Virtual Lab page (currently just `pd.read_csv` + a try/except around parse errors).
- No changes to `estimators/`, `robustness_engine/`, or `simulation_engine/` — they already assume the five fixed column names.
