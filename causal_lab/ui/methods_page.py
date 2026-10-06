"""
Causal Methods page (CAUSAL LAB spec: causal-methods-lab).

Hosts the six additional identification strategies — RCT, Matching,
IV, RDD, Synthetic Control, DML. For the selected method the
researcher either generates its virtual world (known true effect) or
uploads a CSV and maps its columns to the method's roles, then runs
the estimator and sees the estimate, its diagnostics and a
method-specific plot.

Per-method state lives in `st.session_state.method_data[method]`, so
switching methods does not discard work done on another one.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Callable

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from estimators.common import MethodResult
from estimators.dml import estimate_dml
from estimators.iv import estimate_iv
from estimators.matching import estimate_matching
from estimators.rct import estimate_rct
from estimators.rdd import estimate_rdd
from estimators.synthetic_control import estimate_synthetic_control
from simulation_engine import method_worlds as mw
from utils.column_mapping import METHOD_ROLES, prepare_mapped_frame, validate_mapping


@dataclass(frozen=True)
class Param:
    field: str
    label: str
    min_value: float
    max_value: float
    step: float


@dataclass(frozen=True)
class MethodSpec:
    label: str
    assumption: str
    config_cls: type
    world: Callable
    params: tuple[Param, ...]


METHODS: dict[str, MethodSpec] = {
    "rct": MethodSpec(
        "Randomized Controlled Trial",
        "Treatment is randomly assigned, so treated and control groups are comparable in expectation "
        "on observed and unobserved characteristics.",
        mw.RCTWorldConfig, mw.rct_world,
        (Param("n", "Sample size", 50, 20000, 50), Param("ate", "True ATE", -5.0, 5.0, 0.1),
         Param("effect_heterogeneity", "Effect heterogeneity (sd)", 0.0, 3.0, 0.1),
         Param("covariate_strength", "Covariate predictive power", 0.0, 3.0, 0.1),
         Param("share_treated", "Share treated", 0.1, 0.9, 0.05)),
    ),
    "matching": MethodSpec(
        "Matching / Propensity Score",
        "Selection on observables: conditional on the covariates, treatment is as good as random, and "
        "every treated unit has comparable controls (overlap).",
        mw.MatchingWorldConfig, mw.matching_world,
        (Param("n", "Sample size", 100, 20000, 100), Param("att", "True ATT", -5.0, 5.0, 0.1),
         Param("confounding_strength", "Confounding strength", 0.0, 3.0, 0.1),
         Param("effect_heterogeneity", "Effect heterogeneity", 0.0, 3.0, 0.1)),
    ),
    "iv": MethodSpec(
        "Instrumental Variables",
        "The instrument moves the treatment (relevance) and affects the outcome only through the "
        "treatment (exclusion). Exclusion cannot be tested from the data.",
        mw.IVWorldConfig, mw.iv_world,
        (Param("n", "Sample size", 100, 20000, 100), Param("effect", "True effect", -5.0, 5.0, 0.1),
         Param("instrument_strength", "Instrument strength", 0.0, 3.0, 0.05),
         Param("endogeneity", "Endogeneity (unobserved confounding)", 0.0, 3.0, 0.1)),
    ),
    "rdd": MethodSpec(
        "Regression Discontinuity",
        "Treatment switches on when the running variable crosses a known cutoff, and units cannot "
        "precisely manipulate which side they fall on; everything else varies smoothly at the cutoff.",
        mw.RDDWorldConfig, mw.rdd_world,
        (Param("n", "Sample size", 200, 50000, 100), Param("effect", "True jump at cutoff", -5.0, 5.0, 0.1),
         Param("cutoff", "Cutoff", -5.0, 5.0, 0.1), Param("curvature", "Curvature of E[Y|X]", 0.0, 5.0, 0.1),
         Param("noise_sd", "Noise (sd)", 0.05, 5.0, 0.05)),
    ),
    "synthetic_control": MethodSpec(
        "Synthetic Control",
        "Before treatment, a weighted average of untreated donor units reproduces the treated unit's "
        "outcome path, and donors are not affected by the treatment.",
        mw.SyntheticControlWorldConfig, mw.synthetic_control_world,
        (Param("n_donors", "Donor units", 3, 80, 1), Param("n_periods", "Periods", 6, 100, 1),
         Param("treatment_period", "First treated period", 2, 99, 1),
         Param("effect", "True effect", -10.0, 10.0, 0.1), Param("noise_sd", "Noise (sd)", 0.0, 3.0, 0.05)),
    ),
    "dml": MethodSpec(
        "Double Machine Learning",
        "All confounders are observed among the covariates (unconfoundedness), possibly acting "
        "non-linearly; the treatment effect is constant (partially linear model).",
        mw.DMLWorldConfig, mw.dml_world,
        (Param("n", "Sample size", 200, 10000, 100), Param("theta", "True theta", -5.0, 5.0, 0.1),
         Param("n_covariates", "Covariates", 3, 50, 1),
         Param("nonlinearity", "Non-linearity of confounding", 0.0, 3.0, 0.1)),
    ),
}

NO_COLUMN = "—"


def _state(method: str) -> dict:
    store = st.session_state.setdefault("method_data", {})
    return store.setdefault(method, {"df": None, "truth": None, "mapping": None, "options": {},
                                     "source": None, "result": None, "error": None, "dropped": 0,
                                     "file_id": None})


def _virtual_options(method: str, truth: dict) -> dict:
    roles = truth["roles"]
    if method == "rdd":
        return {"cutoff": roles["cutoff"], "bandwidth": None}
    if method == "synthetic_control":
        return {"treated_unit": roles["treated_unit"], "treatment_period": roles["treatment_period"]}
    return {}


def _run_estimator(method: str, df: pd.DataFrame, m: dict, options: dict) -> MethodResult:
    if method == "rct":
        return estimate_rct(df, m["outcome"], m["treatment"], m.get("covariates"))
    if method == "matching":
        return estimate_matching(df, m["outcome"], m["treatment"], m.get("covariates"))
    if method == "iv":
        return estimate_iv(df, m["outcome"], m["treatment"], m.get("instruments"), m.get("controls"))
    if method == "rdd":
        return estimate_rdd(df, m["outcome"], m["running"], options["cutoff"], options.get("bandwidth"))
    if method == "synthetic_control":
        return estimate_synthetic_control(df, m["unit"], m["period"], m["outcome"],
                                          options["treated_unit"], options["treatment_period"])
    if method == "dml":
        return estimate_dml(df, m["outcome"], m["treatment"], m.get("covariates"))
    raise KeyError(method)


# --------------------------------------------------------------------------
# Data input
# --------------------------------------------------------------------------
def _virtual_world_inputs(method: str, spec: MethodSpec, state: dict, L) -> None:
    defaults = spec.config_cls()
    values = {}
    cols = st.columns(3)
    for i, p in enumerate(spec.params):
        default = getattr(defaults, p.field)
        is_int = isinstance(default, int) and isinstance(p.step, int)
        widget_args = dict(min_value=int(p.min_value) if is_int else float(p.min_value),
                           max_value=int(p.max_value) if is_int else float(p.max_value),
                           value=default, step=p.step, key=f"mw_{method}_{p.field}")
        values[p.field] = cols[i % 3].number_input(p.label, **widget_args)
    values["seed"] = int(st.number_input("Random seed", min_value=0, value=42, step=1, key=f"mw_{method}_seed"))

    if st.button(f"⚗️ {L('methods.generate')}", type="primary", key=f"mw_{method}_generate"):
        valid_fields = {f.name for f in fields(spec.config_cls)}
        try:
            df, truth = spec.world(spec.config_cls(**{k: v for k, v in values.items() if k in valid_fields}))
        except ValueError as exc:
            st.error(str(exc))
            return
        state.update(df=df, truth=truth, mapping=dict(truth["roles"]), options=_virtual_options(method, truth),
                     source="virtual", result=None, error=None, dropped=0)
        st.success(f"Generated {len(df)} rows. True effect ({truth['estimand']}) = {truth['true_effect']:.4f}")


def _upload_inputs(method: str, state: dict, L) -> None:
    uploaded = st.file_uploader("CSV file", type=["csv"], key=f"mw_{method}_upload")
    if uploaded is not None and uploaded.file_id != state["file_id"]:
        try:
            raw = pd.read_csv(uploaded)
        except Exception as exc:
            st.error(f"Could not read file: {exc}")
            return
        state.update(raw=raw, file_id=uploaded.file_id, result=None, error=None)
    raw = state.get("raw")
    if raw is None or state["file_id"] is None:
        return

    st.markdown(f"**{L('methods.mapping')}**")
    columns = list(raw.columns)
    mapping: dict = {}
    cols = st.columns(2)
    for i, role in enumerate(METHOD_ROLES[method]):
        target = cols[i % 2]
        if role.multi:
            mapping[role.key] = target.multiselect(role.label + ("" if role.required else " (optional)"),
                                                   columns, key=f"mw_{method}_map_{role.key}")
        else:
            choice = target.selectbox(role.label, [NO_COLUMN] + columns, key=f"mw_{method}_map_{role.key}")
            mapping[role.key] = None if choice == NO_COLUMN else choice

    options: dict = {}
    if method == "rdd" and mapping.get("running") in raw.columns \
            and pd.api.types.is_numeric_dtype(raw[mapping["running"]]):
        running = raw[mapping["running"]].dropna()
        options["cutoff"] = st.number_input("Cutoff", value=float(running.median()), key=f"mw_{method}_cutoff")
        bw = st.number_input("Bandwidth (0 = automatic, Imbens-Kalyanaraman)", min_value=0.0, value=0.0,
                             key=f"mw_{method}_bw")
        options["bandwidth"] = bw or None
    if method == "synthetic_control" and mapping.get("unit") in raw.columns and mapping.get("period") in raw.columns:
        units = sorted(raw[mapping["unit"]].dropna().unique().tolist(), key=str)
        periods = sorted(raw[mapping["period"]].dropna().unique().tolist())
        c1, c2 = st.columns(2)
        options["treated_unit"] = c1.selectbox("Treated unit", units, key=f"mw_{method}_treated")
        options["treatment_period"] = c2.selectbox("First treated period", periods,
                                                   index=len(periods) // 2, key=f"mw_{method}_tperiod")

    problems = validate_mapping(raw, method, mapping)
    if method == "rdd" and "cutoff" not in options:
        problems.append("Running variable: select a numeric column to set the cutoff.")
    if method == "synthetic_control" and "treated_unit" not in options:
        problems.append("Unit / Period: select both columns to choose the treated unit and period.")
    if problems:
        for p in problems:
            st.error(p)
        state.update(df=None, source=None)
        return

    if (mapping, options) != (state["mapping"], state["options"]) or state["source"] != "upload":
        state.update(result=None, error=None)      # results belong to the previous mapping
    df, dropped = prepare_mapped_frame(raw, method, mapping)
    state.update(df=df, truth=None, mapping=mapping, options=options, source="upload", dropped=dropped)
    if dropped:
        st.info(f"{dropped} row(s) with missing values in the mapped columns were dropped.")


# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------
def _metrics(result: MethodResult, truth: dict | None, L) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Estimate ({result.estimand})", f"{result.estimate:.4f}")
    if result.se is not None:
        c2.metric("Std. error", f"{result.se:.4f}")
        c3.metric("95% CI", f"[{result.ci_low:.3f}, {result.ci_high:.3f}]")
    else:
        c2.metric("Std. error", "—")
        c3.metric("Placebo p-value", f"{result.p_value:.3f}")
    if truth is not None:
        st.markdown(f"#### {L('methods.truth')}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Estimate", f"{result.estimate:.4f}")
        c2.metric("True effect", f"{truth['true_effect']:.4f}")
        c3.metric("Bias", f"{result.estimate - truth['true_effect']:+.4f}")
    for w in result.warnings:
        st.warning(w)


def _balance_chart(balance: pd.DataFrame, columns: list[tuple[str, str]]) -> go.Figure:
    fig = go.Figure()
    for col, name in columns:
        fig.add_trace(go.Scatter(x=balance[col], y=balance["covariate"], mode="markers",
                                 marker=dict(size=11), name=name))
    for x in (-0.1, 0.1):
        fig.add_vline(x=x, line_dash="dot", line_color="gray")
    fig.update_layout(title="Covariate balance (standardized mean difference)",
                      xaxis_title="Standardized difference", height=320, margin=dict(t=50, b=30))
    return fig


def _binned(x: pd.Series, y: pd.Series, n_bins: int = 20) -> pd.DataFrame:
    bins = pd.qcut(x, q=min(n_bins, x.nunique()), duplicates="drop")
    return pd.DataFrame({"x": x, "y": y}).groupby(bins, observed=True).mean()


def _plots(method: str, result: MethodResult, state: dict) -> None:
    d = result.details
    df, m = state["df"], state["mapping"]
    truth = state["truth"]
    if method == "rct":
        if len(d["balance"]):
            st.plotly_chart(_balance_chart(d["balance"], [("std_diff", "Treated vs control")]),
                            use_container_width=True)
            st.dataframe(d["balance"].round(4), use_container_width=True)
        st.caption(f"Difference in means = {d['difference_in_means']:.4f} (SE {d['difference_in_means_se']:.4f}); "
                   f"{d['n_treated']} treated, {d['n_control']} control.")
    elif method == "matching":
        c1, c2 = st.columns(2)
        ps = d["propensity"]
        fig = go.Figure()
        for flag, name in ((1, "Treated"), (0, "Control")):
            fig.add_trace(go.Histogram(x=ps.loc[ps["treated"] == flag, "propensity"], name=name,
                                       opacity=0.6, nbinsx=40, histnorm="probability density"))
        fig.update_layout(barmode="overlay", title="Propensity-score overlap",
                          xaxis_title="Propensity score", height=320, margin=dict(t=50, b=30))
        c1.plotly_chart(fig, use_container_width=True)
        c2.plotly_chart(_balance_chart(d["balance"], [("std_diff_before", "Before matching"),
                                                      ("std_diff_after", "After matching")]),
                        use_container_width=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("IPW ATT", f"{d['ipw_att']:.4f}", help=f"Bootstrap SE {d['ipw_se']:.4f}")
        c2.metric("Naive difference in means", f"{d['naive_difference']:.4f}")
        c3.metric("Distinct controls used", d["n_controls_used"])
        st.caption(d["notes"])
    elif method == "iv":
        z = m["instruments"][0]
        first = _binned(df[z], df[m["treatment"]])
        fig = go.Figure(go.Scatter(x=first["x"], y=first["y"], mode="markers+lines"))
        fig.update_layout(title=f"First stage: mean of {m['treatment']} by {z}", xaxis_title=z,
                          yaxis_title=m["treatment"], height=320, margin=dict(t=50, b=30))
        c1, c2 = st.columns(2)
        c1.plotly_chart(fig, use_container_width=True)
        c2.plotly_chart(_comparison_chart(result, "2SLS", d["ols_estimate"], d["ols_se"], "Naive OLS", truth),
                        use_container_width=True)
        st.caption(f"First-stage F = {d['first_stage_f']:.2f}, partial R² = {d['partial_r2']:.3f}. "
                   f"Exclusion restriction cannot be tested from the data.")
    elif method == "rdd":
        plot = d["plot_data"]
        cutoff, h = d["cutoff"], d["bandwidth"]
        fig = go.Figure()
        for side, mask in (("below", plot["x"] < cutoff), ("above", plot["x"] >= cutoff)):
            b = _binned(plot.loc[mask, "x"], plot.loc[mask, "y"])
            fig.add_trace(go.Scatter(x=b["x"], y=b["y"], mode="markers", name=f"Binned means ({side})",
                                     marker=dict(size=8)))
        for key, lo, hi in (("fit_left", cutoff - h, cutoff), ("fit_right", cutoff, cutoff + h)):
            xs = np.linspace(lo, hi, 50)
            fit = d[key]
            fig.add_trace(go.Scatter(x=xs, y=fit["intercept"] + fit["slope"] * (xs - cutoff), mode="lines",
                                     line=dict(width=3), name="Local linear fit", showlegend=key == "fit_left"))
        fig.add_vline(x=cutoff, line_dash="dash", line_color="red", annotation_text="Cutoff")
        fig.update_layout(title="Outcome against the running variable", xaxis_title=m["running"],
                          yaxis_title=m["outcome"], height=420, margin=dict(t=50, b=30))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("**Bandwidth sensitivity**")
        st.dataframe(d["sensitivity"].round(4), use_container_width=True)
        man = d["manipulation"]
        st.caption(f"Bandwidth rule: {d['bandwidth_rule']}. Manipulation check: {man['count_below']} obs just "
                   f"below vs {man['count_above']} just above the cutoff (p = {man['p_value']:.3f}). {d['notes']}")
    elif method == "synthetic_control":
        paths, tp = d["paths"], d["treatment_period"]
        c1, c2 = st.columns(2)
        fig = go.Figure([go.Scatter(x=paths["period"], y=paths["treated"], name=f"{d['treated_unit']}"),
                         go.Scatter(x=paths["period"], y=paths["synthetic"], name="Synthetic",
                                    line=dict(dash="dash"))])
        fig.add_vline(x=tp - 0.5, line_dash="dot", line_color="red", annotation_text="Treatment")
        fig.update_layout(title="Treated vs synthetic control", height=360, margin=dict(t=50, b=30))
        c1.plotly_chart(fig, use_container_width=True)
        fig = go.Figure()
        for donor, gaps in d["placebo_gaps"].items():
            fig.add_trace(go.Scatter(x=paths["period"], y=gaps, mode="lines", showlegend=False,
                                     line=dict(color="lightgray", width=1)))
        fig.add_trace(go.Scatter(x=paths["period"], y=paths["gap"], name="Treated gap",
                                 line=dict(color="crimson", width=3)))
        fig.add_vline(x=tp - 0.5, line_dash="dot", line_color="red")
        fig.update_layout(title="Gap: treated vs placebo donors", height=360, margin=dict(t=50, b=30))
        c2.plotly_chart(fig, use_container_width=True)
        st.markdown("**Donor weights**")
        st.dataframe(d["weights"][d["weights"]["weight"] > 1e-3].round(4), use_container_width=True)
        st.caption(f"Pre-treatment RMSPE = {d['pre_rmspe']:.4f}; post/pre RMSPE ratio = {d['rmspe_ratio']:.2f}; "
                   f"placebo p-value over {d['n_donors'] + 1} units.")
    elif method == "dml":
        st.plotly_chart(_comparison_chart(result, "DML", d["ols_estimate"], d["ols_se"],
                                          "Naive OLS (linear controls)", truth), use_container_width=True)
        c1, c2 = st.columns(2)
        c1.metric("Out-of-fold R² — outcome model", f"{d['r2_outcome']:.3f}")
        c2.metric("Out-of-fold R² — treatment model", f"{d['r2_treatment']:.3f}")
        st.caption(f"{d['n_folds']}-fold cross-fitting with {d['learner']}.")


def _comparison_chart(result: MethodResult, name: str, other: float, other_se: float, other_name: str,
                      truth: dict | None) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=[result.estimate, other], y=[name, other_name], mode="markers", marker=dict(size=12),
        error_x=dict(type="data", array=[1.96 * result.se, 1.96 * other_se], visible=True)))
    if truth is not None:
        fig.add_vline(x=truth["true_effect"], line_dash="dash", line_color="green", annotation_text="True effect")
    fig.update_layout(title="Estimate with 95% CI", xaxis_title="Effect", height=260, margin=dict(t=50, b=30))
    return fig


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------
def render(L) -> None:
    st.title(f"🧭 {L('methods.title')}")
    st.caption(L("methods.intro"))

    method = st.selectbox(L("methods.choose"), list(METHODS), format_func=lambda k: METHODS[k].label,
                          key="methods_choice")
    spec = METHODS[method]
    state = _state(method)
    st.info(f"**{L('methods.assumption')}:** {spec.assumption}")

    source = st.radio(L("methods.source"), ["virtual", "upload"], horizontal=True, key=f"mw_{method}_source",
                      format_func=lambda s: L("methods.source_virtual") if s == "virtual" else L("methods.source_upload"))
    if source == "virtual":
        _virtual_world_inputs(method, spec, state, L)
    else:
        _upload_inputs(method, state, L)

    if state["df"] is None or state["source"] != source:
        return
    with st.expander(f"Data preview ({len(state['df'])} rows)"):
        st.dataframe(state["df"].head(20), use_container_width=True)

    if st.button(f"▶️ {L('methods.estimate')}", type="primary", key=f"mw_{method}_run"):
        with st.spinner("Estimating..."):
            try:
                state.update(result=_run_estimator(method, state["df"], state["mapping"], state["options"]),
                             error=None)
            except ValueError as exc:
                state.update(result=None, error=str(exc))

    if state["error"]:
        st.error(state["error"])
    result = state["result"]
    if result is None:
        return
    st.divider()
    _metrics(result, state["truth"] if state["source"] == "virtual" else None, L)
    _plots(method, result, state)
    st.code(result.summary_text, language="text")
