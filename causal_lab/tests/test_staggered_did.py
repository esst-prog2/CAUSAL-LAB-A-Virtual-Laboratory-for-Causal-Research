import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from estimators.did import estimate_did
from estimators.staggered_did import estimate_staggered_did
from simulation_engine.dgp import VirtualWorldConfig, generate

STAGGERED_DYNAMIC = dict(staggered_adoption=True, dynamic_effects="severe", share_treated=0.6)


def test_cs_recovers_truth_where_twfe_is_biased():
    cs_errors, twfe_errors = [], []
    for seed in range(12):
        df, truth = generate(VirtualWorldConfig(seed=seed, **STAGGERED_DYNAMIC))
        cs = estimate_staggered_did(df, n_bootstrap=49, seed=seed)
        cs_errors.append(cs.att - truth["true_att"])
        twfe_errors.append(estimate_did(df).att - truth["true_att"])
    print("CS bias:", np.mean(cs_errors), "TWFE bias:", np.mean(twfe_errors))

    def t_stat(errors):         # mean error in units of its own standard error
        return abs(np.mean(errors)) / (np.std(errors, ddof=1) / np.sqrt(len(errors)))

    assert t_stat(cs_errors) < 3            # no detectable bias
    assert t_stat(twfe_errors) > 5          # clearly biased
    assert abs(np.mean(twfe_errors)) > 2 * abs(np.mean(cs_errors))


def test_cs_matches_twfe_in_a_simple_design():
    df, truth = generate(VirtualWorldConfig(n_units=300, seed=2))
    cs = estimate_staggered_did(df, n_bootstrap=49)
    assert abs(cs.att - truth["true_att"]) < 3 * cs.se
    assert cs.n_cohorts == 1 and cs.comparison == "never_treated"


def test_event_study_aggregation_has_zero_reference():
    df, _ = generate(VirtualWorldConfig(seed=4, **STAGGERED_DYNAMIC))
    es = estimate_staggered_did(df, n_bootstrap=19).event_study
    assert -1 not in set(es["rel_period"])         # base period g-1 is the reference, never estimated
    post = es[es["rel_period"] >= 0]
    slope = np.polyfit(post["rel_period"], post["estimate"], 1)[0]
    assert slope < 0                                 # the (negative) effect grows with exposure


def test_not_yet_treated_used_when_everyone_is_treated():
    df, _ = generate(VirtualWorldConfig(seed=5, n_units=40, share_treated=0.9, staggered_adoption=True))
    # make every unit eventually treated
    df.loc[df["period"] == df["period"].max(), "D"] = 1
    cs = estimate_staggered_did(df, n_bootstrap=9)
    assert cs.comparison == "not_yet_treated"


def test_dynamic_effects_truth_is_mean_over_treated_cells():
    df, truth = generate(VirtualWorldConfig(seed=3, **STAGGERED_DYNAMIC))
    treated = df[df["D"] == 1]
    assert abs((treated["Y1"] - treated["Y0"]).mean() - truth["true_att"]) < 1e-12


if __name__ == "__main__":
    test_cs_recovers_truth_where_twfe_is_biased()
    test_cs_matches_twfe_in_a_simple_design()
    test_event_study_aggregation_has_zero_reference()
    test_not_yet_treated_used_when_everyone_is_treated()
    test_dynamic_effects_truth_is_mean_over_treated_cells()
    print("test_staggered_did: OK")
