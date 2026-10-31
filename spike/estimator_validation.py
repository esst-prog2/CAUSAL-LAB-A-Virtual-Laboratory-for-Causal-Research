"""
Validation study of every estimator: bias, standard errors, coverage and
the size and power of its test, with Monte Carlo standard errors
(Morris, White & Crowther 2019).

For each method, three kinds of scenario are drawn from its virtual world:
  - default: the world of the Causal Methods page (bias, coverage, SE / SD, power);
  - null: the same world with a true effect of 0 (size: how often the test
    rejects "no effect" at 5% although there is none; should be about 5%);
  - small: a small sample, where standard errors are most often too optimistic.
plus the RDD with robust bias-corrected inference, IV with a weak
instrument, and Callaway & Sant'Anna on staggered Virtual Worlds.

    python spike/estimator_validation.py OUTPUT [scenario-label ...]

Writes OUTPUT.json (every replication) and OUTPUT.md (the table); OUTPUT
names go to spike/ and must not exist. Replication r uses seed r.
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "causal_lab"))

from estimators.registry import WORLDS, run_method, virtual_options     # noqa: E402
from estimators.staggered_did import estimate_staggered_did              # noqa: E402
from simulation_engine.dgp import VirtualWorldConfig, generate           # noqa: E402
from utils.i18n import LocalizedError                                    # noqa: E402

warnings.filterwarnings("ignore")


@dataclass(frozen=True)
class Scenario:
    label: str
    method: str
    changes: dict
    reps: int = 1000
    options: dict | None = None


EFFECT = {"rct": "ate", "matching": "att", "iv": "effect", "rdd": "effect", "synthetic_control": "effect",
          "dml": "theta"}
SMALL = {"rct": {"n": 60}, "matching": {"n": 200}, "iv": {"n": 200}, "rdd": {"n": 400},
         "synthetic_control": {"n_donors": 8}, "dml": {"n": 300}}

SCENARIOS: list[Scenario] = []
for m in EFFECT:
    reps = 200 if m == "dml" else 1000
    SCENARIOS += [Scenario(f"{m}/default", m, {}, reps),
                  Scenario(f"{m}/null", m, {EFFECT[m]: 0.0}, reps),
                  Scenario(f"{m}/small", m, SMALL[m], reps)]
SCENARIOS += [Scenario("rdd/robust", "rdd", {}, 1000, {"inference": "robust"}),
              Scenario("rdd/robust-small", "rdd", SMALL["rdd"], 1000, {"inference": "robust"}),
              Scenario("iv/weak", "iv", {"instrument_strength": 0.3}, 1000),
              Scenario("staggered/default", "staggered", {}, 500),
              Scenario("staggered/null", "staggered", {"true_att": 0.0}, 500)]


def run(sc: Scenario) -> list[dict]:
    out = []
    for r in range(sc.reps):
        try:
            if sc.method == "staggered":
                cfg = replace(VirtualWorldConfig(staggered_adoption=True), seed=r, **sc.changes)
                df, truth = generate(cfg)
                res = estimate_staggered_did(df)
                # The staggered result has no p-value: the normal test its CI uses.
                out.append(dict(seed=r, truth=float(truth["true_att"]), estimate=float(res.att), se=float(res.se),
                                ci_low=float(res.ci_low), ci_high=float(res.ci_high),
                                p_value=float(2 * stats.norm.sf(abs(res.att / res.se)))))
                continue
            world = WORLDS[sc.method]
            cfg = replace(world.config_cls(), seed=r, **sc.changes)
            df, truth = world.generate(cfg)
            res = run_method(sc.method, df, dict(truth["roles"]),
                             {**virtual_options(sc.method, truth), **(sc.options or {})}, light=True)
            out.append(dict(seed=r, truth=float(truth["true_effect"]), estimate=float(res.estimate),
                            se=None if res.se is None else float(res.se),
                            ci_low=None if res.ci_low is None else float(res.ci_low),
                            ci_high=None if res.ci_high is None else float(res.ci_high),
                            p_value=None if res.p_value is None else float(res.p_value)))
        except LocalizedError:
            out.append(dict(seed=r, failed=True))
    return out


def summarize(reps: list[dict]) -> dict:
    ok = [r for r in reps if not r.get("failed")]
    est = np.array([r["estimate"] for r in ok])
    truth = np.array([r["truth"] for r in ok])
    err = est - truth
    n = len(ok)
    s = dict(n=n, failed=len(reps) - n, truth=float(truth.mean()), bias=float(err.mean()),
             bias_mcse=float(err.std(ddof=1) / np.sqrt(n)), emp_sd=float(est.std(ddof=1)),
             rmse=float(np.sqrt(np.mean(err ** 2))))
    if all(r["se"] is not None for r in ok):
        se = np.array([r["se"] for r in ok])
        cov = (np.array([r["ci_low"] for r in ok]) <= truth) & (truth <= np.array([r["ci_high"] for r in ok]))
        s.update(mean_se=float(se.mean()), se_ratio=float(se.mean() / est.std(ddof=1)),
                 coverage=float(cov.mean()), coverage_mcse=float(np.sqrt(cov.mean() * (1 - cov.mean()) / n)))
    if all(r["p_value"] is not None for r in ok):
        rej = np.array([r["p_value"] < 0.05 for r in ok])
        s.update(rejection=float(rej.mean()), rejection_mcse=float(np.sqrt(rej.mean() * (1 - rej.mean()) / n)))
    return s


def table(results: dict) -> str:
    lines = ["| Scenario | Worlds | Failed | True effect | Bias (MCSE) | SE / SD | Coverage 95% (MCSE) | "
             "Rejects H0: effect = 0 at 5% (MCSE) |", "|---|---|---|---|---|---|---|---|"]
    for label, s in results.items():
        cov = f"{100 * s['coverage']:.1f}% ({100 * s['coverage_mcse']:.1f})" if "coverage" in s else "—"
        rej = f"{100 * s['rejection']:.1f}% ({100 * s['rejection_mcse']:.1f})" if "rejection" in s else "—"
        ratio = f"{s['se_ratio']:.3f}" if "se_ratio" in s else "—"
        lines.append(f"| {label} | {s['n']} | {s['failed']} | {s['truth']:+.3f} | {s['bias']:+.4f} ({s['bias_mcse']:.4f}) "
                     f"| {ratio} | {cov} | {rej} |")
    return "\n".join(lines)


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out = out if out.is_absolute() else Path(__file__).resolve().parent / out
    only = set(sys.argv[2:])
    todo = [sc for sc in SCENARIOS if not only or sc.label in only]
    for ext in (".json", ".md"):
        assert not out.with_suffix(ext).exists(), f"{out.with_suffix(ext)} exists"
    raw, results = {}, {}
    for sc in todo:
        t = time.time()
        raw[sc.label] = run(sc)
        results[sc.label] = summarize(raw[sc.label])
        s = results[sc.label]
        print(f"{sc.label:22s} bias {s['bias']:+.4f} se/sd {s.get('se_ratio', float('nan')):.3f} "
              f"cov {s.get('coverage', float('nan')):.3f} rej {s.get('rejection', float('nan')):.3f} "
              f"failed {s['failed']} ({time.time() - t:.0f} s)", flush=True)
    out.with_suffix(".json").write_text(json.dumps({"results": results, "replications": raw}), encoding="utf-8")
    out.with_suffix(".md").write_text(table(results) + "\n", encoding="utf-8")
    print(table(results))
