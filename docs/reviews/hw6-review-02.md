# HW6 review 2 — Invented functionality, names and assumptions

- **Date:** 2026-10-16
- **Branch:** `hw6-review`, after review 1 (`a999d2f`)
- **Criteria** (slide points copied by the user): functions, parameters and features nobody asked for; arbitrary thresholds; unexplained fallbacks; accepted-but-ignored parameters; names that promise more than they deliver; agent-added features without documentation or tests.

## Scope and method

- **Static audit** of every `.py` file under `causal_lab/` except the tests, using an AST script kept outside the repository:
  - parameters never used in their function body;
  - functions referenced nowhere else;
  - dataclass fields never read.
- **Provenance of the numeric thresholds**: `git log -S` on each threshold, plus a search of the specs.
- **Repository-wide search** (`grep AppTest causal_lab/tests`) to see whether the app-level behaviours added in earlier sessions are tested.
- **Not covered:** the numeric constants inside the theoretical-model solver (documented in its archived design) and the heuristic weights of the method-recommendation engine (original MVP code, documented as a heuristic in its spec).

## Findings

| # | Finding | Type | Evidence | Action |
|---|---|---|---|---|
| 2.1 | `compare_with_estimate(predicted, estimate, ci_low, ci_high)` **ignored `estimate`**, and **silently swapped** a reversed interval, a fallback no spec mentions. An estimate typed outside its own CI, or a reversed CI, still produced a verdict. | Confirmed defect (ignored parameter + unrequested fallback) | AST audit: `predictions.py:74 compare_with_estimate(estimate)` unused; old lines 78–79 `if ci_low > ci_high: swap`; spec `theory-predictions` had no such rule | **Fixed.** Raises a translated `LocalizedError` (`err.pred_bad_ci`) unless lower ≤ estimate ≤ upper; the Theoretical Model page shows it as an error. Spec updated by archived change `2026-10-16-hw6-assumption-checks` |
| 2.2 | App-level behaviours added by the agent in earlier sessions had **no test in the repository**: dashboard shortcuts, page kept on language switch, upload loaded once (a later generation wins), no ground truth for uploaded data, config snapshot, Card & Krueger button. They were only checked by scripts in a temporary folder. | Confirmed gap (agent features without tests) | `grep -rl AppTest causal_lab/tests` → none | **Fixed.** New `tests/test_app_flows.py` (5 AppTest tests). Mutation check: removing the `file_id` guard of the upload makes `test_uploaded_data_has_no_ground_truth_and_a_later_generation_wins` fail (1 failed), and restoring it passes |
| 2.3 | Unused parameters in `_score_iv(design)`, `_score_rdd(diag)`, `_score_rct(diag)` and in the catalogue builders' `n`. | Intentional design | Every scorer and every builder is called through one shared signature (`_ALL_SCORERS`, `CatalogueEntry.builder`) | **No change** — documented here |
| 2.4 | `DiagnosisResult.as_table`, `MethodScore.as_dict` and `StressTestReport.summary_table` are referenced nowhere. | Dead code candidates | AST audit | **Deferred to review 6** (dead code) |
| 2.5 | Result fields never read by the app: `EventStudyResult.reference_period`, `StaggeredDiDResult.group_time`, `MonteCarloSummary.n_reps/mae/mean_estimate`. | Public result data, not behaviour | Read by no caller, but part of the returned results | **No change** — they are outputs, not ignored inputs |
| 2.6 | Store-id adjacency (distance 1) as "neighbourhood" is assumed by three modules: the DGP, the Spillovers check and the robustness battery. It is only meaningful in the Virtual World. | Documented assumption with limited validity | `dgp.py`, `stress_test.py` `_check_spillovers`, `robustness.py` | **Documented** (README §5 known limitations, review 1); consolidation is looked at in review 4 |
| 2.7 | Names: "Matching / Propensity Score" now denotes covariate (Mahalanobis) matching plus propensity-score IPW; "Identification Strength" sounds like proof, but it counts diagnostic passes. | Naming risk | README §3, spec `break-my-design-stress-test` (heuristic disclaimer present in the app and spec) | **No change.** The method name is the family name used by the recommendation engine. The score's meaning is the subject of review 3 |

### Provenance of numeric thresholds

| Threshold | Where | Introduced | Documented in |
|---|---|---|---|
| p < 0.10 for the stress-test checks | `stress_test.py:87` and others | original MVP `b435bae` | spec `break-my-design-stress-test` |
| corrected ρ > 0.2 (Serial Correlation) | `stress_test.py:116` | agent, `7d3a5a0` | spec (no literature source; agent-chosen) |
| `INTENSITY_TO_VALUE` | `dgp.py:29` | original MVP | spec `virtual-world-generation` |
| leave-one-out cap of 10 treated units | `robustness.py:58` | original MVP | spec `robustness-battery` |
| event-study window ±6 | `event_study.py:38` | original MVP | spec `event-study-estimation` |
| `_LEVEL_TO_RISK` weights | `recommendation.py:29` | original MVP | spec `method-recommendation` (heuristic) |
| weak-instrument F = 10 | `iv.py:24` | agent, `9895bd7` | spec; Staiger & Stock (1997) rule of thumb |
| `MIN_OBS_PER_SIDE` = 10 (RDD) | `rdd.py:29` | agent, `9895bd7` | spec (agent-chosen) |
| \|SMD\| > 0.1 imbalance | `rct.py:26` | agent, `9895bd7` | spec; common rule of thumb |
| bootstrap 199 / 200 replications | `staggered_did.py:34`, `matching.py:42` | agent | archived designs |

All thresholds are documented in a spec or design. Two are agent-chosen without a literature source (ρ > 0.2 and `MIN_OBS_PER_SIDE`); they are left unchanged, but their provenance is recorded here.

## Tests executed

- `pytest test_app_flows.py test_theory_predictions.py test_i18n_coverage.py`: **14 passed**.
- Mutation check described in 2.2: **1 failed** with the guard removed, then **passed** once `app.py` was restored with `git checkout -- causal_lab/app.py`; the file had no other change.
- `pytest` (whole repository): **99 passed** (111.7 s).
- `openspec validate --specs`: **27 passed**.

## Remaining risks

- The AST audit is a heuristic: dynamic uses, such as `getattr` or format strings, can hide references, so the review 6 candidates still need a manual check.
