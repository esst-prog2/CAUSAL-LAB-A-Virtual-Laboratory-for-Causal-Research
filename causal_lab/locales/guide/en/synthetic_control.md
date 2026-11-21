#### The idea

When **one unit**, such as a country, a state or a city, is treated, build its counterfactual as a **weighted average of untreated donor units**. The weights are chosen so that the synthetic unit reproduces the treated unit's outcome path before treatment. After treatment, the gap between the treated unit and its synthetic twin estimates the effect.

#### What it estimates

The effect on the treated unit in each post-treatment period, $\tau_t = Y_{1t} - \sum_j w_j Y_{jt}$, with $w_j \ge 0$ and $\sum_j w_j = 1$. Causal Lab's headline number is the mean post-treatment gap.

#### What it rests on

- **A good pre-treatment fit** over a long enough period. Without one, the weights do not reproduce the treated unit's dynamics.
- **The fit carries over.** The same weights would have tracked the treated unit without treatment. This is plausible when the outcome is driven by common factors that the donors share.
- **No shock at the same date** to the treated unit only, and **no spillovers onto the donors**.
- **Convex hull.** The treated unit is not extreme, so a convex combination of donors can match it.

#### What Causal Lab does

- **Estimator.** The weights minimise the pre-treatment distance $\lVert y_{1,pre} - Y_{0,pre} w \rVert^2$ on the simplex. With covariates, the weights match standardised predictors instead, with an importance matrix $V$ chosen to minimise the pre-treatment prediction error (Abadie, Diamond and Hainmueller, 2010).
- **Inference.** Placebo-in-space permutation: every donor is treated in turn as if it were treated. The $p$-value is the rank of the treated unit's post/pre RMSPE ratio. No standard error is reported.
- **Diagnostics.**
  - The pre-treatment RMSPE, and a warning when the fit is poor.
  - The donor weights and the predictor balance.
  - A warning when there are fewer than 19 donors. The $p$-value cannot then fall below 5%, however large the effect.

#### When it fails

- A short or poorly fitted pre-period.
- Few donors, or donors affected by the policy or by spillovers.
- A treated unit outside the range of the donors.
- Reading the permutation $p$-value as a sampling-based test. It is a ranking among the observed units.
