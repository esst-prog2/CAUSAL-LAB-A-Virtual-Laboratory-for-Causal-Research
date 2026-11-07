# The DiD study behind the demo

Until 2026-11-07 this text was section 1 of the README. Section 1 is now the short description of the December demo; this is what the Guided Demo page shows in detail, with the earlier plan kept as history.

The demo is the **🎓 Guided Demo** page. It tests the app's main claim as a short methods paper would: on data where the answer is known, does difference-in-differences recover it, and does the lab say when it cannot? Every number on the page comes from the engines or from a stored simulation study; none is typed in its text.

**1. Question and design.** Each Virtual World has 100 units over 20 periods. 30% of them are treated from period 10, with a true effect of −0.50. Four threats are varied one at a time, each at five levels from *none* to *severe*:
- diverging pre-trends;
- confounding;
- staggered adoption with effects that grow over time;
- anticipation.

In every world, the page records:
- the two-way fixed-effects DiD, with standard errors clustered by unit;
- the joint lead test of Break My Design, with a wild cluster bootstrap p-value at the 10% level.

**Decision rule: how much bias is too much.** The DiD is acceptable in a scenario when |bias| ≤ 10% of the true effect **and** its 95% interval covers the truth in at least 90% of the worlds. The author fixed this rule on 2026-10-30, after seeing the pre-trends results and before simulating the three other threats; the planning log records it. It answers the question raised in review issue #1.

**What this rule is not.** It evaluates this DiD simulation study. It does not control the application, determine recommendations, validate the question analyser, establish the validity of a real-world estimate, or apply to the eight methods. It is relative to the true effect, so it does not apply at a zero effect, where absolute bias and the rejection rate judge instead. Its verdicts hold for this design: a 10% bias gives coverage of about 92% at 100 units and 83% at 400 (`spike/bias_coverage_check_results.md`).

**2. One world each way (seed 42), as an illustration.** With parallel trends, the DiD gives −0.49, 95% CI [−0.662, −0.325], and the pre-trend test passes (p = 0.991). With severe divergence, it gives +1.107 [0.938, 1.275] and the test warns (p = 0.003).

**3. The simulation study, as evidence.** There are 4 threats × 5 levels × 1,000 worlds. Following Morris, White & Crowther (2019), each statistic comes with its Monte Carlo SE. The study was computed by `spike/demo_study.py`, and every replication is stored with its seed in `causal_lab/data/demo_study/results.json`. Under the decision rule:

| Threat | Acceptable up to | First level beyond the rule | Pre-trend test warns there |
|---|---|---|---|
| Diverging pre-trends | none | low: bias +0.236 (47% of the effect), coverage 31.3% | 14.2% |
| Confounding | medium | high: bias +0.106 (21%), coverage 82.3% | 11.5% |
| Staggered adoption, growing effects | high | severe: bias +0.094 (7%), coverage 87.6% | 10.3% |
| Anticipation | medium | high: bias +0.056 (11%), coverage 91.5% | 43.3% |

Without any threat, the pre-trend test warns in 9.2% of the worlds, or 10.3% in the staggered design, whose baseline already has staggered adoption.

For diverging pre-trends, the levels in detail:

| Diverging pre-trends | Bias | Coverage of the 95% CI | Significant, wrong sign | Pre-trend test warns | Coverage when the test does not warn |
|---|---|---|---|---|---|
| none | −0.004 (0.003) | 94.9% (0.7) | 0.0% | 9.2% | 95.7% (n = 908) |
| low | +0.236 | 31.3% (1.5) | 0.0% | 14.2% | 31.6% (n = 858) |
| medium | +0.556 | 0.0% | 8.1% | 40.0% | 0.0% (n = 600) |
| high | +0.956 | 0.0% | 99.6% | 84.2% | 0.0% (n = 158) |
| severe | +1.596 | 0.0% | 100.0% | 99.9% | 0.0% (n = 1) |

