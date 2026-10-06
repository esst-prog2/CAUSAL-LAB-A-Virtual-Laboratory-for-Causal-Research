# Planning Log

One line per decision about this project — a requirement, a number, a name, a tool. Newest entry on top. Lines are never rewritten; corrections get a new line.

---

- 2026-10-06: `fix-correctness-and-readme-gaps` results. Calibration spike re-run (n = 200 per scenario, each check paired with its own lever), false alarm on clean worlds / detection at severe:
  - Parallel Trends 14% / 100%
  - Anticipation 8% / 97%
  - Spillovers 8% / 100%
  - Serial Correlation 0% / 100%
  - Heterogeneous Effects 10% / 100%
  
  Clean-world Identification Strength rose from 57.6 to 92.2. DiD matches linearmodels PanelOLS (coefficient within 1e-8, clustered SE within 2%). New threat levers: `differential_trend` (slope 0.08·v noise-SD per period) and `anticipation` (0.5·v noise-SD shift one period early). Found along the way and fixed: DML results were not bit-reproducible with `n_jobs=-1` prediction — decided by: Claude
- 2026-10-06: The "make it perfect" work is split into two OpenSpec changes on `main`, keeping the single-branch setup the user asked for:
  - `fix-correctness-and-readme-gaps`: calculations, app bugs, README promises.
  - `complete-french-translation`: every UI string goes through the i18n layer.
  
  Each is committed and pushed when its tests pass — decided by: Claude
- 2026-10-06: Correction of the 2026-10-03 entry. Recalibrating the Spillovers, Heterogeneous Effects and Serial Correlation checks is no longer deferred to the next level; it is done now, together with every other known defect. "Fix everything so it is perfect" is read as: every README section 4 acceptance criterion and every promise in section 3 must actually hold, which includes:
  - the plain-language parallel-trends verdict;
  - the treated-vs-untreated trend plot;
  - a full French interface;
  - DiD validated against a reference package — decided by: user
- 2026-10-06: Wrap-up, all done on `main`:
  - Tasks 5.3 of both changes closed by a scripted end-to-end run of the two CSV-upload flows. It used the real page code, with only `st.file_uploader` stubbed: an IV run on an uploaded CSV with a bad mapping rejected by role name; a Tullock model calibrated per year on an uploaded lobbying CSV, with Δ measured as treated − control, compared with that IV estimate.
  - Both OpenSpec changes archived into `openspec/specs/` (24 specs, all valid).
  - The merged `hw4-spike` branch was deleted, so the repo has a single branch, `main` — decided by: user
- 2026-10-06: Both changes merged straight into `main` (fast-forward to f588c06, no pull requests). The two feature branches were deleted locally and on GitHub so the repo keeps a single working branch. Manual browser smoke tests (tasks 5.3 of both changes) and OpenSpec archiving are still pending — decided by: user
- 2026-10-06: Implementation choices for `add-theoretical-model`.
  - Numerical Nash solver: 64-point grid plus bounded Brent best responses; Gauss–Seidel iteration, then damped Jacobi; 8 seeded starts with early exit on duplicates; convergence at 1e-8 of the strategy range (the precision limit of a 1-D maximizer). An equilibrium is accepted only if its 400-point deviation check shows a relative gain ≤ 1e-6.
  - Comparative statics: central differences with h = 1e-3·max(1, |θ|).
  - Downs and Niskanen are solved by closed form, then deviation-checked.
  - Editor: token whitelist before `sympy.parse_expr`.
  - Results: every catalogue closed form is matched within 1e-3; solve times are 0.02–1.4 s for up to 6 agents — decided by: Claude
