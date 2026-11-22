#### The idea

Compare how the outcome **changes** over time in a group that receives the treatment with how it changes in a group that does not. The control group's change stands in for what would have happened to the treated group without treatment. Subtracting it removes everything that is fixed within units and everything that moves both groups alike.

#### What it estimates

The **average treatment effect on the treated** (ATT):

$$\tau_{ATT} = E[Y_{post}(1) - Y_{post}(0) \mid D = 1],$$

estimated in the two-group, two-period case by
$(\bar Y^{T}_{post} - \bar Y^{T}_{pre}) - (\bar Y^{C}_{post} - \bar Y^{C}_{pre})$.

#### What it rests on

- **Parallel trends.** Without treatment, treated and control units would have followed the same average trend. This is about an unobserved counterfactual and cannot be tested; trends before treatment only make it more or less plausible.
- **No anticipation.** Outcomes do not move before the treatment starts because units expect it.
- **No spillovers** onto the control units, and a **stable composition** of the groups.
- **With staggered adoption,** homogeneous effects over time and across cohorts, or an estimator that does not need them.

#### What Causal Lab does

- **Estimator.** Two-way fixed effects, $Y_{it} = \alpha_i + \gamma_t + \beta D_{it} + \varepsilon_{it}$.
- **Inference.** Standard errors clustered by unit (Bertrand, Duflo and Mullainathan, 2004), with the CR1 small-sample factor and the unit dummies not counted in it, as in Stata's `xtreg, fe`. The interval uses a Student $t$ with $G-1$ degrees of freedom, where $G$ is the number of clusters. The result warns when there are fewer than 30 clusters or fewer than 10 per arm.
- **Staggered adoption.** The heterogeneity-robust estimator of Callaway and Sant'Anna (2021) is available. It estimates one effect per adoption cohort and period against never-treated or not-yet-treated units, aggregates them, and uses an analytic variance with Welch–Satterthwaite degrees of freedom.
- **Diagnostics.**
  - The joint test of the pre-treatment leads, with a wild cluster bootstrap $p$-value.
  - Warnings for a non-binary treatment and for treatment that switches off.
  - The Guided Demo's simulation study: 4 threats × 5 levels × 1,000 worlds, judged by a rule fixed in advance, and a supplement with effects that differ across units.
- **Sensitivity to violations of parallel trends** (Estimation page, event-study tab). Following Rambachan and Roth (2023), the difference in trends may bend by at most $M$ per period. For each $M$, a fixed-length interval (Armstrong and Kolesár, 2018) covers the average post-treatment effect with probability at least 95% under every such violation; $M = 0$ allows exactly the linear trends seen before treatment. One treatment date and a balanced panel are needed. The estimator's weights are chosen with a working covariance and its standard error estimated from the units, because with few treated units the paper's choice on the estimated covariance under-covered (88.5% on 200 study worlds).

#### When it fails

- **Diverging pre-trends.** In the stored study, a low level of divergence gives a bias of 47% of the true effect and 31.3% coverage, while the pre-trend test warns in only 14.2% of worlds.
- **A passed pre-test is weak evidence.** Conditioning on it can make the bias worse (Roth, 2022). Rambachan and Roth (2023) show how to report results under bounded violations; Causal Lab does it on the Estimation page (see above).
- **Staggered timing with effects that change over time.** Two-way fixed effects then compare later adopters with earlier ones whose effects are still growing (Goodman-Bacon, 2021; de Chaisemartin and D'Haultfœuille, 2020).
- **Few treated clusters.** Clustered inference is then unreliable.
