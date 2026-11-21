#### The idea

If every variable that drives both treatment and outcome is measured, compare each treated unit with untreated units that look the same on those variables. Within such matched comparisons, treatment is as good as random.

#### What it estimates

Here, the **average treatment effect on the treated** (ATT):

$$\tau_{ATT} = E[Y(1) - Y(0) \mid D = 1].$$

#### What it rests on

- **Selection on observables (unconfoundedness).** $\{Y(0), Y(1)\} \perp D \mid X$. Treatment is independent of the potential outcomes once the covariates $X$ are fixed. This cannot be verified.
- **Overlap (common support).** For the ATT, every treated unit has comparable controls: $P(D=1 \mid X) < 1$.
- **Covariates measured before treatment.** Matching on a variable the treatment affects biases the estimate.

#### What Causal Lab does

- **Estimator.** Nearest-neighbour covariate matching with replacement, in Mahalanobis distance, with the bias correction of Abadie and Imbens (2011). The matched control's outcome is adjusted by a regression on $X$ among the controls used.
- **Inference.** The Abadie–Imbens (2006) variance for the ATT. The bootstrap is not used, because it is invalid for nearest-neighbour matching.
- **Propensity score.** A logit propensity score, for the overlap diagnostic and for an inverse-probability-weighting estimate, reported alongside with a bootstrap standard error.
- **Diagnostics.**
  - Standardised mean differences before and after matching, with a warning above 0.1.
  - The number of treated units outside the controls' propensity range.
  - The number of distinct controls used.

#### When it fails

- **An unmeasured confounder.** No balance table can reveal it. Sensitivity analysis, such as Rosenbaum bounds or E-values, asks how strong it would need to be.
- **Poor overlap.** Treated units with no comparable control force extrapolation.
- **Post-treatment covariates,** or "bad controls".
- **Many covariates with few controls.** Matches become inexact, and the bias correction carries more weight.