The study supports five findings:
- **When nothing is wrong, the method works and its uncertainty is honest.** Coverage is at its nominal level (94.9%, MCSE 0.7), there is no detectable bias, and the empirical and the reported standard errors are both 0.097. The pre-trend test raises false alarms at 9.2%, close to its nominal 10%.
- **Diverging pre-trends are the most damaging threat.** Even the *low* level breaks the rule. At *high* and *severe*, the DiD reports a significant effect of the wrong sign in almost every world.
- **Confounding is nearly invisible to the pre-trend test.** At *severe*, the bias is 47% of the effect, yet the test warns in only 14.6% of the worlds, barely above its 9.2% false-alarm rate.
- **Staggered adoption with growing effects fails on coverage, not on bias.** At *severe*, the bias stays at 7% of the effect, but the coverage falls to 87.6%.
- **Passing the test does not make the estimate trustworthy.** With *low* diverging pre-trends, 858 of the 1,000 worlds pass the test, yet only 31.6% of their intervals cover the truth. Estimating only after a passed pretest changes the estimator's distribution (Roth, 2022).

**4. Reproducibility, live.** A button re-runs the first 20, 50 or 100 worlds of any threat and level and checks them, value by value, against the stored ones. It says "identical". Each world takes about a second on the free online server (20 worlds by default) and much less on a laptop.

**5. Replication of Card & Krueger (1994), Table 3.** The page recomputes rows 1, 2 and 4 from the raw survey data and sets each cell next to the published one:
- 17 of the 18 published numbers agree to two decimals, including the DiD, 2.75 (1.34);
- the last one is a standard error, 1.08 against 1.07 published. Combining the published, rounded cell SEs, √(0.52² + 0.94²) = 1.074, also gives 1.07, so the gap is rounding.

**6. What this does not show.** The page says so:
- the simulated worlds are simple;
- a passed test is not a proof;
- a replication checks the computation, not the identification.

**Then, quickly, the rest of the lab:**
- **Causal Methods:** six other designs on worlds with a known effect (RCT, matching, IV, RDD, synthetic control, DML).
- **Theoretical Model:** solves a game, predicts the treatment effect, and compares the prediction with the causal estimate.
- **Report:** exports the analysis with its references and a reproducibility section, as PDF, Word, LaTeX or Markdown.

Every page is available in English and in French. The numbers above are those of the stored study: diverging pre-trends computed on 2026-10-29, the three other threats on 2026-10-30, all with seeds 20261029 + r. On 2026-11-07 the intervals were recomputed with Student t (99 degrees of freedom) from the stored estimates and standard errors, without re-simulating (`spike/demo_study_student_t.py`); coverage moved by up to 1.2 points, and no verdict changed.

> **Earlier plan (the brief, kept as history).** I open the app in the browser and upload a CSV: one row per unit per time period, a treatment date, and an outcome column. It shows a plot of average outcomes for treated and untreated units over time, with the treatment date marked. Below it, a diagnosis panel says "Parallel trends: questionable — pre-trend slope difference is 0.34, p = 0.02" and "Recommended: difference-in-differences, but check anticipation effects first." I click "Run DiD" and it shows a coefficient, a standard error, and a two-way fixed-effects regression table. I click "Break this design" and it re-runs the same estimator on a version of the data where I know the true effect is zero, so I can see whether the method still finds a false effect.
>
> If I don't have real data, I click "Generate a synthetic world" first: it creates a panel with a known, chosen treatment effect, so I can check that the estimator recovers close to that number before trusting it on anything real.
>
> **Note (hw6 review 1, 2026-10-16).** This demo is the original plan, and two parts of it differ from what is delivered (section 3):
> - The diagnosis reports a joint test of the pre-treatment leads, with its p-value and a plausible / questionable / violated verdict. It does not report a "pre-trend slope difference".
> - "Break My Design" runs the five diagnostic checks of section 3. It does not re-run the estimator on a placebo version of the data where the true effect is zero.
