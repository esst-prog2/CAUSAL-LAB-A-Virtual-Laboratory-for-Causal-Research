# Identification Strength: review and decision record

**Status: replaced by a qualitative summary on 2026-11-07, on the agent's judgement under your instruction to keep it only if defensible. The change is one commit, so you can revert it.** This record exists so that you can decide, and defend what you decide.

## What it was

`identification_strength` in `robustness_engine/stress_test.py`: 100 × (checks passed) / (checks that can be computed). It was shown as "N / 100" with a progress bar on Break My Design and in the report.

- **Variables.** For DiD, five PASS/WARNING verdicts with equal weight: parallel trends, anticipation, spillovers, serial correlation, heterogeneous effects. For the other methods, 2 to 4 checks.
- **Transparent and reproducible?** Yes: the formula is simple and seeded.
- **Calibrated?** In part: false alarms and detection per check are measured in `spike/`. The total was only ever checked on clean worlds (mean 92.8) and under severe threats (56 to 76).

## Why it was not defensible

**1. It does not track the error it appears to measure.** `spike/identification_score_check_results.md`, 200 worlds per row, true effect −0.50:

| Scenario | Mean score | Worlds at 80 or more | Bias as a share of the effect |
|---|---|---|---|
| No threat | 91.5 | 96% | 0% |
| Confounding, high | 91.7 | 92% | 21% |
| Confounding, severe | 91.8 | 96% | 48% |
| Diverging pre-trends, low | 89.7 | 92% | 48% |
| Diverging pre-trends, medium | 84.1 | 86% | 112% |
| Diverging pre-trends, severe | 72.5 | 66% | 320% |

A world where the DiD is off by half the effect scores as high as a clean one. A world with the wrong sign still scores 72.

**2. It counts things that are not threats to identification.**
- Serial correlation affects standard errors, and clustering by unit already addresses it.
- Effect heterogeneity does not bias a non-staggered DiD: it still estimates an ATT.

Yet a warning on either lowers "identification strength".

**3. Equal weights have no basis.** Nothing says that a failed anticipation check matters as much as failed parallel trends.

**4. The denominator changes with the data.** Card & Krueger read 100/100 on 1 of 5 checks, that check being heterogeneity, which says nothing about parallel trends.

**5. It invites the wrong reading.** "92 / 100" with a progress bar looks like a probability that the design is valid. A disclaimer under a number does not undo that.

## The options

| | For | Against |
|---|---|---|
| **A. Remove any summary** | Nothing to misread; the per-check verdicts remain | A reader gets no synthesis, and must work out which checks concern identification |
| **B. Keep a number with a rubric** | Familiar, compact | Every weight would need a theoretical or empirical basis. None exists, and the table above is evidence against. **Not recommended** |
| **C. Qualitative summary** | Says what the checks can honestly say, and separates identification from inference | Categories can still be over-read; "no warning" must not sound like "valid" |

The names proposed in your brief ("strong identification conditions", "conditional", "weak") were not used. Passing these checks cannot establish strong conditions: the table above is the proof. The categories say what the checks found, not how strong the design is.

## What was done (option C)

`summary_of_checks`, from the checks aimed at the identifying assumption only:

| Category | When | What the page says |
|---|---|---|
| `warning` | At least one such check warned | Treat the estimate as doubtful until that threat is ruled out |
| `no_warning` | At least one computed, none warned | This is not evidence of validity: such checks can miss serious violations |
| `insufficient` | None could be computed | They say nothing about it |

- **DiD identification checks:** parallel trends, anticipation, spillovers.
- **Other methods:** `IDENTIFYING_CHECKS` in `robustness_engine/method_stress.py`.
- The per-check verdicts stay as they were.
- `identification_strength` remains in the code only for the calibration spikes, whose stored results use it. The app does not show it.
- The calibration test now asks that at least 65% of clean worlds raise no identifying warning. Three tests at the 10% level would leave about 73%.

**Limit.** Which checks count as "aimed at the identifying assumption" is itself a judgement, listed in the code so that it can be challenged.

## Your decision

Keep it, go to option A, or revert. If you revert, the table above is what a jury can ask you about.
