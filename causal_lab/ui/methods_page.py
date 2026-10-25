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

from dataclasses import asdict, dataclass, fields
from typing import Callable

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from estimators.common import Z_95, MethodResult
from code_generator.methods import code_options, generate_method_code
from estimators.rdd import INFERENCES
from estimators.registry import run_method, virtual_options
from robustness_engine.method_stress import run_method_stress_test
from simulation_engine.method_monte_carlo import run_method_monte_carlo
from simulation_engine import method_worlds as mw
from utils.column_mapping import METHOD_ROLES, prepare_mapped_frame, validate_mapping
from ui.page_text import F, R, error_text
from utils.i18n import LocalizedError


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
                       Param("curvature", 0.0, 5.0, 0.1), Param("noise_sd", 0.05, 5.0, 0.05),
                       Param("compliance", 0.05, 1.0, 0.05))),
    "synthetic_control": MethodSpec(mw.SyntheticControlWorldConfig, mw.synthetic_control_world,
                                    (Param("n_donors", 3, 80, 1), Param("n_periods", 6, 100, 1),
                                     Param("treatment_period", 2, 99, 1), Param("effect", -10.0, 10.0, 0.1),
                                     Param("noise_sd", 0.0, 3.0, 0.05), Param("n_covariates", 0, 10, 1))),
    "dml": MethodSpec(mw.DMLWorldConfig, mw.dml_world,
                      (Param("n", 200, 10000, 100), Param("theta", -5.0, 5.0, 0.1),
                       Param("n_covariates", 3, 50, 1), Param("nonlinearity", 0.0, 3.0, 0.1))),
}

NO_COLUMN = "—"


def _state(method: str) -> dict:
    store = st.session_state.setdefault("method_data", {})
    return store.setdefault(method, {"df": None, "truth": None, "mapping": None, "options": {},
                                     "source": None, "result": None, "error": None, "dropped": 0,
                                     "file_id": None})


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
        config = spec.config_cls(**{k: v for k, v in values.items() if k in valid_fields})
        try:
            df, truth = spec.world(config)
        except LocalizedError as exc:
            st.error(error_text(exc))
            return
        options = virtual_options(method, truth)
        if method == "rdd":
            options["inference"] = st.session_state.get("mw_rdd_inference", "conventional")
        state.update(df=df, truth=truth, mapping=dict(truth["roles"]), options=options,
                     source="virtual", result=None, error=None, dropped=0, config=asdict(config),
                     stress=None, mc=None)
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
        options["inference"] = st.session_state.get("mw_rdd_inference", "conventional")
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
        error_x=dict(type="data", array=[Z_95 * result.se, Z_95 * other_se], visible=True)))
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
        c1.metric(L("methods.ipw_att"), f"{d['ipw_att']:.4f}", help=F("methods.bootstrap_se", se=d["ipw_se"], n=d["ipw_bootstrap_used"]))
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
        rb = d["robust"]
        st.caption(F("methods.rdd_robust_caption", estimate=rb["estimate_bc"], se=rb["se"], lo=rb["ci_low"],
                     hi=rb["ci_high"], p=rb["p_value"]))
        if d["first_stage"] is not None:
            fs = d["first_stage"]
            st.caption(F("methods.rdd_first_stage_caption", jump=fs["jump"], se=fs["se"], f=fs["f"]))
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
        if d["predictors"] is not None:
            st.markdown(f"**{L('methods.sc_predictors_title')}**")
            st.dataframe(_translated_table(d["predictors"].round(4), L), width="stretch")
            st.caption(L("methods.sc_predictors_caption"))
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
    st.title(f"🧭 {L('methods.title')}")
    st.caption(L("methods.intro"))

    method = st.selectbox(L("methods.choose"), list(METHODS), format_func=lambda k: L(f"method.{k}"),
                          key="methods_choice")
    spec = METHODS[method]
    state = _state(method)
    st.info(f"**{L('methods.assumption')}:** {L(f'methods.assumption.{method}')}")

    if method == "rdd":
        inference = st.radio(L("methods.rdd_inference"), list(INFERENCES), horizontal=True, key="mw_rdd_inference",
                             format_func=lambda v: L(f"methods.rdd_inference.{v}"))
        if state["options"] and state["options"].get("inference", "conventional") != inference:
            state["options"] = {**state["options"], "inference": inference}
            state.update(result=None, stress=None, mc=None)       # results belong to the other inference

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
                state.update(result=run_method(method, state["df"], state["mapping"], state["options"]),
                             error=None, stress=None)
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

    st.divider()
    tab_stress, tab_mc, tab_code = st.tabs([f"💥 {L('methods.stress_title')}", f"🎲 {L('methods.mc_title')}",
                                            f"💻 {L('methods.code_title')}"])
    with tab_stress:
        _stress_section(method, state, result, L)
    with tab_mc:
        _monte_carlo_section(method, state, L)
    with tab_code:
        _code_section(method, state, result, L)


