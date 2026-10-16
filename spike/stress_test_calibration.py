"""
Spike (issue #3): with every causal threat switched off, what
Identification Strength score does the app report, and which of the
5 "Break My Design" checks fire?

Loops VirtualWorldConfig() -> generate() -> run_stress_test() 200 times
with every threat off (the clean world), then once more per threat
lever set to "severe" (200 reps each), to get a false-alarm rate and a
detection rate per check.

Deterministic: each scenario reuses seeds 0..199, so re-running this
script reproduces the same table. Writes the table to the output file
given as the required first argument; a relative path is taken relative
to this script's folder, as before.

The output file is never replaced silently. The two committed result
files (stress_test_calibration_results.md, the hw4 spike of 2026-10-03,
and stress_test_calibration_results_after_fix.md, of 2026-10-06) are
historical records. Without an argument the script used to overwrite the
first one, and did so during the hw6 final verification. Now:
  - no output argument            -> refused, nothing computed;
  - output file already exists    -> refused before computing, unless --overwrite;
  - parent folder missing / write fails -> error, non-zero exit, no "Written to".

Each check is paired with the DGP lever it is meant to detect. The
original spike (2026-10-03) paired Parallel Trends with `confounding`
and had no lever for Anticipation; the generator now has
`differential_trend` and `anticipation` levers for exactly those
checks (change fix-correctness-and-readme-gaps).

Run from the repository root:
    .venv/Scripts/python.exe spike/stress_test_calibration.py NEW_RESULTS.md [--overwrite]
"""
from __future__ import annotations

import argparse
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

# Which VirtualWorldConfig threat lever this check is meant to detect.
CHECK_TO_THREAT = {
    "Parallel Trends": "differential_trend",
    "Anticipation": "anticipation",
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
            report = run_stress_test(df, treatment_period=cfg.treatment_period,
                                     ids_encode_neighbourhood=True)
        for check in report.checks:
            if check.verdict == "WARNING":
                warning_counts[check.name] += 1
        scores.append(report.identification_strength)
    rates = {name: warning_counts[name] / n_reps for name in CHECK_NAMES}
    mean_score = sum(scores) / len(scores)
    return rates, mean_score


def _output_path(argv: list[str] | None) -> tuple[Path, bool]:
    """Parse the command line and check the destination before any computation."""
    parser = argparse.ArgumentParser(description="Stress-test calibration spike (1,200 simulated worlds).")
    parser.add_argument("output", help="results file to create; relative paths are taken from the spike/ folder")
    parser.add_argument("--overwrite", action="store_true",
                        help="replace OUTPUT if it already exists (never the default)")
    args = parser.parse_args(argv)
    out_path = Path(__file__).resolve().parent / args.output
    if not out_path.parent.is_dir():
        parser.error(f"output folder does not exist: {out_path.parent}")
    if out_path.is_dir():
        parser.error(f"output is a folder, not a file: {out_path}")
    if out_path.exists() and not args.overwrite:
        parser.error(f"output file already exists and was left unchanged: {out_path} "
                     "(choose a new name, or pass --overwrite to replace it)")
    return out_path, args.overwrite


def _write(out_path: Path, table: str, overwrite: bool) -> None:
    # Exclusive creation ("x") closes the gap between the check above and
    # the write, 5 minutes later: a file created meanwhile is not replaced.
    try:
        with out_path.open("w" if overwrite else "x", encoding="utf-8") as f:
            f.write(table)
    except OSError as exc:
        sys.exit(f"error: the results were NOT saved to {out_path}: {exc}")


def main(argv: list[str] | None = None) -> None:
    out_path, overwrite = _output_path(argv)
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

    _write(out_path, table, overwrite)
    print(f"Written to {out_path}")


if __name__ == "__main__":
    main()
