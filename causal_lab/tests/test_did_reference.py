"""DiD validated against a reference package (README section 5, first
risk): our two-way fixed-effects estimate and clustered SE must match
linearmodels' PanelOLS with entity and time effects."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from linearmodels.panel import PanelOLS

from estimators.did import estimate_did
from simulation_engine.dgp import VirtualWorldConfig, generate


def _reference(df):
    panel = df.set_index(["unit", "period"])
    return PanelOLS(panel["Y"], panel[["D"]], entity_effects=True, time_effects=True).fit(
        cov_type="clustered", cluster_entity=True)


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
    test_did_recovers_true_effect_of_two()
    test_no_treatment_variation_raises()
    print("test_did_reference: OK")