# --------------------------------------------------------------------------
# Break My Design, Monte Carlo and code for the six methods
# --------------------------------------------------------------------------
# Seconds per replication on the default worlds (IPW bootstrap skipped).
MC_SECONDS = {"rct": 0.01, "matching": 0.02, "iv": 0.07, "rdd": 0.01, "synthetic_control": 0.16, "dml": 4.6}
MC_DEFAULT_REPS = {"rct": 200, "matching": 200, "iv": 200, "rdd": 200, "synthetic_control": 100, "dml": 10}
STRESS_STYLE = {"PASS": ("✓", st.success), "WARNING": ("⚠", st.warning), "N/A": ("–", st.info)}
LANGUAGES = (("python", "Python", "py"), ("r", "R", "R"), ("stata", "Stata", "do"))


def _stress_section(method: str, state: dict, result: MethodResult, L) -> None:
    if st.button(f"💥 {L('methods.stress_run')}", key=f"mw_{method}_stress"):
        with st.spinner(L("methods.estimating")):
            try:
                state["stress"] = run_method_stress_test(method, state["df"], state["mapping"], state["options"],
                                                         result)
            except LocalizedError as exc:
                st.error(error_text(exc))
    report = state.get("stress")
    if report is None:
        return
    for check in report.checks:
        icon, show = STRESS_STYLE[check.verdict]
        show(f"**{L(f'mcheck.{check.slug}')}** {icon} {L(f'verdict.{check.verdict}')} — {R(check.message)}")
    if report.identification_strength is None:
        st.info(L("break.no_score"))
    else:
        st.progress(report.identification_strength / 100)
        st.markdown(f"### {report.identification_strength:.0f} / 100")
        st.caption(F("break.score_basis", k=report.n_computable, n=len(report.checks)))
    st.caption(L("break.disclaimer"))


def _size_factor(method: str, config) -> float:
    """Runtime grows roughly with the sample size relative to the default world."""
    field = "n_donors" if method == "synthetic_control" else "n"
    default = getattr(METHODS[method].config_cls(), field)
    return max(getattr(config, field) / default, 0.1)


def _monte_carlo_section(method: str, state: dict, L) -> None:
    if state["source"] != "virtual" or not state.get("config"):
        st.info(L("methods.mc_only_virtual"))
        return
    config = METHODS[method].config_cls(**state["config"])
    st.caption(F("methods.mc_intro", seed=config.seed))
    reps = int(st.number_input(L("methods.mc_reps"), min_value=2, max_value=2000, value=MC_DEFAULT_REPS[method],
                               step=1, key=f"mw_{method}_mc_reps"))
    # The V search of a covariate synthetic control costs about 25 times the outcome-only fit.
    slow = 25 if method == "synthetic_control" and getattr(config, "n_covariates", 0) else 1
    st.caption(F("methods.mc_time", seconds=reps * MC_SECONDS[method] * _size_factor(method, config) * slow))
    if st.button(f"🎲 {L('methods.mc_run')}", key=f"mw_{method}_mc_run"):
        bar = st.progress(0.0)
        try:
            extra = {"inference": state["options"].get("inference", "conventional")} if method == "rdd" else None
            state["mc"] = run_method_monte_carlo(method, config, n_reps=reps, base_seed=config.seed,
                                                 progress=lambda done, total: bar.progress(done / total),
                                                 extra_options=extra)
        except LocalizedError as exc:
            st.error(error_text(exc))
    mc = state.get("mc")
    if mc is None:
        return
    st.success(F("methods.mc_done", reps=mc.n_reps, failed=mc.n_failed))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(L("common.bias"), f"{mc.bias:+.4f}")
    c2.metric(L("common.rmse"), f"{mc.rmse:.4f}")
    c3.metric(L("common.coverage"), "—" if mc.coverage is None else f"{mc.coverage:.1%}")
    c4.metric(L("methods.mc_rejection"), f"{mc.rejection_rate:.1%}")
    c1, c2, c3 = st.columns(3)
    c1.metric(L("methods.true_effect"), f"{mc.true_effect:.4f}")
    c2.metric(L("common.ci_length"), "—" if mc.avg_ci_length is None else f"{mc.avg_ci_length:.4f}")
    c3.metric(L("methods.mc_se_ratio"), "—" if mc.se_ratio is None else f"{mc.se_ratio:.3f}")
    fig = go.Figure(go.Histogram(x=mc.estimates, nbinsx=40, name=L("common.estimate")))
    fig.add_vline(x=mc.true_effect, line_dash="dash", line_color="green", annotation_text=L("methods.true_effect"))
    fig.update_layout(title=L("methods.mc_hist"), xaxis_title=L("methods.effect"), height=320,
                      margin=dict(t=50, b=30))
    st.plotly_chart(fig, width="stretch")


def _code_section(method: str, state: dict, result: MethodResult, L) -> None:
    st.caption(L("methods.code_caption"))
    path = st.text_input(L("code.data_path"), value=f"{method}.csv", key=f"mw_{method}_code_path")
    code = generate_method_code(method, state["mapping"],
                                code_options(method, state["df"], state["mapping"], state["options"], result),
                                data_path=path, lang=st.session_state.lang)
    st.download_button(F("code.download", language="CSV"), state["df"].to_csv(index=False), path,
                       key=f"mw_{method}_code_csv")
    for tab, (language, label, ext) in zip(st.tabs([label for _, label, _ in LANGUAGES]), LANGUAGES):
        with tab:
            st.code(code[language], language=language)
            st.download_button(F("code.download", language=label), code[language], f"causal_lab_{method}.{ext}",
                               key=f"mw_{method}_code_{language}")
