"""
Size and power of the two manipulation checks of the RD estimator, on RD
virtual worlds (simulation_engine.method_worlds.rdd_world, n = 1,000):

- binomial: counts within h/2 on each side of the cutoff (the check used
  until 2026-11-22);
- Cattaneo, Jansson & Ma (2020): the local-polynomial density test, as
  computed by the authors' package rddensity (jackknife standard error,
  its default).

Size: worlds as drawn (no manipulation). Power: a share of the units just
below the cutoff (within 0.1 of it) move just above it (within 0.05), as
when people sort onto the favourable side. 500 worlds per scenario; a test
rejects at p < 0.05.

    python spike/rd_density_validation.py
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "causal_lab"))
warnings.filterwarnings("ignore")

from estimators.rdd import estimate_rdd  # noqa: E402
from simulation_engine.method_worlds import RDDWorldConfig, rdd_world  # noqa: E402
from rddensity import rddensity  # noqa: E402

N_WORLDS = 500


def sort_onto_cutoff(df, share: float, rng):
    below = df.index[(df["X"] < 0) & (df["X"] >= -0.1)]
    movers = rng.choice(below, size=int(round(share * len(below))), replace=False)
    df = df.copy()
    df.loc[movers, "X"] = rng.uniform(0.0, 0.05, len(movers))
    return df


def main() -> None:
    for share in (0.0, 0.2, 0.4):
        rej_binom = rej_cjm = 0
        for seed in range(N_WORLDS):
            df, _ = rdd_world(RDDWorldConfig(n=1000, seed=seed))
            if share:
                df = sort_onto_cutoff(df, share, np.random.default_rng(10_000 + seed))
            res = estimate_rdd(df, "Y", "X", cutoff=0.0)
            rej_binom += res.details["manipulation"]["p_value"] < 0.05
            rej_cjm += float(rddensity(X=df["X"].to_numpy(), c=0.0).test["p_jk"]) < 0.05
        label = "size (no manipulation)" if share == 0 else f"power, {share:.0%} of units within 0.1 below move above"
        print(f"{label:48s} binomial {rej_binom / N_WORLDS:.3f}   Cattaneo-Jansson-Ma {rej_cjm / N_WORLDS:.3f}",
              flush=True)


if __name__ == "__main__":
    main()
