# Second rater: procedure and Cohen's kappa

**Status: no second rating exists yet, so no kappa has been computed.** The labels of both evaluation sets come from one rater, the agent that wrote the analyser.

## Choosing and briefing the rater

Choose someone who has taken a course in causal inference or econometrics and has not worked on the analyser. Then:

1. Send **only** `rater_sheet.csv` (and `v2/rater_sheet.csv` if you want both sets), with the instructions below. Do not point to the repository: `question_set.json` holds the labels and `results.json` the answers.
2. Ask the person not to use the app, and not to look the papers up. The labels concern the wording of each title.
3. Do not discuss any question before the sheet is returned.
4. Keep the returned file unchanged, under a new name such as `rater_sheet_filled.csv`.

## Instructions for the rater

> You will see titles of published articles, each phrased as a question. For each one, decide what the wording of the title asks. Do not look the article up. Work alone, and do not revise your answers after finishing. There are no trick questions, and it should take about 30 minutes.
>
> **Intent column: write exactly one word.**
> - **causal**: it asks what something does to something else ("does X reduce Y", "the effect of X on Y", "is X a cause of Y").
> - **predictive**: it asks whether something can be predicted or forecast.
> - **descriptive**: it asks how much, how many or what happened, with no cause named.
> - **ambiguous**: it asks about an association, a relationship, a difference between groups, or "why" without naming a change, or you cannot tell.
>
> **Threshold column: write exactly one word.** Does the title describe a value or rule that decides who is treated?
> - **yes**: an eligibility rule, a cutoff that assigns treatment, a close election, or a named regression discontinuity.
> - **unclear**: a number or threshold whose role you cannot tell.
> - **no**: none, or an ordinary threshold that assigns nothing.

The instructions leave out the rule for mixed titles written for version 2 (`v2/PROTOCOL.md`), so that the rater decides those cases freely. Report them as disagreements if they differ.

## Computing the agreement

```bash
python spike/compute_kappa.py docs/evaluation/rater_sheet_filled.csv docs/evaluation/question_set.json
```

The script refuses a sheet with any blank or invalid cell. It reports the number of questions, raw agreement, chance agreement, Cohen's kappa, PABAK, agreement per category, the most frequent confusions and every disagreement.

## What to report

- Number of questions rated, raw agreement and kappa, for intent and threshold separately.
- Each disagreement, with the two labels.
- The categories with the most disagreement.

## After the rating

- **Do not overwrite the frozen labels.** They stay as the first rater's.
- If disagreements are worth settling, the two raters discuss them and record the settled labels in a separate file, with the reason for each.
- Rescoring the frozen results with settled labels makes a **second, declared analysis**. It does not replace the first, and the analyser must not be touched.

## Reading kappa

Kappa is agreement beyond chance: κ = (p_o − p_e) / (1 − p_e), where p_o is observed agreement and p_e is the agreement expected if each rater labelled independently with their own category frequencies (Cohen, 1960).

**Do not read it alone.**

- **Prevalence.** When one category dominates, chance agreement is high and kappa falls, even with high raw agreement (Feinstein & Cicchetti, 1990). In a 2 x 2 example, 90% agreement can give a kappa of zero (`tests/test_compute_kappa.py`). The sets here are unbalanced: 33 of 56 causal in the first, and almost no thresholds. So report raw agreement and per-category agreement with kappa. PABAK (Byrt, Bishop & Carlin, 1993) is given as a contrast, since it assumes balanced categories, which is also not true here.
- **Bias.** Raters using a category at different rates also shift kappa.
- **Benchmarks.** Landis & Koch's (1977) labels ("substantial" for 0.61 to 0.80) were offered as convenient conventions, not derived results. Use them only with that caveat.
- **Precision.** With about 56 questions, the interval around kappa is wide. Report that it is imprecise, and avoid fine comparisons.
- **What it measures.** Agreement is not validity. Two raters can share the same misreading. Also, kappa says nothing about the analyser: it says how well-defined the labels are, and therefore how far to trust the scores against them.

## References

- Byrt, T., Bishop, J., & Carlin, J. B. (1993). Bias, prevalence and kappa. *Journal of Clinical Epidemiology*, 46(5), 423-429.
- Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological Measurement*, 20(1), 37-46.
- Feinstein, A. R., & Cicchetti, D. V. (1990). High agreement but low kappa: I. The problems of two paradoxes. *Journal of Clinical Epidemiology*, 43(6), 543-549.
- Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement for categorical data. *Biometrics*, 33(1), 159-174.
