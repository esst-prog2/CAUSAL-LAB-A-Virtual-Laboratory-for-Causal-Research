"""
What the Identification Strength score says when the DiD is badly biased: the mean
score over worlds at each level of two threats, next to the bias of the DiD there.
Uses the app's own stress test and estimator.

    python spike/identification_score_check.py
writes spike/identification_score_check_results.md.
"""
from __future__ import annotations

import os
import sys
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "causal_lab"))

from estimators.did import estimate_did  # noqa: E402
from robustness_engine.stress_test import identification_strength, run_stress_test  # noqa: E402
from simulation_engine.demo_study import SEED_BASE  # noqa: E402
from simulation_engine.dgp import VirtualWorldConfig, generate  # noqa: E402

N_REPS = 200
SCENARIOS = {"no threat": {}, "diverging pre-trends, low": {"differential_trend": "low"},
             "diverging pre-trends, medium": {"differential_trend": "medium"},
             "confounding, high": {"confounding": "high"}, "confounding, severe": {"confounding": "severe"},
             "diverging pre-trends, severe": {"differential_trend": "severe"}}


def _one(job):
    name, r = job
    cfg = replace(VirtualWorldConfig(), seed=SEED_BASE + r, **SCENARIOS[name])
    df, truth = generate(cfg)
    report = run_stress_test(df, treatment_period=cfg.treatment_period, ids_encode_neighbourhood=True)
    return name, identification_strength(report.checks), float(estimate_did(df).att) - float(truth["true_att"])


def main() -> None:
    with Pool(max(1, (os.cpu_count() or 2) - 2)) as pool:
        rows = pool.map(_one, [(s, r) for s in SCENARIOS for r in range(N_REPS)], chunksize=5)
    lines = ["# Identification Strength next to the DiD's actual bias", "",
             f"From `spike/identification_score_check.py`: {N_REPS} worlds per row, default design, true effect -0.50.", "",
             "| Scenario | Mean score | Share of worlds at 80 or more | Mean bias | Bias as a share of the effect |", "|---|---|---|---|---|"]
    for name in SCENARIOS:
        score = np.array([s for n, s, _ in rows if n == name], dtype=float)
        bias = np.mean([b for n, _, b in rows if n == name])
        lines.append(f"| {name} | {score.mean():.1f} | {np.mean(score >= 80):.0%} | {bias:+.3f} | {abs(bias) / 0.5:.0%} |")
    text = "\n".join(lines) + "\n"
    (ROOT / "spike" / "identification_score_check_results.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
