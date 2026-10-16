# HW6 review 3 — Root causes of recurring defects

- **Date:** 2026-10-16
- **Branch:** `hw6-review`, after review 2 (`a2da5e6`)
- **Criteria** (slide points copied by the user): look for the cause behind repeated symptoms, not the symptom; fix it once at the source; do not patch each case.

## Scope and method

- **Where the symptoms came from:**
  - the defects found by using the app on Card & Krueger (hw5 real use, PLANNING_LOG 2026-10-09);
  - the defects deferred by review 1 (findings 1.x in `hw6-review-01.md`).
- **How each symptom was traced:**
  - read the code path that produced it (stress test, DiD, Callaway & Sant'Anna, Card & Krueger loader);
  - measured the effect on Card & Krueger before and after the fix.
- **Decisions:** four fixes required a methodological choice. They were put to the user, who chose; each choice is logged in PLANNING_LOG.md (2026-10-16, "decided by: user"). The SHEET 407 fix is a data error and needed no choice.
- **Files examined:**
  - `robustness_engine/stress_test.py`
  - `estimators/did.py`
  - `estimators/staggered_did.py`
  - `utils/real_data.py`
  - `app.py` (Break My Design, Estimation)
  - `tests/test_did_reference.py`, `tests/test_card_krueger.py`, `tests/test_staggered_did.py`
  - the four affected specs
  - the linearmodels 7.0 source (`panel/covariance.py`, `panel/model.py`)

## Findings

| # | Root cause | Symptoms it produced | Severity | Evidence | Action |
|---|---|---|---|---|---|
| 3.1 | **"Cannot be computed" had no verdict of its own.** Each check chose WARNING or a "default pass" when it lacked data. | Card & Krueger scored 40/100, mostly for having two periods: Parallel Trends and Anticipation returned WARNING ("not enough data"), and Serial Correlation always returned WARNING with T = 2 (the within residuals are exactly opposite, so the corrected ρ is 1). Conversely, Spillovers and Heterogeneity "passed by default" with too few units. | High (the score misled on any short panel) | Old code on Card & Krueger: PT WARNING, Anticipation WARNING, Spillovers PASS, Serial WARNING, Heterogeneity PASS → 40.0 | **Fixed.** New verdict N/A. Score = 100 × PASS / (computable checks), None if no check is computable. The page states "based on k of the 5 checks". User decision |
| 3.2 | **Neighbourhood assumed from consecutive ids on any data.** | Spillovers check on Card & Krueger compared stores whose sheet numbers happen to be consecutive. | Medium | `_check_spillovers` used `unit ± 1` with no condition | **Fixed.** `run_stress_test(..., *, ids_encode_neighbourhood)` is keyword-only with no default, so every caller must state it. The app passes True only for a generated Virtual World. User decision |
| 3.3 | **Unit dummies counted in the cluster small-sample correction.** | SE 1.91 on Card & Krueger (CI includes 0, p = 0.15) against 1.36 published. Any short panel is affected, because N/K ≈ 2 when T = 2. The PanelOLS check could not detect it: linearmodels' `auto_df=True` (default) silently overrides `count_effects`. | High (wrong inference on real data) | Hand CR1 on Virtual World seed 4: 0.091786 with every dummy counted, 0.089461 without the unit dummies. Linearmodels source: `extra_df = neffects if count_effects`, `count_effects` reset by `_determine_df_adjustment` when `auto_df` | **Fixed.** CR1 with K excluding the unit dummies when units are nested in the clusters (Stata xtreg, fe / reghdfe convention). Normal-based t, p and CI recomputed. Card & Krueger SE: **1.3376**. User decision |
| 3.4 | **Loader assumed `SHEET` is a unique store key.** | Two stores (sheet 407: a chain-2 store in PA and a chain-4 store in NJ) merged into one unit, with four rows and a treatment status that changes within the unit. | Medium (data error) | `raw[raw.SHEET == 407]` → rows 41 (STATE 0) and 167 (STATE 1) | **Fixed.** unit = row in the file (1–410); `sheet` kept as a column. DiD on Card & Krueger: 2.7644 → **2.7500** (published 2.76, tolerance ±0.1, unchanged) |
| 3.5 | **Robust DiD required a balanced panel instead of balancing it.** | The Callaway & Sant'Anna tab showed only an error on Card & Krueger. | Medium | `_wide` raised `err.cs_unbalanced` on any NaN | **Fixed.** Units missing a period are left out and counted (`n_dropped`), as R `did` does with `allow_unbalanced_panel = FALSE`. Card & Krueger: 26 stores dropped (counted independently: 26 units with fewer than two waves); CS ATT 2.7500 on 384 stores, equal to the 2×2 DiD computed by hand on the same stores. User decision |

## Actions

- **Code:**
  - `stress_test.py`: N/A verdict, score formula, explicit neighbourhood flag, T < 3 guard;
  - `did.py`: `_nested_fe_factor`;
  - `staggered_did.py`: drops and counts incomplete units;
  - `real_data.py`: unique unit ids;
  - `app.py`: N/A display, score basis, "no score" message, dropped-units caption;
  - locales: 9 new or changed keys in EN and FR (711 keys each).
- **Callers updated:** app, `test_i18n_coverage.py`, `test_stress_and_engine_fixes.py`, `test_stress_calibration.py`, `spike/stress_test_calibration.py`.
- **Specs:** OpenSpec change `2026-10-16-hw6-root-causes` (validated `--strict`, archived). It modifies 10 requirements in `break-my-design-stress-test`, `did-estimation`, `staggered-did-estimation` and `real-world-data-upload`.
- **README:** "Known limitations" now marks these five as fixed and adds the one still open (below).

## Tests

- **New:**
  - `test_stress_not_applicable.py` (3 tests);
  - `test_clustered_se_does_not_count_the_nested_unit_dummies` (exact, against a CR1 sandwich written out by hand);
  - `test_clustered_se_matches_the_published_standard_error`. Expected value 1.36 from the paper, logged by the user on 2026-10-09; tolerance ±0.1, the project's established Card & Krueger tolerance;
  - `test_every_store_is_its_own_unit` (410 stores, from the same log entry);
  - `test_units_missing_a_period_are_dropped_and_counted`. Expected value: the estimate on the panel balanced beforehand, not a number taken from the program.
- **Changed, not weakened:** `test_did_matches_panelols_point_estimate_and_clustered_se` keeps its 2% tolerance. The PanelOLS reference is now configured with the same convention (`group_debias=True, debiased=True, auto_df=False, count_effects=False`); measured gaps are 0.50%, 0.50% and 0.85%, all from the period dummies, which PanelOLS does not count. The hw5 test (2.76 ± 0.1) is unchanged.
- **Mutation checks:**
  - restoring the old SE (factor forced to 1) makes the exact CR1 test fail and the Card & Krueger SE test fail (SE 1.9247);
  - the old stress-test module, run on Card & Krueger, gives the 40/100 report above, which `test_two_period_real_data_reports_na_instead_of_warnings` rejects.
- **Results:**
  - `pytest` (whole repository): **106 passed** (114.3 s);
  - `openspec validate --specs`: **27 passed**;
  - headless AppTest run of Break My Design and Estimation on Card & Krueger, in EN and FR: no exception. It showed 4 N/A checks, "100 / 100" with the 1-of-5 caption, and "26 unit(s) … left out".
- **Calibration:** the clean-world calibration test still passes. On Virtual Worlds all five checks are computable, so the score there is unchanged.

## Remaining risks

- On Card & Krueger the score is 100/100 on **1 of 5** checks (Heterogeneous Effects). The caption says so, but the number can still be over-read. Showing no score below a minimum number of computable checks would be a new methodological rule, so it was not invented here.
- The robustness battery (`robustness.py`) still has an "exclude neighbours" row based on id adjacency. It is outside this review's decision, which concerned the Spillovers check; it is looked at in review 4 (duplication of the adjacency assumption).
- The 1.36 published SE was quoted from the article by Claude and is "to be checked against the printed table" (PLANNING_LOG 2026-10-09). The test's ±0.1 tolerance does not depend on that check.
