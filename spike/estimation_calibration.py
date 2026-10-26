"""
Calibration of the structural estimators (theory_engine/estimation.py):
coverage of their 95% intervals and the size of Hansen's J test.

1. Logit QRE by maximum likelihood: choices drawn from the QRE of a
   catalogue game at a known lambda, 200 per player.
2. GMM on first-order conditions: constant-elasticity Cournot duopoly
   markets, demand A exp(A1 w) Q^(-1/eta), costs 10 + 2 r_i + u_i (u_i
   unobserved, truncated to +-1 so both firms stay in every market). The
   equilibrium is in closed form: P = eta (c1 + c2) / (2 eta - 1).

    python spike/estimation_calibration.py [replications] [markets]

Deterministic (seed 2026).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "causal_lab"))

import numpy as np                                                           # noqa: E402
import pandas as pd                                                          # noqa: E402

from theory_engine.estimation import fit_logit_qre, gmm_first_order_conditions  # noqa: E402
from theory_engine.finite_games import logit_qre, matrix_catalogue          # noqa: E402
from theory_engine.game import build_custom_game                            # noqa: E402

REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
MARKETS = int(sys.argv[2]) if len(sys.argv) > 2 else 300


def qre(rng) -> None:
    catalogue = matrix_catalogue()
    for key, lam0 in (("inspection", 1.0), ("inspection", 3.0), ("stag_hunt", 2.0)):
        game = catalogue[key]
        x, y = logit_qre(game, lam0)
        wald = lr = bound = 0
        estimates = []
        start = time.time()
        for _ in range(REPS):
            fit = fit_logit_qre(game, rng.multinomial(200, x), rng.multinomial(200, y))
            estimates.append(fit.lam)
            bound += fit.at_bound
            lr += fit.ci_low <= lam0 <= fit.ci_high
            wald += fit.se is not None and abs(fit.lam - lam0) <= 1.96 * fit.se
        print(f"QRE {key}, lambda {lam0}: median {np.median(estimates):.3f}, LR coverage {lr / REPS:.3f}, "
              f"Wald coverage {wald / REPS:.3f}, lower bound only {bound / REPS:.3f} ({time.time() - start:.0f} s)",
              flush=True)


def gmm(rng) -> None:
    game = build_custom_game("ce", {"A": 80, "A1": 0.1, "eta": 1.5, "w": 0, "r1": 0, "r2": 0}, [
        dict(name="F1", strategy="x1", lower="0.001", upper="1e4",
             utility="A*exp(A1*w)*(x1+x2)^(-1/eta)*x1 - (10 + 2*r1)*x1"),
        dict(name="F2", strategy="x2", lower="0.001", upper="1e4",
             utility="A*exp(A1*w)*(x1+x2)^(-1/eta)*x2 - (10 + 2*r2)*x2")])
    truth = np.array([100.0, 0.3, 2.0])
    big_a, a1, eta = truth
    cover, rejections, estimates = np.zeros(3), 0, []
    start = time.time()
    for _ in range(REPS):
        w = rng.normal(size=MARKETS)
        r = rng.uniform(-1, 1, size=(2, MARKETS))
        c = 10 + 2 * r + np.clip(rng.normal(scale=0.5, size=(2, MARKETS)), -1, 1)
        price = eta * c.sum(axis=0) / (2 * eta - 1)
        q = eta * (1 - c / price) * (big_a * np.exp(a1 * w) / price) ** eta
        df = pd.DataFrame(dict(w=w, r1=r[0], r2=r[1], q1=q[0], q2=q[1]))
        fit = gmm_first_order_conditions(game, df, {"x1": "q1", "x2": "q2"}, {"A": 80, "A1": 0.1, "eta": 1.5},
                                         ["w", "r1", "r2"], observed={"w": "w", "r1": "r1", "r2": "r2"})
        estimates.append(fit.estimates)
        cover += (fit.ci_low <= truth) & (truth <= fit.ci_high)
        rejections += fit.j_p < 0.05
    print(f"GMM, {MARKETS} markets: mean (A, A1, eta) {np.mean(estimates, axis=0).round(4)}, "
          f"coverage {(cover / REPS).round(3)}, J test size {rejections / REPS:.3f} ({time.time() - start:.0f} s)")


if __name__ == "__main__":
    generator = np.random.default_rng(2026)
    qre(generator)
    gmm(generator)
