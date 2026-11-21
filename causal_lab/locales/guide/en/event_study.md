#### The idea

An event study is difference-in-differences with **one coefficient per period relative to treatment**. It shows how the effect builds up after treatment. The coefficients before treatment show whether treated and control units were already drifting apart.

#### What it estimates

A path of dynamic effects $\beta_k$, for periods $k$ before ($k<0$) and after ($k \ge 0$) treatment, relative to a reference period, usually $k=-1$:

$$Y_{it} = \alpha_i + \gamma_t + \sum_{k \ne -1} \beta_k \, \mathbf{1}[t - T_{0i} = k] + \varepsilon_{it}.$$

Under parallel trends and no anticipation, $\beta_k$ for $k \ge 0$ is the ATT $k$ periods after adoption, and $\beta_k = 0$ for $k < -1$.

#### What it rests on

- **Parallel trends in every period**, not just on average.
- **No anticipation.**
- **With staggered adoption,** an estimator that does not compare treated cohorts with already-treated ones. Otherwise each $\beta_k$ can mix in effects from other periods (Sun and Abraham, 2021).

#### What Causal Lab does

- **Estimator.** Leads and lags with unit and period fixed effects, reference period $k=-1$, and relative periods binned at $\pm 6$. Never-treated units share the reference category.
- **Inference.** Standard errors clustered by unit, with the same small-sample convention as the DiD and a Student $t$ with $G-1$ degrees of freedom.
- **Staggered adoption.** The event-study aggregation of Callaway and Sant'Anna (2021) is available: each $ATT(e)$ is a cohort-size-weighted average of group–time effects, with an analytic interval.
- **Diagnostics.** The leads are plotted with their intervals. The joint test of the leads, with a wild cluster bootstrap $p$-value, runs on the Break My Design page. Causal Lab says plainly that a quiet pre-test does not establish parallel trends.

#### When it fails

- **Pre-trends that the leads are too noisy to detect.** The leads then look flat while the bias is large. This is the main result of the Guided Demo.
- **Two-way fixed effects under staggered timing and heterogeneous effects.** The coefficients can mix in effects from other periods, and the pre-period ones can show spurious "pre-trends".
- **Binned endpoints,** which absorb every period beyond the window into one coefficient.
