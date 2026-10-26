"""
The six Causal Methods in one place: their virtual world, how a column
mapping and options become an estimator call, and the options a generated
world implies. Shared by the Causal Methods page, the per-method Monte Carlo,
stress test and code generator, so they all run a method the same way.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from estimators.common import MethodResult
from estimators.dml import estimate_dml
from estimators.iv import estimate_iv
from estimators.matching import estimate_matching
from estimators.rct import estimate_rct
from estimators.rdd import estimate_rdd
from estimators.synthetic_control import estimate_synthetic_control
from simulation_engine import method_worlds as mw

METHOD_KEYS = ("rct", "matching", "iv", "rdd", "synthetic_control", "dml")


@dataclass(frozen=True)
class MethodWorld:
    config_cls: type
    generate: Callable[..., tuple[pd.DataFrame, dict]]


WORLDS: dict[str, MethodWorld] = {
    "rct": MethodWorld(mw.RCTWorldConfig, mw.rct_world),
    "matching": MethodWorld(mw.MatchingWorldConfig, mw.matching_world),
    "iv": MethodWorld(mw.IVWorldConfig, mw.iv_world),
    "rdd": MethodWorld(mw.RDDWorldConfig, mw.rdd_world),
    "synthetic_control": MethodWorld(mw.SyntheticControlWorldConfig, mw.synthetic_control_world),
    "dml": MethodWorld(mw.DMLWorldConfig, mw.dml_world),
}


def virtual_options(method: str, truth: dict) -> dict:
    """Estimator options a generated world implies (cutoff, treated unit...)."""
    roles = truth["roles"]
    if method == "rdd":
        return {"cutoff": roles["cutoff"], "bandwidth": None, "inference": "conventional"}
    if method == "synthetic_control":
        return {"treated_unit": roles["treated_unit"], "treatment_period": roles["treatment_period"]}
    return {}


def run_method(method: str, df: pd.DataFrame, m: dict, options: dict, light: bool = False) -> MethodResult:
    """Run `method` on `df` with the column mapping `m` and its options.
    `light` skips side results the Monte Carlo does not use (the IPW bootstrap)."""
    if method == "rct":
        return estimate_rct(df, m["outcome"], m["treatment"], m.get("covariates"))
    if method == "matching":
        return estimate_matching(df, m["outcome"], m["treatment"], m.get("covariates"),
                                 n_bootstrap=0 if light else None)
    if method == "iv":
        return estimate_iv(df, m["outcome"], m["treatment"], m.get("instruments"), m.get("controls"))
    if method == "rdd":
        return estimate_rdd(df, m["outcome"], m["running"], options["cutoff"], options.get("bandwidth"),
                            treatment_col=m.get("treatment"), inference=options.get("inference", "conventional"))
    if method == "synthetic_control":
        return estimate_synthetic_control(df, m["unit"], m["period"], m["outcome"],
                                          options["treated_unit"], options["treatment_period"],
                                          covariate_cols=m.get("covariates"))
    if method == "dml":
        return estimate_dml(df, m["outcome"], m["treatment"], m.get("covariates"))
    raise KeyError(method)
