"""
CAUSAL LAB — Streamlit entry point (v0.1 MVP).

Implements the first end-to-end user journey described in the spec
(Section 54):

    research question -> diagnosis -> method recommendation ->
    virtual world / data -> estimation -> stress test -> robustness ->
    code generation

Every user-facing string goes through the i18n layer: `L(key)` for
fixed text, `F(key, **params)` for text with values, and `R(msg)` for
translatable messages produced by the engines.

Run with:  streamlit run app.py
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from causal_engine.diagnosis import DiagnosisResult, Level, ResearchDesignInput, diagnose
from causal_engine.recommendation import MethodScore, component_slug, recommend
from code_generator.generator import CodeGenParams, generate_all
from estimators.did import estimate_did
from estimators.event_study import estimate_event_study
from estimators.staggered_did import estimate_staggered_did
from robustness_engine.robustness import run_robustness_battery
from robustness_engine.stress_test import run_stress_test
from simulation_engine.dgp import VirtualWorldConfig, generate
from simulation_engine.monte_carlo import run_monte_carlo
from ui.methods_page import render as render_methods_page
from ui.theory_page import render as render_theory_page
from utils.i18n import LocalizedError, render, t, tf
from utils.real_data import load_card_krueger
from utils.validation import REQUIRED_COLUMNS, missing_required_columns

st.set_page_config(page_title="CAUSAL LAB", page_icon="🔬", layout="wide")

# --------------------------------------------------------------------------
# Session state initialisation
# --------------------------------------------------------------------------
if "lang" not in st.session_state:
    st.session_state.lang = "en"
if "design" not in st.session_state:
    st.session_state.design = ResearchDesignInput()
if "diagnosis" not in st.session_state:
    st.session_state.diagnosis = None
if "recommendations" not in st.session_state:
    st.session_state.recommendations = None
if "virtual_df" not in st.session_state:
    st.session_state.virtual_df = None
if "virtual_truth" not in st.session_state:
    st.session_state.virtual_truth = None
if "vw_config" not in st.session_state:
    st.session_state.vw_config = VirtualWorldConfig()
if "virtual_cfg" not in st.session_state:
    # Snapshot of the configuration that generated `virtual_df`: the
    # Virtual Lab widgets keep editing `vw_config` after generation.
    st.session_state.virtual_cfg = None
if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None
if "uploaded_file_id" not in st.session_state:
    st.session_state.uploaded_file_id = None
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

lang = st.session_state.lang

PAGES = [
    "dashboard", "research_question", "diagnosis", "recommendation",
    "virtual_lab", "estimation", "methods", "theory", "break_my_design",
    "robustness", "code", "settings",
]
LEVELS = ["none", "low", "medium", "high", "severe"]


def L(key: str) -> str:
    return t(key, lang)


def F(key: str, **params) -> str:
    return tf(key, lang, **params)


def R(message) -> str:
    return render(message, lang)


def yes_no(flag: bool) -> str:
    return L("common.yes") if flag else L("common.no")


def go_to(page_id: str) -> None:
    st.session_state.page = page_id


def active_df() -> pd.DataFrame | None:
    """Whichever dataset is currently loaded: an uploaded real-world
    dataset takes priority over the simulated Virtual World data."""
    if st.session_state.uploaded_df is not None:
        return st.session_state.uploaded_df
    return st.session_state.virtual_df


def treatment_setup(df: pd.DataFrame) -> tuple[int, bool]:
    """(treatment period, staggered?) for the active dataset: taken from
    the configuration that generated the Virtual World, or inferred from
    the first period in which each unit has D == 1 for uploaded data."""
    if st.session_state.uploaded_df is None and st.session_state.virtual_cfg is not None:
        cfg = st.session_state.virtual_cfg
        return cfg.treatment_period, cfg.staggered_adoption
    first_treated = df.loc[df["D"] == 1].groupby("unit")["period"].min()
    return int(first_treated.min()), first_treated.nunique() > 1


def option_select(container, label_key: str, options: list[str], current: str) -> str:
    """Selectbox over option codes, displayed through the opt.* keys."""
    index = options.index(current) if current in options else 0
    return container.selectbox(L(label_key), options, index=index, format_func=lambda o: L(f"opt.{o}"))


@st.cache_data(show_spinner=False)
def cached_did(df: pd.DataFrame):
    return estimate_did(df)


@st.cache_data(show_spinner=False)
def cached_event_study(df: pd.DataFrame, fixed_treatment_period: int | None):
    return estimate_event_study(df, fixed_treatment_period=fixed_treatment_period)


@st.cache_data(show_spinner=False)
def cached_staggered_did(df: pd.DataFrame):
    return estimate_staggered_did(df)


@st.cache_data(show_spinner=False)
def cached_stress_test(df: pd.DataFrame, treatment_period: int):
    return run_stress_test(df, treatment_period=treatment_period)


@st.cache_data(show_spinner=False)
def cached_robustness(df: pd.DataFrame, treatment_period: int):
    return run_robustness_battery(df, treatment_period=treatment_period)


LEVEL_COLOR = {
    Level.LOW: "🟢", Level.MEDIUM: "🟡", Level.HIGH: "🔴", Level.UNKNOWN: "⚪",
}

# --------------------------------------------------------------------------
# Sidebar navigation
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"## 🔬 {L('app.title')}")
    st.caption(L("app.subtitle"))

    lang_choice = st.radio("🇫🇷 FR | 🇬🇧 EN", ["en", "fr"],
                            index=0 if lang == "en" else 1, horizontal=True,
                            label_visibility="collapsed")
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()

    # Page ids (not translated labels) are the radio values, so the
    # selected page survives a language switch and can be set by the
    # dashboard shortcuts.
    st.radio("Navigation", PAGES, key="page", format_func=lambda p: L(f"nav.{p}"),
             label_visibility="collapsed")
    page = st.session_state.page

    st.divider()
    st.caption(f"🔒 {L('settings.local_mode_note')}")

# --------------------------------------------------------------------------
# DASHBOARD
# --------------------------------------------------------------------------
if page == "dashboard":
    st.title(f"🔬 {L('app.title')}")
    st.subheader(L("app.subtitle"))
    st.markdown(f"**{L('app.tagline')}**")
    st.markdown(f"> {L('home.mission')}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(L("home.metric.question"), yes_no(bool(st.session_state.design.research_question)))
    c2.metric(L("home.metric.diagnosis"), yes_no(st.session_state.diagnosis is not None))
    c3.metric(L("home.metric.recommendations"),
              len(st.session_state.recommendations) if st.session_state.recommendations else 0)
    c4.metric(L("home.metric.dataset"), yes_no(active_df() is not None))

    st.divider()
    cols = st.columns(3)
    cols[0].button(f"📝 {L('home.start_project')}", width="stretch",
                   on_click=go_to, args=("research_question",))
    cols[1].button(f"🧪 {L('home.start_experiment')}", width="stretch",
                   on_click=go_to, args=("virtual_lab",))
    cols[2].button(f"💥 {L('home.diagnose')}", width="stretch",
                   on_click=go_to, args=("break_my_design",))

# --------------------------------------------------------------------------
# STEP 1-5: RESEARCH QUESTION WIZARD
# --------------------------------------------------------------------------
elif page == "research_question":
    st.title(f"📝 {L('nav.research_question')}")
    d = st.session_state.design

    st.subheader(L("step1.title"))
    d.research_question = st.text_area(
        L("step1.question"), value=d.research_question, height=100,
        placeholder=L("step1.placeholder"),
    )

    st.subheader(L("step2.title"))
    c1, c2, c3 = st.columns(3)
    d.treatment_type = option_select(c1, "wizard.treatment_type", ["binary", "continuous", "multiple"],
                                     d.treatment_type)
    d.treatment_timing = option_select(c2, "wizard.treatment_timing",
                                       ["single_date", "staggered", "continuous_time"], d.treatment_timing)
    d.assignment_mechanism = option_select(c3, "wizard.assignment_mechanism",
                                           ["random", "policy", "geographic", "self_selected", "threshold"],
                                           d.assignment_mechanism)

    st.subheader(L("step3.title"))
    d.outcome_type = option_select(st, "wizard.outcome_type",
                                   ["continuous", "binary", "count", "survival", "categorical"], d.outcome_type)

    st.subheader(L("step4.title"))
    d.unit_of_analysis = option_select(st, "wizard.unit_of_analysis",
                                       ["individual", "household", "firm", "municipality", "territory",
                                        "district", "country", "region", "spatial_cell", "time_series"],
                                       d.unit_of_analysis)

    st.subheader(L("step5.title"))
    c1, c2 = st.columns(2)
    d.data_structure = option_select(c1, "wizard.data_structure",
                                     ["cross_section", "panel", "repeated_cross_section", "time_series",
                                      "spatial", "spatio_temporal_panel", "experimental", "survey",
                                      "administrative"], d.data_structure)
    d.has_spatial_component = c2.checkbox(L("wizard.spatial"), value=d.has_spatial_component)

    c1, c2, c3 = st.columns(3)
    d.has_pre_treatment_periods = c1.checkbox(L("wizard.has_pre"), value=d.has_pre_treatment_periods)
    d.n_pre_periods = c2.number_input(L("wizard.n_pre"), min_value=0, value=d.n_pre_periods)
    d.n_post_periods = c3.number_input(L("wizard.n_post"), min_value=0, value=d.n_post_periods)

    st.session_state.design = d

    if st.button(f"➡️ {L('wizard.run')}", type="primary"):
        st.session_state.diagnosis = diagnose(d)
        st.session_state.recommendations = recommend(d, st.session_state.diagnosis)
        st.success(L("wizard.done"))

# --------------------------------------------------------------------------
# CAUSAL DIAGNOSIS ENGINE
# --------------------------------------------------------------------------
elif page == "diagnosis":
    st.title(f"🧠 {L('diagnosis.title')}")

    if st.session_state.diagnosis is None:
        st.info(L("diagnosis.empty"))
    else:
        diag: DiagnosisResult = st.session_state.diagnosis
        cols = st.columns(4)
        for i, (slug, level) in enumerate(diag.as_rows()):
            with cols[i % 4]:
                st.metric(L(f"diagnosis.dim.{slug}"), f"{LEVEL_COLOR[level]} {L(f'level.{level.value}')}")

        if diag.notes:
            st.subheader(L("diagnosis.notes"))
            for note in diag.notes:
                st.warning(R(note))

# --------------------------------------------------------------------------
# METHOD RECOMMENDATION ENGINE
# --------------------------------------------------------------------------
elif page == "recommendation":
    st.title(f"🧪 {L('recommendation.title')}")

    if not st.session_state.recommendations:
        st.info(L("recommendation.empty"))
    else:
        recs: list[MethodScore] = st.session_state.recommendations
        best = recs[0]

        def method_name(score: MethodScore) -> str:
            return L(f"method.{score.key}")

        st.markdown(f"### {L('recommendation.primary_method')}: **{method_name(best)}**")
        st.markdown(f"**{L('recommendation.confidence')}: {L(f'level.{best.confidence}')}**")
        for r in best.rationale:
            st.write("— " + R(r))
        c1, c2 = st.columns(2)
        c1.info(f"**{L('recommendation.main_assumption')}:** {R(best.main_assumption)}")
        c2.warning(f"**{L('recommendation.main_concern')}:** {R(best.main_concern)}")

        st.divider()
        st.subheader(L("recommendation.all_candidates"))

        fig = go.Figure(go.Bar(
            x=[r.overall for r in recs],
            y=[method_name(r) for r in recs],
            orientation="h",
            marker_color=["#2E86AB" if r is best else "#A9C9DE" for r in recs],
        ))
        fig.update_layout(xaxis_title=L("recommendation.score_axis"), yaxis_title="",
                           height=350, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")

        for r in recs:
            with st.expander(f"{method_name(r)} — {r.overall:.0f}/100 ({L(f'level.{r.confidence}')})"):
                st.table(pd.DataFrame(
                    [(L(f"rec.component.{component_slug(k)}"), v) for k, v in r.components.items()],
                    columns=[L("recommendation.component"), L("recommendation.score")]))
                for note in r.rationale:
                    st.write("— " + R(note))
                st.caption(f"{L('recommendation.main_assumption')}: {R(r.main_assumption)}")
                st.caption(f"{L('recommendation.main_concern')}: {R(r.main_concern)}")

        st.caption(L("recommendation.disclaimer"))

# --------------------------------------------------------------------------
# VIRTUAL WORLD
# --------------------------------------------------------------------------
elif page == "virtual_lab":
    st.title(f"🧫 {L('virtual.title')}")
    st.caption(L("virtual.intro"))

    cfg = st.session_state.vw_config
    c1, c2, c3 = st.columns(3)
    cfg.n_units = c1.number_input(L("virtual.n_units"), 20, 2000, cfg.n_units, step=10)
    cfg.n_periods = c2.number_input(L("virtual.n_periods"), 4, 60, cfg.n_periods)
    cfg.treatment_period = c3.number_input(L("virtual.treatment_period"), 2, cfg.n_periods - 1,
                                           min(max(cfg.treatment_period, 2), cfg.n_periods - 1))

    c1, c2, c3 = st.columns(3)
    cfg.share_treated = c1.slider(L("virtual.share_treated"), 0.05, 0.9, cfg.share_treated)
    cfg.true_att = c2.number_input(L("virtual.true_att"), value=cfg.true_att, step=0.1)
    cfg.noise_sd = c3.number_input(L("virtual.noise"), 0.1, 5.0, cfg.noise_sd)

    st.subheader(L("virtual.threats"))

    def threat(container, key: str, value: str) -> str:
        return container.select_slider(L(f"threat.{key}"), LEVELS, value=value,
                                       format_func=lambda v: L(f"intensity.{v}"))

    c1, c2, c3 = st.columns(3)
    cfg.confounding = threat(c1, "confounding", cfg.confounding)
    cfg.spillovers = threat(c2, "spillovers", cfg.spillovers)
    cfg.serial_correlation = threat(c3, "serial_correlation", cfg.serial_correlation)
    c1, c2, c3 = st.columns(3)
    cfg.treatment_heterogeneity = threat(c1, "treatment_heterogeneity", cfg.treatment_heterogeneity)
    cfg.differential_trend = threat(c2, "differential_trend", cfg.differential_trend)
    cfg.anticipation = threat(c3, "anticipation", cfg.anticipation)
    c1, c2, c3 = st.columns(3)
    cfg.dynamic_effects = threat(c1, "dynamic_effects", cfg.dynamic_effects)
    cfg.staggered_adoption = c2.checkbox(L("threat.staggered_adoption"), value=cfg.staggered_adoption)
    cfg.seed = int(c3.number_input(L("common.seed"), min_value=0, value=cfg.seed or 42, step=1))

    st.session_state.vw_config = cfg

    if st.button(f"⚗️ {L('virtual.generate')}", type="primary"):
        df, truth = generate(cfg)
        st.session_state.virtual_df = df
        st.session_state.virtual_truth = truth
        st.session_state.virtual_cfg = replace(cfg)
        st.session_state.uploaded_df = None
        st.success(F("virtual.generated", units=cfg.n_units, periods=cfg.n_periods, rows=len(df),
                     att=truth["true_att"]))

    st.divider()
    st.subheader(L("virtual.upload_title"))
    uploaded = st.file_uploader(L("virtual.upload_label"), type=["csv"])
    # The uploader returns the same file on every rerun: load it once per
    # file, so generating a Virtual World afterwards is not silently
    # overridden by the stale upload.
    if uploaded is not None and uploaded.file_id != st.session_state.uploaded_file_id:
        st.session_state.uploaded_file_id = uploaded.file_id
        try:
            up_df = pd.read_csv(uploaded)
        except Exception as exc:
            st.error(F("common.read_error", error=exc))
        else:
            missing = missing_required_columns(up_df)
            if missing:
                st.error(F("virtual.missing_columns", missing=", ".join(missing),
                           expected=", ".join(REQUIRED_COLUMNS)))
            elif up_df["D"].nunique() < 2:
                st.error(L("virtual.no_variation"))
            else:
                st.session_state.uploaded_df = up_df
                st.session_state.virtual_df = None
                st.session_state.virtual_truth = None
                st.session_state.virtual_cfg = None
                st.success(F("virtual.loaded", rows=len(up_df), columns=", ".join(map(str, up_df.columns))))

    # Real data shipped with the app: the raw Card & Krueger file cannot go
    # through the CSV uploader (fixed-width .dat, no unit/period/D/Y columns).
    if st.button(f"📂 {L('virtual.load_card_krueger')}"):
        st.session_state.uploaded_df = load_card_krueger()
        st.session_state.uploaded_file_id = "card_krueger_1994"
        st.session_state.virtual_df = None
        st.session_state.virtual_truth = None
        st.session_state.virtual_cfg = None
        st.success(F("virtual.card_krueger_loaded", rows=len(st.session_state.uploaded_df)))

    if active_df() is not None:
        st.dataframe(active_df().head(20), width="stretch")
        st.download_button(L("virtual.download"), active_df().to_csv(index=False),
                           "causal_lab_data.csv", mime="text/csv")

    if st.session_state.virtual_df is not None:
        st.divider()
        st.subheader(L("mc.title"))
        st.caption(L("mc.caption"))
        n_reps = st.select_slider(L("mc.replications"), [100, 500, 1000, 5000], value=500)
        if st.button(f"🎲 {L('mc.run')}"):
            with st.spinner(L("mc.running")):
                summary = run_monte_carlo(cfg, n_reps=n_reps, base_seed=int(cfg.seed or 0))
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(L("mc.bias"), f"{summary.bias:+.4f}")
            c2.metric(L("mc.rmse"), f"{summary.rmse:.4f}")
            c3.metric(L("mc.coverage"), f"{summary.coverage:.0%}")
            c4.metric(L("mc.ci_length"), f"{summary.avg_ci_length:.3f}")
            fig = go.Figure(go.Histogram(x=summary.estimates, nbinsx=40))
            fig.add_vline(x=summary.true_att, line_color="red", line_dash="dash",
                           annotation_text=L("common.true_att"))
            fig.update_layout(title=L("mc.histogram_title"), xaxis_title=L("common.estimated_att"), height=350)
            st.plotly_chart(fig, width="stretch")

# --------------------------------------------------------------------------
# ESTIMATION
# --------------------------------------------------------------------------
elif page == "estimation":
    st.title(f"📈 {L('estimation.title')}")
    df = active_df()
    if df is None:
        st.info(L("common.no_dataset"))
    else:
        treatment_period, staggered = treatment_setup(df)

        # Treated vs untreated average outcome over time (README section 3).
        means = df.groupby(["period", "treated_unit"])["Y"].mean().unstack("treated_unit")
        fig = go.Figure()
        for flag, name in ((1, L("trend.treated")), (0, L("trend.untreated"))):
            if flag in means.columns:
                fig.add_trace(go.Scatter(x=means.index, y=means[flag], mode="lines+markers", name=name))
        fig.add_vline(x=treatment_period - 0.5, line_dash="dash", line_color="red",
                      annotation_text=L("trend.first_adoption") if staggered else L("common.treatment"))
        fig.update_layout(title=L("trend.title"), xaxis_title=L("common.period"),
                          yaxis_title=L("trend.y_axis"), height=360)
        st.plotly_chart(fig, width="stretch")

        truth = st.session_state.virtual_truth if st.session_state.uploaded_df is None else None
        tab1, tab2, tab3 = st.tabs([L("method.did"), L("method.event_study"), L("staggered.tab")])

        with tab1:
            try:
                result = cached_did(df)
            except LocalizedError as exc:
                st.error(exc.render(lang))
                result = None
            if result is not None:
                c1, c2, c3 = st.columns(3)
                c1.metric(L("common.estimated_att"), f"{result.att:.4f}")
                c2.metric(L("estimation.cluster_se"), f"{result.se:.4f}")
                c3.metric(L("common.ci95"), f"[{result.ci_low:.3f}, {result.ci_high:.3f}]")

                if truth is not None:
                    true_att = truth["true_att"]
                    st.markdown(f"#### {L('estimation.truth_title')}")
                    c1, c2, c3 = st.columns(3)
                    c1.metric(L("common.estimated_att"), f"{result.att:.4f}")
                    c2.metric(L("common.true_att"), f"{true_att:.4f}")
                    c3.metric(L("common.bias"), f"{result.att - true_att:+.4f}")
                if staggered:
                    st.warning(L("estimation.staggered_warning"))

                st.code(F("estimation.summary", att=result.att, se=result.se, t=result.t_stat,
                          p=result.p_value, lo=result.ci_low, hi=result.ci_high), language="text")

        with tab2:
            # Staggered adoption: each unit's own adoption period is
            # inferred from D; otherwise the common treatment date is used.
            es = cached_event_study(df, None if staggered else treatment_period)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=es.coefficients["rel_period"], y=es.coefficients["estimate"],
                error_y=dict(type="data", array=1.96 * es.coefficients["se"], visible=True),
                mode="markers+lines", name=L("common.estimate")))
            fig.add_hline(y=0, line_dash="dot", line_color="gray")
            fig.add_vline(x=-0.5, line_dash="dash", line_color="red", annotation_text=L("common.treatment"))
            fig.update_layout(title=L("event_study.title"), xaxis_title=L("event_study.x_axis"),
                              yaxis_title=L("event_study.y_axis"), height=400)
            st.plotly_chart(fig, width="stretch")
            st.caption(L("event_study.caption"))

        with tab3:
            st.caption(L("staggered.intro"))
            try:
                cs = cached_staggered_did(df)
            except LocalizedError as exc:
                st.error(exc.render(lang))
                cs = None
            if cs is not None:
                c1, c2, c3 = st.columns(3)
                c1.metric(L("common.estimated_att"), f"{cs.att:.4f}")
                c2.metric(L("staggered.bootstrap_se"), f"{cs.se:.4f}")
                c3.metric(L("common.ci95"), f"[{cs.ci_low:.3f}, {cs.ci_high:.3f}]")
                rows = [{L("staggered.col.estimator"): L("staggered.twfe"), "ATT": cached_did(df).att},
                        {L("staggered.col.estimator"): L("staggered.cs"), "ATT": cs.att}]
                if truth is not None:
                    rows.append({L("staggered.col.estimator"): L("common.true_att"), "ATT": truth["true_att"]})
                st.dataframe(pd.DataFrame(rows).round(4), width="stretch", hide_index=True)
                st.caption(F("staggered.details", cohorts=cs.n_cohorts, units=cs.n_units,
                             comparison=L(f"staggered.comparison.{cs.comparison}")))
                es_cs = cs.event_study
                fig = go.Figure(go.Scatter(
                    x=es_cs["rel_period"], y=es_cs["estimate"],
                    error_y=dict(type="data", array=1.96 * es_cs["se"], visible=True),
                    mode="markers+lines", name=L("staggered.cs")))
                fig.add_hline(y=0, line_dash="dot", line_color="gray")
                fig.add_vline(x=-0.5, line_dash="dash", line_color="red", annotation_text=L("common.treatment"))
                fig.update_layout(title=L("staggered.event_title"), xaxis_title=L("event_study.x_axis"),
                                  yaxis_title=L("event_study.y_axis"), height=400)
                st.plotly_chart(fig, width="stretch")

# --------------------------------------------------------------------------
# CAUSAL METHODS (RCT, Matching, IV, RDD, Synthetic Control, DML)
# --------------------------------------------------------------------------
elif page == "methods":
    render_methods_page(L)

# --------------------------------------------------------------------------
# THEORETICAL MODEL (agents, equilibrium, calibration, predictions)
# --------------------------------------------------------------------------
elif page == "theory":
    render_theory_page(L)

# --------------------------------------------------------------------------
# BREAK MY DESIGN
# --------------------------------------------------------------------------
elif page == "break_my_design":
    st.title(f"💥 {L('break.title')}")
    df = active_df()
    if df is None:
        st.info(L("common.no_dataset"))
    else:
        treatment_period, _ = treatment_setup(df)
        report = cached_stress_test(df, treatment_period)

        pt = next(c for c in report.checks if c.name == "Parallel Trends")
        if pt.assessment:
            {"plausible": st.success, "questionable": st.warning, "violated": st.error}[pt.assessment](
                "### " + F("break.pt_banner", assessment=L(f"assessment.{pt.assessment}")))

        st.subheader(L("break.results"))
        for check in report.checks:
            icon = "✓" if check.verdict == "PASS" else "⚠"
            show = st.success if check.verdict == "PASS" else st.warning
            show(f"**{L(f'check.{check.slug}')}** {icon} {L(f'verdict.{check.verdict}')} — {R(check.message)}")

        st.divider()
        st.subheader(L("break.strength"))
        st.progress(report.identification_strength / 100)
        st.markdown(f"### {report.identification_strength:.0f} / 100")
        st.caption(L("break.disclaimer"))

# --------------------------------------------------------------------------
# ROBUSTNESS
# --------------------------------------------------------------------------
elif page == "robustness":
    st.title(f"🧯 {L('robustness.title')}")
    df = active_df()
    if df is None:
        st.info(L("common.no_dataset"))
    else:
        treatment_period, _ = treatment_setup(df)
        rows = cached_robustness(df, treatment_period)
        col_spec, col_att, col_se, col_n, col_note = (L("robustness.col.specification"), "ATT", L("common.se"),
                                                      "N", L("robustness.col.note"))
        table = pd.DataFrame([{
            col_spec: R(r.specification), col_att: round(r.att, 4),
            col_se: round(r.se, 4), col_n: r.n_obs, col_note: R(r.note),
        } for r in rows])
        st.dataframe(table, width="stretch")

        fig = go.Figure(go.Scatter(
            x=table[col_att], y=table[col_spec], mode="markers",
            error_x=dict(type="data", array=(table[col_se] * 1.96).fillna(0), visible=True),
            marker=dict(size=10),
        ))
        fig.add_vline(x=rows[0].att, line_dash="dot", line_color="gray", annotation_text=L("robustness.baseline_mark"))
        fig.update_layout(height=350, xaxis_title=L("common.estimated_att"), yaxis_title="")
        st.plotly_chart(fig, width="stretch")

# --------------------------------------------------------------------------
# CODE GENERATOR
# --------------------------------------------------------------------------
elif page == "code":
    st.title(f"💻 {L('code.title')}")
    c1, c2 = st.columns(2)
    data_path = c1.text_input(L("code.data_path"), value="data.csv")
    cluster_col = c2.text_input(L("code.cluster"), value="unit")
    params = CodeGenParams(data_path=data_path, cluster_col=cluster_col)
    code = generate_all(params, lang)

    tab1, tab2, tab3 = st.tabs(["Python", "R", "Stata"])
    with tab1:
        st.code(code["python"], language="python")
        st.download_button(F("code.download", language="Python"), code["python"], "causal_lab_did.py")
    with tab2:
        st.code(code["r"], language="r")
        st.download_button(F("code.download", language="R"), code["r"], "causal_lab_did.R")
    with tab3:
        st.code(code["stata"], language="stata")
        st.download_button(F("code.download", language="Stata"), code["stata"], "causal_lab_did.do")

# --------------------------------------------------------------------------
# SETTINGS
# --------------------------------------------------------------------------
elif page == "settings":
    st.title(f"⚙️ {L('settings.language')}")
    st.write(F("settings.current_language", language=st.session_state.lang.upper()))
    st.info(L("settings.local_mode_note"))
    st.caption(L("settings.build_note"))
