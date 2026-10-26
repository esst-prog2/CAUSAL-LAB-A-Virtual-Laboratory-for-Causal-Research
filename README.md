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
- ~~Fuzzy RD, robust bias-corrected RD inference, covariate-weighted synthetic control, and Monte Carlo / stress-test / code-generation support for the six additional methods (those pages remain DiD-only)~~. Built on 2026-10-25, see below.
- ~~Mixed-strategy equilibria, sequential (Stackelberg, bargaining) equilibria, multidimensional strategies, and structural estimation (MLE/GMM) of the theoretical models~~ (built on 2026-10-26, see below).
- ~~Report export (PDF/Word/LaTeX).~~ Built on 2026-10-25, see below.
- ~~Connectors to external data sources (DHS, ACLED, WorldPop, etc.).~~ Built on 2026-10-25, see below.
- ~~Project persistence / saved sessions.~~ Built on 2026-10-25, see below.

**Built anyway on 2026-10-25 (user decision).** The user chose to build the excluded features after all, knowing that this departs from the scope above and from the advice to stay on one method (issue #1). Each one is a separate pull request with its own OpenSpec change:
- **Saving and opening projects** (Settings page). A `.causallab` file is a zip of a JSON manifest and Parquet datasets. It holds the research design, the Virtual Lab settings and ground truth, the real data, and every Causal Methods dataset and mapping. Results are recomputed on opening, and the Theoretical Model page is not saved. The file never leaves the computer, and nothing in it is pickled.
- **Report export** (Report page): PDF, Word, LaTeX or Markdown, in the interface language. It contains:
  - the question and design, the diagnosis and recommendation, and the data;
  - DiD, the event study and, if staggered, Callaway & Sant'Anna, with the true effect for a Virtual World;
  - Break My Design and robustness;
  - the Causal Methods results already computed;
  - the Python, R and Stata code.

  Every number is recomputed by the engines, and the report has tables only, no charts. New dependencies: `python-docx` and `reportlab` (pure Python). The LaTeX output compiles with pdflatex, checked with MiKTeX.
- **Monte Carlo, Break My Design and code for the six Causal Methods**: three tabs under each result on the Causal Methods page.
  - *Monte Carlo* on the method's virtual world. On the default worlds (200 replications, 30 for DML) every method has 93–96% CI coverage and a bias below 0.03.
  - *Break My Design*, one set of checks per method:
    - RCT: joint balance test, arm size;
    - Matching: support, balance after matching, extreme scores, agreement with IPW;
    - IV: F ≥ 10, robust overidentification;
    - RDD: manipulation, Hausman-type bandwidth comparison, placebo cutoffs;
    - Synthetic control: pre-fit, leave-one-out donor, in-time placebo;
    - DML: treatment predictability, stability across sample splits.

    Each check was calibrated before release (`spike/method_calibration_results.md`): false alarms are 0–13.5% on 200 default worlds. Four first-draft rules of thumb fired on 26–94% of clean worlds and were replaced by tests. Three limits remain:
    - the synthetic-control permutation test of the default world is itself anti-conservative (p = 1/21 occurs 9.5% of the time instead of 4.8%), so the in-time placebo uses p < 0.05;
    - the RCT balance test over-rejects with 40 observations (23%);
    - RDD curvature is detected on only 26.5% of worlds.
  - *Code* in Python, R and Stata with the reference packages, using the page's mapping. Every Python and R script was run, and its header states the measured agreement:
    - exact for RCT, Matching and IV in both languages, and for DML in Python;
    - RDD standard error within 0.01%;
    - synthetic control within 0.01% (pysyncon) or 0.1% (R Synth);
    - R DoubleML about 1.4 SE away (other forests and folds);
    - Stata not checked.
  - *Fixed on the way:* the DiD Python script printed statsmodels' default clustered SE, 1.91 on Card & Krueger instead of the app's 1.34. It now applies the same nested-fixed-effects correction.
- **Fuzzy RD and robust bias-corrected RD inference.** The RDD estimator now computes everything side by side, as rdrobust does (Calonico, Cattaneo & Titiunik 2014):
  - the conventional estimate and its HC1 SE, now equal to rdrobust to rounding (the old pooled HC1 differed by 2.6e-5);
  - the bias-corrected estimate and its robust SE, with b = h;
  - with a "treatment received" column, the fuzzy local Wald estimate, its delta-method SE, and the first-stage jump with its F statistic.

  Every one of these equals rdrobust to 1e-14, sharp and fuzzy (`tests/test_external_reference.py`). The Causal Methods page offers conventional or robust inference, and the RDD world gets a compliance setting. With the IK bandwidth both CIs cover 93–95% on the RDD worlds, the robust one being 45% longer. With a bandwidth set too wide by hand, the robust CI protects:

  | Bandwidth (curvature 5) | Conventional coverage | Robust coverage |
  |---|---|---|
  | h = 0.6 | 69% | 95% |
  | h = 0.9 | 0% | 85% |
- **Synthetic control with covariates** (Abadie, Diamond & Hainmueller 2010). The weights match the pre-treatment means of the covariates and of the outcome, and the predictor importance V is chosen to minimise the pre-treatment outcome error. The page shows the predictor balance. Choosing V is not convex and is a local search (Nelder-Mead from k + 1 starts): on 6 worlds the pre-treatment fit was better than pysyncon's in 4 and at most 9% worse in 2. In the default worlds the covariates do not reliably improve on the outcome-only synthetic control, since the outcome path already carries the information (Kaul et al. 2022). Generated scripts say they can differ for that reason.
- **External data connectors** (External Data page). Three sources:
  - DHS Program indicators, by country or region and survey year (public API);
  - WorldPop population by administrative unit and year (geoBoundaries polygons and WorldPop zonal statistics, both public);
  - ACLED conflict events and fatalities per unit and year or month (needs the researcher's ACLED account).

  A fetched dataset can be downloaded or sent to a Causal Methods page.

  **These are the only network requests Causal Lab makes, and they are off until turned on in Settings.** They carry query parameters only (country codes, indicator ids, boundaries, years, and the ACLED credentials, to ACLED alone and never stored); no dataset loaded in the app is sent.

  DHS and WorldPop were checked live on 2026-10-25. ACLED is written to its documented API but could not be run without an account, and the page says so. The tests replay recorded responses offline (`tests/connector_fixtures`); `CAUSAL_LAB_LIVE=1` adds a live check.

**Theory extensions (from 2026-10-26, user decision: a broad project, not limited to one method).**
- **Matrix games and mixed strategies** (Theory page, "Matrix game").
  - A catalogue of 7 games: prisoner's dilemma, matching pennies, battle of the sexes, hawk-dove, stag hunt, tax inspection, rock-paper-scissors. A payoff editor takes up to 6 × 6.
  - **Every Nash equilibrium, pure and mixed**, by vertex enumeration of the best-response polytopes (as Gambit's enummixed). It equals Gambit on 800 test games. nashpy disagreed with Gambit on 41 of 500 generic games, sometimes with an impossible even count, so Gambit is the reference.
  - The **logit quantal response equilibrium** path, by Newton continuation from random play, equal to Gambit to 1e-9 on generic games. In symmetric games (battle of the sexes, hawk-dove) the branch splits: Causal Lab follows the symmetric continuation, Gambit one side.
- **Sequential games** (Theory page, "Sequential (Stackelberg)" and "Bargaining").
  - **Stackelberg:** pick a leader in any multi-agent continuous model. The followers' Nash response is re-solved for each leader strategy, and the leader optimizes over it (subgame-perfect equilibrium). The result is shown next to the simultaneous game. It equals the closed forms of Cournot, Bertrand (sympy backward induction) and Tullock (Dixit 1987).
  - **Bargaining:** the generalized Nash bargaining solution with utility expressions, and Rubinstein's alternating offers. The finite-horizon path converges to (1 − δ2)/(1 − δ1δ2), and the Binmore, Rubinstein & Wolinsky link to the Nash solution is shown.
- **Multidimensional strategies** (Theory page, "Several strategy variables"). Each agent chooses up to 4 variables in a box. The catalogue has probabilistic voting on two issues, multimarket Cournot with a joint cost, and a contest over two prizes; the free editor takes any model written as expressions.
  - **Solver:** each best response is a grid over the agent's box refined by L-BFGS-B with the exact gradient; best responses are iterated from several starts, and the first-order (KKT) conditions are then solved by Newton. A profile is reported only if no agent gains by deviating anywhere in its box, so a non-concave agent's saddle point is rejected and a game with no pure equilibrium reports none.
  - **Checks:** the three catalogue closed forms (including a corner where firms leave a market) to 1e-7, an asymmetric game against sympy's exact solution to 1e-9, a KKT corner, and the scalar Tullock contest.
- **Structural estimation** (Theory page: tab "4 · Structural estimation", and "Estimate λ" under a matrix game).
  - **Logit QRE by maximum likelihood:** λ from observed choice counts, typed or counted in a dataset. Standard error, a 95% interval by inverting the likelihood-ratio test, fitted against observed frequencies, and a test against random play. It equals Gambit's `logit_estimate` to 1e-4 on 38 of 40 random games. On the other 2, every choice falls on a pure equilibrium, so the likelihood rises to 0 as λ grows: Causal Lab then reports only a lower bound, and Gambit stops somewhere on that plateau.
  - **GMM on first-order conditions:** each row of a dataset is one observed equilibrium (e.g. a market). Each agent's first-order condition times the instruments has mean zero at the true parameters. Each parameter is fixed, observed in a column, or estimated. The method is two-step efficient GMM with robust standard errors and Hansen's J test. When the conditions are linear in the parameters, it equals linearmodels' IV-GMM to 1e-8.
  - **Calibration** (`spike/estimation_calibration.py`, 1000 replications, coverage of the 95% intervals):
    - QRE, inspection game, 200 choices per player: LR 95.6% and Wald 95.3% at λ = 1; LR 94.8% and Wald 93.9% at λ = 3.
    - QRE, stag hunt at λ = 2: 37% of samples put every choice on one action, so λ has only a lower bound. The LR interval still covers 98.4%, but the Wald interval only 61.7%. The page therefore leads with the LR interval.
    - Nonlinear GMM (constant-elasticity Cournot, 300 markets): coverage 93.7–94.3%, slightly below 95% as expected for two-step GMM in small samples (Windmeijer 2005). The J test has size 4.9%.

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

  **scipy raised again, to 1.15, later on 2026-10-25** (for the covariate synthetic control):
  - the NNLS of scipy 1.13 and 1.14 stalled on 11% of the inner weight problems ("Maximum number of iterations reached"), which the minimum-versions CI job caught;
  - scipy 1.15 rewrote NNLS;
  - a small ridge term makes those problems' solution unique, so scipy 1.15 and 1.17 now return identical weights.
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
