"""
Spike (issue #3): with every causal threat switched off, what
Identification Strength score does the app report, and which of the
5 "Break My Design" checks fire?

Loops VirtualWorldConfig() -> generate() -> run_stress_test() 200 times
with every threat off (the clean world), then once more per threat
lever set to "severe" (200 reps each), to get a false-alarm rate and a
detection rate per check.

Deterministic: each scenario reuses seeds 0..199, so re-running this
script reproduces the same table. Writes the table to
stress_test_calibration_results.md next to this script.

Run from the repository root:
    .venv/Scripts/python.exe spike/stress_test_calibration.py
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "causal_lab"))

from statsmodels.tools.sm_exceptions import SingularMatrixWarning

from simulation_engine.dgp import VirtualWorldConfig, generate
from robustness_engine.stress_test import run_stress_test

N_REPS = 200

CHECK_NAMES = [
    "Parallel Trends",
    "Anticipation",
    "Spillovers",
    "Serial Correlation",
    "Heterogeneous Effects",
]

# Which VirtualWorldConfig threat lever (if any) this check is meant to
# detect. "Anticipation" has no corresponding lever: the DGP has no
# anticipation-effect parameter at all.
CHECK_TO_THREAT = {
    "Parallel Trends": "confounding",
    "Anticipation": None,
    "Spillovers": "spillovers",
    "Serial Correlation": "serial_correlation",
    "Heterogeneous Effects": "treatment_heterogeneity",
}


def run_batch(threat_kwargs: dict, n_reps: int = N_REPS) -> tuple[dict[str, float], float]:
    """Run n_reps replications with the given threat config, seeds 0..n_reps-1.

    Returns (warning_rate_per_check, mean_identification_strength).
    """
    warning_counts = {name: 0 for name in CHECK_NAMES}
    scores = []
    for seed in range(n_reps):
        cfg = VirtualWorldConfig(seed=seed, **threat_kwargs)
        df, _truth = generate(cfg)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=SingularMatrixWarning)
            report = run_stress_test(df, treatment_period=cfg.treatment_period)
        for check in report.checks:
            if check.verdict == "WARNING":
                warning_counts[check.name] += 1
        scores.append(report.identification_strength)
    rates = {name: warning_counts[name] / n_reps for name in CHECK_NAMES}
    mean_score = sum(scores) / len(scores)
    return rates, mean_score


def main() -> None:
    print(f"Clean world (all threats off), n={N_REPS} ...")
    clean_rates, clean_score = run_batch({})
    print(f"  mean Identification Strength = {clean_score:.1f} / 100")

    detection_rates: dict[str, float | None] = {}
    for check_name, threat_param in CHECK_TO_THREAT.items():
        if threat_param is None:
            detection_rates[check_name] = None
            continue
        print(f"{threat_param}=severe, n={N_REPS} ...")
        rates, score = run_batch({threat_param: "severe"})
        detection_rates[check_name] = rates[check_name]
        print(f"  mean Identification Strength = {score:.1f} / 100")

    lines = []
    lines.append("# Stress-test calibration spike (issue #3)\n")
    lines.append(
        f"Clean-world mean Identification Strength score (n={N_REPS}): "
        f"**{clean_score:.1f} / 100**\n"
    )
    lines.append("| Check | False-alarm rate (clean world) | Detection rate (threat = severe) |")
    lines.append("|---|---|---|")
    for name in CHECK_NAMES:
        detect = detection_rates[name]
        detect_str = f"{detect:.0%}" if detect is not None else "n/a — no corresponding threat in the DGP"
        lines.append(f"| {name} | {clean_rates[name]:.0%} | {detect_str} |")
    table = "\n".join(lines) + "\n"

    print("\n" + table)

    out_path = Path(__file__).resolve().parent / "stress_test_calibration_results.md"
    out_path.write_text(table, encoding="utf-8")
    print(f"Written to {out_path}")


if __name__ == "__main__":
    main()
