# Oral defense simulation

For Thierry. Have someone ask these in a random order, and answer without the page. For each one, you should be able to give the answer, the intuition, the example and a reply to the follow-up. Numbers are from the repository; check them if the code changes, and be ready to open the file.

## Causal inference fundamentals

### 1. What does "causal effect" mean here?
**Answer.** The difference between a unit's outcome with and without treatment, Y(1) − Y(0). We see only one of the two for each unit, so a causal claim always rests on an assumption about the one we do not see.
**Intuition.** Every design is a way of guessing the missing outcome. The designs differ in what licenses the guess.
**Example.** In my Virtual World I generate both Y0 and Y1, so the true effect is known. In real data it never is.
**Follow-up.** *What is an ATT, and why is it not an ATE?* The ATT averages over those treated, the ATE over everyone. They differ when those treated would respond differently.

### 2. What is identification, as opposed to estimation?
**Answer.** Identification asks whether the assumptions pin down the effect with infinite data. Estimation asks how to compute it from finite data.
**Intuition.** A perfect estimator of the wrong comparison is precisely wrong.
**Example.** Severe diverging pre-trends: a tight interval, a significant result, and the wrong sign.
**Follow-up.** *Can data prove identification?* No. Data can sometimes refute an assumption, never establish it.

## Difference-in-differences

### 3. Write the model and say what β is.
**Answer.** Y_it = α_i + γ_t + β D_it + ε_it. With two groups, two periods and a binary treatment, β is the change among the treated minus the change among the controls, and under parallel trends it is the ATT.
**Intuition.** The controls' change stands in for what the treated would have done.
**Example.** Card & Krueger: New Jersey's employment change minus Pennsylvania's, 2.75 FTE with SE 1.34 in the app.
**Follow-up.** *Why cluster by unit?* Outcomes of a unit are correlated over time. Ignoring it makes the SE too small (Bertrand, Duflo & Mullainathan 2004).

### 4. Why a t interval with G − 1 degrees of freedom?
**Answer.** With clusters, the effective sample is about the number of clusters. A t(G−1) reference is the common small-sample choice, as in Stata and fixest. I moved to it on 2026-11-07 after measuring that the normal interval covered 87.8% with 10 units, against 91.2% for t.
**Intuition.** Few clusters mean the variance itself is noisy, so the critical value must be larger.
**Example.** With 100 units the change is small (1.96 to 1.98): stored coverage moved from 94.5% to 94.9%, and no verdict changed.
**Follow-up.** *Does t fix few clusters?* No. With 4 treated of 40 it still covers only about 85%, so the app warns. A wild cluster bootstrap would be the next step.

## Parallel trends

### 5. What exactly is the assumption?
**Answer.** Without treatment, treated and control units' average outcomes would have changed by the same amount. It concerns an unobserved counterfactual after treatment.
**Intuition.** Treated and controls may differ in level, but not in direction of travel.
**Example.** In my study, a differential trend at the "low" level gives a bias of 47% of the effect.
**Follow-up.** *Is it scale-dependent?* Yes. Parallel in levels need not be parallel in logs, so it depends on how the outcome is measured.

### 6. The pre-trend test passes. Are you done?
**Answer.** No. It tests the past, with limited power. At "low" divergence it warns in only 14.2% of worlds while the bias is already 47%. Estimating only after a passed test also changes the sampling distribution (Roth 2022).
**Intuition.** Absence of evidence with a weak test is not evidence of absence.
**Example.** 858 of 1,000 worlds pass at "low"; 31.6% of their intervals cover the truth.
**Follow-up.** *So why run it?* It can catch large violations (84% warned at "high"). It is a filter for bad news, not a certificate. That is why the app now says "not rejected", not "plausible".

## Treatment timing, anticipation and spillovers

