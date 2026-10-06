## Why

After `complete-french-translation`, three known limits remained, and the user asked on 2026-10-06 to fix them all:

1. **Staggered adoption had no correct estimator.** Two-way fixed effects are biased when units adopt at different dates and effects change over time. The app only warned about it.
2. **Matching standard errors were conservative.** They were about 30% too large (100% coverage of a nominal 95% CI), because the matching used an *estimated* propensity score.
3. **Two English blocks remained in the French interface:** the generated scripts' comments and labels, and the per-method technical summary.

## What Changes

- New Callaway & Sant'Anna (2021) heterogeneity-robust DiD:
  - group-time ATTs against never-treated units, or not-yet-treated units when every unit is eventually treated;
  - aggregated into an overall ATT and an event study;
  - unit-level bootstrap SEs.
  
  It appears as a third tab on the Estimation page, next to TWFE and the true effect.
- Virtual World gets a new threat lever, `dynamic_effects`, where effects grow with time since adoption. With staggered adoption it reproduces the Goodman-Bacon bias of TWFE. The true ATT is now defined as the mean effect over treated unit-periods; it is unchanged without staggering or dynamics.
- Matching now matches on the covariates (Mahalanobis distance), with regression bias correction (Abadie & Imbens 2011). This is the setting the Abadie-Imbens variance is derived for. The propensity score is kept for the overlap diagnostic and IPW.
- Generated scripts carry comments and printed labels in the interface language; the code itself is unchanged. Technical summaries are translatable lines.

## Capabilities

### New Capabilities
- `staggered-did-estimation`: Callaway & Sant'Anna estimator and its Estimation-page tab.

### Modified Capabilities
- `matching-estimation`: nearest-neighbour matching on covariates with bias correction.
- `virtual-world-generation`: true ATT definition, plus the dynamic-effects lever.
- `internationalization`: only references and user data remain untranslated.
- `code-generation`: comments and labels follow the language.

## Impact

- New: `estimators/staggered_did.py`, `tests/test_staggered_did.py`.
- Changed: `estimators/{matching,common,rct,iv,rdd,synthetic_control,dml}.py` (summary lines), `simulation_engine/dgp.py`, `code_generator/generator.py`, `app.py`, `ui/methods_page.py`, the locales (702 keys), and tests (`test_matching`, `test_i18n_coverage`).
- README sections 3–5.
