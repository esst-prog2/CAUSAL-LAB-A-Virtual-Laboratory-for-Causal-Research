#### The idea

Treatment is decided, or strongly encouraged, by whether a **running variable** $X$ crosses a known **cutoff** $c$. Examples are an exam score above the scholarship line, or an income below an eligibility threshold. Units just below and just above the cutoff are alike in everything except the treatment, so the jump in the outcome at the cutoff is the effect of the treatment there.

#### What it estimates

- **Sharp design**, where everyone above the cutoff is treated: the effect at the cutoff, $\tau = E[Y(1) - Y(0) \mid X = c]$.
- **Fuzzy design**, where crossing the cutoff only changes the probability of treatment: the ratio of the jump in the outcome to the jump in treatment. This is the effect for **compliers** at the cutoff, the units whose treatment status the cutoff changes.

In both cases the effect is **local**: it says nothing about units far from the cutoff.

#### What it rests on

- **Continuity.** Without treatment, the expected outcome would change smoothly through the cutoff.
- **No precise manipulation.** Units cannot place themselves exactly on the favourable side of the cutoff. If they can, those just above differ systematically from those just below.
- **A real, known cutoff** that is not shared by other policies at the same point.
- **Fuzzy design only:** monotonicity (crossing the cutoff never makes a unit less likely to be treated) and exclusion (the cutoff affects the outcome only through treatment).

#### What Causal Lab does

- **Estimator.** Local linear regression on each side of the cutoff with a triangular kernel. The default bandwidth $h$ is the MSE-optimal bandwidth of Imbens and Kalyanaraman. The fuzzy estimate is the local Wald ratio.
- **Inference.** By default, the robust bias-corrected interval of Calonico, Cattaneo and Titiunik (2014): the bias is estimated with a local quadratic, and the interval accounts for that estimation. The conventional interval is also reported. Standard errors are HC1 on each side; the fuzzy variance uses the delta method.
- **Diagnostics.**
  - Estimates at $h/2$ and $2h$, for sensitivity to the bandwidth.
  - Placebo cutoffs, in the stress test on the Causal Methods page, at the median of the running variable on each side, where there should be no jump.
  - In a fuzzy design, the first-stage jump and its $F$ statistic.
  - A manipulation check: the density test of Cattaneo, Jansson and Ma (2020), run with the authors' package `rddensity`. In a simulation of 500 worlds per scenario it raised a false alarm 4.0% of the time, and detected sorting more often than the simple count comparison it replaced. If the test cannot run on the data, Causal Lab falls back to a binomial test of the counts near the cutoff and says so.

#### When it fails

- **Sorting at the cutoff.** Bunching of observations just above the line is the classic sign.
- **Another discontinuity at the same cutoff**, such as a second programme using the same threshold.
- **Too few observations near the cutoff.** The estimate then rests on functional form, and the interval is wide.
- **Extrapolation.** A local effect at $c$ read as an average effect for everyone.
