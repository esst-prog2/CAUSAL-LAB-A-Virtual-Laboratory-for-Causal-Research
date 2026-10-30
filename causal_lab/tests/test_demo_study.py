"""The Guided demo's evidence (spec: guided-demo).

- The Card & Krueger replication reproduces the published Table 3.
- The stored simulation study is the one the code computes: any
  replication recomputed from its seed gives the stored values.
- The summary statistics are the textbook ones (checked by hand).
- The claims the page makes in words hold in the stored study.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from streamlit.testing.v1 import AppTest

from simulation_engine.demo_study import (CARD_KRUEGER_TABLE3, LEVELS, SEED_BASE, THREATS, Replication,
                                          largest_acceptable, load_study, replicate, replicate_card_krueger, same,
                                          summarize)
from utils.real_data import load_card_krueger

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_card_krueger_table_3_is_reproduced():
    ours = replicate_card_krueger(load_card_krueger())
    mismatches = []
    for row, cols in CARD_KRUEGER_TABLE3.items():
        for col, (mean, se) in cols.items():
            our_mean, our_se = ours[row][col]
            assert abs(our_mean - mean) < 0.005 + 1e-9, (row, col, our_mean, mean)      # every mean, to 2 decimals
            if f"{our_se:.2f}" != f"{se:.2f}":
                mismatches.append((row, col, round(our_se, 3), se))
    # The one difference: NJ - PA after, SE 1.077 recomputed from the data vs 1.07 published. Combining the
    # published, rounded cell SEs gives sqrt(0.52^2 + 0.94^2) = 1.074, i.e. 1.07: a rounding difference.
    assert mismatches == [("fte_after", "diff", 1.077, 1.07)], mismatches
    assert round(float(np.hypot(0.52, 0.94)), 2) == 1.07
    assert round(ours["change_balanced"]["diff"][0], 2) == 2.75 and round(ours["change_balanced"]["diff"][1], 2) == 1.34


def test_summary_statistics_by_hand():
    reps = [Replication(seed=0, true_att=-0.5, estimate=e, se=0.1, ci_low=e - 0.196, ci_high=e + 0.196, p_value=p,
                        pretest_p=0.5, pretest_flag=f)
            for e, p, f in ((-0.5, 0.0, False), (-0.3, 0.01, True), (-0.9, 0.2, False), (-0.4, 0.04, True))]
    s = summarize("none", reps)
    assert np.isclose(s.bias, np.mean([0.0, 0.2, -0.4, 0.1]))
    assert np.isclose(s.rmse, np.sqrt(np.mean([0.0, 0.04, 0.16, 0.01])))
    assert s.coverage == 0.5                                  # -0.5 and -0.4 cover -0.5; -0.3 and -0.9 do not
    assert np.isclose(s.coverage_mcse, np.sqrt(0.25 / 4))
    assert s.rejection == 0.75 and s.detection == 0.5
    assert s.wrong_sign == 0                                  # every significant estimate is negative, like the truth
    assert s.n_pass == 2 and s.coverage_given_pass == 0.5     # passed: -0.5 (covers) and -0.9 (does not)
    assert np.isclose(s.empirical_se, np.std([-0.5, -0.3, -0.9, -0.4], ddof=1))


def test_the_stored_study_is_what_the_code_computes():
    stored = load_study()
    assert stored is not None, "run python spike/demo_study.py"
    meta, study = stored
    assert list(study) == list(THREATS)                                        # every threat, in order
    assert meta["seed_base"] == SEED_BASE
    for threat, levels in study.items():
        assert list(levels) == list(LEVELS)
        assert all(len(levels[level]) == meta["replications_per_level"] >= 1000 for level in LEVELS)
        for level in LEVELS:
            for r in (0, meta["replications_per_level"] - 1):
                assert same(replicate(threat, level, r), levels[level][r]), (threat, level, r)


def test_same_ignores_floating_point_noise_only():
    a = Replication(seed=1, true_att=-0.5, estimate=-0.49, se=0.1, ci_low=-0.69, ci_high=-0.29, p_value=1e-6,
                    pretest_p=0.4, pretest_flag=False)
    from dataclasses import replace
    assert same(a, replace(a, estimate=-0.49 * (1 + 1e-12)))
    assert not same(a, replace(a, estimate=-0.4901))
    assert not same(a, replace(a, pretest_flag=True))


def test_the_decision_rule_by_hand():
    def world(estimate, covered=True):
        lo, hi = (estimate - 0.2, estimate + 0.2) if covered else (estimate + 0.1, estimate + 0.2)
        return Replication(seed=0, true_att=-0.5, estimate=estimate, se=0.1, ci_low=lo, ci_high=hi, p_value=0.001,
                           pretest_p=0.5, pretest_flag=False)
    # bias -0.04 (8% of 0.5) with 9 of 10 covered: acceptable; bias +0.06 (12%): not; 8 of 10 covered: not.
    ok = summarize("none", [world(-0.54)] * 9 + [world(-0.54, covered=False)])
    too_biased = summarize("low", [world(-0.44)] * 10)
    undercovers = summarize("medium", [world(-0.5)] * 8 + [world(-0.5, covered=False)] * 2)
    assert ok.acceptable and not too_biased.acceptable and not undercovers.acceptable
    assert np.isclose(ok.bias_share, 0.08) and np.isclose(too_biased.bias_share, 0.12)
    levels = dict(zip(LEVELS, [ok, ok, too_biased, ok, ok], strict=True))
    assert largest_acceptable(levels) == "low"                                 # the first failure ends the range
    assert largest_acceptable(dict(zip(LEVELS, [too_biased] * 5, strict=True))) is None


def test_the_claims_made_in_words_hold_in_the_stored_study():
    _, study = load_study()
    reps = study["differential_trend"]
    s = {level: summarize(level, reps[level]) for level in LEVELS}
    clean, severe = s["none"], s["severe"]
    assert abs(clean.coverage - 0.95) < 3 * clean.coverage_mcse + 0.01          # close to nominal
    assert abs(clean.bias) < 3 * clean.bias_mcse + 0.005                       # no detectable bias
    assert abs(clean.empirical_se / clean.mean_model_se - 1) < 0.1             # honest standard errors
    assert severe.coverage < 0.2 and abs(severe.bias) > 0.5                    # "biased ... covers in only ..."
    assert severe.wrong_sign > 0.9 and clean.wrong_sign == 0                   # "a significant effect of the wrong sign"
    detection = [s[level].detection for level in LEVELS]
    assert detection == sorted(detection)                                      # the test warns more as trends diverge
    assert s["high"].detection < 1                                             # "can still go unnoticed"
    assert s["high"].coverage_given_pass is not None


def test_the_answers_per_threat_stated_in_the_readme():
    # README section 1: how far each threat can go under the author's rule, and what the pretest sees.
    _, study = load_study()
    s = {t: {lv: summarize(lv, reps) for lv, reps in levels.items()} for t, levels in study.items()}
    assert {t: largest_acceptable(by_level) for t, by_level in s.items()} == {
        "differential_trend": "none", "confounding": "medium", "staggered_dynamic": "high", "anticipation": "medium"}
    baseline = s["confounding"]["none"].detection
    assert s["confounding"]["severe"].detection < 2 * baseline                 # confounding is nearly invisible
    assert s["confounding"]["severe"].bias_share > 0.4
    sev = s["staggered_dynamic"]["severe"]
    assert sev.bias_share <= 0.10 and sev.coverage < 0.90                     # fails the rule on coverage alone


def test_the_demo_page_renders_in_both_languages():
    for lang in ("en", "fr"):
        at = AppTest.from_file(APP, default_timeout=600)
        at.session_state["lang"] = lang
        at.run()
        at.sidebar.radio(key="page").set_value("demo").run()
        assert not at.exception, [e.message for e in at.exception]
        text = " ".join(str(m.value) for m in at.markdown)
        assert ("17 of 18" if lang == "en" else "17 sur 18") in text
        # one world, overview, one table per threat, replication
        assert len(at.dataframe) == 3 + len(THREATS)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("test_demo_study: OK")
