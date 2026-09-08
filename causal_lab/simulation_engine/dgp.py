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
    rng = np.random.default_rng(config.seed)

    n_treated = max(1, int(round(config.n_units * config.share_treated)))
    unit_ids = np.arange(config.n_units)
    treated_units = set(rng.choice(unit_ids, size=n_treated, replace=False).tolist())

    # Time-invariant covariate, correlated with treatment status if
    # `confounding` is turned on (this is the classic omitted-variable
    # bias channel: X1 affects both selection into treatment and the
    # outcome trend).
    confound_strength = INTENSITY_TO_VALUE[config.confounding]
    x1 = rng.normal(0, 1, size=config.n_units)
    if confound_strength > 0:
        # Bias unit selection toward high-X1 units.
        propensity = 1 / (1 + np.exp(-confound_strength * x1))
        treated_units = set(
            unit_ids[rng.random(config.n_units) < propensity * config.share_treated * 2][:n_treated].tolist()
        )
        if len(treated_units) < 1:
            treated_units = {int(unit_ids[np.argmax(x1)])}

    # Staggered adoption: treated units start treatment at different times.
    if config.staggered_adoption:
        adoption_period = {
            u: int(rng.integers(config.treatment_period, config.treatment_period + config.n_periods // 3))
            for u in treated_units
        }
    else:
        adoption_period = {u: config.treatment_period for u in treated_units}

    # Unit fixed effects and time fixed effects (common trend).
    unit_fe = rng.normal(0, 1, size=config.n_units)
    time_fe = np.cumsum(rng.normal(0.05, 0.1, size=config.n_periods))

    # Serial correlation in the idiosyncratic error term (AR(1)).
    rho = min(0.95, INTENSITY_TO_VALUE[config.serial_correlation] / 2.2)

    # Treatment-effect heterogeneity across units.
    het_strength = INTENSITY_TO_VALUE[config.treatment_heterogeneity]
    unit_effect = config.true_att + rng.normal(0, het_strength, size=config.n_units) if het_strength > 0 \
        else np.full(config.n_units, config.true_att)

    # Spillovers: control units located "near" a treated unit (here,
    # simplified as units with adjacent id) partially absorb the effect.
    spill_strength = INTENSITY_TO_VALUE[config.spillovers]

    rows = []
    eps_prev = np.zeros(config.n_units)
    for t in range(config.n_periods):
        eps = rho * eps_prev + rng.normal(0, config.noise_sd, size=config.n_units) * np.sqrt(1 - rho ** 2)
        eps_prev = eps
        for u in unit_ids:
            is_treated_unit = u in treated_units
            is_treated_now = is_treated_unit and t >= adoption_period.get(u, 10 ** 9)

            y0 = unit_fe[u] + time_fe[t] + confound_strength * 0.3 * x1[u] * (t / config.n_periods) + eps[u]

            spill_bonus = 0.0
            if spill_strength > 0 and not is_treated_unit:
                # A control unit adjacent (id distance 1) to *any*
                # currently-treated unit leaks part of the effect.
                neighbours_treated = any(
                    (abs(u - tu) == 1) and (t >= adoption_period.get(tu, 10 ** 9))
                    for tu in treated_units
                )
                if neighbours_treated:
                    spill_bonus = spill_strength * unit_effect[u] * 0.5

            y1 = y0 + unit_effect[u]
            y_observed = y1 if is_treated_now else (y0 + spill_bonus)

            rows.append(dict(
                unit=int(u),
                period=int(t),
                treated_unit=int(is_treated_unit),
                post=int(t >= config.treatment_period),
                treated_now=int(is_treated_now),
                D=int(is_treated_now),
                X1=float(x1[u]),
                Y0=float(y0),
                Y1=float(y1),
                Y=float(y_observed),
            ))

    df = pd.DataFrame(rows)

    realized_effects = [unit_effect[u] for u in treated_units]
    truth = dict(
        true_att=float(np.mean(realized_effects)) if realized_effects else float(config.true_att),
        design_att=float(config.true_att),
        treated_units=sorted(treated_units),
        adoption_period=adoption_period,
        confounding=config.confounding,
        spillovers=config.spillovers,
        serial_correlation=config.serial_correlation,
        staggered_adoption=config.staggered_adoption,
    )
    return df, truth
