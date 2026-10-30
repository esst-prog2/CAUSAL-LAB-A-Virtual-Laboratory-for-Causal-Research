"""
Run the simulation study of the Guided demo page and store every
replication in causal_lab/data/demo_study/results.json.

    python spike/demo_study.py [replications] [threat ...]
        computes the given threats (all by default) and merges them into the
        stored study, keeping the threats it does not recompute;
    python spike/demo_study.py [replications] THREAT --part
        computes one threat into part_<THREAT>.json (to run threats in
        parallel processes), and
    python spike/demo_study.py --merge
        merges the part files into the stored study.

Deterministic: replication r uses seed SEED_BASE + r at every threat and
level (causal_lab/simulation_engine/demo_study.py). About 0.2 s per
replication on a laptop.
"""
from __future__ import annotations

import json
import platform
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "causal_lab"))

from simulation_engine.demo_study import (LEVELS, RESULTS_FILE, SEED_BASE, THREATS, Replication,  # noqa: E402
                                          load_study, run_level, save_study, summarize)


def _versions() -> dict:
    out = {"python": platform.python_version()}
    out.update({p: metadata.version(p) for p in ("numpy", "pandas", "scipy", "statsmodels")})
    return out


def compute(threat: str, reps: int) -> dict[str, list[Replication]]:
    out = {}
    for level in LEVELS:
        t = time.time()
        out[level] = run_level(threat, level, reps)
        s = summarize(level, out[level])
        print(f"{threat:18s} {level:7s} bias {s.bias:+.3f} coverage {s.coverage:.3f} detection {s.detection:.3f} "
              f"acceptable {s.acceptable} ({time.time() - t:.0f} s)", flush=True)
    return out


def store(study: dict, reps: int, runtime: float, previous: dict | None) -> None:
    meta = dict(previous or {})
    meta.update({"replications_per_level": reps, "seed_base": SEED_BASE,
                 "computed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "versions": _versions(), "script": "spike/demo_study.py",
                 "threats": list(study)})
    meta["runtime_seconds"] = round(meta.get("runtime_seconds", 0) + runtime)
    save_study(study, meta)


if __name__ == "__main__":
    args = sys.argv[1:]
    stored = load_study()
    previous_meta, study = stored if stored else ({}, {})
    if args == ["--merge"]:
        for part in sorted(RESULTS_FILE.parent.glob("part_*.json")):
            payload = json.loads(part.read_text(encoding="utf-8"))
            study[payload["threat"]] = {lv: [Replication(**r) for r in reps] for lv, reps in payload["levels"].items()}
            previous_meta["runtime_seconds"] = previous_meta.get("runtime_seconds", 0) + payload["runtime_seconds"]
            part.unlink()
        reps = {len(v) for levels in study.values() for v in levels.values()}
        assert len(reps) == 1, f"threats have different replication counts: {reps}"
        study = {t: study[t] for t in THREATS if t in study}
        store(study, reps.pop(), 0, previous_meta)
        print("merged:", list(study))
        sys.exit(0)

    part = "--part" in args
    args = [a for a in args if a != "--part"]
    reps = int(args[0]) if args and args[0].isdigit() else 1000
    threats = [a for a in args if not a.isdigit()] or list(THREATS)
    start = time.time()
    if part:
        (threat,) = threats
        levels = compute(threat, reps)
        RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        (RESULTS_FILE.parent / f"part_{threat}.json").write_text(json.dumps(
            {"threat": threat, "runtime_seconds": round(time.time() - start),
             "levels": {lv: [asdict(r) for r in rs] for lv, rs in levels.items()}}), encoding="utf-8")
        print(f"part saved, {time.time() - start:.0f} s")
    else:
        for threat in threats:
            study[threat] = compute(threat, reps)
        study = {t: study[t] for t in THREATS if t in study}
        store(study, reps, time.time() - start, previous_meta)
        print(f"saved, {time.time() - start:.0f} s")
