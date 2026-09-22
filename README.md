# Causal Lab

A small tool that lets someone with a panel dataset and a treatment date find out — with real numbers, not a guess — whether a difference-in-differences design is even appropriate for their data, and if so, run it correctly.

## 1. The demo

I open the app in the browser and upload a CSV: one row per unit per time period, a treatment date, and an outcome column. It shows a plot of average outcomes for treated and untreated units over time, with the treatment date marked. Below it, a diagnosis panel says "Parallel trends: questionable — pre-trend slope difference is 0.34, p = 0.02" and "Recommended: difference-in-differences, but check anticipation effects first." I click "Run DiD" and it shows a coefficient, a standard error, and a two-way fixed-effects regression table. I click "Break this design" and it re-runs the same estimator on a version of the data where I know the true effect is zero, so I can see whether the method still finds a false effect.

If I don't have real data, I click "Generate a synthetic world" first: it creates a panel with a known, chosen treatment effect, so I can check that the estimator recovers close to that number before trusting it on anything real.

## 2. The shape

```
in            a panel CSV (unit, time, outcome, treatment indicator) —
              real data or a synthetic dataset generated in-app with a
              known true effect
out           a diagnosis of whether parallel trends plausibly hold,
              a DiD coefficient with standard error, and a plot
on screen     upload or generate → see the pre/post trend plot and the
              diagnosis → run the estimator → see the result next to
              the true effect if the data was synthetic
```

## 3. The size

**First useful version does:**
- Generate a synthetic panel dataset with a chosen, known treatment effect (the "virtual world").
- Accept an uploaded CSV in the same panel shape.
- Plot treated vs. untreated average outcomes over time.
- Check pre-treatment trends and report a plain-language verdict ("plausible" / "questionable" / "violated") with the number behind it.
- Run a two-way fixed-effects DiD estimator and report the coefficient, standard error, and p-value.
- When run on synthetic data, show the estimate next to the true effect that was used to generate it.

**Not this term:**
- Event study / leads-and-lags estimator.
- IV, RDD, matching, synthetic control, RCT, DML.
- Automatic method recommendation across multiple designs (only DiD is supported; the app says so rather than pretending to choose between methods).
- "Break My Design" as a general stress-test suite — only the one specific check above (re-running on a zero-effect synthetic dataset) ships this term.
- Code generation (R / Python / Stata export).
- Bilingual interface — English only for v1; French labels can be added once the English version is stable, since translating a moving target wastes effort twice.
- Report export (PDF/Word/LaTeX).
- Connectors to external data sources (DHS, ACLED, WorldPop, etc.).
- Project persistence / saved sessions.

A person with a messy panel CSV and a treatment date can use this version alone: upload, see whether parallel trends look reasonable, get a DiD estimate. Nothing else needs to exist for that to be useful.

## 4. How we would know it works

- Given a synthetic dataset generated with a treatment effect of, say, 2.0, the DiD estimator reports a coefficient within a reasonable margin of 2.0.
- Given a panel CSV missing the treatment indicator column, the app reports an error naming that column instead of running.
- Given a synthetic dataset built with deliberately diverging pre-trends (violated parallel trends), the diagnosis panel flags it as "questionable" or "violated," not "plausible."

## 5. What could stop this

- **Statistical correctness under review.** I have used DiD in coursework but never implemented the estimator (and its standard errors) from scratch for arbitrary panel shapes — unbalanced panels, staggered treatment timing, and clustering are all places I could get the math wrong without noticing. I will validate every estimator against a known R/Python package (e.g., `linearmodels` or `fixest`) on the same synthetic data before trusting my own numbers.
- **Real data availability.** I don't yet have a real panel dataset I'm allowed to show in class. The demo will run on the synthetic "virtual world" generator by default; if I obtain a usable real dataset later (course data, a public panel dataset), I'll add it, but the project does not depend on it.
- **Scope creep.** The original version of this idea had ten modules and two languages. This README cuts it to one estimator and one diagnosis. If I find myself building anything from the "not this term" list before the four items above work reliably, that's the signal I've drifted.
