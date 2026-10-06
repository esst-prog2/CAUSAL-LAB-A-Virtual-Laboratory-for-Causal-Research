"""
Virtual World — synthetic Data Generating Process (CAUSAL LAB spec,
Sections 15-16).

Generates a synthetic panel dataset with an explicitly known ground
truth: potential outcomes Y(0), Y(1), and a true Average Treatment
Effect on the Treated (ATT). The researcher can toggle a set of
"causal threats" (confounding, spillovers, staggered adoption,
serial correlation) with an intensity level, exactly as described in
Sections 15-18 of the spec ("Causal Threats Generator").

This lets the app show:

    Estimated ATT = ...
    True ATT      = ...
    Bias          = Estimated - True

which is the pedagogical core of the Virtual Lab / Learning Mode.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from utils.i18n import LocalizedError

INTENSITY_TO_VALUE = {"none": 0.0, "low": 0.3, "medium": 0.7, "high": 1.2, "severe": 2.0}


@dataclass
class VirtualWorldConfig:
    n_units: int = 100
    n_periods: int = 20
    treatment_period: int = 10
    share_treated: float = 0.3
    true_att: float = -0.5

    # Causal threats (spec Section 18)
    confounding: str = "none"          # none|low|medium|high|severe
    spillovers: str = "none"
    serial_correlation: str = "none"
    staggered_adoption: bool = False
    treatment_heterogeneity: str = "none"
    differential_trend: str = "none"   # treated units drift away before treatment
    anticipation: str = "none"         # treated units react one period early
    dynamic_effects: str = "none"      # effect grows with time since adoption

    noise_sd: float = 1.0
    seed: int | None = 42


def generate(config: VirtualWorldConfig) -> tuple[pd.DataFrame, dict]:
    """Generate a synthetic panel dataset.

    Returns
    -------
    df : pandas.DataFrame
        Columns: unit, period, treated_unit, post, treated_now, D,
        Y0, Y1, Y, X1 (a time-invariant covariate).
    truth : dict
        Ground-truth quantities (true_att, per-unit true effects)
        that a real researcher would never observe, used only for
        pedagogical bias evaluation in the Virtual Lab.
    """
    if not 1 <= config.treatment_period < config.n_periods:
        raise LocalizedError("err.dgp_treatment_period")

    rng = np.random.default_rng(config.seed)
    n_units, n_periods = config.n_units, config.n_periods

    n_treated = min(n_units - 1, max(1, int(round(n_units * config.share_treated))))
    unit_ids = np.arange(n_units)

    # Time-invariant covariate, correlated with treatment status if
    # `confounding` is turned on (this is the classic omitted-variable
    # bias channel: X1 affects both selection into treatment and the
    # outcome trend).
    confound_strength = INTENSITY_TO_VALUE[config.confounding]
    x1 = rng.normal(0, 1, size=n_units)
    if confound_strength > 0:
        # Bias unit selection toward high-X1 units: draw exactly
        # n_treated units with probability proportional to a logistic
        # propensity score in X1.
        propensity = 1 / (1 + np.exp(-confound_strength * x1))
        treated_arr = rng.choice(unit_ids, size=n_treated, replace=False,
                                 p=propensity / propensity.sum())
    else:
        treated_arr = rng.choice(unit_ids, size=n_treated, replace=False)
    treated_units = set(int(u) for u in treated_arr)
    is_treated_unit = np.isin(unit_ids, treated_arr)

    # Staggered adoption: treated units start treatment at different
    # times, always strictly inside the observation window so that every
    # treated unit is actually treated at some point.
    if config.staggered_adoption:
        last_start = min(n_periods - 1, config.treatment_period + max(1, n_periods // 3) - 1)
        adoption_period = {
            u: int(rng.integers(config.treatment_period, last_start + 1))
            for u in sorted(treated_units)
        }
    else:
        adoption_period = {u: config.treatment_period for u in sorted(treated_units)}
    # Per-unit adoption period (never-treated units: +infinity).
    adoption = np.full(n_units, np.inf)
    for u, a in adoption_period.items():
        adoption[u] = a

    # Unit fixed effects and time fixed effects (common trend).
    unit_fe = rng.normal(0, 1, size=n_units)
    time_fe = np.cumsum(rng.normal(0.05, 0.1, size=n_periods))

    # Serial correlation in the idiosyncratic error term: stationary
    # AR(1) with marginal standard deviation `noise_sd` in every period.
    rho = min(0.95, INTENSITY_TO_VALUE[config.serial_correlation] / 2.2)
    eps = np.empty((n_periods, n_units))
    eps[0] = rng.normal(0, config.noise_sd, size=n_units)
    for t in range(1, n_periods):
        eps[t] = rho * eps[t - 1] + rng.normal(0, config.noise_sd, size=n_units) * np.sqrt(1 - rho ** 2)

    # Treatment-effect heterogeneity across units.
    het_strength = INTENSITY_TO_VALUE[config.treatment_heterogeneity]
    unit_effect = config.true_att + rng.normal(0, het_strength, size=n_units) if het_strength > 0 \
        else np.full(n_units, config.true_att)

    # Spillovers: control units located "near" a treated unit (here,
    # simplified as units with adjacent id) partially absorb the effect
    # from the first period in which a neighbouring treated unit is
    # treated.
    spill_strength = INTENSITY_TO_VALUE[config.spillovers]
    neighbour_adoption = np.full(n_units, np.inf)
    neighbour_adoption[1:] = np.minimum(neighbour_adoption[1:], adoption[:-1])
    neighbour_adoption[:-1] = np.minimum(neighbour_adoption[:-1], adoption[1:])

    # Panel arrays of shape (n_periods, n_units).
    t_grid = np.arange(n_periods)[:, None]
    treated_now = is_treated_unit[None, :] & (t_grid >= adoption[None, :])

    # Differential trend: treated units' untreated outcome drifts by
    # 0.08 * intensity noise-SDs per period relative to controls
    # (violated parallel trends), centred on the treatment date.
    trend_slope = 0.08 * INTENSITY_TO_VALUE[config.differential_trend] * config.noise_sd
    differential = trend_slope * is_treated_unit[None, :] * (t_grid - config.treatment_period)

    y0 = (unit_fe[None, :] + time_fe[:, None]
          + confound_strength * 0.3 * x1[None, :] * (t_grid / n_periods) + differential + eps)
    # Dynamic effects: a treated unit's effect grows by 25% * intensity of
    # its base effect for every period since its own adoption. Combined
    # with staggered adoption this is exactly the case where two-way
    # fixed effects are biased (Goodman-Bacon 2021).
    growth_rate = 0.25 * INTENSITY_TO_VALUE[config.dynamic_effects]
    exposure = np.where(np.isfinite(adoption)[None, :], np.maximum(t_grid - adoption[None, :], 0), 0)
    effect_now = unit_effect[None, :] * (1 + growth_rate * exposure)
    y1 = y0 + effect_now
    spill_bonus = np.where(
        (spill_strength > 0) & ~is_treated_unit[None, :] & (t_grid >= neighbour_adoption[None, :]),
        spill_strength * unit_effect[None, :] * 0.5,
        0.0,
    )
    # Anticipation: in the period just before its own adoption, a
    # treated unit's outcome already moves by 0.5 * intensity noise-SDs
    # in the direction of the effect, while D is still 0.
    direction = np.sign(config.true_att) if config.true_att != 0 else 1.0
    anticipation_shift = np.where(
        is_treated_unit[None, :] & (t_grid == adoption[None, :] - 1),
        0.5 * INTENSITY_TO_VALUE[config.anticipation] * config.noise_sd * direction,
        0.0,
    )
    y_observed = np.where(treated_now, y1, y0 + spill_bonus + anticipation_shift)

    df = pd.DataFrame(dict(
        unit=np.tile(unit_ids, n_periods),
        period=np.repeat(np.arange(n_periods), n_units),
        treated_unit=np.tile(is_treated_unit.astype(int), n_periods),
        post=np.repeat((np.arange(n_periods) >= config.treatment_period).astype(int), n_units),
        treated_now=treated_now.ravel().astype(int),
        D=treated_now.ravel().astype(int),
        X1=np.tile(x1, n_periods),
        Y0=y0.ravel(),
        Y1=y1.ravel(),
        Y=y_observed.ravel(),
    ))

    # True ATT = mean effect over the treated unit-periods actually observed
    # (what DiD-type estimators target). Without staggering or dynamic
    # effects it equals the mean unit effect among treated units.
    realized_effects = effect_now[treated_now]
    truth = dict(
        true_att=float(np.mean(realized_effects)) if realized_effects.size else float(config.true_att),
        design_att=float(config.true_att),
        treated_units=sorted(treated_units),
        adoption_period=adoption_period,
        confounding=config.confounding,
        spillovers=config.spillovers,
        serial_correlation=config.serial_correlation,
        staggered_adoption=config.staggered_adoption,
        differential_trend=config.differential_trend,
        anticipation=config.anticipation,
    )
    return df, truth
