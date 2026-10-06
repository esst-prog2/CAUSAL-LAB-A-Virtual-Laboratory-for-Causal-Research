## Context

The engines (`dgp.py`, `stress_test.py`, `monte_carlo.py`, `event_study.py`, `robustness.py`, `generator.py`, `diagnosis.py`) have been unchanged since the original MVP. A review of that MVP, done in an earlier snapshot of the code on 2026-10-06, had already produced fixes for every defect listed in proposal.md. They are ported here, then extended where the README demands more: two DGP levers, the plain-language verdict, the trend plot, and the reference-package check. See proposal.md for motivation and specs/ for the behavior contract.

## Goals / Non-Goals

**Goals:**
- Every README section 4 criterion is backed by an automated test, except the French-interface criterion, which belongs to the follow-up change `complete-french-translation`.
- The calibration spike is re-run on the fixed code, and its numbers go into the README.

**Non-Goals:**
- Heterogeneity-robust staggered DiD estimators (Callaway & Sant'Anna). These remain backlog. The app now warns when timing is staggered.
- Changing the 0.10 significance level of the checks, or the 0–100 score formula.

## Decisions

- **Spillover test: DiD of adjacent vs other controls**, not adjacency counting. Counting fires on almost every random assignment (100% false alarms in the spike). The DiD measures the thing spillovers do: adjacent controls move after treatment. It is still keyed on id adjacency, since that is the Virtual World's neighbourhood, and it says so when ids are not numeric.
- **Serial correlation: within-unit Durbin-Watson with Nickell correction.** Fixed-effects residuals have an autocorrelation of about −1/(T−1) even under i.i.d. errors. Adding it back before applying the 0.2 threshold avoids false PASSes on short panels. Rejected alternative: Wooldridge's test, which needs a second regression and gives the same answer here.
- **Heterogeneity: variance-ratio F test of pre/post changes, treated vs control.** Under a homogeneous effect, both groups' changes have the same noise variance. A larger variance for treated units is exactly what effect heterogeneity adds. The old CV of outcome levels measured unit fixed effects, not effects.
- **Anticipation: first-difference test.** The old pooled two-period regression kept the unit fixed effects in the error, so its power was low. Differencing them out is the standard fix.
- **Parallel trends: explicit lead dummies omitting the last pre-period.** `treated * C(period)` plus unit FE is rank-deficient. The verdict thresholds 0.10 and 0.01 follow the README's three-level wording.
- **New DGP levers sized in noise-SD units.** A slope of 0.08·v per period for `differential_trend`, and a shift of 0.5·v one period early for `anticipation`, where v is the intensity value (severe = 2.0). This gives detection above 80% at "severe" with the default 100×20 panel. The spike measures it.
- **App state.**
  - Pages are identified by ids, with labels via `format_func`.
  - Shortcuts use `on_click` callbacks, because session state cannot be written after the radio widget has been created.
  - The upload is keyed by `file_id`.
  - A configuration snapshot is taken with `dataclasses.replace` at generation time.
  - Estimators are cached with `st.cache_data`, keyed on the DataFrame.
- **`width="stretch"`** replaces `use_container_width`, which will be removed in Streamlit releases after 2025-12-31. This requires `streamlit>=1.50`.
- **Reference check against `linearmodels.PanelOLS`**, already a dependency. The coefficients are identical. The clustered SEs differ only by a small-sample factor, so the tolerance is 2%.
- **DML reproducibility.** Found while running the tests: random-forest prediction with `n_jobs=-1` sums the trees in thread order, which changes the last bits of the result. Prediction now runs on one core. Fitting stays parallel.

## Risks / Trade-offs

- [Re-calibrated checks may still false-alarm at about the 10% test size on clean data] → This is inherent to a 0.10 level. The spec bound is ≤ 20%, and the README states the measured rates.
- [The spillover test needs enough adjacent and non-adjacent controls] → With fewer than 2 of either, it defaults to PASS with an explicit message.
- [The original spike result file is a historical record] → The after-fix numbers go to a separate `stress_test_calibration_results_after_fix.md`. The spike script now takes the output name as an argument.
