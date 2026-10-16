"""DiD validated against a reference package (README section 5, first
risk): our two-way fixed-effects estimate and clustered SE must match
linearmodels' PanelOLS with entity and time effects.

Since hw6 review 3 the unit fixed effects nested in the clusters are not
counted in the small-sample correction (Stata xtreg/reghdfe convention).
PanelOLS is configured as close to that convention as it allows: G/(G-1)
(group_debias), no effect counted (auto_df=False, count_effects=False;
auto_df=True would silently override count_effects). It still does not
count the period dummies, hence the 2% tolerance. The exact convention is
checked separately against a CR1 sandwich written out by hand."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

from estimators.did import estimate_did
from simulation_engine.dgp import VirtualWorldConfig, generate


def _reference(df):
    panel = df.set_index(["unit", "period"])
    return PanelOLS(panel["Y"], panel[["D"]], entity_effects=True, time_effects=True).fit(
        cov_type="clustered", cluster_entity=True, group_debias=True, debiased=True,
        auto_df=False, count_effects=False)


def test_did_matches_panelols_point_estimate_and_clustered_se():
    for kwargs in (dict(), dict(staggered_adoption=True, treatment_heterogeneity="medium"),
                   dict(serial_correlation="high", n_units=60)):
        df, _ = generate(VirtualWorldConfig(seed=4, **kwargs))
        ours = estimate_did(df)
        ref = _reference(df)
        assert abs(ours.att - float(ref.params["D"])) < 1e-8, kwargs
        # statsmodels and linearmodels use slightly different small-sample
        # corrections for clustered SEs; they must agree to within 2%.
        assert abs(ours.se / float(ref.std_errors["D"]) - 1) < 0.02, (kwargs, ours.se, float(ref.std_errors["D"]))


def test_clustered_se_does_not_count_the_nested_unit_dummies():
    # CR1 = G/(G-1) * (N-1)/(N-K) * (X'X)^-1 (sum_g X_g'e_g e_g'X_g) (X'X)^-1,
    # with K excluding the unit dummies, which are nested in the clusters.
    df, _ = generate(VirtualWorldConfig(seed=4, n_units=40, n_periods=8, treatment_period=5))
    dummies = pd.get_dummies(df[["unit", "period"]].astype(str), drop_first=True, dtype=float)
    x = np.column_stack([np.ones(len(df)), df["D"].to_numpy(float), dummies.to_numpy()])
    y = df["Y"].to_numpy(float)
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    resid = y - x @ beta
    bread = np.linalg.inv(x.T @ x)
    meat = sum(np.outer(s, s) for s in (x[i].T @ resid[i] for i in df.groupby("unit").indices.values()))
    n, g = len(df), df["unit"].nunique()
    k = x.shape[1] - (g - 1)
    se = np.sqrt((bread @ meat @ bread)[1, 1] * g / (g - 1) * (n - 1) / (n - k))
    ours = estimate_did(df)
    assert abs(ours.att - beta[1]) < 1e-8
    assert abs(ours.se / se - 1) < 1e-8, (ours.se, se)
    assert abs(ours.ci_high - ours.ci_low - 2 * 1.959964 * ours.se) < 1e-5


def test_did_recovers_true_effect_of_two():
    df, truth = generate(VirtualWorldConfig(n_units=300, true_att=2.0, seed=11))
    result = estimate_did(df)
    assert abs(result.att - truth["true_att"]) < 3 * result.se


def test_no_treatment_variation_raises():
    df, _ = generate(VirtualWorldConfig(seed=1))
    df["D"] = 0
    try:
        estimate_did(df)
    except ValueError as exc:
        assert "no variation" in str(exc)
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    test_did_matches_panelols_point_estimate_and_clustered_se()
    test_clustered_se_does_not_count_the_nested_unit_dummies()
    test_did_recovers_true_effect_of_two()
    test_no_treatment_variation_raises()
    print("test_did_reference: OK")
