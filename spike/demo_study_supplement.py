"""
Compute the supplement of the simulation study: effects that differ across
units (simulation_engine.demo_study.SUPPLEMENT), stored in
causal_lab/data/demo_study/supplement_unit_heterogeneity.json, apart from
the four threats of results.json.

    python spike/demo_study_supplement.py [replications]

Same design, seeds (SEED_BASE + r), estimator and pre-trend test as the main
study; about 0.2 s per replication.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "causal_lab"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from demo_study import _versions  # noqa: E402
from simulation_engine.demo_study import (LEVELS, SEED_BASE, SUPPLEMENT, SUPPLEMENT_FILE, run_level,  # noqa: E402
                                          save_study, summarize)


def main() -> None:
    from datetime import datetime, timezone
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    start = time.time()
    study = {}
    for threat in SUPPLEMENT:
        study[threat] = {}
        for level in LEVELS:
            t = time.time()
            study[threat][level] = run_level(threat, level, reps)
            s = summarize(level, study[threat][level])
            print(f"{threat} {level:7s} true {s.true_att:+.3f} bias {s.bias:+.4f} ({s.bias_share:.3f}) "
                  f"coverage {s.coverage:.3f} detection {s.detection:.3f} acceptable {s.acceptable} "
                  f"({time.time() - t:.0f} s)", flush=True)
    meta = {"replications_per_level": reps, "seed_base": SEED_BASE,
            "computed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "runtime_seconds": round(time.time() - start), "versions": _versions(),
            "script": "spike/demo_study_supplement.py", "threats": list(study),
            "note": "Supplement to results.json, added 2026-11-22: effects that differ across units."}
    save_study(study, meta, SUPPLEMENT_FILE)


if __name__ == "__main__":
    main()
