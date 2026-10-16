# Causal Lab

A small tool that lets someone with a panel dataset and a treatment date find out — with real numbers, not a guess — whether a difference-in-differences design is even appropriate for their data, and if so, run it correctly.

## 1. The demo

I open the app in the browser and upload a CSV: one row per unit per time period, a treatment date, and an outcome column. It shows a plot of average outcomes for treated and untreated units over time, with the treatment date marked. Below it, a diagnosis panel says "Parallel trends: questionable — pre-trend slope difference is 0.34, p = 0.02" and "Recommended: difference-in-differences, but check anticipation effects first." I click "Run DiD" and it shows a coefficient, a standard error, and a two-way fixed-effects regression table. I click "Break this design" and it re-runs the same estimator on a version of the data where I know the true effect is zero, so I can see whether the method still finds a false effect.

If I don't have real data, I click "Generate a synthetic world" first: it creates a panel with a known, chosen treatment effect, so I can check that the estimator recovers close to that number before trusting it on anything real.

> **Note (hw6 review 1, 2026-10-16).** This demo is the original plan, and two parts of it differ from what is delivered (section 3):
> - The diagnosis reports a joint test of the pre-treatment leads, with its p-value and a plausible / questionable / violated verdict. It does not report a "pre-trend slope difference".
> - "Break My Design" runs the five diagnostic checks of section 3. It does not re-run the estimator on a placebo version of the data where the true effect is zero.

## 2. The shape

```
in            a panel CSV with five columns (unit, period, outcome Y,
              treatment indicator D, treated-group flag treated_unit) —
              real data or a synthetic dataset generated in-app with a
              known true effect
out           a diagnosis of whether parallel trends plausibly hold,
              a DiD coefficient with standard error, and a plot
on screen     upload or generate → see the pre/post trend plot and the
              diagnosis → run the estimator → see the result next to
              the true effect if the data was synthetic
```

## 3. The size

