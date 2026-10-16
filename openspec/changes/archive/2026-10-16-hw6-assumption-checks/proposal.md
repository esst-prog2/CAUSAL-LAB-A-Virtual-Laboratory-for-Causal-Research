## Why

The hw6 review 2 (invented functionality and assumptions) found that `compare_with_estimate` accepted an `estimate` argument and never used it. It also silently swapped a reversed interval, a fallback no spec asked for. As a result, an inconsistent estimate entered by hand still produced a verdict.

## What Changes

- An estimate outside its own interval, including a reversed interval, is refused with a translated error; the bounds are no longer swapped.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `theory-predictions`: the comparison validates the estimate against its interval.

## Impact

`causal_lab/theory_engine/predictions.py`, `causal_lab/ui/theory_page.py`, locales (key `err.pred_bad_ci`), `causal_lab/tests/test_theory_predictions.py`.
