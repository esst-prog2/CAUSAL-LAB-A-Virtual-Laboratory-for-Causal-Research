#### The idea

The treatment $D$ is confounded, but a variable $Z$, the **instrument**, shifts $D$ and has no other route to the outcome $Y$. The part of the variation in $D$ that comes from $Z$ is as good as random, so it identifies the effect. Classic instruments are lotteries, distance to a facility, and rules that change eligibility.

#### What it estimates

With a binary instrument and treatment, under monotonicity, the **local average treatment effect** (LATE), the effect for **compliers**, the units who take the treatment because of the instrument (Imbens and Angrist, 1994):

$$\tau_{LATE} = \frac{E[Y \mid Z=1] - E[Y \mid Z=0]}{E[D \mid Z=1] - E[D \mid Z=0]}.$$

With a constant effect, it is the effect of $D$ for everyone.

#### What it rests on

- **Relevance.** $Z$ moves $D$. This one can be tested.
- **Exclusion.** $Z$ affects $Y$ only through $D$. It cannot be tested and must be argued.
- **Independence.** $Z$ is as good as randomly assigned.
- **Monotonicity.** Nobody takes the treatment *less* because of the instrument (no defiers).

#### What Causal Lab does

- **Estimator.** Two-stage least squares with optional controls, and heteroskedasticity-robust standard errors. The OLS coefficient is shown for comparison.
- **Instrument strength.** The first-stage $F$ statistic and partial $R^2$. Below $F = 10$, the instrument is flagged as weak. With one instrument and $10 < F < 104.7$, the result says that the usual 5% $t$-test does not keep its size (Lee, McCrary, Moreira and Porter, 2022).
- **Weak-instrument-robust inference.** The Anderson–Rubin confidence set, valid however weak the instrument. It can be an interval, two unbounded rays, or the whole line when the instrument carries no information.
- **Over-identification.** With several instruments, the stress test on the Causal Methods page checks whether they agree. It cannot show that the exclusion restriction holds.

#### When it fails

- **Weak instruments.** 2SLS is then biased towards OLS, and its Wald interval is unreliable.
- **Exclusion violated.** For example, distance to a college may also affect wages through the local labour market.
- **Defiers,** which break the LATE interpretation.
- **Reading a LATE as an ATE.** Compliers may differ from the population.
