#### The idea

A single series, such as monthly hospital admissions or yearly accidents, is observed for a long time before and after an intervention at a known date. The trend before the intervention is projected forward as the counterfactual. A change in **level** or **slope** at the intervention date is read as its effect.

#### What it estimates

The change in level and in trend at the intervention date, typically from a segmented regression:

$$Y_t = \beta_0 + \beta_1 t + \beta_2 \mathbf{1}[t \ge T_0] + \beta_3 (t - T_0)\,\mathbf{1}[t \ge T_0] + \varepsilon_t,$$

where $\beta_2$ is the immediate change in level and $\beta_3$ the change in slope.

#### What it rests on

- **The pre-intervention trend would have continued.** This includes its seasonality.
- **Nothing else changed at the same date,** such as another policy or a change in how the outcome is measured.
- **Enough points before and after,** and a model of autocorrelation and seasonality.

#### What Causal Lab does

**Advice only: Causal Lab has no interrupted time series estimator.** It considers the design when the question and the data fit it: one series, a known intervention date and no comparison group. It then states the assumptions above. To estimate, use a segmented regression with autocorrelation-robust (Newey–West) standard errors, or an ARIMA model with an intervention term. If a comparable unaffected series exists, difference-in-differences or a synthetic control is usually more credible.

#### When it fails

- **Another event at the intervention date.** Without a comparison group, nothing separates its effect from the intervention's.
- **Non-linear trends, seasonality or regression to the mean,** for example an intervention introduced because the outcome had just peaked.
- **Too few observations** to estimate the pre-intervention trend.
