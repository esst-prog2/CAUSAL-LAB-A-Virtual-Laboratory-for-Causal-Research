"""
Calibrating a theoretical model on data (CAUSAL LAB spec:
theory-data-calibration).

Every model parameter gets one source:

    manual      a fixed value
    statistic   mean / median / sd / min / max / sum / count of a column,
                optionally on rows where another column equals a value
    regression  slope or intercept of an OLS regression y ~ x

The dataset's structure (cross-section, panel, repeated
cross-section, time series) decides the default scope of
computation. The equilibrium is then solved once for the pooled
sample, once per group, or once per period (an equilibrium path),
warm-starting each solve from the previous unit's equilibrium so the
path stays on one equilibrium branch.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from theory_engine.game import Game, solve_equilibrium
from utils.i18n import LocalizedError, Msg

STATISTICS = ("mean", "median", "sd", "min", "max", "sum", "count")


class CalibrationError(LocalizedError):
    pass


@dataclass
class ParameterSource:
    kind: str = "manual"                     # manual | statistic | regression
    value: float | None = None               # manual
    statistic: str = "mean"                  # statistic
    column: str | None = None
    filter_column: str | None = None
    filter_value: object = None
    y: str | None = None                     # regression
    x: str | None = None
    coefficient: str = "slope"               # slope | intercept

    def describe(self) -> Msg:
        if self.kind == "manual":
            return Msg("source.manual", value=self.value)
        if self.kind == "statistic":
            if self.filter_column:
                return Msg("source.statistic_filtered", stat=Msg(f"stat.{self.statistic}"), column=self.column,
                           filter=self.filter_column, value=self.filter_value)
            return Msg("source.statistic", stat=Msg(f"stat.{self.statistic}"), column=self.column)
        return Msg("source.regression", coef=Msg(f"coef.{self.coefficient}"), y=self.y, x=self.x)


def _numeric(df: pd.DataFrame, column: str | None, name: str) -> pd.Series:
    if column is None or column not in df.columns:
        raise CalibrationError("err.cal_missing_column", name=name, column=column)
    if not pd.api.types.is_numeric_dtype(df[column]):
        raise CalibrationError("err.cal_not_numeric", name=name, column=column)
    return df[column]


def compute_parameter(df: pd.DataFrame | None, source: ParameterSource, name: str) -> float:
    if source.kind == "manual":
        if source.value is None:
            raise CalibrationError("err.cal_no_value", name=name)
        return float(source.value)
    if df is None:
        raise CalibrationError("err.cal_needs_data", name=name)

    if source.kind == "statistic":
        data = df
        if source.filter_column:
            if source.filter_column not in df.columns:
                raise CalibrationError("err.cal_missing_filter", name=name, column=source.filter_column)
            data = df[df[source.filter_column].astype(str) == str(source.filter_value)]
            if data.empty:
                raise CalibrationError("err.cal_no_rows", name=name, column=source.filter_column,
                                       value=source.filter_value)
        if source.statistic == "count":
            return float(len(data))
        series = _numeric(data, source.column, name).dropna()
        if series.empty:
            raise CalibrationError("err.cal_empty", name=name, column=source.column)
        stat = {"mean": series.mean, "median": series.median, "sd": lambda: series.std(ddof=1),
                "min": series.min, "max": series.max, "sum": series.sum}.get(source.statistic)
        if stat is None:
            raise CalibrationError("err.cal_unknown_stat", name=name, stat=source.statistic)
        return float(stat())

    if source.kind == "regression":
        y = _numeric(df, source.y, name)
        x = _numeric(df, source.x, name)
        mask = y.notna() & x.notna()
        if mask.sum() < 3 or x[mask].nunique() < 2:
            raise CalibrationError("err.cal_regression", name=name, y=source.y, x=source.x)
        slope, intercept = np.polyfit(x[mask].to_numpy(float), y[mask].to_numpy(float), 1)
        return float(slope if source.coefficient == "slope" else intercept)

    raise CalibrationError("err.cal_unknown_kind", name=name, kind=source.kind)


def calibrate(df: pd.DataFrame | None, sources: dict[str, ParameterSource]) -> dict[str, float]:
    return {name: compute_parameter(df, src, name) for name, src in sources.items()}


def detect_structure(df: pd.DataFrame, unit_col: str | None, period_col: str | None) -> str:
    """cross-section | panel | repeated cross-section | time series."""
    has_unit = bool(unit_col) and unit_col in df.columns
    has_period = bool(period_col) and period_col in df.columns
    if not has_period or df[period_col].nunique() < 2:
        return "cross-section"
    if not has_unit:
        return "repeated cross-section" if df[period_col].duplicated().any() else "time series"
    if df[unit_col].nunique() == 1:
        return "time series"
    per_unit_periods = df.groupby(unit_col)[period_col].nunique()
    return "panel" if (per_unit_periods > 1).mean() > 0.5 else "repeated cross-section"


def default_scope(structure: str) -> str:
    return "pooled" if structure == "cross-section" else "period"


def solve_by_scope(game: Game, df: pd.DataFrame | None, sources: dict[str, ParameterSource],
                   scope: str = "pooled", scope_column: str | None = None) -> pd.DataFrame:
    """One row per unit of computation: unit, calibrated parameters,
    equilibrium strategies, outcomes, and verification status."""
    if scope == "pooled" or df is None:
        units = [("All data", df)]
    else:
        if not scope_column or scope_column not in df.columns:
            raise CalibrationError("err.cal_scope", scope=scope)
        keys = sorted(df[scope_column].dropna().unique(), key=lambda v: (isinstance(v, str), v))
        units = [(k, df[df[scope_column] == k]) for k in keys]

    rows = []
    previous = None
    for unit, subset in units:
        row: dict = {"unit": unit}
        try:
            values = calibrate(subset, sources)
        except CalibrationError as exc:
            rows.append({**row, "status": exc.msg})
            continue
        row.update({f"param:{k}": v for k, v in values.items()})
        try:
            result = solve_equilibrium(game, values, start=previous) if previous else solve_equilibrium(game, values)
            if not result.found and previous:
                result = solve_equilibrium(game, values)
        except LocalizedError as exc:
            rows.append({**row, "status": exc.msg})
            continue
        except ValueError as exc:
            rows.append({**row, "status": str(exc)})
            continue
        if not result.found:
            rows.append({**row, "status": result.message})
            continue
        eq = result.equilibria[0]
        previous = eq.strategies
        row.update({f"strategy:{k}": v for k, v in eq.strategies.items()})
        row.update({f"outcome:{k}": v for k, v in eq.outcomes.items()})
        row["status"] = Msg("status.verified") if eq.verified else Msg("status.unverified")
        row["n_equilibria"] = len(result.equilibria)
        rows.append(row)
    return pd.DataFrame(rows)
