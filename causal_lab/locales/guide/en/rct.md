#### The idea

The researcher assigns the treatment by a chance mechanism, such as a coin flip, a lottery or a computer draw. Assignment is then independent of everything that could affect the outcome, observed or not. Treated and control groups differ only by chance and by the treatment, so a difference in their mean outcomes estimates the effect of the treatment.

#### What it estimates

The **average treatment effect** (ATE) in the study sample:

$$\tau = E[Y_i(1) - Y_i(0)],$$

where $Y_i(1)$ and $Y_i(0)$ are the outcomes unit $i$ would have with and without treatment. Only one of the two is ever observed; randomisation makes the groups exchangeable, so $E[Y \mid D=1] - E[Y \mid D=0] = \tau$.

#### What it rests on

- **Randomisation carried out as described.** Nobody chose, or could predict, who was treated.
- **No interference (SUTVA).** One unit's treatment does not change another unit's outcome.
- **Compliance and no differential attrition.** Units receive the treatment they are assigned, and outcomes are not missing more often in one group. When they are, the comparison of groups as assigned estimates the intention-to-treat effect, not the effect of the treatment received.

#### What Causal Lab does

- **Estimator.** The difference in means, from a regression of $Y$ on $D$. With baseline covariates, the regression-adjusted estimator of Lin (2013), with the covariates centred and interacted with $D$. It keeps the same estimand and is asymptotically never less precise than the difference in means.
- **Inference.** HC2 heteroskedasticity-robust standard errors and a 95% normal interval.
- **Diagnostics.** A balance table of standardised mean differences. A warning names every covariate whose difference exceeds 0.1. The stress test on the Causal Methods page runs a joint Wald test of whether the covariates predict assignment.

#### When it fails

- Assignment that was not random in practice, such as a manipulated list or a partial roll-out.
- Attrition that differs between the groups.
- Spillovers, such as vaccinated neighbours protecting the unvaccinated.
- A sample unlike the population of interest: the effect is internally valid but may not transport (external validity).
- Imbalance by chance in a small sample. Covariate adjustment helps, but does not repair a broken randomisation.
