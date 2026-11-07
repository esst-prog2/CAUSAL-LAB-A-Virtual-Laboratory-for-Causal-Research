"""Clean-world calibration of the "Break My Design" checks (hw6 review 1).

The requirement "Checks are calibrated on the Virtual World" in
openspec/specs/break-my-design-stress-test/spec.md had no automated test:
it was only checked by running spike/stress_test_calibration.py by hand.
This test enforces the clean-world half of that requirement.

Expected values come from that spec, not from running this program:
- each check's false-alarm rate on threat-free worlds is at most 20%;
- at least 65% of threat-free worlds raise no warning on the three checks aimed
  at the identifying assumption (three tests at the 10% level would leave 73%).

Provenance: these bounds were written into the spec by Claude in change
fix-correctness-and-readme-gaps (2026-10-06) and merged into main by the
user. The detection half of the requirement (>= 80% per threat) still
relies on the spike script, because it needs 1000 more simulated worlds.
"""
import sys
import warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from robustness_engine.stress_test import NO_WARNING, run_stress_test
from simulation_engine.dgp import VirtualWorldConfig, generate

N_WORLDS = 200              # "Measured over 200 seeded replications" (spec)
MAX_FALSE_ALARM = 0.20      # spec bound per check
MIN_CLEAN_NO_WARNING = 0.65 # spec bound on the share of clean worlds with no identifying warning


def test_clean_world_false_alarms_and_summary_meet_the_spec():
    warnings.simplefilter("ignore")
    alarms: dict[str, int] = {}
    no_warning = 0
    for seed in range(N_WORLDS):
        cfg = VirtualWorldConfig(seed=seed)
        df, _ = generate(cfg)
        report = run_stress_test(df, treatment_period=cfg.treatment_period, ids_encode_neighbourhood=True)
        no_warning += report.summary == NO_WARNING
        for check in report.checks:
            alarms[check.name] = alarms.get(check.name, 0) + (check.verdict == "WARNING")
    rates = {name: count / N_WORLDS for name, count in alarms.items()}
    share = no_warning / N_WORLDS
    print("clean-world false-alarm rates:", rates, "no identifying warning:", share)
    assert len(rates) == 5
    assert all(rate <= MAX_FALSE_ALARM for rate in rates.values()), rates
    assert share >= MIN_CLEAN_NO_WARNING, share


if __name__ == "__main__":
    test_clean_world_false_alarms_and_summary_meet_the_spec()
    print("test_stress_calibration: OK")
