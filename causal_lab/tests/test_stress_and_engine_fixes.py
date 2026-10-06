import sys
import warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from causal_engine.diagnosis import ResearchDesignInput, diagnose, Level
from code_generator.generator import CodeGenParams, generate_stata_code
from estimators.event_study import estimate_event_study
from robustness_engine.robustness import run_robustness_battery
from robustness_engine.stress_test import run_stress_test
from simulation_engine.dgp import VirtualWorldConfig, generate
from simulation_engine.monte_carlo import run_monte_carlo


def _verdicts(**threats):
    cfg = VirtualWorldConfig(n_units=200, n_periods=20, treatment_period=10, seed=11, **threats)
    df, _ = generate(cfg)
    report = run_stress_test(df, treatment_period=10)
    return {c.name: c.verdict for c in report.checks}


def test_stress_test_clean_world_passes():
    verdicts = _verdicts()
    assert verdicts["Serial Correlation"] == "PASS"
    assert verdicts["Spillovers"] == "PASS"
    assert verdicts["Heterogeneous Effects"] == "PASS"


def test_stress_test_detects_serial_correlation():
    assert _verdicts(serial_correlation="severe")["Serial Correlation"] == "WARNING"


def test_stress_test_detects_spillovers():
    assert _verdicts(spillovers="severe", true_att=-2.0)["Spillovers"] == "WARNING"


def test_stress_test_detects_heterogeneity():
    assert _verdicts(treatment_heterogeneity="severe")["Heterogeneous Effects"] == "WARNING"


def test_staggered_units_are_all_treated():
    cfg = VirtualWorldConfig(n_units=60, n_periods=12, treatment_period=10,
                              staggered_adoption=True, seed=1)
    df, truth = generate(cfg)
    ever_treated = set(df.loc[df["D"] == 1, "unit"])
    assert ever_treated == set(truth["treated_units"])


def test_confounded_selection_keeps_treated_share():
    cfg = VirtualWorldConfig(n_units=100, share_treated=0.3, confounding="severe", seed=5)
    _, truth = generate(cfg)
    assert len(truth["treated_units"]) == 30


def test_event_study_is_full_rank():
    df, _ = generate(VirtualWorldConfig(n_units=100, n_periods=16, treatment_period=8, seed=3))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        estimate_event_study(df, fixed_treatment_period=8)


def test_monte_carlo_coverage_reasonable():
    summary = run_monte_carlo(VirtualWorldConfig(n_units=60, n_periods=8, treatment_period=4),
                              n_reps=40)
    assert abs(summary.bias) < 0.1
    assert summary.coverage >= 0.8


def test_robustness_handles_string_unit_ids():
    df, _ = generate(VirtualWorldConfig(n_units=40, n_periods=10, treatment_period=5, seed=2))
    df["unit"] = "u" + df["unit"].astype(str)
    rows = run_robustness_battery(df, treatment_period=5)
    assert rows[0].specification.startswith("Baseline")


def test_heterogeneity_keyword_not_triggered_by_substring():
    design = ResearchDesignInput(research_question="Effect of a wage subsidy on average village income levels")
    assert diagnose(design).treatment_heterogeneity == Level.HIGH  # "income"
    design = ResearchDesignInput(research_question="Effect of a wage subsidy on average village output")
    assert diagnose(design).treatment_heterogeneity == Level.MEDIUM


def test_stata_code_absorbs_declared_columns():
    code = generate_stata_code(CodeGenParams())
    assert "encode" not in code
    assert "absorb(unit period)" in code


def test_diverging_pretrends_flagged_questionable_or_violated():
    df, _ = generate(VirtualWorldConfig(n_units=200, differential_trend="severe", seed=3))
    report = run_stress_test(df, treatment_period=10)
    pt = next(c for c in report.checks if c.name == "Parallel Trends")
    assert pt.verdict == "WARNING"
    assert pt.assessment in ("questionable", "violated")


def test_clean_world_parallel_trends_plausible():
    df, _ = generate(VirtualWorldConfig(n_units=200, seed=3))
    pt = next(c for c in run_stress_test(df, treatment_period=10).checks if c.name == "Parallel Trends")
    assert pt.assessment == "plausible"


def test_assessment_thresholds():
    from robustness_engine.stress_test import parallel_trends_assessment
    assert parallel_trends_assessment(0.5) == "plausible"
    assert parallel_trends_assessment(0.05) == "questionable"
    assert parallel_trends_assessment(0.001) == "violated"


def test_anticipation_detected():
    assert _verdicts(anticipation="severe")["Anticipation"] == "WARNING"


def test_anticipation_shift_is_before_adoption_only():
    df, truth = generate(VirtualWorldConfig(n_units=40, anticipation="severe", seed=5))
    clean, _ = generate(VirtualWorldConfig(n_units=40, seed=5))
    diff = (df["Y"] - clean["Y"]).abs()
    shifted_periods = set(df.loc[diff > 1e-12, "period"])
    assert shifted_periods == {9}
    assert (df.loc[df["period"] == 9, "D"] == 0).all()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("test_stress_and_engine_fixes: OK")
