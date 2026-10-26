"""
Monte Carlo evaluation of the six Causal Methods on their virtual worlds.

For one world configuration, replication r draws the world with seed
base_seed + r, runs the method exactly as the Causal Methods page does
(estimators.registry), and compares the estimate with that replication's
true effect. Reported: bias, RMSE, MAE, coverage and mean length of the 95%
CI, mean SE over the sampling SD of the estimates, and how often the method
rejects "no effect" at 5%. Synthetic control has no standard error: coverage,
CI length and SE ratio are None, and rejections use its placebo p-value.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

import numpy as np

from estimators.registry import WORLDS, run_method, virtual_options
from utils.i18n import LocalizedError


@dataclass
class MethodMonteCarloSummary:
    method: str
    n_reps: int
    n_failed: int                 # replications where the estimator refused the data
    bias: float
    rmse: float
    mae: float
    coverage: float | None
    avg_ci_length: float | None
    se_ratio: float | None        # mean SE / sampling SD of the estimates
    rejection_rate: float         # share with p < 0.05
    mean_estimate: float
    true_effect: float
    estimates: list[float]
    errors: list[float]


def run_method_monte_carlo(method: str, config, n_reps: int = 100, base_seed: int = 0,
                           progress: Callable[[int, int], None] | None = None) -> MethodMonteCarloSummary:
    if n_reps < 2:
        raise LocalizedError("err.mc_reps", value=n_reps)
    world = WORLDS[method]
    estimates, truths, ses, covered, lengths, rejected = [], [], [], [], [], []
    failed = 0
    for r in range(n_reps):
        df, truth = world.generate(replace(config, seed=base_seed + r))
        try:
            result = run_method(method, df, dict(truth["roles"]), virtual_options(method, truth), light=True)
        except LocalizedError:
            failed += 1
            continue
        finally:
            if progress is not None:
                progress(r + 1, n_reps)
        estimates.append(result.estimate)
        truths.append(truth["true_effect"])
        rejected.append(result.p_value is not None and result.p_value < 0.05)
        if result.se is not None:
            ses.append(result.se)
            covered.append(result.ci_low <= truth["true_effect"] <= result.ci_high)
            lengths.append(result.ci_high - result.ci_low)
    if len(estimates) < 2:
        raise LocalizedError("err.mc_failed", failed=failed, reps=n_reps)

    est, errors = np.array(estimates), np.array(estimates) - np.array(truths)
    with_se = len(ses) == len(estimates)
    return MethodMonteCarloSummary(
        method=method, n_reps=n_reps, n_failed=failed,
        bias=float(errors.mean()), rmse=float(np.sqrt(np.mean(errors ** 2))), mae=float(np.mean(np.abs(errors))),
        coverage=float(np.mean(covered)) if with_se else None,
        avg_ci_length=float(np.mean(lengths)) if with_se else None,
        se_ratio=float(np.mean(ses) / est.std(ddof=1)) if with_se and est.std(ddof=1) > 0 else None,
        rejection_rate=float(np.mean(rejected)),
        mean_estimate=float(est.mean()), true_effect=float(np.mean(truths)),
        estimates=est.tolist(), errors=errors.tolist(),
    )