### 7. Why does staggered adoption threaten two-way fixed effects?
**Answer.** TWFE is a weighted average of 2 x 2 comparisons, some using already-treated units as controls. If effects change over time, those comparisons are contaminated (Goodman-Bacon 2021).
**Intuition.** A unit whose effect is still growing is not a clean control.
**Example.** With severe growth, bias is 6.9% and coverage 87.6% in my design. Callaway & Sant'Anna compares each cohort only with clean controls.
**Follow-up.** *Why is your staggered bias so small?* Adoption spans about a third of the periods and 70% of units are never treated, so clean comparisons dominate. This is specific to my design, not a general reassurance.

### 8. What is anticipation, and how does it bias DiD?
**Answer.** Units react before treatment starts, here one period early, in the direction of the effect. The pre-period baseline is then already affected, so the post-minus-pre change is understated.
**Intuition.** You are comparing against a contaminated "before".
**Example.** At "high", bias is 11.2% of the effect and coverage 91.5%: it fails on bias only.
**Follow-up.** *How would you fix it?* If its length is known, drop or shift the anticipation periods out of the baseline.

### 9. What do spillovers do?
**Answer.** They break the assumption that one unit's treatment does not affect another (SUTVA). Controls near treated units absorb part of the effect, so the comparison is contaminated. The check compares adjacent and distant controls, and only runs where unit IDs encode neighbours, meaning the Virtual World.
**Intuition.** If the comparison group is partly treated, the difference shrinks.
**Example.** On real data this check is N/A: I do not pretend to know who neighbours whom.
**Follow-up.** *Are spillovers in your simulation study?* No. They are in the simulator and the check, not in the four threats of the stored study.

## Effect heterogeneity

### 10. Issue #1 named effect heterogeneity. Is it in your study?
**Answer.** Partly, and I should be precise. Heterogeneity over time since adoption is in the study, as the staggered threat. Heterogeneity across units is in the simulator (`treatment_heterogeneity`) but is **not** one of the study's threats. I have asked whether to add it [state what the professor answered].
**Intuition.** With a single adoption date, heterogeneity across units does not bias the ATT; it matters mainly with staggered timing or for external validity.
**Example.** The Heterogeneous Effects check compares the variance of changes in the two groups. A warning there no longer counts against identification.
**Follow-up.** *What would you expect?* Little bias with one date, by the argument above, but that is a prediction until it is simulated.

## Relative bias, coverage, power

### 11. Define bias, relative bias and coverage, and say how each is computed.
**Answer.** Bias: mean of (estimate − truth) over worlds. Relative bias: |bias| / |truth|. Coverage: share of worlds whose interval contains the truth, each with a Monte Carlo SE, about 0.003 and 0.9 points here. `simulation_engine/demo_study.py`.
**Intuition.** Bias is about where the estimator centres; coverage is about whether the uncertainty it reports is honest.
**Example.** Staggered "severe": 6.9% relative bias, fine by that half, yet 87.6% coverage, so it fails.
**Follow-up.** *Why report Monte Carlo SEs?* A simulation is an estimate too (Morris, White & Crowther 2019).

### 12. What does your rule do with a true effect of zero?
**Answer.** It does not apply. Relative bias is undefined, the code returns NaN and no scenario is called acceptable. I judge absolute bias and size instead. With zero effect, simulated rejection is about 5% and bias indistinguishable from zero. The old code would have divided by zero.
**Intuition.** "10% of nothing" is nothing, so any error would fail.
**Example.** Near zero it is also misleading: a bias of 0.01 on an effect of 0.02 is 50%, yet negligible.
**Follow-up.** *Where is "too close to zero"?* The code only guards numerically. There is no principled line, so report absolute bias alongside whenever the effect is small.

### 13. Why does the same 10% bias give different coverage in different samples?
**Answer.** Coverage depends on bias relative to the SE, not relative to the effect. A larger sample shrinks the SE, not the bias. See `spike/bias_coverage_check_results.md` for simulated values at 100 and 400 units, 92.2% and 82.8%.
**Intuition.** A sharper instrument aimed slightly off misses more often.
**Example.** Real threat: anticipation at "high" keeps its bias at 400 units, with coverage falling from 91.5% to 76.9%.
**Follow-up.** *So is your rule universal?* No. The verdicts hold for this design: 100 units, 20 periods.

