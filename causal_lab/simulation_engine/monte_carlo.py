"""
Monte Carlo simulation runner (CAUSAL LAB spec, Section 17).

Repeatedly draws a fresh dataset from the Virtual World DGP, applies
the DiD estimator, and aggregates bias / RMSE / coverage / CI length
across replications. Used to compare how estimator performance
degrades as causal threats are turned on.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from scipy import stats

from estimators.did import DiDResult, estimate_did
from simulation_engine.dgp import VirtualWorldConfig, generate


@dataclass
class MonteCarloSummary:
    n_reps: int
    bias: float
    rmse: float
    mae: float
    coverage: float
    avg_ci_length: float
    mean_estimate: float
    true_att: float
    estimates: list[float]


def run_monte_carlo(config: VirtualWorldConfig, n_reps: int = 200, ci_level: float = 0.95,
                     base_seed: int = 0) -> MonteCarloSummary:
    z = float(stats.norm.ppf(0.5 + ci_level / 2))

    estimates: list[float] = []
    true_atts: list[float] = []
    covered = 0
    ci_lengths: list[float] = []

    for r in range(n_reps):
        rep_config = replace(config, seed=base_seed + r)
        df, truth = generate(rep_config)
        result: DiDResult = estimate_did(df)
        estimates.append(result.att)
        # The realized ATT differs across replications when treatment
        # effects are heterogeneous, so each estimate is compared with
        # its own replication's truth.
        true_atts.append(truth["true_att"])

        lo = result.att - z * result.se
        hi = result.att + z * result.se
        ci_lengths.append(hi - lo)
        if lo <= truth["true_att"] <= hi:
            covered += 1

    estimates_arr = np.array(estimates)
    errors = estimates_arr - np.array(true_atts)

    return MonteCarloSummary(
        n_reps=n_reps,
        bias=float(np.mean(errors)),
        rmse=float(np.sqrt(np.mean(errors ** 2))),
        mae=float(np.mean(np.abs(errors))),
        coverage=covered / n_reps,
        avg_ci_length=float(np.mean(ci_lengths)),
        mean_estimate=float(np.mean(estimates_arr)),
        true_att=float(np.mean(true_atts)),
        estimates=estimates,
    )
