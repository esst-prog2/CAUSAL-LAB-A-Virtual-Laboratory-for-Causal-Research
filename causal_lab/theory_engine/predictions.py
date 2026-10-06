"""
Theory-based predictions and their comparison with causal estimates
(CAUSAL LAB spec: theory-predictions).

A treatment is modelled as a shift of one parameter, theta -> theta + delta.
The predicted effect on each equilibrium strategy and outcome is the
exact difference between the equilibrium re-solved at theta + delta
(warm-started from the baseline) and the baseline equilibrium; the
marginal derivative is reported alongside.

delta can be measured from the data as the parameter's source
evaluated on treated rows minus control rows.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from theory_engine.calibration import CalibrationError, ParameterSource, compute_parameter
from theory_engine.game import Equilibrium, Game, comparative_statics, solve_equilibrium


@dataclass
class Prediction:
    parameter: str
    delta: float
    baseline: Equilibrium
    shifted: Equilibrium
    effects: dict[str, float]          # strategy / outcome -> shifted - baseline
    derivatives: dict[str, float]      # d/dparameter at the baseline


def delta_from_data(df: pd.DataFrame, source: ParameterSource, treatment_column: str, name: str) -> float:
    """Parameter source on treated rows (treatment == 1) minus control rows (== 0)."""
    if source.kind == "manual":
        raise CalibrationError(f"Parameter '{name}' is set manually; a data-based shift needs a data source.")
    if treatment_column not in df.columns:
        raise CalibrationError(f"Treatment column '{treatment_column}' is not in the data.")
    treated = df[df[treatment_column] == 1]
    control = df[df[treatment_column] == 0]
    if treated.empty or control.empty:
        raise CalibrationError(f"Treatment column '{treatment_column}' must contain both 0 and 1.")
    return compute_parameter(treated, source, name) - compute_parameter(control, source, name)


def predict_shift(game: Game, values: dict[str, float], parameter: str, delta: float,
                  baseline: Equilibrium | None = None) -> Prediction:
    if baseline is None:
        result = solve_equilibrium(game, values)
        if not result.found:
            raise ValueError(result.message)
        baseline = result.equilibria[0]
    shifted_values = {**game.parameters, **values, parameter: float(values.get(parameter, game.parameters[parameter])) + delta}
    shifted_result = solve_equilibrium(game, shifted_values, start=baseline.strategies)
    if not shifted_result.found:
        shifted_result = solve_equilibrium(game, shifted_values)
    if not shifted_result.found:
        raise ValueError(f"No equilibrium after shifting {parameter} by {delta:g}: {shifted_result.message}")
    shifted = shifted_result.equilibria[0]
    effects = {k: shifted.strategies[k] - baseline.strategies[k] for k in baseline.strategies}
    effects.update({k: shifted.outcomes[k] - baseline.outcomes[k] for k in baseline.outcomes})
    derivatives = comparative_statics(game, values, parameter, baseline)
    return Prediction(parameter, delta, baseline, shifted, effects, derivatives)


VERDICT_CONSISTENT = "consistent"
VERDICT_MAGNITUDE = "magnitude differs"
VERDICT_SIGN = "sign contradicts"


def compare_with_estimate(predicted: float, estimate: float, ci_low: float, ci_high: float) -> str:
    """Spec rule: inside the CI -> consistent; CI excludes zero on the
    opposite side of the prediction -> sign contradicts; else magnitude differs."""
    if ci_low > ci_high:
        ci_low, ci_high = ci_high, ci_low
    if ci_low <= predicted <= ci_high:
        return VERDICT_CONSISTENT
    if (ci_low > 0 and predicted < 0) or (ci_high < 0 and predicted > 0):
        return VERDICT_SIGN
    return VERDICT_MAGNITUDE


