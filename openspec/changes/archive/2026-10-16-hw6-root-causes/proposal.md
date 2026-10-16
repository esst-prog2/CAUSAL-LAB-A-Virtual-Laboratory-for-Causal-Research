## Why

HW6 review 3 traced recurring wrong results on real data to four root causes, each fixed at the source rather than per symptom:

1. A check that cannot be computed returned WARNING (or a "default" PASS), so the Identification Strength score measured the shape of the data, not the design. Card & Krueger (two periods) scored 40/100 mainly because Parallel Trends, Anticipation and Serial Correlation cannot be computed with two periods.
2. The Spillovers check treated consecutive unit ids as neighbours on any dataset, though only the Virtual World encodes a neighbourhood that way.
3. The DiD clustered SE counted the unit dummies, which are nested in the clusters, in its small-sample correction: 1.91 instead of about 1.36 on Card & Krueger.
4. Card & Krueger's `SHEET` is not a unique store id (sheet 407 is two stores), and the robust DiD refused any unbalanced panel.

The decisions on (1), (2), (3) and the robust-DiD sample were taken by the user (PLANNING_LOG.md, 2026-10-16).

## What Changes

- New verdict N/A for checks that cannot be computed; the score counts only computable checks and is absent when none is.
- `run_stress_test` takes an explicit, keyword-only `ids_encode_neighbourhood`; the app passes True only for a generated Virtual World.
- Serial Correlation needs at least three periods.
- DiD clustered SE: CR1 without the nested unit dummies (Stata xtreg/reghdfe convention).
- Card & Krueger unit = store row; `SHEET` kept as `sheet`.
- Robust DiD drops units missing a period and reports how many.

## Impact

- Code: `robustness_engine/stress_test.py`, `estimators/did.py`, `estimators/staggered_did.py`, `utils/real_data.py`, `app.py`, locales.
- Tests: new `test_stress_not_applicable.py`; new tests in `test_did_reference.py`, `test_card_krueger.py`, `test_staggered_did.py`.
