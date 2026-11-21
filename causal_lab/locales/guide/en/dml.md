#### The idea

Double machine learning keeps the selection-on-observables assumption of matching, but lets flexible machine-learning models absorb how the covariates affect treatment and outcome. It then estimates the effect from what those models cannot explain. Cross-fitting, where each prediction comes from a model trained on other data, prevents over-fitting from biasing the estimate (Chernozhukov et al., 2018).

#### What it estimates

Causal Lab uses the **partially linear model**

$$Y = \theta D + g(X) + \varepsilon, \qquad D = m(X) + v.$$

$\theta$ is the effect if it is the same for everyone. When the effect varies with $X$, $\theta$ is a **variance-weighted average** of the conditional effects, weighting each $X$ by $\mathrm{Var}(D \mid X)$. It is then **not the ATE**; the interactive model targets the ATE instead.

#### What it rests on

- **Selection on observables,** as for matching: no unmeasured confounder.
- **Overlap.** Treatment varies at every value of $X$. If $m(X)$ predicts $D$ almost perfectly, there is nothing left to learn from.
- **Nuisance functions learned well enough.** The product of the errors in predicting $Y$ and $D$ must shrink fast enough, roughly faster than $n^{-1/2}$.

#### What Causal Lab does

- **Estimator.** 5-fold cross-fitting. In each fold, random forests (200 trees, minimum 5 observations per leaf) trained on the other folds predict $\ell(X)=E[Y \mid X]$ and $m(X)=E[D \mid X]$. $\theta$ is the slope of the outcome residuals on the treatment residuals (Robinson, 1988).
- **Inference.** A standard error from the influence function $\psi = (u - \theta v)\,v$, and a 95% normal interval.
- **Diagnostics.**
  - The cross-fitted $R^2$ of both models.
  - A warning when $R^2$ for the treatment exceeds 0.95, a sign of poor overlap.
  - The OLS coefficient with linear controls, for comparison.

#### When it fails

- **An unmeasured confounder.** Machine learning does not remove it.
- **Near-deterministic treatment** (poor overlap).
- **Reading $\theta$ as the ATE** when effects are heterogeneous.
- **One random split.** Results can move with the fold assignment. Repeating the cross-fitting and taking the median is the usual remedy; Causal Lab uses one fixed seed.
