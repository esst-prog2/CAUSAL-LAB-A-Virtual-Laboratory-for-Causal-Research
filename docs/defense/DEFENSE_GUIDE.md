# Defense guide: Causal Lab

For Thierry, to prepare the December defense. Every number below comes from the code or the stored results at the time of writing, and each section names where to check it. If the code changes, check the numbers again.

**How to use it.** Read Part 1 first, then rehearse Part 3 aloud without looking, then run the fuller simulation in [ORAL_DEFENSE.md](ORAL_DEFENSE.md), which adds intuition, an example and a follow-up to each question. Do not recite: you must be able to explain each answer in your own words, and to open the file it cites.

## Part 1. The decision rule: 10% bias, 90% coverage

### What the rule says

DiD is **acceptable** in a scenario when both of these hold over 1,000 simulated worlds:

- |bias| ≤ 10% of the true effect;
- the 95% confidence interval contains the true effect in at least 90% of the worlds.

### Where it is defined

| What | Where |
|---|---|
| The two numbers | `MAX_BIAS_SHARE`, `MIN_COVERAGE` in `causal_lab/simulation_engine/demo_study.py` |
| The rule itself | `Summary.acceptable` in the same file |
| "Acceptable up to which level" | `largest_acceptable` in the same file |
| Display | `ui/demo_page.py` (table with ✓/✗, dashed line at 90%) |
| Tests | `tests/test_demo_study.py`, including the limit cases and a zero effect |
| When you decided it | `PLANNING_LOG.md`, 2026-10-30 |

### How each quantity is computed

**The true effect is known because the data are simulated.** `simulation_engine/dgp.py` builds both potential outcomes for every unit and period: `y1 = y0 + effect_now`. So `true_att` is simply the mean of `effect_now` over the treated unit-periods actually observed. It is not estimated. With default settings it equals −0.50. With dynamic effects it grows (−0.63 to −1.36 in the staggered scenario), so each estimate is compared with its own world's truth.

**Bias.** Average error over the worlds: `err = est - truth`, `bias = err.mean()`. Its Monte Carlo standard error is `err.std(ddof=1) / sqrt(n)`, about 0.003 here.

**Relative bias.** 100 × |E[τ̂] − τ| / |τ|, computed as `|bias| / |true_att|` in `Summary.bias_share`, the mean estimate standing for E[τ̂].

**Absolute against relative.** Absolute bias is in the outcome's units and always exists. Relative bias is a share of the effect and needs a non-zero effect.

**Coverage.** The share of worlds where `ci_low <= truth <= ci_high`. The interval is the one the app reports (`estimators/did.py`): estimate ± t × cluster-robust SE, with t from a Student distribution with G − 1 degrees of freedom (1.98 at 100 units). **Until 2026-11-07 it was 1.96.** The stored intervals were recomputed from the stored estimates and SEs without re-simulating, and no verdict changed. Its Monte Carlo standard error is `sqrt(p(1-p)/n)`, about 0.009 at 90%.

### Five quantities not to confuse

| Quantity | Question it answers | In the default world |
|---|---|---|
| **Bias** | On average, how far is the estimator from the truth? | −0.004 with no threat |
| **Relative bias** | How large is that compared with the effect? | 0.8% |
| **Coverage probability** | How often does the interval contain the truth? | 94.9% (nominal 95%) |
| **Interval width** | How precise is the estimate? | About 2 × 1.98 × 0.097 = 0.38 |
| **Power** | If there is an effect, how often is it detected (H0: effect = 0 rejected)? | 99.8% |

They can move separately. A very wide interval has high coverage and poor precision. A precise estimator with a small bias can have terrible coverage. High power says nothing about being right: with severe diverging pre-trends the rejection rate is 100%, and the estimate has the **wrong sign** (true −0.50, bias +1.60).

### The trap: relative bias at or near zero

Relative bias divides by the true effect. Three consequences:

1. **At a true effect of zero it does not exist.** The code used to divide by zero. Corrected on 2026-11-05: `rule_applies` is false, `bias_share` is NaN and `acceptable` is false, because the rule cannot say anything there. The study never hits this case, since all its true effects are non-zero, so no stored result changed.
2. **Near zero it explodes.** A trivial bias of 0.01 on a true effect of 0.02 is 50%. The rule would call that unacceptable although the error is negligible.
3. **The same absolute bias passes or fails depending on the effect.** Compare two rows of the stored study:

   | Scenario | True effect | Bias | Relative | Bias half of the rule |
   |---|---|---|---|---|
   | Confounding, high | −0.50 | +0.106 | 21.3% | fails |
   | Staggered, severe | −1.36 | +0.094 | 6.9% | passes |

   A nearly identical absolute bias gets opposite verdicts. (The staggered row fails anyway, on coverage: 87.6%.)