- 2026-10-06: New dependency `sympy>=1.12` for the theoretical model: symbolic utilities, first-order conditions, best responses and LaTeX display of the equations — decided by: Claude
- 2026-10-06: `add-causal-method-estimators` committed on its branch (9895bd7). The theoretical-model feature goes on a separate branch `add-theoretical-model` with its own OpenSpec change, so the two can be reviewed as separate PRs — decided by: user
- 2026-10-06: The theoretical model is linked to data in both directions. Calibrate: model parameters are computed from the loaded dataset (column statistics, filtered subgroups, regression coefficients), and one equilibrium is solved per unit of computation that the data structure allows (pooled, per group, per period). Predict: comparative statics give the predicted sign and size of a treatment-induced parameter shift, which is compared with a causal estimate from the app — decided by: user
- 2026-10-06: New feature, a "Theoretical Model" option. Agents interact through utility/payoff equations, and the app derives first-order conditions and best responses and solves the Nash equilibrium. It has two entry points: (1) a catalogue of ready-made models, public choice (median voter, probabilistic voting, Tullock rent-seeking, Niskanen bureaucracy, voluntary public-good provision) plus classic interactions (Cournot, differentiated Bertrand); (2) a free editor where the user writes the utility function of each of N agents — decided by: user
- 2026-10-06: Implementation choices for `add-causal-method-estimators`. Shared `MethodResult` type. RCT: Lin (2013) covariate adjustment, HC2 SEs. Matching: 1-NN propensity-score matching with Abadie–Imbens SE, plus Hájek IPW with bootstrap SE. IV: linearmodels IV2SLS with robust SEs, weak-instrument warning below first-stage F = 10. RDD: triangular-kernel local linear, Imbens–Kalyanaraman bandwidth, 0.5x/2x sensitivity, binomial manipulation check. Synthetic control: outcome-only SLSQP weights, placebo-in-space p-value. DML: partially linear model, 5-fold cross-fitting, random forests (new dependency `scikit-learn>=1.4`). The page lives in `causal_lab/ui/methods_page.py`. Measured CI coverage on each default virtual world: RCT 94%, IV 94%, RDD 94% (200 reps each), DML 93% (60 reps), Matching 100% (its SE is ~30% too large, i.e. conservative) — decided by: Claude
- 2026-10-06: Workflow for this change: branch `add-causal-method-estimators`, OpenSpec change of the same name (proposal, specs, design, tasks) written first, then implemented and tested in the same session; nothing committed or pushed without the user's explicit go-ahead — decided by: user
- 2026-10-06: The new methods run on both (a) a dedicated synthetic data generator per method with a known true effect, shown next to the estimate, and (b) an uploaded CSV whose columns the user maps (outcome, treatment, instrument, running variable, covariates...). This deliberately departs, for the new methods only, from the 2026-09-22 "fixed columns, no column-mapping UI" decision; the existing DiD/panel upload keeps its five fixed columns — decided by: user
- 2026-10-06: Scope reversal: the six methods listed under README "Not this term" — RCT, Matching / Propensity Score, Instrumental Variables (2SLS), Regression Discontinuity, Synthetic Control, Double Machine Learning — become actual runnable estimators this term (previously only scored by the recommendation engine) — decided by: user
- 2026-10-03: README.md updated (section 4 Spillovers criterion qualified, section 5 new risk item) with the spike's measured numbers; no code changed this week — recalibrating the Spillovers, Heterogeneous Effects, and Serial Correlation checks in `robustness_engine/stress_test.py` is next level's work, not this one's — decided by: user
- 2026-10-03: Later levels backlog (not specced yet): (1) recalibrate the three broken "Break My Design" checks found by the hw4 spike — Spillovers (ignores the `spillovers` parameter, keys only on unit-id adjacency), Heterogeneous Effects (CV>1.0 threshold too tight for sampling noise), Serial Correlation (Durbin-Watson computed on raw row order, not within unit, so it has zero detection power); (2) heterogeneity-robust DiD estimator for staggered timing (Callaway & Sant'Anna / de Chaisemartin & D'Haultfoeuille), already flagged as a concern by the diagnosis and recommendation engines but not implemented — decided by: user
- 2026-10-03: Spike answer (issue #3, n=200 per scenario, `spike/stress_test_calibration.py`): clean-world mean Identification Strength = 57.6/100. False-alarm / detection rates per check: Parallel Trends 15%/21% (confounding=severe), Anticipation 2%/n/a (no corresponding DGP lever), Spillovers 100%/100%, Serial Correlation 0%/0% (Durbin-Watson computed on row order, never within unit — it has no power at all), Heterogeneous Effects 94%/100%. Spillovers and Heterogeneous Effects fire on clean data almost every time; Serial Correlation never fires regardless of the actual threat; the headline score never really moves (57.6 to 58.0) whichever single threat is severe, because the two broken checks dominate it in both directions — decided by: user
- 2026-10-03: Spike question (issue #3): with every causal threat switched off, what Identification Strength score does the app report, and which of the 5 "Break My Design" checks fire? — decided by: user
- 2026-10-03: Spike answer counts as: a 5-row table (one row per check: Parallel Trends, Anticipation, Spillovers, Serial Correlation, Heterogeneous Effects) with the false-alarm rate over 200 clean-world replications and, where the DGP has a corresponding threat lever, the detection rate over 200 replications with that threat set to "severe"; plus the clean-world mean Identification Strength score — decided by: user

- 2026-09-26: Added `AGENTS.md` (planning-log rule at the top) and `CLAUDE.md` (`@AGENTS.md`) per grading feedback, so any agent working in this repo picks up the logging rule automatically instead of relying on it being repeated each session — decided by: user

- 2026-09-22: Both open changes applied and archived: `validate-upload-columns` (new `causal_lab/utils/validation.py` + `tests/test_validation.py`, wired into `app.py`'s upload handler) and `document-delivered-mvp-scope` (README.md sections 3-5 rewritten); a project-local `.venv/` was created to install `causal_lab/requirements.txt` and actually run the tests and a live Streamlit smoke test, since neither existed before — decided by: user
- 2026-09-22: MVP scope drift resolved by documenting the delivered scope (not by trimming code): change `document-delivered-mvp-scope` proposes rewriting README.md sections 3-5 to recognize event study, method recommendation, the 5-check stress test, code generation, and EN/FR i18n as delivered, not "not this term" — decided by: user

- 2026-09-22: Uploaded CSVs will require exactly 5 fixed columns (unit, period, Y, D, treated_unit) with no column-mapping UI; missing columns must be named in an upload-time error instead of failing later — decided by: user
- 2026-09-22: Change `validate-upload-columns` scaffolded via `openspec new change` with proposal.md, a delta spec on real-world-data-upload, and tasks.md (design.md skipped: no cross-cutting/dependency/perf complexity applies); implementation not yet started — decided by: Claude
- 2026-09-22: openspec/specs/ populated with 12 capability spec files (research-design-wizard, causal-diagnosis, method-recommendation, virtual-world-generation, monte-carlo-evaluation, real-world-data-upload, did-estimation, event-study-estimation, break-my-design-stress-test, robustness-battery, code-generation, internationalization) reverse-engineered from the current causal_lab/ code, all passing `openspec validate --specs` — decided by: user
- 2026-09-22: OpenSpec CLI (`@fission-ai/openspec`) v1.13.0 installed globally via npm and initialized in this repo (`openspec/` + `.claude/` skills/commands for spec-driven change workflow), Node.js 24.19.0 LTS installed first via winget since it was missing — decided by: user
- 2026-09-22: Repo history reconciled by merging `origin/main` (GitHub README edit) into local `main` and pushing — decided by: user
- 2026-09-22: Project keeps a planning log; one line per decision (date, what, who), append-only, never rewritten — decided by: user
