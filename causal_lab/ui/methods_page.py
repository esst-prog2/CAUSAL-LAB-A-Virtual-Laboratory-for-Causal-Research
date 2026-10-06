"""
Causal Methods page (CAUSAL LAB spec: causal-methods-lab).

Hosts the six additional identification strategies — RCT, Matching,
IV, RDD, Synthetic Control, DML. For the selected method the
researcher either generates its virtual world (known true effect) or
uploads a CSV and maps its columns to the method's roles, then runs
the estimator and sees the estimate, its diagnostics and a
method-specific plot.

Per-method state lives in `st.session_state.method_data[method]`, so
switching methods does not discard work done on another one. Every
string goes through the i18n layer (keys methods.*, mparam.*, and the
engines' own message keys).
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
from utils.i18n import LocalizedError, render as render_message, tf


@dataclass(frozen=True)
class Param:
    field: str
    min_value: float
    max_value: float
    step: float


@dataclass(frozen=True)
class MethodSpec:
    config_cls: type
    world: Callable
    params: tuple[Param, ...]


METHODS: dict[str, MethodSpec] = {
    "rct": MethodSpec(mw.RCTWorldConfig, mw.rct_world,
                      (Param("n", 50, 20000, 50), Param("ate", -5.0, 5.0, 0.1),
                       Param("effect_heterogeneity", 0.0, 3.0, 0.1), Param("covariate_strength", 0.0, 3.0, 0.1),
                       Param("share_treated", 0.1, 0.9, 0.05))),
    "matching": MethodSpec(mw.MatchingWorldConfig, mw.matching_world,
                           (Param("n", 100, 20000, 100), Param("att", -5.0, 5.0, 0.1),
                            Param("confounding_strength", 0.0, 3.0, 0.1),
                            Param("effect_heterogeneity", 0.0, 3.0, 0.1))),
    "iv": MethodSpec(mw.IVWorldConfig, mw.iv_world,
                     (Param("n", 100, 20000, 100), Param("effect", -5.0, 5.0, 0.1),
                      Param("instrument_strength", 0.0, 3.0, 0.05), Param("endogeneity", 0.0, 3.0, 0.1))),
    "rdd": MethodSpec(mw.RDDWorldConfig, mw.rdd_world,
                      (Param("n", 200, 50000, 100), Param("effect", -5.0, 5.0, 0.1), Param("cutoff", -5.0, 5.0, 0.1),
                       Param("curvature", 0.0, 5.0, 0.1), Param("noise_sd", 0.05, 5.0, 0.05))),
    "synthetic_control": MethodSpec(mw.SyntheticControlWorldConfig, mw.synthetic_control_world,
                                    (Param("n_donors", 3, 80, 1), Param("n_periods", 6, 100, 1),
                                     Param("treatment_period", 2, 99, 1), Param("effect", -10.0, 10.0, 0.1),
                                     Param("noise_sd", 0.0, 3.0, 0.05))),
    "dml": MethodSpec(mw.DMLWorldConfig, mw.dml_world,
                      (Param("n", 200, 10000, 100), Param("theta", -5.0, 5.0, 0.1),
                       Param("n_covariates", 3, 50, 1), Param("nonlinearity", 0.0, 3.0, 0.1))),
}

NO_COLUMN = "—"


_LANG = "en"   # set at the start of each render; read by format_func closures


def _lang() -> str:
    return _LANG


def F(key: str, **params) -> str:
    return tf(key, _lang(), **params)


def R(message) -> str:
    return render_message(message, _lang())


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
        values[p.field] = cols[i % 3].number_input(L(f"mparam.{method}.{p.field}"), **widget_args)
    values["seed"] = int(st.number_input(L("common.seed"), min_value=0, value=42, step=1, key=f"mw_{method}_seed"))

    if st.button(f"⚗️ {L('methods.generate')}", type="primary", key=f"mw_{method}_generate"):
        valid_fields = {f.name for f in fields(spec.config_cls)}
        try:
            df, truth = spec.world(spec.config_cls(**{k: v for k, v in values.items() if k in valid_fields}))
        except LocalizedError as exc:
            st.error(exc.render(_lang()))
            return
        state.update(df=df, truth=truth, mapping=dict(truth["roles"]), options=_virtual_options(method, truth),
                     source="virtual", result=None, error=None, dropped=0)
        st.success(F("methods.generated", rows=len(df), estimand=truth["estimand"], value=truth["true_effect"]))


def _upload_inputs(method: str, state: dict, L) -> None:
    uploaded = st.file_uploader(L("methods.csv_file"), type=["csv"], key=f"mw_{method}_upload")
    if uploaded is not None and uploaded.file_id != state["file_id"]:
        try:
            raw = pd.read_csv(uploaded)
        except Exception as exc:
            st.error(F("common.read_error", error=exc))
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
        label = R(role.label) + ("" if role.required else f" ({L('methods.optional')})")
        if role.multi:
            mapping[role.key] = target.multiselect(label, columns, key=f"mw_{method}_map_{role.key}")
        else:
            choice = target.selectbox(label, [NO_COLUMN] + columns, key=f"mw_{method}_map_{role.key}")
            mapping[role.key] = None if choice == NO_COLUMN else choice

    options: dict = {}
    if method == "rdd" and mapping.get("running") in raw.columns \
            and pd.api.types.is_numeric_dtype(raw[mapping["running"]]):
        running = raw[mapping["running"]].dropna()
        options["cutoff"] = st.number_input(L("methods.cutoff"), value=float(running.median()),
                                            key=f"mw_{method}_cutoff")
        bw = st.number_input(L("methods.bandwidth"), min_value=0.0, value=0.0, key=f"mw_{method}_bw")
        options["bandwidth"] = bw or None
    if method == "synthetic_control" and mapping.get("unit") in raw.columns and mapping.get("period") in raw.columns:
        units = sorted(raw[mapping["unit"]].dropna().unique().tolist(), key=str)
        periods = sorted(raw[mapping["period"]].dropna().unique().tolist())
        c1, c2 = st.columns(2)
        options["treated_unit"] = c1.selectbox(L("methods.treated_unit"), units, key=f"mw_{method}_treated")
        options["treatment_period"] = c2.selectbox(L("methods.first_treated_period"), periods,
                                                   index=len(periods) // 2, key=f"mw_{method}_tperiod")

    problems = [R(p) for p in validate_mapping(raw, method, mapping)]
    if method == "rdd" and "cutoff" not in options:
        problems.append(L("methods.need_running"))
    if method == "synthetic_control" and "treated_unit" not in options:
        problems.append(L("methods.need_unit_period"))
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
        st.info(F("methods.dropped", n=dropped))


# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------
def _metrics(result: MethodResult, truth: dict | None, L) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric(F("methods.estimate_of", estimand=R(result.estimand)), f"{result.estimate:.4f}")
    if result.se is not None:
        c2.metric(L("methods.std_error"), f"{result.se:.4f}")
        c3.metric(L("common.ci95"), f"[{result.ci_low:.3f}, {result.ci_high:.3f}]")
    else:
        c2.metric(L("methods.std_error"), "—")
        c3.metric(L("methods.placebo_p"), f"{result.p_value:.3f}")
    if truth is not None:
        st.markdown(f"#### {L('methods.truth')}")
        c1, c2, c3 = st.columns(3)
        c1.metric(L("common.estimate"), f"{result.estimate:.4f}")
        c2.metric(L("methods.true_effect"), f"{truth['true_effect']:.4f}")
        c3.metric(L("common.bias"), f"{result.estimate - truth['true_effect']:+.4f}")
    for w in result.warnings:
        st.warning(R(w))


def _balance_chart(balance: pd.DataFrame, columns: list[tuple[str, str]], L) -> go.Figure:
    fig = go.Figure()
    for col, name in columns:
        fig.add_trace(go.Scatter(x=balance[col], y=balance["covariate"], mode="markers",
                                 marker=dict(size=11), name=name))
    for x in (-0.1, 0.1):
        fig.add_vline(x=x, line_dash="dot", line_color="gray")
    fig.update_layout(title=L("methods.balance_title"), xaxis_title=L("methods.std_diff"),
                      height=320, margin=dict(t=50, b=30))
    return fig


def _binned(x: pd.Series, y: pd.Series, n_bins: int = 20) -> pd.DataFrame:
    bins = pd.qcut(x, q=min(n_bins, x.nunique()), duplicates="drop")
    return pd.DataFrame({"x": x, "y": y}).groupby(bins, observed=True).mean()


def _comparison_chart(result: MethodResult, name: str, other: float, other_se: float, other_name: str,
                      truth: dict | None, L) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=[result.estimate, other], y=[name, other_name], mode="markers", marker=dict(size=12),
        error_x=dict(type="data", array=[1.96 * result.se, 1.96 * other_se], visible=True)))
    if truth is not None:
        fig.add_vline(x=truth["true_effect"], line_dash="dash", line_color="green",
                      annotation_text=L("methods.true_effect"))
    fig.update_layout(title=L("methods.estimate_ci"), xaxis_title=L("methods.effect"), height=260,
                      margin=dict(t=50, b=30))
    return fig


def _translated_table(df: pd.DataFrame, L) -> pd.DataFrame:
    """Rename the engines' technical column names for display."""
    return df.rename(columns=lambda c: L(f"col.{c}"))


