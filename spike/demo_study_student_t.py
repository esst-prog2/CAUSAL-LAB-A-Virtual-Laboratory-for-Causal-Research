"""
One-off migration of the stored Guided Demo study (2026-11-07), when the DiD interval
went from normal to Student t with G - 1 degrees of freedom. Nothing is re-simulated:
estimates, standard errors and pre-trend tests are unchanged, and the interval and
p-value are deterministic functions of them. tests/test_demo_study.py recomputes some
replications from their seeds and checks that they match the migrated values.

    python spike/demo_study_student_t.py
"""
from __future__ import annotations

import json
from pathlib import Path

from scipy import stats

PATH = Path(__file__).resolve().parent.parent / "causal_lab" / "data" / "demo_study" / "results.json"
N_UNITS = 100


def main() -> None:
    payload = json.loads(PATH.read_text(encoding="utf-8"))
    crit = float(stats.t.ppf(0.975, N_UNITS - 1))
    n = 0
    for levels in payload["threats"].values():
        for reps in levels.values():
            for r in reps:
                r["ci_low"], r["ci_high"] = r["estimate"] - crit * r["se"], r["estimate"] + crit * r["se"]
                r["p_value"] = float(2 * stats.t.sf(abs(r["estimate"] / r["se"]), N_UNITS - 1))
                n += 1
    payload["metadata"]["inference_migration"] = ("2026-11-07: interval and p-value recomputed with Student t, "
                                                  f"{N_UNITS - 1} df (spike/demo_study_student_t.py); estimates, SEs "
                                                  "and pre-trend tests unchanged, computed 2026-10-30.")
    PATH.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print("replications migrated:", n)


if __name__ == "__main__":
    main()
