"""
Validation of estimators/honest_did.py (Rambachan & Roth 2023, Delta^SD(M)).

1. Coverage under the worst case: with the covariance of a real event study,
   the FLCI's estimator and its worst-case bias delta (second differences at
   +/- M), 100,000 draws of beta_hat ~ N(delta + tau, Sigma) at each M.
2. The study's virtual worlds with diverging pre-trends (linear, so M = 0
   holds): 1,000 worlds per level; coverage of
   the true ATT by the plain DiD interval and by the FLCI at M = 0.

    python spike/honest_did_validation.py
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "causal_lab"))

from estimators.did import estimate_did  # noqa: E402
from estimators.honest_did import _max_bias, _second_difference_basis, flci, problem_from_panel  # noqa: E402
from simulation_engine.demo_study import SEED_BASE, design  # noqa: E402
from simulation_engine.dgp import generate  # noqa: E402

def worst_case_coverage(n_draws: int = 100_000) -> None:
    cfg = replace(design("differential_trend", "none"), seed=SEED_BASE)
    df, truth = generate(cfg)
    problem = problem_from_panel(df, cfg.treatment_period)
    rng = np.random.default_rng(1)
    n_pre = len(problem.pre)
    b = _second_difference_basis(n_pre, len(problem.post))
    for m in (0.0, 0.02, 0.05):
        r = flci(problem, m)
        w = np.array([r.weights_pre[int(k)] for k in problem.pre])
        c = np.concatenate([w, [0.0], problem.l])
        delta = b @ (m * np.sign(b.T @ c))                               # the worst case for this estimator
        delta = np.delete(delta, n_pre)                                  # drop the reference period
        tau = np.full(len(problem.post), truth["true_att"])
        beta = delta + np.concatenate([np.zeros(n_pre), tau])
        v = np.concatenate([w, problem.l])
        draws = rng.multivariate_normal(beta, problem.sigma, n_draws) @ v
        half = (r.ci_high - r.ci_low) / 2
        covered = np.mean(np.abs(draws - float(problem.l @ tau)) <= half)
        print(f"worst case, M = {m:<5}: bias {abs(_max_bias(problem, w, m)):.4f}, coverage {covered:.3f}", flush=True)


def study_worlds(n_worlds: int = 1000) -> None:
    for level in ("none", "low", "medium"):
        did_cov = honest_cov = 0
        for r in range(n_worlds):
            cfg = replace(design("differential_trend", level), seed=SEED_BASE + r)
            df, truth = generate(cfg)
            att = truth["true_att"]
            did = estimate_did(df)
            did_cov += did.ci_low <= att <= did.ci_high
            h = flci(problem_from_panel(df, cfg.treatment_period), 0.0)
            honest_cov += h.ci_low <= att <= h.ci_high
        print(f"diverging pre-trends, {level:6s}: DiD coverage {did_cov / n_worlds:.3f}, "
              f"FLCI (M = 0) coverage {honest_cov / n_worlds:.3f}", flush=True)


if __name__ == "__main__":
    worst_case_coverage()
    study_worlds()