**For a null effect**, use absolute bias and the rejection rate, which is then the size of the test. Say this before you are asked.

### Why these thresholds, honestly

**They are judgement, not theorems.** Say so first. No result in statistics makes 10% or 90% the correct line. The rule answers the question in review issue #1: "how much bias is too much", which "nothing generates for you".

Arguments you can defend:

- **10%**: the effect in this design is −0.50, so the tolerance is 0.05, half a tenth of a noise SD. Below that, the error would not change a substantive reading of the effect's size. That is your substantive judgement about this effect.
- **90%**: a nominal 95% interval that covers 90% misses twice as often as promised, so its error rate is 10% instead of 5%. Beyond that, a reader is misled about the uncertainty.
- **Comparison with Bradley (1978), checked but with care.** Bradley's "liberal" robustness criterion concerns the **Type I error of a test**: an actual rate between 0.5α and 1.5α, that is 0.025 to 0.075 at α = 0.05. I confirmed this from papers that quote it and could not read the original, which is paywalled, so check it in the library before citing a page. Applying it to coverage is **your own step**, through the duality of tests and intervals: 1 − 0.075 = 92.5%. Bradley does not write about coverage in simulations of this kind. So say: "by analogy with Bradley's criterion, my 90% is more permissive". Then give your reason, or be ready to tighten it. At 92.5%, confounding "medium" (92.2%) and staggered "high" (91.9%) would also fail, and anticipation "medium" (93.7%) would pass.
- **Two conditions, because each catches what the other misses**, as the stored study shows:

  | Scenario | Relative bias | Coverage | What fails |
  |---|---|---|---|
  | Anticipation, high | 11.2% | 91.5% | bias only |
  | Staggered, severe | 6.9% | 87.6% | coverage only |
  | Confounding, high | 21.3% | 82.3% | both |

### Weaknesses to state before the professor does

1. **The rule depends on precision. This was simulated, not only calculated** (`spike/bias_coverage_check_results.md`, 1,000 worlds per cell). A bias of exactly 10% (0.05) added to clean worlds gives:

   | Units | SE | Bias / SE | Coverage, simulated | Normal formula |
   |---|---|---|---|---|
   | 100 | 0.097 | 0.52 | 92.2% | 93.5% |
   | 400 | 0.049 | 1.03 | 82.8% | 82.7% |

   The formula is Φ(t − b/SE) + Φ(−t − b/SE). **Earlier versions of this guide said "about 93%" at 100 units, which is the formula. The simulation is lower, so quote it.** The reason for the gap is that clean coverage is itself just under 95%. A real threat behaves the same way: anticipation "high" keeps its bias at 400 units (+0.060) while coverage goes from 91.5% to 76.9%.

   *Intuition:* a fixed bias does not shrink with the sample, but the interval does, so a sharper estimate aimed slightly off misses more often. The relationship depends on sample size, the SE, the interval's construction, the effect's size and the simulation's design. So the two thresholds are not independent, and the verdicts hold for this design: 100 units, 20 periods.
2. **Not fully pre-specified.** You fixed the rule after seeing the pre-trends results and before the three other threats. The README and the log say so. It is a partial pre-specification; do not call it more.
3. **Monte Carlo error near the limits.** Anticipation at "high" is 11.2% ± 0.6 points, about 2 Monte Carlo SEs above 10%. Staggered at "high" has coverage 91.9% ± 0.9, about 2 SEs above 90%. Those verdicts are less firm than the others.
4. **It only applies where the truth is known.** On real data no one knows the bias, so the rule says nothing about a real study. It answers: under which violations does this estimator go wrong, and by how much?

### What happens when the criteria fail, and what they are not

The Guided Demo marks the scenario ✗ and reports the last acceptable level. **Nothing else happens.** The 10% and 90% criteria evaluate the DiD simulation study. They do not:
- control the application;
- determine method recommendations;
- validate the question analyser;
- establish the validity of a real-world estimate;
- apply to all eight methods.

