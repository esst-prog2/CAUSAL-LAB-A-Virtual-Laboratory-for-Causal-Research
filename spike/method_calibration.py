"""
Calibration of the six Causal Methods' Monte Carlo and Break My Design checks.

1. Monte Carlo on each method's default virtual world: bias, RMSE, coverage,
   SE / SD and rejection rate (estimators.registry, as the app runs them).
2. Each Break My Design check's warning rate on worlds without the threat
   (false alarms) and, where a world parameter turns the threat on, with it
   (detection). Deterministic: scenario s reuses seeds 0..n-1.

    python spike/method_calibration.py method_calibration_results.md

The output file must not exist yet (relative names go to spike/).
"""
from __future__ import annotations

import sys
import time
import warnings
from collections import Counter
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "causal_lab"))

from estimators.registry import METHOD_KEYS, WORLDS, virtual_options          # noqa: E402
from robustness_engine.method_stress import run_method_stress_test           # noqa: E402
from simulation_engine.method_monte_carlo import run_method_monte_carlo      # noqa: E402

MC_REPS = {"dml": 30}
STRESS = [            # (method, change, label, replications)
    ("rct", {}, "default", 200), ("rct", {"n": 40}, "n = 40", 200),
    ("matching", {}, "default", 200), ("matching", {"confounding_strength": 3.0}, "confounding 3", 200),
    ("iv", {}, "default", 200), ("iv", {"instrument_strength": 0.3}, "instrument strength 0.3", 200),
    ("rdd", {}, "default", 200), ("rdd", {"curvature": 5.0}, "curvature 5", 200),
    ("synthetic_control", {}, "default", 200), ("synthetic_control", {"noise_sd": 3.0}, "noise 3", 200),
    ("dml", {}, "default", 20),
]


def main(argv: list[str]) -> None:
    out = Path(argv[0])
    if not out.is_absolute():
        out = Path(__file__).resolve().parent / out
    if out.exists():
        raise SystemExit(f"{out} exists; give a new file name")
    warnings.filterwarnings("ignore")
    lines = ["# Causal Methods calibration", "",
             "## Monte Carlo on the default worlds", "",
             "| Method | Replications | Bias | RMSE | 95% CI coverage | SE / SD | Rejects no effect (5%) |",
             "|---|---|---|---|---|---|---|"]
    for method in METHOD_KEYS:
        n = MC_REPS.get(method, 200)
        start = time.time()
        mc = run_method_monte_carlo(method, WORLDS[method].config_cls(), n_reps=n)
        fmt = lambda v, spec: "—" if v is None else format(v, spec)            # noqa: E731
        lines.append(f"| {method} | {n} | {mc.bias:+.4f} | {mc.rmse:.4f} | {fmt(mc.coverage, '.1%')} | "
                     f"{fmt(mc.se_ratio, '.3f')} | {mc.rejection_rate:.1%} |")
        print(method, f"{time.time() - start:.0f}s", flush=True)
    lines += ["", "## Break My Design: warning rate per check", "",
              "| Method | World | Replications | Check | Warning | N/A | Mean score |", "|---|---|---|---|---|---|---|"]
    for method, change, label, n in STRESS:
        warn, na, scores = Counter(), Counter(), []
        for seed in range(n):
            df, truth = WORLDS[method].generate(replace(WORLDS[method].config_cls(), seed=seed, **change))
            report = run_method_stress_test(method, df, dict(truth["roles"]), virtual_options(method, truth))
            for c in report.checks:
                warn[c.slug] += c.verdict == "WARNING"
                na[c.slug] += c.verdict == "N/A"
            if report.identification_strength is not None:
                scores.append(report.identification_strength)
        mean = sum(scores) / len(scores) if scores else float("nan")
        for slug in warn:
            lines.append(f"| {method} | {label} | {n} | {slug} | {warn[slug] / n:.1%} | {na[slug] / n:.1%} | {mean:.1f} |")
        print(method, label, flush=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"written {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
