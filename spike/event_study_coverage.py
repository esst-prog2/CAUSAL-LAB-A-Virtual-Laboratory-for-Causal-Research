"""
Coverage of the event study's own 95% intervals (estimators/event_study.py,
the app's defaults: window 6, clustered by unit, Student t with G - 1 df) on
the study's worlds without violation (300 worlds): the post coefficients
should cover -0.5 and the pre coefficients 0, each 95% of the time.

    python spike/event_study_coverage.py
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "causal_lab"))

from estimators.event_study import estimate_event_study  # noqa: E402
from simulation_engine.demo_study import SEED_BASE, design  # noqa: E402
from simulation_engine.dgp import generate  # noqa: E402

N = 300
hits: dict[int, list[bool]] = {}
for r in range(N):
    cfg = replace(design("differential_trend", "none"), seed=SEED_BASE + r)
    df, truth = generate(cfg)
    es = estimate_event_study(df, fixed_treatment_period=cfg.treatment_period)
    for row in es.coefficients.itertuples():
        if row.rel_period == -1:
            continue
        target = truth["true_att"] if row.rel_period >= 0 else 0.0
        hits.setdefault(int(row.rel_period), []).append(row.ci_low <= target <= row.ci_high)
for k in sorted(hits):
    print(f"k = {k:+d}: coverage {np.mean(hits[k]):.3f}")
allc = np.concatenate([np.array(v) for v in hits.values()])
print(f"all coefficients: {allc.mean():.3f} (Monte Carlo SE per coefficient ~{np.sqrt(.95 * .05 / N):.3f})")