### 14. Why 10% and 90%, and not other numbers?
**Answer.** They are my judgement, not theorems. 10% of −0.50 is 0.05, which would not change how the effect is read. 90% means an interval that misses at most twice as often as promised. Bradley's (1978) liberal robustness criterion, for test size, allows 0.5α to 1.5α, which by the duality of tests and intervals would mean 92.5% at α = 0.05. So my line is more permissive, and I say so.
**Intuition.** A line has to be drawn somewhere, and drawing it openly beats hiding it.
**Example.** Under 92.5%, confounding "medium" (92.2%) would fail too.
**Follow-up.** *Was it pre-specified?* Partly: after seeing the pre-trends results, before the other threats.

### 15. What is power, and why is high power not reassuring?
**Answer.** The probability of rejecting no effect when there is one. It says nothing about whether the estimate is right.
**Intuition.** A biased estimator can be very sure of the wrong thing.
**Example.** Severe pre-trends: rejection 100%, wrong sign 100%.
**Follow-up.** *What is your power with no threat?* 99.8%, since the effect is about 5 SEs. That design choice makes coverage, not power, the informative measure.

### 16. Do the 10% and 90% criteria validate the app?
**Answer.** No. They evaluate the DiD simulation study only. They do not control the app, determine recommendations, validate the question analyser, establish real-world estimates, or apply to the other methods.
**Intuition.** They answer "under which violations does this estimator go wrong?", and only where the truth is known.
**Example.** On Card & Krueger the rule says nothing, since the truth is unknown.
**Follow-up.** *And the other methods?* Validated against reference packages and by Monte Carlo coverage, with no such rule.

## Simulation design

### 17. What is weak about your simulation?
**Answer.** One design; threats varied one at a time and never combined; linear trends and normal noise; a large effect relative to noise; level names that are my own scale.
**Intuition.** Clean simulations show mechanisms, not real-world frequencies.
**Example.** Real data can combine confounding and anticipation. I have no result on that.
**Follow-up.** *How is it reproducible?* Seed base + r, every replication stored, and the page re-runs them and compares. The interval was migrated on 2026-11-07 without re-simulation, since it is a function of the stored estimate and SE.

## Question interpretation and ambiguity

### 18. How does the analyser read a question, and why not use a language model?
**Answer.** Regular expressions in reusable families, English and French, keeping the words behind each conclusion. My choice: local, reproducible, traceable, and data stay on the machine. The cost is coverage of wordings.
**Intuition.** It reads grammar, not meaning. It cannot understand what it has no pattern for.
**Example.** "Does job insecurity deteriorate health?" is read as ambiguous, because "deteriorate" is not on the list.
**Follow-up.** *So what happens then?* It asks, and the researcher ticks a box. A wrong "not causal" is the error to avoid, and a false causal reading too.

### 19. What happens with "Is X associated with Y?"
**Answer.** Ambiguous: it abstains, marks X and Y "to confirm", and asks for the aim. It does not call it causal, and it does not call it non-causal.
**Intuition.** An association may be meant causally or not; only the researcher knows.
**Example.** "Is earnings quality associated with CSR?" read this way in the evaluation.
**Follow-up.** *And "Does X predict Y"?* Predictive, even if the authors mean causality, as in "Does Corporate Governance Predict Firms' Market Values?". Labels concern wording, and the box covers that case.

## RDD and thresholds

### 20. How does it recognise a possible RDD, and does it then recommend one?
**Answer.** It separates an assignment rule ("eligibility at age 65"), a number of unclear role ("a BMI over 30") and an ordinary threshold ("threshold effect"). A rule only infers an assignment, and asks whether it is sharp and can be manipulated. RDD needs the form too.
**Intuition.** A number is not a discontinuity: something must jump at it, and nothing else may.
**Example.** "Does a BMI over 30 raise mortality?" asks about the role of the value and holds every method back.
**Follow-up.** *Is this validated?* Implicit thresholds, no: neither evaluation set has one. That is a gap, and development tests cover it only.

