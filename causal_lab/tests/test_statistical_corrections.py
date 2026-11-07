"""The statistical review of 2026-11-07: each defect it found, with a value that can
be checked by hand or against a theorem, and what must stay as it was."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from scipy import stats

from causal_engine.diagnosis import ResearchDesignInput, diagnose
from causal_engine.recommendation import recommend
from estimators.did import estimate_did
from estimators.event_study import estimate_event_study
from estimators.staggered_did import estimate_staggered_did
from simulation_engine.dgp import VirtualWorldConfig, generate
from utils.i18n import LocalizedError


def _keys(result):
    return [m.key for m in result.warnings]


def test_empty_cells_do_not_crash_the_did_and_are_left_out():
    df, _ = generate(VirtualWorldConfig(seed=1))
    holed = df.copy()
    holed.loc[5, "Y"] = np.nan
    result = estimate_did(holed)
    assert result.n_obs == len(df) - 1
    assert abs(result.att - estimate_did(df.drop(index=5)).att) < 1e-12
    event = estimate_event_study(holed, fixed_treatment_period=10)
    assert event.n_obs == len(df) - 1


def test_the_interval_is_student_t_with_g_minus_one_degrees_of_freedom():
    df, _ = generate(VirtualWorldConfig(n_units=12, n_periods=6, treatment_period=3, seed=2))
    r = estimate_did(df)
    assert r.n_clusters == 12
    half = stats.t.ppf(0.975, 11) * r.se
    assert abs(r.ci_high - r.att - half) < 1e-10 and abs(r.att - r.ci_low - half) < 1e-10
    assert abs(r.p_value - 2 * stats.t.sf(abs(r.att / r.se), 11)) < 1e-12


def test_event_study_and_did_agree_when_they_are_the_same_model():
    # With two periods, the one event-study coefficient is the DiD: same estimate, same SE.
    df, _ = generate(VirtualWorldConfig(n_units=100, n_periods=4, treatment_period=2, seed=3))
    two = df[df["period"].isin([1, 2])]
    did = estimate_did(two)
    row = estimate_event_study(two, fixed_treatment_period=2).coefficients.query("rel_period == 0").iloc[0]
    assert abs(row["estimate"] - did.att) < 1e-10 and abs(row["se"] - did.se) < 1e-10
    assert abs(row["ci_low"] - did.ci_low) < 1e-10 and abs(row["ci_high"] - did.ci_high) < 1e-10


def test_few_clusters_non_binary_treatment_and_reversal_are_said():
    df, _ = generate(VirtualWorldConfig(n_units=20, n_periods=6, treatment_period=3, seed=4))
    assert "warn.did_few_clusters" in _keys(estimate_did(df))
    many, _ = generate(VirtualWorldConfig(seed=4))
    assert _keys(estimate_did(many)) == []
    few_treated, _ = generate(VirtualWorldConfig(n_units=40, share_treated=0.1, seed=4))
    assert "warn.did_few_clusters" in _keys(estimate_did(few_treated))
    continuous = many.assign(D=many["D"] * 2.5)
    assert "warn.did_not_binary" in _keys(estimate_did(continuous))
    off = many.copy()
    off.loc[(off["treated_unit"] == 1) & (off["period"] >= 15), "D"] = 0
    assert "warn.did_reversal" in _keys(estimate_did(off))


def _biennial():
    # Periods 0, 2, 4. Cohort g = 2: two units; never treated: two units. Effects by hand:
    # cohort changes from period 0: +3 and +5 at t = 2 (mean 4), control changes +1 and +1.
    rows = []
    paths = {"a": (0, 3, 3), "b": (0, 5, 5), "c": (0, 1, 2), "d": (0, 1, 2)}
    for unit, ys in paths.items():
        for t, y in zip((0, 2, 4), ys):
            rows.append(dict(unit=unit, period=t, Y=float(y), D=int(unit in "ab" and t >= 2)))
    return pd.DataFrame(rows)


def test_callaway_santanna_uses_the_last_observed_period_before_adoption():
    r = estimate_staggered_did(_biennial())
    gt = r.group_time.set_index("period")["att"]
    # ATT(2, 2) = (3 + 5) / 2 - 1 = 3; ATT(2, 4) = (3 + 5) / 2 - 2 = 2; overall 2.5.
    assert gt[2] == 3 and gt[4] == 2 and r.att == 2.5 and r.n_cohorts == 1


def test_callaway_santanna_with_every_second_period_recovers_the_effect():
    df, truth = generate(VirtualWorldConfig(n_units=300, n_periods=20, treatment_period=10, staggered_adoption=True,
                                            seed=4))
    biennial = estimate_staggered_did(df[df["period"] % 2 == 0])
    assert biennial.ci_low <= truth["true_att"] <= biennial.ci_high


def test_yearly_results_are_unchanged_by_the_base_period_rule():
    # On consecutive periods the last period before g is g - 1: the rule changes nothing.
    df, _ = generate(VirtualWorldConfig(n_units=60, staggered_adoption=True, seed=6))
    r = estimate_staggered_did(df)
    g, t = r.group_time.iloc[-1][["cohort", "period"]]
    wide = df.pivot(index="unit", columns="period", values="Y")
    first = df[df["D"] == 1].groupby("unit")["period"].min()
    members = first.index[first == g]
    never = df.loc[df["treated_unit"] == 0, "unit"].unique()
    by_hand = (wide.loc[members, t] - wide.loc[members, g - 1]).mean() - (wide.loc[never, t] - wide.loc[never, g - 1]).mean()
    assert abs(r.group_time.iloc[-1]["att"] - by_hand) < 1e-10


def test_callaway_santanna_refuses_a_treatment_that_switches_off():
    df, _ = generate(VirtualWorldConfig(n_units=60, staggered_adoption=True, seed=7))
    off = df.copy()
    off.loc[(off["treated_unit"] == 1) & (off["period"] >= 18), "D"] = 0
    try:
        estimate_staggered_did(off)
    except LocalizedError as error:
        assert error.msg.key == "err.cs_not_absorbing"
        return
    raise AssertionError("a treatment that switches off must be refused")


def test_units_treated_from_the_first_period_are_counted():
    df, _ = generate(VirtualWorldConfig(n_units=60, staggered_adoption=True, seed=8))
    early = sorted(df.loc[df["treated_unit"] == 1, "unit"].unique())[:3]
    d = df.copy()
    d.loc[d["unit"].isin(early), "D"] = 1
    r = estimate_staggered_did(d)
    assert r.n_always_treated == 3 and 0 not in set(r.group_time["cohort"])


def test_did_with_self_selection_says_why_parallel_trends_are_doubtful():
    design = ResearchDesignInput(assignment_mechanism="self_selected", n_pre_periods=4, answers_confirmed=True)
    did = next(r for r in recommend(design, diagnose(design)) if r.key == "did")
    assert "rec.note.did_self_selected" in [m.key for m in did.rationale]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("test_statistical_corrections: OK")
