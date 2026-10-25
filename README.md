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
- ~~Project persistence / saved sessions.~~ Built on 2026-10-25, see below.

**Built anyway on 2026-10-25 (user decision).** The user chose to build the excluded features after all, knowing that this departs from the scope above and from the advice to stay on one method (issue #1). Each one is a separate pull request with its own OpenSpec change:
- **Saving and opening projects** (Settings page). A `.causallab` file is a zip of a JSON manifest and Parquet datasets. It holds the research design, the Virtual Lab settings and ground truth, the real data, and every Causal Methods dataset and mapping. Results are recomputed on opening, and the Theoretical Model page is not saved. The file never leaves the computer, and nothing in it is pickled.

A person with a messy panel CSV and a treatment date can use this version alone: upload, see whether parallel trends look reasonable, get a DiD estimate. Nothing else needs to exist for that to be useful — everything above it is additional, not a prerequisite for it.

## 4. How we would know it works

- Given a synthetic dataset generated with a treatment effect of, say, 2.0, the DiD estimator reports a coefficient within a reasonable margin of 2.0.
- Given a panel CSV missing the treatment indicator column, the app reports an error naming that column instead of running.
- Given a synthetic dataset built with deliberately diverging pre-trends (violated parallel trends), the diagnosis panel flags it as "questionable" or "violated," not "plausible."
- Given any panel run through the event-study estimator, its coefficient for the period immediately before treatment (k = -1, the reference period) is exactly zero by construction.
- Given a research design declared with random assignment, the method recommendation ranks Randomized Controlled Trial above every other candidate method.
- Given panel data where control units adjacent to a treated unit shift after treatment (Virtual World with spillovers), the "Break My Design" Spillovers check reports WARNING with the number of adjacent controls, the estimated shift and its p-value, and the overall Identification Strength score is below 100. Adjacency alone, without a shift, does not trigger it (8% false alarms on threat-free worlds, see section 5).
- Given the same column names, the generated Python, R, and Stata scripts all fit the same two-way fixed-effects model with standard errors clustered on the same column.
- Switching the sidebar language toggle from EN to FR redraws every page's text in French, including messages produced by the engines (stress-test details, rationales, warnings, errors, model texts), falling back to English for any translation key that's missing. Checked by `tests/test_i18n_coverage.py`: 720 keys on 2026-10-25, identical in EN and FR. A scripted French render audit of every page also found no untranslated text outside code blocks. Generated scripts, the per-method technical log (labelled "English"), references, and the user's own column names stay as they are.

## 5. What could stop this

- **Statistical correctness.**
  - **DiD, validated.** The DiD estimator is validated against `linearmodels.PanelOLS` on the same synthetic data, including staggered and serially correlated worlds. The coefficients agree to 1e-8 and the clustered SEs to within 2%.
  - **Other estimators, validated since 2026-10-25.** The six additional estimators are checked by Monte Carlo coverage on their virtual worlds (93–100%) and, by `tests/test_external_reference.py`, against an established implementation on committed datasets:

    | Estimator | Reference | Agreement |
    |---|---|---|
    | RCT (difference in means, Lin 2013), HC2 | R `estimatr` (`lm_robust`, `lm_lin`) | estimate and SE to rounding |
    | IV (2SLS), HC0 | R `estimatr` (`iv_robust`) | estimate and SE to rounding |
    | Sharp RDD, fixed bandwidth, triangular kernel, HC1 | `rdrobust` (conventional) | estimate to rounding, SE to 3e-5 |
    | Matching (ATT, bias-corrected, Abadie-Imbens SE) | R `Matching` (Sekhon) | estimate and SE to rounding (since 2026-10-25, see below) |
    | Synthetic control weights | `pysyncon` (custom V) | weights to 1e-5 |
    | DML (partially linear) | `DoubleML` (same folds and forests) | estimate and SE to rounding |
    | IV first-stage F (HC0) | R `estimatr` (`diagnostics = TRUE`) | to rounding |
    | Imbens-Kalyanaraman bandwidth | R `rdrobust` 0.80, `bwselect = "IK"` | 0.4% (tolerance 1%) |
    | Callaway & Sant'Anna, never- and not-yet-treated | R `did` (`base_period = "universal"`, `aggte`) | ATT and event study to rounding; bootstrap SE within 4% of the analytical one |

    The reference values are stored in `tests/external_reference/expected.json`, so the tests need neither R nor these packages; `make_reference.py` there regenerates them. Eleven deliberately wrong versions of the estimators all make the test fail, for example:
    - HC1 instead of HC2;
    - a uniform kernel;
    - no bias correction;
    - the working-paper IK constant;
    - unweighted Callaway & Sant'Anna aggregation.

    On the IK bandwidth, R `rdd` 0.57 gives a different value (0.752 instead of 0.625). It follows the 2009 working paper (a regularization of 720 instead of 2160, pooled variance); a line-by-line port of it reproduces its value exactly, so the gap is that choice, not an error. Causal Lab follows the published 2012 version.
  - **Matching: aligned with R and Stata on 2026-10-25.** Causal Lab used to fit the bias-correction regression on all controls. R `Matching`, Stata `nnmatch` and Abadie & Imbens (2011) fit it on the matched controls, weighted by how often each is used. With identical matches, that was the only difference: 0.04 SE on the noisy test dataset.

    On 500 Matching worlds the two were equally good:

    | Bias regression | Bias | RMSE | Coverage |
    |---|---|---|---|
    | All controls (before) | −0.006 | 0.092 | 96.8% |
    | Matched controls, weighted by use (now) | −0.006 | 0.094 | 95.8% |

    The reference convention was adopted so that results can be reproduced exactly in R or Stata.
  - **Staggered timing is handled.** When adoption is staggered, the app warns that two-way fixed effects can be biased and offers the Callaway & Sant'Anna estimator, which is validated by Monte Carlo (see section 3) and, since 2026-10-25, against the R package `did` by its authors.
  - **Matching standard errors are calibrated.** Matching moved from the propensity score to the covariates, with bias correction. This brought CI coverage from a conservative 100% to 97%, and made the estimates more precise (95.8% on 500 worlds since the bias regression follows R and Stata).
- **Real data availability.**
  - *Original plan:* I don't yet have a real panel dataset I'm allowed to show in class. The demo will run on the synthetic "virtual world" generator by default; if I obtain a usable real dataset later (course data, a public panel dataset), I'll add it, but the project does not depend on it.
  - *Since hw5:* the app ships one public real dataset with documented provenance, Card & Krueger (1994), loaded from a button on the Virtual Lab page (`causal_lab/data/card_krueger_1994/SOURCE.md`). `tests/test_card_krueger.py` checks that the DiD reproduces the published +2.76 FTE effect.
- **Limitations found by using the app on real data** (hw5 real use, PLANNING_LOG 2026-10-09; hw6 review 1), **fixed in hw6 review 3** (`docs/reviews/hw6-review-03.md`):
  - With only two periods, Serial Correlation raised a false warning, and the parallel-trends and anticipation checks could not be computed but counted against the score (40/100 on Card & Krueger). Non-computable checks are now N/A and are left out of the score, which states how many checks it is based on.
  - The robust (Callaway & Sant'Anna) tab refused unbalanced panels. It now leaves out units missing a period and says how many (26 stores on Card & Krueger), as the R package `did` does by default.
  - The Spillovers check used unit-id adjacency on any data. It is now N/A outside the Virtual World.
  - The clustered DiD standard error counted the absorbed unit fixed effects in its small-sample correction: 1.91 on Card & Krueger. It now follows the Stata xtreg/reghdfe convention: 1.34. That is exactly the published SE for the same sample: Card & Krueger (1994), Table 3, p. 780, row 4 (balanced sample), 2.75 (1.34). The 1.36 printed in row 3 is for all available observations, a different sample (verified against the printed table on 2026-10-16).
  - Store id `SHEET` 407 is used by two different stores (a KFC in Pennsylvania, a Wendy's in New Jersey), which the loader merged into one unit. Each store is now its own unit. The DiD on Card & Krueger is now 2.75 (2.76 published).
- **Card & Krueger score, reviewed on 2026-10-20:** 100/100 rests on 1 of 5 checks. This is correct under the documented rules, not a bug:
  - Parallel Trends and Anticipation need two pre-treatment periods, and the data have one;
  - Serial Correlation needs three periods, and the data have two;
  - Spillovers is N/A on real data (user decision of 2026-10-16);
  - the computable check, Heterogeneous Effects, gives a variance ratio of 0.61 (New Jersey vs. Pennsylvania), so it passes.

  `tests/test_stress_not_applicable.py` pins each reason. The app states the 1-of-5 basis, but a single number remains easy to over-read.
- **Minimum dependency versions, tested on 2026-10-20 (Python 3.11):** installing exactly the minima of `requirements.txt` revealed two verified defects:
  - pip then resolves pyarrow 26, which needs NumPy ≥ 2.0, so `import pyarrow` fails with `numpy==1.26` and Streamlit's tables would break. With pyarrow 21 instead, 29 of the 30 test files pass at the minima;
  - the failing one, `test_app_flows.py`, shows that switching the language sends the user back to the dashboard with Streamlit 1.50 to 1.63. The page is kept only from 1.64 onwards: the language-dependent labels of the navigation widget change its identity in older versions.

  **Fixed on 2026-10-25 by raising the minima** (user decision): `streamlit>=1.64` and `numpy>=2.0`. NumPy 2 in turn needs the first NumPy-2 releases of pandas (2.2.2), scipy (1.13), statsmodels (0.14.2) and scikit-learn (1.4.2). In a fresh Python 3.11 environment with exactly these minima (pip resolved pyarrow 25.0.1), all 143 tests pass.
- **Statistical convention of two checks:** Parallel Trends and Spillovers used statsmodels' default cluster correction, which counts the unit dummies. That is the convention hw6 review 3 replaced in the DiD estimator, and it made both checks somewhat conservative. **Aligned with the DiD on 2026-10-25** (user decision): they now use `estimators.did.nested_fe_factor`, and `tests/test_stress_hand_computed_regressions.py` pins the new hand values (cluster factor 28/15 instead of 14/3). Re-running the calibration spike on the same 1,200 worlds (`spike/stress_test_calibration_results_2026-10-25.md`):

  | Check | False alarm (clean), before → after | Detection (severe), before → after |
  |---|---|---|
  | Parallel Trends | 14% → **20%** | 100% → 100% |
  | Spillovers | 8% → 9% | 100% → 100% |
  | Anticipation, Serial Correlation, Heterogeneous Effects | unchanged (not affected) | unchanged |

  The clean-world score fell from 92.2 to 90.8. At a nominal 10% level, Parallel Trends raised a false alarm on 20% of clean worlds. The old convention had been hiding a known weakness: the clustered Wald test of a default world's 9 leads, with 100 clusters of which 30 are treated, over-rejects.
- **Parallel Trends: wild cluster bootstrap since 2026-10-25** (user decision). Diagnosis on the same clean worlds:

  | Variant of the joint lead test | False alarms at 10% |
  |---|---|
  | Classical F (the Virtual World noise is i.i.d.) | 10.5% |
  | Clustered, F(q, G − 1), the previous test | 18.4% (1,000 worlds) |
  | Hotelling F(q, G − q) | 14% |
  | CR2 + Hotelling | 14% |
  | Hotelling on the 30 treated clusters | 3% |
  | **Wild cluster restricted bootstrap (Rademacher)** | **10.4%** (1,000 worlds) |

  The check now uses the bootstrap (Cameron, Gelbach & Miller 2008; MacKinnon & Webb 2017): it enumerates all 2^G sign patterns up to 9 units, and otherwise uses 999 draws with a fixed seed. Constant small-sample factors cancel, so the dummy-count question no longer matters for this check.

  Because a Rademacher p-value is at least 2/2^G, the check is N/A with fewer than 5 units: it could never warn at 10%, and a PASS would be misleading. Power, from 500 worlds per `differential_trend` level:

  | Level | low | medium | high | severe |
  |---|---|---|---|---|
  | Previous test | 22% | 54% | 92% | 100% |
  | Bootstrap | 14% | 37% | 83% | 99.8% |

  The drop is power that came from over-rejection. Calibration spike (`spike/stress_test_calibration_results_2026-10-25_bootstrap.md`): Parallel Trends 10% false alarms and 100% detection, clean-world score 92.8. Validation:
  - the Wald statistic equals statsmodels' clustered Wald;
  - the p-value equals an independent first-difference enumeration (`tests/test_stress_hand_computed_regressions.py`);
  - 5 of 5 mutants are caught.

  Runtime: 0.06 s on a default world, 1.8 s on 2,000 units.
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
  - Parallel Trends: a full-rank lead test (with a wild cluster bootstrap p-value since 2026-10-25).

  Re-running the spike with a dedicated threat lever for every check (`spike/stress_test_calibration_results_after_fix.md`, 200 replications each):

  | Check | False alarm (clean) | Detection (severe) |
  |---|---|---|
  | Parallel Trends | 14% | 100% |
  | Anticipation | 8% | 97% |
  | Spillovers | 8% | 100% |
  | Serial Correlation | 0% | 100% |
  | Heterogeneous Effects | 10% | 100% |

  The clean-world score is now 92.2/100 (90.8 after the cluster convention was aligned, then 92.8 with the Parallel Trends bootstrap, both on 2026-10-25; see above). A severe threat lowers it to 56–76. The remaining false alarms are the expected cost of testing at the 10% level; the score is still a diagnostic heuristic, not a proof.

## 6. Running it

```bash
cd causal_lab
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py             # opens http://localhost:8501
```

`causal_lab/.streamlit/config.toml` makes the server listen on this machine only and turns off Streamlit's usage statistics, as the app promises ("Your data remain local"; "no data is sent anywhere"). To share the app on a network on purpose: `streamlit run app.py --server.address 0.0.0.0`.

GitHub Actions (`.github/workflows/tests.yml`) runs the whole suite on every push and pull request twice, on Python 3.11: once with the newest versions pip resolves, once with exactly the minima of `requirements.txt`. It also runs `openspec validate --specs`.

Each file in `causal_lab/tests/` runs as a plain script (`python tests/test_card_krueger.py`) and needs nothing beyond `requirements.txt`. With pytest installed, which is a test runner and not an app dependency, `python -m pytest` from the repository root runs them all. The AppTest files drive the whole app and take about two minutes.

The stress-test calibration (1,200 simulated worlds, about 6 minutes) must be given a new output file; a relative name is taken from the `spike/` folder:

```bash
python spike/stress_test_calibration.py results_2026-10-16.md              # creates spike/results_2026-10-16.md
python spike/stress_test_calibration.py results_2026-10-16.md --overwrite  # replaces it, only if you mean to
```

Without an output name, or if the file already exists, the script stops before simulating anything and changes no file; `--overwrite` is the only way to replace a file. `spike/stress_test_calibration_results.md` (hw4, 2026-10-03) and `spike/stress_test_calibration_results_after_fix.md` (2026-10-06) are historical records; do not overwrite them. These rules are tested by `causal_lab/tests/test_calibration_output.py`, which runs a copy of the script in a temporary folder.
