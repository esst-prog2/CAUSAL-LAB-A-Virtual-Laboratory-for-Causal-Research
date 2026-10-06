"""
Virtual worlds for the Causal Methods page: one synthetic data
generator per identification strategy (RCT, Matching, IV, RDD,
Synthetic Control, DML).

Each generator builds data that satisfies its method's identifying
assumption, with an explicitly known true effect, and exposes the
parameters that make the method succeed or fail (instrument strength,
confounding strength, non-linearity...). Like `dgp.generate`, each
returns `(df, truth)`, where `truth["true_effect"]` is what the
estimator should recover.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def _sigmoid(x):
    return 1 / (1 + np.exp(-x))


# --------------------------------------------------------------------------
# Randomized Controlled Trial
# --------------------------------------------------------------------------
@dataclass
class RCTWorldConfig:
    n: int = 500
    ate: float = 1.0
    effect_heterogeneity: float = 0.5   # sd of individual effects
    covariate_strength: float = 1.0     # how much X predicts Y
    share_treated: float = 0.5
    noise_sd: float = 1.0
    seed: int = 42


def rct_world(cfg: RCTWorldConfig) -> tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(cfg.seed)
    x = rng.normal(size=(cfg.n, 3))
    d = (rng.random(cfg.n) < cfg.share_treated).astype(int)
    tau = cfg.ate + cfg.effect_heterogeneity * x[:, 0]
    y0 = cfg.covariate_strength * (x @ np.array([1.0, 0.5, -0.5])) + rng.normal(0, cfg.noise_sd, cfg.n)
    y = y0 + d * tau
    df = pd.DataFrame({"Y": y, "D": d, "X1": x[:, 0], "X2": x[:, 1], "X3": x[:, 2]})
    return df, dict(true_effect=float(tau.mean()), estimand="ATE",
                    roles=dict(outcome="Y", treatment="D", covariates=["X1", "X2", "X3"]))


# --------------------------------------------------------------------------
# Matching / Propensity Score (selection on observables)
# --------------------------------------------------------------------------
@dataclass
class MatchingWorldConfig:
    n: int = 1000
    att: float = 1.0
    confounding_strength: float = 1.0   # how strongly X drives selection and Y
    effect_heterogeneity: float = 0.5   # effect varies with X1 -> ATT != ATE
    noise_sd: float = 1.0
    seed: int = 42


def matching_world(cfg: MatchingWorldConfig) -> tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(cfg.seed)
    x = rng.normal(size=(cfg.n, 3))
    index = cfg.confounding_strength * (0.8 * x[:, 0] + 0.5 * x[:, 1] - 0.3 * x[:, 2]) - 0.5
    d = (rng.random(cfg.n) < _sigmoid(index)).astype(int)
    tau = cfg.att + cfg.effect_heterogeneity * (x[:, 0] - x[d == 1, 0].mean())
    y0 = cfg.confounding_strength * (1.5 * x[:, 0] + x[:, 1] + 0.5 * x[:, 2]) + rng.normal(0, cfg.noise_sd, cfg.n)
    y = y0 + d * tau
    df = pd.DataFrame({"Y": y, "D": d, "X1": x[:, 0], "X2": x[:, 1], "X3": x[:, 2]})
    return df, dict(true_effect=float(tau[d == 1].mean()), estimand="ATT",
                    true_ate=float(tau.mean()),
                    roles=dict(outcome="Y", treatment="D", covariates=["X1", "X2", "X3"]))


# --------------------------------------------------------------------------
# Instrumental Variables
# --------------------------------------------------------------------------
@dataclass
class IVWorldConfig:
    n: int = 1000
    effect: float = 1.0
    instrument_strength: float = 1.0    # first-stage coefficient of Z on D
    endogeneity: float = 1.0            # unobserved U drives both D and Y
    noise_sd: float = 1.0
    seed: int = 42


def iv_world(cfg: IVWorldConfig) -> tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(cfg.seed)
    u = rng.normal(size=cfg.n)                 # unobserved confounder
    x = rng.normal(size=cfg.n)                 # observed exogenous control
    z = rng.binomial(1, 0.5, cfg.n)            # randomly assigned instrument
    d = (cfg.instrument_strength * z + cfg.endogeneity * u + 0.3 * x
         + rng.normal(size=cfg.n) > 0.5).astype(int)
    y = cfg.effect * d + 1.5 * cfg.endogeneity * u + 0.5 * x + rng.normal(0, cfg.noise_sd, cfg.n)
    df = pd.DataFrame({"Y": y, "D": d, "Z": z, "X": x})
    return df, dict(true_effect=float(cfg.effect), estimand="LATE (constant effect)",
                    roles=dict(outcome="Y", treatment="D", instruments=["Z"], controls=["X"]))


# --------------------------------------------------------------------------
# Regression Discontinuity (sharp)
# --------------------------------------------------------------------------
@dataclass
class RDDWorldConfig:
    n: int = 2000
    effect: float = 1.0
    cutoff: float = 0.0
    curvature: float = 1.0              # non-linearity of E[Y|X]
    noise_sd: float = 0.5
    seed: int = 42


def rdd_world(cfg: RDDWorldConfig) -> tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(cfg.seed)
    x = rng.uniform(cfg.cutoff - 1, cfg.cutoff + 1, cfg.n)
    xc = x - cfg.cutoff
    d = (x >= cfg.cutoff).astype(int)
    mu = 0.5 + 0.8 * xc + cfg.curvature * (-0.6 * xc ** 2 + 0.4 * xc ** 3)
    y = mu + cfg.effect * d + rng.normal(0, cfg.noise_sd, cfg.n)
    df = pd.DataFrame({"Y": y, "X": x, "D": d})
    return df, dict(true_effect=float(cfg.effect), estimand="Effect at the cutoff",
                    roles=dict(outcome="Y", running="X", cutoff=cfg.cutoff))


# --------------------------------------------------------------------------
# Synthetic Control
# --------------------------------------------------------------------------
@dataclass
class SyntheticControlWorldConfig:
    n_donors: int = 20
    n_periods: int = 30
    treatment_period: int = 20
    effect: float = -2.0
    n_factors: int = 2
    noise_sd: float = 0.3
    seed: int = 42


def synthetic_control_world(cfg: SyntheticControlWorldConfig) -> tuple[pd.DataFrame, dict]:
    if not 2 <= cfg.treatment_period < cfg.n_periods:
        raise ValueError("treatment_period must satisfy 2 <= treatment_period < n_periods")
    rng = np.random.default_rng(cfg.seed)
    n_units = cfg.n_donors + 1
    trend = np.cumsum(rng.normal(0.1, 0.2, cfg.n_periods))
    factors = np.cumsum(rng.normal(0, 0.5, (cfg.n_periods, cfg.n_factors)), axis=0)
    donor_loadings = rng.uniform(0, 2, (cfg.n_donors, cfg.n_factors))
    donor_fe = rng.normal(5, 1, cfg.n_donors)
    # The treated unit is a sparse convex combination of donors, so a
    # synthetic control that reproduces it exists by construction.
    true_w = np.zeros(cfg.n_donors)
    support = rng.choice(cfg.n_donors, size=min(4, cfg.n_donors), replace=False)
    true_w[support] = rng.dirichlet(np.ones(len(support)))
    loadings = np.vstack([true_w @ donor_loadings, donor_loadings])
    unit_fe = np.concatenate([[true_w @ donor_fe], donor_fe])

    y0 = (unit_fe[None, :] + trend[:, None] + factors @ loadings.T
          + rng.normal(0, cfg.noise_sd, (cfg.n_periods, n_units)))
    effect_path = np.where(np.arange(cfg.n_periods) >= cfg.treatment_period, cfg.effect, 0.0)
    y = y0.copy()
    y[:, 0] += effect_path

    names = ["treated"] + [f"donor_{j:02d}" for j in range(1, cfg.n_donors + 1)]
    df = pd.DataFrame({
        "unit": np.tile(names, cfg.n_periods),
        "period": np.repeat(np.arange(cfg.n_periods), n_units),
        "Y": y.ravel(),
    })
    return df, dict(true_effect=float(cfg.effect), estimand="Mean post-treatment effect on the treated unit",
                    true_weights=dict(zip(names[1:], true_w.round(4))),
                    roles=dict(unit="unit", period="period", outcome="Y",
                               treated_unit="treated", treatment_period=cfg.treatment_period))


# --------------------------------------------------------------------------
# Double Machine Learning (partially linear model)
# --------------------------------------------------------------------------
@dataclass
class DMLWorldConfig:
    n: int = 1000
    theta: float = 0.5
    n_covariates: int = 10
    nonlinearity: float = 1.0           # 0 = linear confounding, 1+ = strongly non-linear
    noise_sd: float = 1.0
    seed: int = 42


def dml_world(cfg: DMLWorldConfig) -> tuple[pd.DataFrame, dict]:
    if cfg.n_covariates < 3:
        raise ValueError("n_covariates must be at least 3")
    rng = np.random.default_rng(cfg.seed)
    x = rng.uniform(-2, 2, (cfg.n, cfg.n_covariates))
    a = cfg.nonlinearity
    m = 0.5 * x[:, 0] + a * (np.sin(2 * x[:, 0]) + 0.5 * x[:, 1] ** 2) + 0.3 * x[:, 2]
    g = x[:, 0] + a * (2 * np.cos(x[:, 0]) * x[:, 1] + x[:, 1] ** 2 + np.abs(x[:, 2]))
    d = m + rng.normal(0, 1, cfg.n)
    y = cfg.theta * d + g + rng.normal(0, cfg.noise_sd, cfg.n)
    cols = {f"X{k + 1}": x[:, k] for k in range(cfg.n_covariates)}
    df = pd.DataFrame({"Y": y, "D": d, **cols})
    return df, dict(true_effect=float(cfg.theta), estimand="theta (partially linear model)",
                    roles=dict(outcome="Y", treatment="D", covariates=list(cols)))
