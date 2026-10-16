## Why

The hw6 review 1 (specification versus implementation) found a feature that no spec describes: the Card & Krueger (1994) loader and button added in hw5. Its behaviour, which dataset is loaded, how it replaces the active data and what the test guarantees, was only recorded in the planning log.

## What Changes

- Add a "Bundled real dataset" requirement to `real-world-data-upload`, describing the behaviour that already exists. No code change.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `real-world-data-upload`: adds the bundled-real-dataset requirement.

## Impact

Specification only. The behaviour already exists in `causal_lab/app.py` (Virtual Lab page) and `causal_lab/utils/real_data.py`, and is tested by `causal_lab/tests/test_card_krueger.py`.