def _plots(method: str, result: MethodResult, state: dict, L) -> None:
    d = result.details
    df, m = state["df"], state["mapping"]
    truth = state["truth"] if state["source"] == "virtual" else None
    if method == "rct":
        if len(d["balance"]):
            st.plotly_chart(_balance_chart(d["balance"], [("std_diff", L("methods.treated_vs_control"))], L),
                            width="stretch")
            st.dataframe(_translated_table(d["balance"].round(4), L), width="stretch")
        st.caption(F("methods.rct_caption", dim=d["difference_in_means"], se=d["difference_in_means_se"],
                     treated=d["n_treated"], control=d["n_control"]))
    elif method == "matching":
        c1, c2 = st.columns(2)
        ps = d["propensity"]
        fig = go.Figure()
        for flag, name in ((1, L("methods.treated")), (0, L("methods.control"))):
            fig.add_trace(go.Histogram(x=ps.loc[ps["treated"] == flag, "propensity"], name=name,
                                       opacity=0.6, nbinsx=40, histnorm="probability density"))
        fig.update_layout(barmode="overlay", title=L("methods.overlap_title"),
                          xaxis_title=L("methods.propensity"), height=320, margin=dict(t=50, b=30))
        c1.plotly_chart(fig, width="stretch")
        c2.plotly_chart(_balance_chart(d["balance"], [("std_diff_before", L("methods.before_matching")),
                                                      ("std_diff_after", L("methods.after_matching"))], L),
                        width="stretch")
        c1, c2, c3 = st.columns(3)
        c1.metric(L("methods.ipw_att"), f"{d['ipw_att']:.4f}", help=F("methods.bootstrap_se", se=d["ipw_se"]))
        c2.metric(L("methods.naive_difference"), f"{d['naive_difference']:.4f}")
        c3.metric(L("methods.controls_used"), d["n_controls_used"])
        st.caption(R(d["notes"]))
    elif method == "iv":
        z = m["instruments"][0]
        first = _binned(df[z], df[m["treatment"]])
        fig = go.Figure(go.Scatter(x=first["x"], y=first["y"], mode="markers+lines"))
        fig.update_layout(title=F("methods.first_stage_title", treatment=m["treatment"], instrument=z),
                          xaxis_title=z, yaxis_title=m["treatment"], height=320, margin=dict(t=50, b=30))
        c1, c2 = st.columns(2)
        c1.plotly_chart(fig, width="stretch")
        c2.plotly_chart(_comparison_chart(result, "2SLS", d["ols_estimate"], d["ols_se"], L("methods.naive_ols"),
                                          truth, L), width="stretch")
        st.caption(F("methods.iv_caption", f=d["first_stage_f"], r2=d["partial_r2"]))
    elif method == "rdd":
        plot = d["plot_data"]
        cutoff, h = d["cutoff"], d["bandwidth"]
        fig = go.Figure()
        for side, mask in ((L("methods.below"), plot["x"] < cutoff), (L("methods.above"), plot["x"] >= cutoff)):
            b = _binned(plot.loc[mask, "x"], plot.loc[mask, "y"])
            fig.add_trace(go.Scatter(x=b["x"], y=b["y"], mode="markers", marker=dict(size=8),
                                     name=F("methods.binned_means", side=side)))
        for key, lo, hi in (("fit_left", cutoff - h, cutoff), ("fit_right", cutoff, cutoff + h)):
            xs = np.linspace(lo, hi, 50)
            fit = d[key]
            fig.add_trace(go.Scatter(x=xs, y=fit["intercept"] + fit["slope"] * (xs - cutoff), mode="lines",
                                     line=dict(width=3), name=L("methods.local_linear_fit"),
                                     showlegend=key == "fit_left"))
        fig.add_vline(x=cutoff, line_dash="dash", line_color="red", annotation_text=L("methods.cutoff"))
        fig.update_layout(title=L("methods.rdd_title"), xaxis_title=m["running"], yaxis_title=m["outcome"],
                          height=420, margin=dict(t=50, b=30))
        st.plotly_chart(fig, width="stretch")
        st.markdown(f"**{L('methods.bandwidth_sensitivity')}**")
        st.dataframe(_translated_table(d["sensitivity"].round(4), L), width="stretch")
        man = d["manipulation"]
        rule = L("methods.rule_user") if d["bandwidth_rule"] == "user" else d["bandwidth_rule"]
        st.caption(F("methods.rdd_caption", rule=rule, below=man["count_below"], above=man["count_above"],
                     p=man["p_value"], notes=R(d["notes"])))
    elif method == "synthetic_control":
        paths, tp = d["paths"], d["treatment_period"]
        c1, c2 = st.columns(2)
        fig = go.Figure([go.Scatter(x=paths["period"], y=paths["treated"], name=str(d["treated_unit"])),
                         go.Scatter(x=paths["period"], y=paths["synthetic"], name=L("methods.synthetic"),
                                    line=dict(dash="dash"))])
        fig.add_vline(x=tp - 0.5, line_dash="dot", line_color="red", annotation_text=L("common.treatment"))
        fig.update_layout(title=L("methods.sc_paths_title"), height=360, margin=dict(t=50, b=30))
        c1.plotly_chart(fig, width="stretch")
        fig = go.Figure()
        for donor, gaps in d["placebo_gaps"].items():
            fig.add_trace(go.Scatter(x=paths["period"], y=gaps, mode="lines", showlegend=False,
                                     line=dict(color="lightgray", width=1)))
        fig.add_trace(go.Scatter(x=paths["period"], y=paths["gap"], name=L("methods.treated_gap"),
                                 line=dict(color="crimson", width=3)))
        fig.add_vline(x=tp - 0.5, line_dash="dot", line_color="red")
        fig.update_layout(title=L("methods.sc_gaps_title"), height=360, margin=dict(t=50, b=30))
        c2.plotly_chart(fig, width="stretch")
        st.markdown(f"**{L('methods.donor_weights')}**")
        st.dataframe(_translated_table(d["weights"][d["weights"]["weight"] > 1e-3].round(4), L), width="stretch")
        st.caption(F("methods.sc_caption", pre=d["pre_rmspe"], ratio=d["rmspe_ratio"], units=d["n_donors"] + 1))
    elif method == "dml":
        st.plotly_chart(_comparison_chart(result, "DML", d["ols_estimate"], d["ols_se"],
                                          L("methods.naive_ols_linear"), truth, L), width="stretch")
        c1, c2 = st.columns(2)
        c1.metric(L("methods.r2_outcome"), f"{d['r2_outcome']:.3f}")
        c2.metric(L("methods.r2_treatment"), f"{d['r2_treatment']:.3f}")
        st.caption(F("methods.dml_caption", folds=d["n_folds"], learner=d["learner"]))


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------
def render(L) -> None:
    global _LANG
    _LANG = st.session_state.get("lang", "en")
    st.title(f"🧭 {L('methods.title')}")
    st.caption(L("methods.intro"))

    method = st.selectbox(L("methods.choose"), list(METHODS), format_func=lambda k: L(f"method.{k}"),
                          key="methods_choice")
    spec = METHODS[method]
    state = _state(method)
    st.info(f"**{L('methods.assumption')}:** {L(f'methods.assumption.{method}')}")

    source = st.radio(L("methods.source"), ["virtual", "upload"], horizontal=True, key=f"mw_{method}_source",
                      format_func=lambda s: L("methods.source_virtual") if s == "virtual" else L("methods.source_upload"))
    if source == "virtual":
        _virtual_world_inputs(method, spec, state, L)
    else:
        _upload_inputs(method, state, L)

    if state["df"] is None or state["source"] != source:
        return
    with st.expander(F("methods.preview", rows=len(state["df"]))):
        st.dataframe(state["df"].head(20), width="stretch")

    if st.button(f"▶️ {L('methods.estimate')}", type="primary", key=f"mw_{method}_run"):
        with st.spinner(L("methods.estimating")):
            try:
                state.update(result=_run_estimator(method, state["df"], state["mapping"], state["options"]),
                             error=None)
            except LocalizedError as exc:
                state.update(result=None, error=exc.msg)
            except ValueError as exc:
                state.update(result=None, error=str(exc))

    if state["error"]:
        st.error(R(state["error"]))
    result = state["result"]
    if result is None:
        return
    st.divider()
    _metrics(result, state["truth"] if state["source"] == "virtual" else None, L)
    _plots(method, result, state, L)
    with st.expander(L("methods.technical_summary")):
        st.code("\n".join(R(line) for line in result.summary_lines), language="text")
