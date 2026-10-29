"""
The simulation study and the replication shown on the Guided demo page.

1. Simulation study. Does two-way fixed-effects difference-in-differences
   recover a known effect, and does the pre-trend test say when it cannot?
   For each level of diverging pre-trends, R Virtual Worlds are drawn with
   the default design (100 units, 20 periods, treatment at period 10, 30%
   treated, ATT = -0.5, noise SD 1), and in each one the DiD estimate, its
   cluster-robust standard error and the pre-trend test of Break My Design
   are recorded. Performance is summarised as recommended by Morris, White
   & Crowther (2019): bias, empirical SE, RMSE, coverage of the 95% CI and
   rejection rate, each with its Monte Carlo standard error. Coverage among
   the worlds that pass the pre-trend test is reported too: estimating only
   after a passed pretest changes the sampling distribution (Roth 2022).

   Replication r of level k uses seed SEED_BASE + r, so the same r gives the
   same draw of the noise at every level, and any replication can be
   recomputed on its own (tests/test_demo_study.py does).

2. Replication. Card & Krueger (1994), Table 3: mean FTE employment per
   store by state and wave, and the balanced-sample difference-in-
   differences, recomputed from the raw data and compared with the
   published values.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd

from estimators.did import estimate_did
from robustness_engine.stress_test import _check_parallel_trends
from simulation_engine.dgp import VirtualWorldConfig, generate

LEVELS = ("none", "low", "medium", "high", "severe")      # differential_trend intensities
SEED_BASE = 20261029
RESULTS_FILE = Path(__file__).resolve().parent.parent / "data" / "demo_study" / "results.json"


@dataclass(frozen=True)
class Replication:
    seed: int
    true_att: float
    estimate: float
    se: float
    ci_low: float                      # the 95% CI and p-value the app reports for this estimate
    ci_high: float
    p_value: float
    pretest_p: float | None
    pretest_flag: bool                 # the pre-trend check of Break My Design warned


def design(level: str) -> VirtualWorldConfig:
    """The default Virtual World with diverging pre-trends at `level`."""
    return replace(VirtualWorldConfig(), differential_trend=level)


def replicate(level: str, r: int) -> Replication:
    cfg = replace(design(level), seed=SEED_BASE + r)
    df, truth = generate(cfg)
    did = estimate_did(df)
    pretest = _check_parallel_trends(df, "Y", "unit", "period", "treated_unit", cfg.treatment_period)
    return Replication(seed=cfg.seed, true_att=float(truth["true_att"]), estimate=float(did.att),
                       se=float(did.se), ci_low=float(did.ci_low), ci_high=float(did.ci_high),
                       p_value=float(did.p_value), pretest_p=pretest.p_value,
                       pretest_flag=pretest.verdict == "WARNING")


def run_level(level: str, n_reps: int, start: int = 0) -> list[Replication]:
    return [replicate(level, r) for r in range(start, start + n_reps)]


@dataclass(frozen=True)
class Summary:
    level: str
    n_reps: int
    true_att: float
    mean_estimate: float
    bias: float
    bias_mcse: float
    empirical_se: float
    mean_model_se: float
    rmse: float
    coverage: float
    coverage_mcse: float
    rejection: float                   # H0: ATT = 0 rejected at 5%
    rejection_mcse: float
    wrong_sign: float                  # significant at 5% with the sign opposite to the true effect
    detection: float                   # pre-trend test warned
    detection_mcse: float
    n_pass: int                        # worlds where the pre-trend test did not warn
    coverage_given_pass: float | None


def _share(flags: np.ndarray) -> tuple[float, float]:
    p = float(np.mean(flags))
    return p, float(np.sqrt(p * (1 - p) / len(flags)))


def summarize(level: str, reps: list[Replication]) -> Summary:
    est = np.array([r.estimate for r in reps])
    se = np.array([r.se for r in reps])
    truth = np.array([r.true_att for r in reps])
    covered = (np.array([r.ci_low for r in reps]) <= truth) & (truth <= np.array([r.ci_high for r in reps]))
    rejected = np.array([r.p_value for r in reps]) < 0.05
    flagged = np.array([r.pretest_flag for r in reps])
    n = len(reps)
    coverage, coverage_mcse = _share(covered)
    rejection, rejection_mcse = _share(rejected)
    wrong_sign = float(np.mean(rejected & (np.sign(est) != np.sign(truth))))
    detection, detection_mcse = _share(flagged)
    err = est - truth
    passed = ~flagged
    return Summary(
        level=level, n_reps=n, true_att=float(truth.mean()), mean_estimate=float(est.mean()),
        bias=float(err.mean()), bias_mcse=float(err.std(ddof=1) / np.sqrt(n)),
        empirical_se=float(est.std(ddof=1)), mean_model_se=float(se.mean()),
        rmse=float(np.sqrt(np.mean(err ** 2))),
        coverage=coverage, coverage_mcse=coverage_mcse, rejection=rejection, rejection_mcse=rejection_mcse,
        wrong_sign=wrong_sign, detection=detection, detection_mcse=detection_mcse,
        n_pass=int(passed.sum()), coverage_given_pass=float(covered[passed].mean()) if passed.any() else None,
    )


# --------------------------------------------------------------------------
# Stored study (spike/demo_study.py writes it)
# --------------------------------------------------------------------------
def save_study(results: dict[str, list[Replication]], metadata: dict, path: Path = RESULTS_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"metadata": metadata, "seed_base": SEED_BASE,
               "levels": {level: [asdict(r) for r in reps] for level, reps in results.items()}}
    path.write_text(json.dumps(payload, indent=1), encoding="utf-8")


def load_study(path: Path = RESULTS_FILE) -> tuple[dict, dict[str, list[Replication]]] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["metadata"], {level: [Replication(**r) for r in reps]
                                 for level, reps in payload["levels"].items()}


# --------------------------------------------------------------------------
# Card & Krueger (1994), Table 3 (p. 780): mean FTE employment per store,
# standard errors in parentheses. Rows 1-2 use all available observations,
# row 4 the balanced sample of stores observed in both waves.
# --------------------------------------------------------------------------
CARD_KRUEGER_TABLE3 = {
    "fte_before": {"pa": (23.33, 1.35), "nj": (20.44, 0.51), "diff": (-2.89, 1.44)},
    "fte_after": {"pa": (21.17, 0.94), "nj": (21.03, 0.52), "diff": (-0.14, 1.07)},
    "change_balanced": {"pa": (-2.28, 1.25), "nj": (0.47, 0.48), "diff": (2.75, 1.34)},
}


def _mean_se(x: pd.Series) -> tuple[float, float]:
    x = x.dropna()
    return float(x.mean()), float(x.std(ddof=1) / np.sqrt(len(x)))


def _diff(nj: tuple[float, float], pa: tuple[float, float]) -> tuple[float, float]:
    """NJ minus PA, the two samples independent."""
    return nj[0] - pa[0], float(np.hypot(nj[1], pa[1]))


def replicate_card_krueger(df: pd.DataFrame) -> dict[str, dict[str, tuple[float, float]]]:
    """Table 3 rows 1, 2 and 4 recomputed from the store-level data
    (columns unit, period 0/1, treated_unit 1 = New Jersey, Y = FTE)."""
    out = {}
    for row, period in (("fte_before", 0), ("fte_after", 1)):
        wave = df[df["period"] == period]
        pa = _mean_se(wave.loc[wave["treated_unit"] == 0, "Y"])
        nj = _mean_se(wave.loc[wave["treated_unit"] == 1, "Y"])
        out[row] = {"pa": pa, "nj": nj, "diff": _diff(nj, pa)}
    wide = df.pivot_table(index=["unit", "treated_unit"], columns="period", values="Y").dropna()
    change = (wide[1] - wide[0]).rename("change").reset_index()
    pa = _mean_se(change.loc[change["treated_unit"] == 0, "change"])
    nj = _mean_se(change.loc[change["treated_unit"] == 1, "change"])
    out["change_balanced"] = {"pa": pa, "nj": nj, "diff": _diff(nj, pa)}
    return out