## Method recommendation and assumptions

### 21. How is a method chosen, and why no scores?
**Answer.** Each method must first pass its necessary conditions. Those that do are put in an argued order. Hand-set numbers like RCT 98 suggested a precision nobody had established, so they were removed.
**Intuition.** You can challenge an argument; you cannot challenge an 88.
**Example.** One treated state and 15 pre-periods: synthetic control before DiD, since its counterfactual is explicit and its fit can be inspected.
**Follow-up.** *Isn't the order still a claim?* Yes, and an arguable one: a strong instrument can beat a DiD with doubtful trends. The page says so.

### 22. Why did you remove Identification Strength?
**Answer.** I measured it next to the true bias. It reads 91.7 where the DiD is biased by 21%, against 91.5 with no threat, and 72.5 at 320%. It also counted serial correlation and heterogeneity, which are not threats to identification. It is now a qualitative summary that never says "valid" (`docs/IDENTIFICATION_STRENGTH.md`).
**Intuition.** A number that does not move with the error is not measuring it.
**Example.** Card & Krueger read 100/100 on one check. It now reads "insufficient": the data say nothing about parallel trends.
**Follow-up.** *Couldn't you reweight it?* Any weights would need a basis, and passing these checks cannot establish validity anyway.

## Evaluation design and independent validation

### 23. How do you know the analyser works?
**Answer.** Three frozen evaluations on 172 published titles, one per version. Causal recall is 0.64, 0.60 and 0.83 against a bar of 0.70; but version 2 scores 0.80 on the third set, so the pass is mostly the set, not the code. Precision 0.95 to 1.00, one causal question called non-causal in all, no wrong method given a form. Version 3 fails the threshold bar (3 false positives for 2); two were bugs, corrected in version 3.1, which is not evaluated. So it rarely overclaims and often abstains. The labels are from one rater who wrote the analyser, so these are provisional until a second rater checks them [state the kappa if one exists].
**Intuition.** I report the failure because the bar was set before the run.
**Example.** A title gave a design clue in only 5 of 72 cases, so the form does most of the work.
**Follow-up.** *Why not tune until it passes?* The set would stop measuring generalisation. Any new version needs a new set.

### 24. What is kappa, and what are its limits?
**Answer.** Agreement beyond chance: (p_o − p_e)/(1 − p_e). With unbalanced categories it can be low despite high agreement (Feinstein & Cicchetti 1990), so I report raw and per-category agreement too.
**Intuition.** If almost everything is "causal", agreeing on it is unimpressive.
**Example.** 90% agreement can give a kappa of 0; this is tested in `test_compute_kappa.py`.
**Follow-up.** *Does it validate the analyser?* No. It says how well-defined the labels are.

## Software architecture

### 25. Walk me through the architecture.
**Answer.** Pages hold no statistics. `causal_engine` reads and recommends; `estimators` estimates; `simulation_engine` generates known truths; `robustness_engine` tries to break designs; `report_engine` rebuilds everything, typing no number. Tests run in CI on the newest and minimum versions.
**Intuition.** Each number should have one source.
**Example.** A review on 2026-11-07 found the event study's SE at 0.402 against the DiD's 0.284 on the same model. It had bypassed the shared correction, and a test now compares them.
**Follow-up.** *What else did that review find?* A crash on empty cells, Callaway & Sant'Anna failing on biennial data and accepting a treatment that switches off.

## Limitations of Causal Lab

### 26. What can this app not do?
**Answer.** It cannot establish identification. It cannot detect a false answer on the form. It has no ITS estimator, though it can recommend ITS. It reads wording, not meaning. French and implicit thresholds are unvalidated. No student has tested it yet [update after the tests]. The theory module is outside the original brief.
**Intuition.** It is an aid to research design, not a referee.
**Example.** If a researcher declares a random assignment that was not random, the app recommends an RCT.
**Follow-up.** *What would you do next?* A second rater, students' questions as a new set, combined threats, a sensitivity table for the decision rule, and an ITS estimator.