**Delivered:**
- Generate a synthetic panel dataset with a chosen, known treatment effect (the "virtual world"), with a Causal Threats Generator to add confounding, spillovers, serial correlation, staggered adoption, treatment-effect heterogeneity, diverging pre-trends, anticipation, and effects growing over time at a chosen intensity.
- Accept an uploaded CSV in the same panel shape, validated against the five required columns at upload time — a missing column is reported by name instead of failing later.
- Plot treated vs. untreated average outcomes over time, with the treatment date marked (Estimation page).
- Check pre-treatment trends and report a plain-language verdict ("plausible" / "questionable" / "violated") with the number behind it, as one of five checks in a "Break My Design" stress-test battery (parallel trends, anticipation, spillovers, serial correlation, heterogeneous effects) that also reports an overall Identification Strength score.
- Run a heterogeneity-robust DiD for staggered adoption (Callaway & Sant'Anna 2021), with an event study and bootstrap SEs, shown next to TWFE and the true effect. On staggered worlds with growing effects, TWFE has a bias of +0.21 and 38% CI coverage, while Callaway & Sant'Anna has a bias of +0.006 and 93% coverage (60 Monte Carlo worlds).
- Run a two-way fixed-effects DiD estimator and report the coefficient, standard error, and p-value. It is validated against `linearmodels.PanelOLS`: identical coefficient and clustered standard errors within 2% (`tests/test_did_reference.py`).
- Run an Event Study (leads-and-lags) estimator and plot dynamic, period-by-period treatment effects around the treatment date.
- Score seven candidate causal-identification methods (RCT, DiD, Event Study, Synthetic Control, RDD, IV, Matching) against the declared research design with a transparent, explainable Method Suitability Score, and recommend the best fit — the app shows its work rather than picking silently.
- Generate ready-to-run Python, R, and Stata scripts that reproduce the DiD analysis.
- Run in English or French, switchable from the sidebar at any time.
- When run on synthetic data, show the estimate next to the true effect that was used to generate it, including a Monte Carlo mode that reports bias, RMSE, and confidence-interval coverage across many replications.
- Run six more identification strategies as actual estimators on a "Causal Methods" page:
  - Randomized Controlled Trial: difference in means and covariate-adjusted ATE.
  - Matching: covariate (Mahalanobis) nearest-neighbour ATT with bias correction, plus IPW ATT.
  - Instrumental Variables: 2SLS with a first-stage F statistic.
  - Regression Discontinuity: sharp design, local linear with the Imbens–Kalyanaraman bandwidth.
  - Synthetic Control: placebo-in-space p-value.
  - Double Machine Learning: cross-fitted partially linear model.
  
  Each runs on its own virtual world, with a known true effect shown next to the estimate, or on an uploaded CSV whose columns you map to the method's roles.
- Build a theoretical model of interacting agents on a "Theoretical Model" page.
  - **Models.** Pick from a catalogue or write your own in a free editor (with safe parsing):
    - Public choice: median voter, probabilistic voting, Tullock rent-seeking, Niskanen bureaucracy, voluntary public-good provision.
    - Markets: Cournot, differentiated Bertrand.
  - **Equations and equilibrium.** The app shows each agent's utility, first-order condition and best response. It solves the pure-strategy Nash equilibrium (closed form, or numerically with a check that no agent gains from a unilateral deviation).
  - **Calibration.** Parameters are set from the data, as column statistics, filtered subgroups or regression coefficients. One equilibrium is solved per group or per period, depending on the detected data structure.
  - **Prediction.** A treatment is modelled as a parameter shift, and the predicted effect is compared with a causal estimate (verdict: consistent / magnitude differs / sign contradicts).

**Not this term:**
- Fuzzy RD, robust bias-corrected RD inference, covariate-weighted synthetic control, and Monte Carlo / stress-test / code-generation support for the six additional methods (those pages remain DiD-only).
- Mixed-strategy and sequential (Stackelberg, bargaining) equilibria, multidimensional strategies, and structural estimation (MLE/GMM) of the theoretical models; calibration is by explicit moments.
- Report export (PDF/Word/LaTeX).
- Connectors to external data sources (DHS, ACLED, WorldPop, etc.).
- Project persistence / saved sessions.

A person with a messy panel CSV and a treatment date can use this version alone: upload, see whether parallel trends look reasonable, get a DiD estimate. Nothing else needs to exist for that to be useful — everything above it is additional, not a prerequisite for it.

## 4. How we would know it works

- Given a synthetic dataset generated with a treatment effect of, say, 2.0, the DiD estimator reports a coefficient within a reasonable margin of 2.0.
- Given a panel CSV missing the treatment indicator column, the app reports an error naming that column instead of running.
- Given a synthetic dataset built with deliberately diverging pre-trends (violated parallel trends), the diagnosis panel flags it as "questionable" or "violated," not "plausible."
- Given any panel run through the event-study estimator, its coefficient for the period immediately before treatment (k = -1, the reference period) is exactly zero by construction.
- Given a research design declared with random assignment, the method recommendation ranks Randomized Controlled Trial above every other candidate method.
- Given panel data where control units adjacent to a treated unit shift after treatment (Virtual World with spillovers), the "Break My Design" Spillovers check reports WARNING with the number of adjacent controls, the estimated shift and its p-value, and the overall Identification Strength score is below 100. Adjacency alone, without a shift, does not trigger it (8% false alarms on threat-free worlds, see section 5).
- Given the same column names, the generated Python, R, and Stata scripts all fit the same two-way fixed-effects model with standard errors clustered on the same column.
- Switching the sidebar language toggle from EN to FR redraws every page's text in French, including messages produced by the engines (stress-test details, rationales, warnings, errors, model texts), falling back to English for any translation key that's missing. Checked by `tests/test_i18n_coverage.py`: 712 keys, identical in EN and FR. A scripted French render audit of every page also found no untranslated text outside code blocks. Generated scripts, the per-method technical log (labelled "English"), references, and the user's own column names stay as they are.

## 5. What could stop this

- **Statistical correctness.**
  - **DiD, validated.** The DiD estimator is validated against `linearmodels.PanelOLS` on the same synthetic data, including staggered and serially correlated worlds. The coefficients agree to 1e-8 and the clustered SEs to within 2%.
  - **Other estimators, Monte Carlo only.** The six additional estimators are checked by Monte Carlo coverage on their virtual worlds (93–100%), not yet against an external package.
  - **Staggered timing is handled.** When adoption is staggered, the app warns that two-way fixed effects can be biased and offers the Callaway & Sant'Anna estimator, which is validated by Monte Carlo (see section 3).
  - **Matching standard errors are calibrated.** Matching moved from the propensity score to the covariates, with bias correction. This brought CI coverage from a conservative 100% to 97%, and made the estimates more precise.
- **Real data availability.**
  - *Original plan:* I don't yet have a real panel dataset I'm allowed to show in class. The demo will run on the synthetic "virtual world" generator by default; if I obtain a usable real dataset later (course data, a public panel dataset), I'll add it, but the project does not depend on it.
  - *Since hw5:* the app ships one public real dataset with documented provenance, Card & Krueger (1994), loaded from a button on the Virtual Lab page (`causal_lab/data/card_krueger_1994/SOURCE.md`). `tests/test_card_krueger.py` checks that the DiD reproduces the published +2.76 FTE effect.
- **Limitations found by using the app on real data** (hw5 real use, PLANNING_LOG 2026-10-09; hw6 review 1), **fixed in hw6 review 3** (`docs/reviews/hw6-review-03.md`):
  - With only two periods, Serial Correlation raised a false warning, and the parallel-trends and anticipation checks could not be computed but counted against the score (40/100 on Card & Krueger). Non-computable checks are now N/A and are left out of the score, which states how many checks it is based on.
  - The robust (Callaway & Sant'Anna) tab refused unbalanced panels. It now leaves out units missing a period and says how many (26 stores on Card & Krueger), as the R package `did` does by default.
  - The Spillovers check used unit-id adjacency on any data. It is now N/A outside the Virtual World.
  - The clustered DiD standard error counted the absorbed unit fixed effects in its small-sample correction: 1.91 on Card & Krueger. It now follows the Stata xtreg/reghdfe convention: 1.34. That is exactly the published SE for the same sample: Card & Krueger (1994), Table 3, p. 780, row 4 (balanced sample), 2.75 (1.34). The 1.36 printed in row 3 is for all available observations, a different sample (verified against the printed table on 2026-10-16).
  - Store id `SHEET` 407 is used by two different stores (a KFC in Pennsylvania, a Wendy's in New Jersey), which the loader merged into one unit. Each store is now its own unit. The DiD on Card & Krueger is now 2.75 (2.76 published).
- **Still open:** on Card & Krueger only one check (Heterogeneous Effects) can be computed, so its score of 100/100 rests on 1 of 5 checks. The app says so, but a single number remains easy to over-read.
- **Scope creep, and it already happened.** The original version of this idea had ten modules and two languages; this README initially cut it to one estimator and one diagnosis specifically to avoid that. The tripwire fired anyway: event study, cross-method recommendation, the full stress-test battery, code generation, and the French interface were all built before the four core acceptance criteria above were validated against a known package. Section 3 now documents what was actually delivered instead of leaving this README stale about it — but the underlying risk is unchanged: the four original acceptance criteria are still the real bar, and nothing on the delivered list above substitutes for validating the estimator itself.
- **The "Break My Design" score — recalibrated on 2026-10-06.** The hw4 spike (`spike/stress_test_calibration_results.md`) found three of the five checks useless:
  - Spillovers fired on 100% of threat-free worlds;
  - Heterogeneous Effects fired on 94%;
  - Serial Correlation never fired.

  The clean-world score was stuck at 57.6/100. The checks now test what their names say:
  - Spillovers: a DiD of adjacent vs. other controls;
  - Serial Correlation: within-unit residual autocorrelation, corrected for the fixed-effects bias;
  - Heterogeneous Effects: a variance-ratio test of treated vs. control pre/post changes;
  - Anticipation: a first-difference test;
  - Parallel Trends: a full-rank lead test.

  Re-running the spike with a dedicated threat lever for every check (`spike/stress_test_calibration_results_after_fix.md`, 200 replications each):

  | Check | False alarm (clean) | Detection (severe) |
  |---|---|---|
  | Parallel Trends | 14% | 100% |
  | Anticipation | 8% | 97% |
  | Spillovers | 8% | 100% |
  | Serial Correlation | 0% | 100% |
  | Heterogeneous Effects | 10% | 100% |

  The clean-world score is now 92.2/100. A severe threat lowers it to 56–76. The remaining false alarms are the expected cost of testing at the 10% level; the score is still a diagnostic heuristic, not a proof.

## 6. Running it

```bash
cd causal_lab
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py             # opens http://localhost:8501
```

Each file in `causal_lab/tests/` runs as a plain script (`python tests/test_card_krueger.py`) and needs nothing beyond `requirements.txt`. With pytest installed, which is a test runner and not an app dependency, `python -m pytest` from the repository root runs them all. The AppTest files drive the whole app and take about two minutes.

The stress-test calibration (1,200 simulated worlds, about 6 minutes) must be given a new output file; a relative name is taken from the `spike/` folder:

```bash
python spike/stress_test_calibration.py results_2026-10-16.md              # creates spike/results_2026-10-16.md
python spike/stress_test_calibration.py results_2026-10-16.md --overwrite  # replaces it, only if you mean to
```

Without an output name, or if the file already exists, the script stops before simulating anything and changes no file; `--overwrite` is the only way to replace a file. `spike/stress_test_calibration_results.md` (hw4, 2026-10-03) and `spike/stress_test_calibration_results_after_fix.md` (2026-10-06) are historical records; do not overwrite them. These rules are tested by `causal_lab/tests/test_calibration_output.py`, which runs a copy of the script in a temporary folder.
