"""
How the 10% bias and 90% coverage rule depends on precision, checked by simulation
with the app's own world and estimator. Adds nothing to the stored Guided Demo study.

For the default world (100 units) and one four times larger (400 units), 1,000 worlds:
  clean      no threat. A bias of exactly 10% of the effect (0.05) is then added to each
             estimate, so the question "what coverage does a 10% bias imply?" is answered
             with the estimator's real sampling distribution, not with a normal formula;
  anticipation high   a real threat whose bias does not shrink with the sample;
  null       a true effect of zero, where relative bias does not exist.

    python spike/bias_coverage_check.py
writes spike/bias_coverage_check_results.md and .json.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np
from scipy.stats import norm, t as student_t

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "causal_lab"))

from estimators.did import estimate_did  # noqa: E402
from simulation_engine.demo_study import SEED_BASE  # noqa: E402
from simulation_engine.dgp import VirtualWorldConfig, generate  # noqa: E402

N_REPS = 1000
SIZES = (100, 400)
EFFECT = -0.5
SCENARIOS = {"clean": {}, "anticipation_high": {"anticipation": "high"}, "null": {"true_att": 0.0}}


def _one(job: tuple[str, int, int]) -> tuple[str, int, float, float, float]:
    scenario, n_units, r = job
    cfg = replace(VirtualWorldConfig(), n_units=n_units, seed=SEED_BASE + r, **SCENARIOS[scenario])
    df, truth = generate(cfg)
    did = estimate_did(df)
    return scenario, n_units, float(did.att), float(did.se), float(truth["true_att"])


def _crit(n_units: int) -> float:
    return float(student_t.ppf(0.975, n_units - 1))         # the interval the app reports


def _coverage(est, se, truth, n_units: int) -> float:
    c = _crit(n_units)
    return float(np.mean((est - c * se <= truth) & (truth <= est + c * se)))


def _normal_coverage(bias: float, se: float, n_units: int) -> float:
    c = _crit(n_units)
    return float(norm.cdf(c - bias / se) + norm.cdf(-c - bias / se))


def main() -> None:
    jobs = [(s, n, r) for s in SCENARIOS for n in SIZES for r in range(N_REPS)]
    with Pool(max(1, (os.cpu_count() or 2) - 2)) as pool:
        rows = pool.map(_one, jobs, chunksize=20)
    out = {}
    for scenario in SCENARIOS:
        for n in SIZES:
            est, se, truth = map(np.array, zip(*[(a, b, c) for s, m, a, b, c in rows if s == scenario and m == n]))
            err = est - truth
            cell = {"bias": float(err.mean()), "bias_mcse": float(err.std(ddof=1) / np.sqrt(N_REPS)),
                    "empirical_se": float(est.std(ddof=1)), "mean_model_se": float(se.mean()),
                    "coverage": _coverage(est, se, truth, n), "ci_width": float(np.mean(2 * _crit(n) * se)),
                    "rejection": float(np.mean(np.abs(est / se) > _crit(n)))}
            cell["coverage_mcse"] = float(np.sqrt(cell["coverage"] * (1 - cell["coverage"]) / N_REPS))
            if scenario == "clean":
                shift = 0.10 * abs(EFFECT)
                cell["coverage_with_10pct_bias"] = _coverage(est + shift, se, truth, n)
                cell["normal_formula_10pct_bias"] = _normal_coverage(shift, cell["mean_model_se"], n)
                cell["bias_over_se_at_10pct"] = shift / cell["mean_model_se"]
            out[f"{scenario}_{n}"] = cell
    results = {"n_reps": N_REPS, "seed_base": SEED_BASE, "cells": out}
    (ROOT / "spike" / "bias_coverage_check_results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    c1, c4 = out["clean_100"], out["clean_400"]
    a1, a4 = out["anticipation_high_100"], out["anticipation_high_400"]
    n1, n4 = out["null_100"], out["null_400"]
    md = f"""# Does the 10% and 90% rule depend on precision?

From `spike/bias_coverage_check.py`: {N_REPS} worlds per cell, the app's world and estimator, seeds from {SEED_BASE}. Monte Carlo SE of a coverage near 0.9 is about 0.01.

## A bias of exactly 10% of the effect (0.05), added to the estimates of clean worlds

| Units | Model SE | Empirical SE | Bias / SE | Coverage, simulated | Coverage, normal formula |
|---|---|---|---|---|---|
| 100 | {c1['mean_model_se']:.4f} | {c1['empirical_se']:.4f} | {c1['bias_over_se_at_10pct']:.3f} | {c1['coverage_with_10pct_bias']:.3f} | {c1['normal_formula_10pct_bias']:.3f} |
| 400 | {c4['mean_model_se']:.4f} | {c4['empirical_se']:.4f} | {c4['bias_over_se_at_10pct']:.3f} | {c4['coverage_with_10pct_bias']:.3f} | {c4['normal_formula_10pct_bias']:.3f} |

## A real threat: anticipation at "high"

The bias does not shrink with the sample, so coverage falls as the SE falls.

| Units | Bias (MCSE) | Share of the effect | Model SE | Coverage (MCSE) | Width of the 95% CI |
|---|---|---|---|---|---|
| 100 | {a1['bias']:+.4f} ({a1['bias_mcse']:.4f}) | {abs(a1['bias']) / abs(EFFECT):.1%} | {a1['mean_model_se']:.4f} | {a1['coverage']:.3f} ({a1['coverage_mcse']:.3f}) | {a1['ci_width']:.3f} |
| 400 | {a4['bias']:+.4f} ({a4['bias_mcse']:.4f}) | {abs(a4['bias']) / abs(EFFECT):.1%} | {a4['mean_model_se']:.4f} | {a4['coverage']:.3f} ({a4['coverage_mcse']:.3f}) | {a4['ci_width']:.3f} |

## A true effect of zero, where relative bias does not exist

Judge absolute bias and the size of the test (rejection rate, nominal 5%).

| Units | Bias (MCSE) | Coverage (MCSE) | Rejection rate of H0: effect = 0 |
|---|---|---|---|
| 100 | {n1['bias']:+.4f} ({n1['bias_mcse']:.4f}) | {n1['coverage']:.3f} ({n1['coverage_mcse']:.3f}) | {n1['rejection']:.3f} |
| 400 | {n4['bias']:+.4f} ({n4['bias_mcse']:.4f}) | {n4['coverage']:.3f} ({n4['coverage_mcse']:.3f}) | {n4['rejection']:.3f} |
"""
    (ROOT / "spike" / "bias_coverage_check_results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