If the professor asks "does the app enforce it?", the answer is no: it is the verdict of a simulation study.

**Zero and near-zero effects, simulated.** With a true effect of zero (`spike/bias_coverage_check_results.md`), bias is -0.0039 (MCSE 0.0031) at 100 units, coverage 94.9% and rejection 5.1%. Relative bias does not exist there.

### Results (stored in `causal_lab/data/demo_study/results.json`, 1,000 worlds per cell)

| Threat | Acceptable up to | First level beyond | Bias there | Coverage there | Pre-trend test warns there |
|---|---|---|---|---|---|
| Diverging pre-trends | none | low | +0.236 (47%) | 31.3% | 14.2% |
| Confounding | medium | high | +0.106 (21%) | 82.3% | 11.5% |
| Staggered, dynamic effects | high | severe | +0.094 (6.9%) | 87.6% | 10.3% |
| Anticipation | medium | high | +0.056 (11.2%) | 91.5% | 43.3% |

**The finding that matters:** where DiD first goes wrong, the pre-trend test usually does not warn. In three of the four rows it barely differs from its 10% false-alarm level (9.2% with no threat), because those threats leave little trace in the pre-period, or the test has little power at that level. Passing a pre-test does not establish parallel trends (Roth 2022).

## Part 2. Module by module

### Method names and counts: know these exactly

The **recommendation** covers 8 methods: RCT, RDD, DiD, event study, synthetic control, IV, interrupted time series and matching (`causal_engine/recommendation.py`, `METHOD_KEYS`).

The **estimators** are not the same list: DiD, event study and Callaway & Sant'Anna on the Estimation page, plus RCT, matching, IV, RDD, synthetic control and DML on the Causal Methods page (`estimators/registry.py`).

Two mismatches to state yourself:
- **ITS can be recommended but the app has no ITS estimator.** The recommendation is advice only there.
- **DML has an estimator but is never recommended.** It is an estimation technique under selection on observables, not a separate design.

### causal_engine/question_reading.py and question_analysis.py

