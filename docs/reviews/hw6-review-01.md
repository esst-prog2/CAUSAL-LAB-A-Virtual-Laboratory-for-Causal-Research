# HW6 review 1 — Specification versus implementation

- **Date:** 2026-10-16
- **Branch:** `hw6-review`, starting from `5eb32b6`
- **Review criteria:** the Session 6 slides were not available to the agent. The criteria used are the slide points the user copied into the assignment: spec drift, unrequested features, and tests whose expected values were copied from the program.

## Scope and files examined

- **Specs:** all 27 capability specs under `openspec/specs/`, read in full for `break-my-design-stress-test`, `did-estimation`, `real-world-data-upload`, `staggered-did-estimation` and `virtual-world-generation`. The others were checked by their requirement titles against the code and tests. `openspec/changes/` held only archived changes.
- **Documentation:** `README.md` (sections 1–5) and the hw4/hw5 entries of `PLANNING_LOG.md`.
- **Code:** `causal_lab/robustness_engine/stress_test.py` (the five checks and the score), `causal_lab/estimators/did.py`, `causal_lab/utils/real_data.py` and `causal_lab/app.py` (Virtual Lab, Estimation, Break My Design).
- **Data:** the Card & Krueger data, inspected with `read_card_krueger_raw()` and `load_card_krueger()`.
- **Not reviewed line by line:** the theoretical-model specs and code, the six Causal Methods estimators, and the i18n layer. They were only checked through their existing tests.

## Findings

| # | Finding | Type | Evidence | Action |
|---|---|---|---|---|
| 1.1 | The spec requirement "Checks are calibrated on the Virtual World" (clean-world false alarm ≤ 20% per check, mean score ≥ 85) had **no automated test**. It was only checked by running the spike by hand. | Confirmed gap (spec not enforced) | `spec.md` lines 73–87; `git grep identification_strength causal_lab/tests` found no mean-score assertion | **Fixed.** New test `tests/test_stress_calibration.py` (200 seeded clean worlds) |
| 1.2 | README §1, "The demo", describes a "pre-trend slope difference" message and a "Break this design" re-run on zero-effect data. Neither exists: Break My Design runs five diagnostics. | Documentation drift (an original plan, not a defect in the code) | README l.7 vs `stress_test.py` `run_stress_test` | **Documented.** A dated note under §1 lists the differences; the original text is kept |
| 1.3 | README §2 announces a 4-column CSV; the app requires 5 columns (`unit, period, Y, D, treated_unit`). | Documentation drift | README l.14 vs `utils/validation.py` `REQUIRED_COLUMNS` | **Fixed** in README §2 |
| 1.4 | README §4 says "663 keys"; the locales have 704. | Stale number | `len(en.json) == 704` | **Fixed** |
| 1.5 | README §5 "Real data availability" still said no real dataset exists; Card & Krueger has shipped since hw5. | Obsolete documentation | `causal_lab/data/card_krueger_1994/`, `tests/test_card_krueger.py` | **Fixed.** The original sentence is kept as "original plan", with a dated update |
| 1.6 | The limitations found in hw5 real use (PLANNING_LOG 2026-10-09 (a)–(d)) were absent from user-facing documentation. | Missing documentation | PLANNING_LOG lines 7–11 | **Documented** in README §5 "Known limitations"; the root causes are left to review 3 |
| 1.7 | The README claims the DiD clustered SE is "within 2% of PanelOLS". This is true (Card & Krueger: 1.9059 vs 1.9048), but both apply a small-sample correction that counts the absorbed unit fixed effects. On Card & Krueger the independent textbook formula gives **1.3579**, matching the paper's 1.36, against our 1.9059: a factor √((N−1)/(N−K)·G/(G−1)) ≈ 1.44 with N = 794, G = 409. The reference test shares the convention, so it cannot detect this. | Confirmed inconsistency between the README/spec validation claim and an independent reference | Hand formula: SE = √(var ΔY_NJ / n_NJ + var ΔY_PA / n_PA), on 309 NJ + 74 PA stores | **Documented** in README §5; fix deferred to review 3 (it changes a statistical definition and needs the user's decision) |
| 1.8 | In the Card & Krueger file, `SHEET` 407 is used by **two different stores**: chain 2 in PA and chain 4 in NJ. The codebook calls SHEET a "unique store id", and the loader merges the two into one unit with 4 rows, both treated and control. | Confirmed data-ingestion defect | `read_card_krueger_raw()`: 410 rows, 409 unique SHEET; `load_card_krueger()` unit 407 has 4 rows | **Documented**; fix in review 3 (root cause: no (unit, period) uniqueness rule) |
| 1.9 | The hw5 Card & Krueger button (Virtual Lab) was not described in any spec. | Feature without a spec | `openspec/specs/real-world-data-upload` had no such requirement | **Fixed** with archived OpenSpec change `2026-10-16-hw6-spec-alignment` (requirement "Bundled real dataset") |
| 1.10 | "Cannot be computed" is handled inconsistently across checks: Parallel Trends and Anticipation return WARNING, Heterogeneity and Spillovers return PASS, and Serial Correlation has no guard. Every WARNING lowers the score, so a lack of evidence reads as evidence of failure. | Confirmed design inconsistency, but **it follows the spec** (PT "not enough data → WARNING"; score = 100·PASS/5) | `stress_test.py` l.68, 128/136, 160, 195; spec l.22–24, 69–71 | **Not changed here.** It needs a methodological decision; raised in review 3 |

## Tests executed

- `pytest causal_lab/tests/test_stress_calibration.py`: **1 passed** (61.8 s). Measured clean-world false-alarm rates: Parallel Trends 0.14, Anticipation 0.075, Spillovers 0.075, Serial Correlation 0.0, Heterogeneous Effects 0.10; mean score 92.2.
- `pytest` (whole repository): **93 passed** (110 s).
- `openspec validate hw6-spec-alignment --strict`: valid. `openspec validate --specs`: **27 passed**.

## Remaining risks / open questions

- The spec bounds enforced by the new test (≤ 20%, ≥ 85) were written by the agent on 2026-10-06, not by the user. They are spec requirements, not program output, but their provenance is recorded here.
- The detection half of the calibration requirement (≥ 80% per threat) is still only checked by the spike script, because it needs 1000 more simulated worlds.
- Findings 1.7, 1.8 and 1.10 are carried over to review 3.
