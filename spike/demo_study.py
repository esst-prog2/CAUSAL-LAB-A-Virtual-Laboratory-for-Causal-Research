"""
Run the simulation study of the Guided demo page and store every
replication in causal_lab/data/demo_study/results.json.

    python spike/demo_study.py [replications per level]      (default 1000)

Deterministic: replication r of every level uses seed SEED_BASE + r
(causal_lab/simulation_engine/demo_study.py). About 0.16 s per replication.
"""
from __future__ import annotations

import platform
import sys
import time
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "causal_lab"))

from simulation_engine.demo_study import LEVELS, SEED_BASE, run_level, save_study, summarize  # noqa: E402

REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

if __name__ == "__main__":
    start = time.time()
    results = {}
    for level in LEVELS:
        t = time.time()
        results[level] = run_level(level, REPS)
        s = summarize(level, results[level])
        print(f"{level:7s} bias {s.bias:+.3f} coverage {s.coverage:.3f} rejection {s.rejection:.3f} "
              f"detection {s.detection:.3f} coverage|pass {s.coverage_given_pass} ({time.time() - t:.0f} s)", flush=True)
    versions = {"python": platform.python_version()}
    versions.update({p: metadata.version(p) for p in ("numpy", "pandas", "scipy", "statsmodels")})
    save_study(results, {
        "replications_per_level": REPS, "seed_base": SEED_BASE,
        "computed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runtime_seconds": round(time.time() - start), "versions": versions,
        "script": "spike/demo_study.py",
    })
    print(f"saved, {time.time() - start:.0f} s")