- **Purpose.** Read what a research question asks, before any method.
- **Why it exists.** It is an extension, not the claim (professor's decision, 2026-11-09): the front door that keeps the wrong method from being picked. A form alone led to answers that ignored the question: on 2026-11-01 a question about a scholarship cutoff got DiD. Always give both numbers, and the three sets: on the second set it was right 95% of the time when it said causal (18/19) but caught 0.60 of causal questions against a target of 0.70; version 3, on a third set, catches 0.83 (25/30) with no false causal reading, but version 2 would catch 0.80 on that same set, so most of the difference is the set.
- **Inputs.** The question text, and the form (`ResearchDesignInput`).
- **Outputs.** `QuestionAnalysis`: the intent (causal, predictive, descriptive, ambiguous), eight elements each with a status (stated, inferred, to confirm, unknown), the implied form fields, follow-up questions and what blocks a ranking.
- **Logic.** Deterministic regular expressions in reusable families (verbs with inflections, auxiliaries, connectors), in English and French. The words behind each conclusion are kept. Rules are tried in a fixed order: strong causal structures, then explicit prediction, association, verb clauses, explicit description, comparisons and statements. Anything else is ambiguous.
- **Assumptions.** Wording reflects intent. A title or a question can omit nearly everything about design.
- **Limits.** It is pattern matching, not understanding. It reads wording, and **says nothing about identifiability**: a question can be plainly causal and impossible to answer. See `docs/evaluation/REPORT.md` for measured performance.
- **Interactions.** `diagnosis.py` calls it. `recommendation.py` uses its intent, blocks and inferences. `ui/question_panel.py` displays it, and the report prints it.
- **Example.** "Does Medicare eligibility at age 65 change health care use?": causal; treatment and outcome quoted; "eligibility" plus "at age 65" implies an assignment threshold, inferred, and the follow-up asks whether the cutoff is sharp.
- **Professor might ask.** Why not a language model? (Your choice: local, reproducible, each conclusion traceable, and your data stay on the machine. The cost is lower coverage of wordings.) What happens with an unrecognised sentence? (Ambiguous; it asks. It does not call it non-causal.)

### causal_engine/diagnosis.py

- **Purpose.** Turn the form into risk levels (endogeneity, confounding, spillovers, heterogeneity, data structure).
- **Inputs and outputs.** `ResearchDesignInput` to `DiagnosisResult` (levels and notes, the question's signals and its analysis).
- **Logic.** Direct, documented mappings, such as: random assignment gives low endogeneity; no pre-period gives high confounding.
- **Limits.** Heuristic levels, not estimates. Keyword flags can misfire.
- **Interactions.** Feeds the recommendation; its levels decide a few explanatory notes, not the order.
- **Example.** A question with "neighboring territories" raises the spillover flag.
- **Professor might ask.** Is "HIGH" a measurement? (No, a label from a rule.)

### causal_engine/recommendation.py

- **Purpose.** Say which designs are credible for this study, and why the others are less so.
- **Why it exists.** An earlier scored engine, run over 1,620 wizard designs, ranked IV first in 462 with no instrument being asked for. A method now must pass its conditions first.
- **Logic.** Gates per method give `supported`, `needs_info` or `not_supported`. The question is checked against the form. Supported methods follow an argued order: designs whose comparison comes from the assignment; comparisons over time (synthetic control first with one treated unit, or a few and at least 10 pre-periods); IV; ITS; matching.
- **Why no scores.** The earlier numbers (RCT 98, RDD 88, ...) were hand-set and suggested a precision nobody had established. Removed on 2026-11-05, at your request. Over 25,920 designs, the first choice changed in 610 (2.4%); each change is explainable.
- **Assumptions.** The researcher's answers are honest and correct. The order concerns internal validity under stated conditions.
- **Limits.** It cannot detect a false answer. The order is an argument, and you should be able to attack it yourself: a strong IV can be better than a DiD with doubtful trends. No method is superior everywhere.
- **Example.** One treated state and 15 pre-periods: synthetic control comes before DiD, since its counterfactual is built explicitly and its fit can be inspected.
- **Professor might ask.** Why is IV below DiD? (The exclusion restriction cannot be tested at all; parallel trends can at least be examined before treatment. But pre-trend tests are weak, as your own study shows, so this is an argument and not a fact.)

### simulation_engine/ (dgp.py, monte_carlo.py, demo_study.py, method_worlds.py, method_monte_carlo.py)

- **Purpose.** Create data where the true effect is known, then measure how estimators behave.
- **Why it exists.** It is the core of the assignment: on real data, bias cannot be measured.
- **Inputs.** `VirtualWorldConfig` (units, periods, share treated, effect, threats and their intensity).
- **Outputs.** A panel with `Y0`, `Y1`, `Y`, and the truth; summaries of bias, RMSE, coverage and rejection, each with Monte Carlo SEs (Morris, White & Crowther 2019).
- **Logic.** Y0 = unit effect + common time trend + threat terms + AR(1) noise. Y1 = Y0 + effect. Seeds are `SEED_BASE + r`, so any replication can be recomputed.
- **Assumptions.** The threats take the functional forms written in the code, such as a linear differential trend. Results hold for those forms.
- **Limits.** One design (100 units, 20 periods, 30% treated, noise SD 1). Threats are varied **one at a time**, never combined. The level names (low, severe) are the code's scale, not a real-world magnitude.
- **Example.** Severe staggered adoption with growing effects: the true ATT is −1.36, the DiD is biased by +0.094, and coverage drops to 87.6%.
- **Professor might ask.** Why 1,000 replications? (Coverage near 90% then has a Monte Carlo SE of about 0.9 points, enough to separate most scenarios from the limit, though not all: see Part 1.)

### estimators/

- **Why it exists.** The study needs a correct estimator, and "not DiD here" needs real alternatives.
- **Problem it addresses.** Turning a design into an effect with an honest uncertainty.
- **Inputs and outputs.** A data frame and column roles; an estimate, SE, interval, p-value, and warnings where the data make them unreliable.
- **Logic.**
  - *DiD:* Y_it = α_i + γ_t + β·D_it + ε_it by OLS, cluster-robust SE by unit (Bertrand, Duflo & Mullainathan 2004), unit dummies not counted in the small-sample factor, Student t with G − 1 degrees of freedom.
  - *Event study:* the same, with one coefficient per period relative to treatment, and k = −1 as reference.
  - *Callaway & Sant'Anna:* one comparison per cohort and period, base period the last observed before adoption, clean controls only, analytic variance with Welch-Satterthwaite degrees of freedom.
  - *RCT:* difference in means or Lin's adjustment, HC2.
  - *Matching:* Mahalanobis nearest neighbour with bias correction, Abadie-Imbens variance.
  - *IV:* 2SLS, first-stage F, Anderson-Rubin set.
  - *RDD:* local linear, IK bandwidth, robust bias-corrected interval.
  - *Synthetic control:* simplex weights, placebo-in-space p-value, no SE.
  - *DML:* cross-fitted partialling out.
- **Assumptions.** Each method's identifying assumption, stated on its page. For TWFE DiD: parallel trends, no anticipation, no spillovers, and with staggered timing, effects that do not change over time.
- **Limits.**
  - A correct calculation is not a credible design.
  - DiD: with few clusters the interval is unreliable, and the app warns.
  - RDD: the manipulation check is a binomial comparison of counts, a simple stand-in for a density test.
  - Synthetic control: below 19 donors, no effect can reach 5%, and the app warns.
- **Interactions.** Called by the pages, the simulation, the stress tests, the report and the code generator through one registry, so that each runs a method the same way.
- **Validation.** Reference packages on committed data (`tests/test_external_reference.py`, `test_did_reference.py`), the published Card & Krueger result (`test_card_krueger.py`), a coverage study (`spike/estimator_validation_2026-10-31.md`), and hand-computed values (`test_statistical_corrections.py`).
- **Example.** Card & Krueger: ATT 2.75, SE 1.34, 95% interval 0.12 to 5.38, with 410 clusters.
- **Professor might ask.** Why cluster by unit? (Serial correlation within a unit; ignoring it over-rejects badly.) Why not always use Callaway & Sant'Anna? (With one adoption date it reduces to the same comparison; it needs clean controls and absorbing treatment.)

### robustness_engine/ (stress_test.py, method_stress.py, robustness.py)

- **Why it exists.** Because an estimate alone hides its weakest assumption.
- **Problem it addresses.** Looking for evidence against the design, on the data.
- **Inputs and outputs.** The data and the treatment date; PASS, WARNING or N/A per check, a qualitative summary, and a re-estimation table.
- **Logic.** Parallel trends: joint test of treated × pre-period terms, wild cluster bootstrap p-value at the 10% level. Anticipation: change between the last two pre-periods. Spillovers: adjacent against distant controls. Serial correlation and heterogeneity are reported, but concern inference and interpretation, not identification. Re-estimation: other windows, leave-one-unit-out, other comparison groups. Calibration in `spike/`.
- **Assumptions.** Each test has its own; Spillovers needs IDs that encode neighbours.
- **Limits.** A check that does not warn says little: at a bias of 47%, the pre-trend test warned in 14.2% of worlds.
- **Identification Strength was removed**, after being measured against the true bias: 91.7 at a bias of 21%, against 91.5 with no threat, and 72.5 at 320%. See `docs/IDENTIFICATION_STRENGTH.md`; the decision is yours to confirm.
- **Interactions.** Reads the estimators, and writes into the report.
- **Example.** Card & Krueger: 4 of 5 checks are N/A, and the summary is "insufficient".
- **Professor might ask.** Why 10% and not 5% for pre-tests? (Low power: a pre-test should err toward warning.)

### theory_engine/ and ui/theory_page.py

- **Why it exists.** To compare a causal estimate with what a behavioural model predicts. It is **outside the original brief**: be ready to say so.
- **Inputs and outputs.** A game from the catalogue or the editor, and data for calibration; an equilibrium, a predicted treatment effect, and a comparison verdict.
- **Logic.** First-order conditions and best responses, solved in closed form or numerically; parameters calibrated from data; QRE and GMM estimation.
- **Assumptions.** The model's functional forms and that agents play the equilibrium.
- **Limits.** Agreement with an estimate does not validate either one.
- **Interactions.** Takes a causal estimate from the estimators; otherwise separate from the claim of this project.
- **Example.** Cournot: a cost shift predicts a price change, compared with an estimate.
- **Professor might ask.** Why is this in a causal inference project? Answer plainly, and describe it as an extension.

### report_engine/

- **Why it exists.** So that an analysis can leave the app with its numbers and references intact.
- **Inputs and outputs.** The session; PDF, Word, LaTeX or Markdown.
- **Logic.** It reruns the same engines and types no number.
- **Limits.** Tables only, and only what has been run.
- **Example.** A staggered world gives the DiD, event study, Callaway & Sant'Anna and checks.
- **Professor might ask.** How do you know its numbers match? (`tests/test_report.py` compares them with the engines.)

### code_generator/

- **Why it exists.** So that results can be reproduced outside the app.
- **Inputs and outputs.** A column mapping; Python, R and Stata scripts.
- **Limits.** Python and R scripts were run; **Stata was not checked**.
- **Example.** The DiD script applies the same small-sample correction as the app.
- **Professor might ask.** Do they agree with the app? (Each header states the measured agreement.)

### data_connectors/ and utils/

- **Why they exist.** Connectors bring in external data; utils hold translation, project files, column mapping, data validation and references.
- **Inputs and outputs.** An API request or a file; a table and its provenance. A project file holds the design and data.
- **Limits.** ACLED was written to its documented API and **not run live**, since it requires an account. Connectors do not make the data suitable for a design.
- **Example.** A `.causallab` file saves a project; opening it restores the design.
- **Professor might ask.** Is data sent anywhere? (Locally, no. The online demo processes uploads on the host, and says so.)

### ui/ and app.py

- **Why they exist.** To let someone use the engines without writing code.
- **Logic.** None of their own: pages call the engines and show results, in English or French.
- **Example.** `ui/question_panel.py` shows the analysis as you type.
- **Limits.** The online free tier sleeps and has little memory.
- **Professor might ask.** Where would you put a new method? (An estimator, a world, then the registry; the page follows.)

## Part 3. Twenty hard questions

**1. In one sentence, what is the contribution?**
A simulation study of difference-in-differences, 1,000 worlds per level with a known true effect, judged by a rule fixed in advance (at most 10% bias, at least 90% coverage): with low diverging pre-trends DiD is already 47% biased, and the pre-trend test warns in only 14.2% of those worlds. If asked about the question screen: it is an extension, the front door that keeps students from picking the wrong method. On the set the professor saw, it was right 95% of the time when it said "causal" but caught 0.60 of causal questions against a target of 0.70; version 3 caught 0.83 on a third set, where version 2 would have caught 0.80. This order is the professor's, in writing, on 2026-11-09.

**2. Issue #1 asked for one method. Why are there eight?**
Be factual. The README records that you built beyond the brief on 2026-10-25, knowing it departed from that advice. DiD remains the only method under the full simulation study with the decision rule. Then state what your professor confirmed in writing on 2026-11-09: the DiD bias study is the main contribution, the question analysis an extension. The other methods are what the front door needs to say "not DiD here". Do not claim more than that.

**3. How much bias is too much?**
Give the rule, say that it is a judgement fixed for this design, and give the two weaknesses from Part 1: dependence on precision, and that it is only partly pre-specified.

**4. Why 10% rather than 5% or 20%?**
There is no theorem. With an effect of −0.50, 10% is 0.05, a size that would not change how the effect is read. At 5% (0.025) only the mildest levels would pass, and Monte Carlo noise (0.003) would still be small. At 20%, confounding at "high" (21%) would nearly pass with 82% coverage, which is why coverage is required too. It would be reasonable to report how the verdicts change under other thresholds.

**5. What does your rule do when the true effect is zero?**
It does not apply, and says so (`rule_applies`). Relative bias is undefined there. Judge absolute bias and the size of the test instead. This was a real defect, corrected on 2026-11-05.

**6. Coverage was 91.9% and you called it fine. Isn't that just failure below nominal?**
It is below 95%, and the rule tolerates that up to 90%. Bradley's liberal criterion for test size, carried over to coverage by duality, would ask 92.5%. The defense is that the rule sets a limit for "goes wrong too much", not for "perfect". Under a stricter criterion the anticipation row would fail earlier.

**7. Can a biased estimator have good coverage?**
Yes, if the bias is small relative to the SE or the interval is wide. Anticipation at "medium": 6.2% bias with 93.7% coverage. Hence two conditions.

**8. Would your conclusions hold with 1,000 units?**
Not as stated. The SE would shrink, so the same bias would produce worse coverage. The coverage verdicts depend on sample size. The relative-bias verdicts barely would, since bias does not shrink with n.

**9. What is the difference between bias and power?**
Bias is about being right on average; power is about detecting an effect. In the severe pre-trends scenario, the DiD rejects H0 100% of the time with an estimate of the wrong sign. High power can make a wrong answer look certain.

**10. A pre-trend test passes. Are parallel trends satisfied?**
No. It is a test about the past, with limited power: at "low" divergence it warns in 14.2% of worlds while the bias is already 47%. Estimating only after a passed test also changes the sampling distribution (Roth 2022); the page reports coverage conditional on passing.

**11. Why does TWFE fail with staggered adoption?**
Already-treated units act as controls. If effects change over time, those comparisons get wrong or even negative weights (Goodman-Bacon 2021). The app offers Callaway & Sant'Anna, which compares each cohort only with clean controls. In your scenario, the problem appears only at extreme growth, because a third of periods are spread across adoption dates and many units are never treated: that is specific to this design.

**12. Why did you remove the credibility scores? Isn't a ranking still a claim?**
Yes, it is a claim, but an argued one that can be challenged, and it holds only under stated conditions. A number such as 88 pretended to a measurement nobody made. The page says the order is qualitative and concerns internal validity.

**13. Why is an RCT above an RDD if your text says no method is always superior?**
Conditional on their conditions holding, the randomisation creates comparability across the whole sample, while RDD only near a cutoff and relies on continuity. A broken RCT (attrition, non-compliance) can be worse than a good RDD, and an RCT in a small selected sample may have less external validity.

**14. How do you know the analyser works?**
Report the three frozen evaluations (`docs/evaluation/REPORT.md`, `v2/REPORT.md`, `v3/REPORT.md`), failures included. On 172 published titles: causal recall 0.64, 0.60 and 0.83 for versions 1 to 3, each on its own set, so it fails its 0.70 bar twice and passes once; precision 0.95, 0.95 and 1.00; one causal question called non-causal in all; no wrong method. Say at once that version 2 would score 0.80 on the third set: the pass is mostly the set. Version 3 also fails the threshold bar (3 false positives for 2). Then the limits: labels by a single rater who wrote the analyser, English titles only, no implicit threshold, and a method metric whose form already encodes the design. A title gave a design clue in 5 of 72 cases, so the form does most of the work. Say that before you are asked.

**15. Couldn't you just tune it until the evaluation passes?**
That would destroy the measure. Each set is frozen by hash before its single run. A correction needs a new set, and each version got one. Version 3 was developed on 216 other titles only, frozen by commit, and only then were the test titles read; the test pool's hash was recorded before development. The same version 2 scores 0.60 on one set and 0.80 on another, which is why one run is never reported alone. The 23 published-study cases and the tests were used for development and prove nothing about generalisation.

**16. Why does an untouched form give no recommendation?**
Otherwise a question would receive DiD from defaults the researcher never gave, which is exactly a default method. A box lets you confirm that the defaults do describe your study.

**17. Can a researcher get a wrong recommendation by lying on the form?**
Yes. The gates check answers, not reality. Some diagnostics can later test it on data: a McCrary-type density check, balance tables, a first-stage F. The app is not a referee.

**18. The app can recommend an interrupted time series. Can it estimate one?**
No. It explains the design and points to it. This is a known gap, and you can say what would close it: a segmented regression with its checks and a validation in the same manner.

**19. What does "the application does not establish causal identification" mean concretely?**
Identification depends on assumptions about the world: exclusion, parallel trends, no manipulation. Data can sometimes refute them, never prove them. The app helps state and probe them; the argument belongs to the researcher.

**20. What would you do with six more months?**
A second rater for the labels, an evaluation on questions written by students, in French too, combined threats in the simulation, a sensitivity table for the decision rule, an ITS estimator, and a decision about the scope of the theory module.

## Practical check before the defense

- Open the Guided Demo and read the table aloud, row by row.
- Change `MAX_BIAS_SHARE` locally to 0.05 and see which verdicts change; revert it.
- Type five questions of your own into the app, including one you expect it to get wrong.
- Open `docs/evaluation/REPORT.md` and be able to explain one failure in detail.
- For each row of "Five quantities", give the definition without looking.

## References cited here and not in the app's bibliography

- Bradley, J. V. (1978). Robustness? *British Journal of Mathematical and Statistical Psychology*, 31(2), 144-152. https://doi.org/10.1111/j.2044-8317.1978.tb00581.x

An earlier version of this guide attributed a 40% standardised-bias marker to Collins, Schafer & Kam (2001). I could not verify it in a source I could read, so it was removed. Do not cite it unless you have checked the article.
