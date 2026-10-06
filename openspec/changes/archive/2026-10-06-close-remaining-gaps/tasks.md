## 1. Staggered adoption

- [x] 1.1 Add the `dynamic_effects` lever to the Virtual World and redefine `true_att` as the mean effect over treated unit-periods. Verify in `tests/test_staggered_did.py` that `true_att` equals the mean of Y1 − Y0 over D = 1.
- [x] 1.2 Add `estimators/staggered_did.py` (Callaway & Sant'Anna). Verify by Monte Carlo (60 worlds: TWFE bias +0.21 with 38% coverage, CS +0.006 with 93%) and by the tests: no detectable CS bias, TWFE clearly biased, the not-yet-treated fallback, and a single-cohort agreement.
- [x] 1.3 Add the Estimation-page "Robust DiD" tab and the dynamic-effects slider. Verify with the end-to-end run that CS is closer to the truth than TWFE on a staggered world.

## 2. Matching

- [x] 2.1 Switch to covariate (Mahalanobis) matching with regression bias correction. Verify the 200-world experiment (97% coverage, SE/SD 1.09) and `test_matching_standard_error_is_calibrated` (60 worlds).

## 3. Remaining English

- [x] 3.1 Make the technical summaries translatable lines, and make the generated scripts' comments and labels follow the language. Verify with `test_generated_scripts_and_summaries_follow_language`, and with the French audit including code blocks (0 problems).

## 4. Close the loop

- [x] 4.1 Run all tests and the end-to-end script, update the README and PLANNING_LOG, and verify `openspec validate close-remaining-gaps --strict`.
