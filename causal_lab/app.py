"""
CAUSAL LAB — Streamlit entry point (v0.1 MVP).

Implements the first end-to-end user journey described in the spec
(Section 54):

    research question -> diagnosis -> method recommendation ->
    virtual world / data -> estimation -> stress test -> robustness ->
    code generation

Run with:  streamlit run app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from causal_engine.diagnosis import DiagnosisResult, Level, ResearchDesignInput, diagnose
from causal_engine.recommendation import MethodScore, recommend
from code_generator.generator import CodeGenParams, generate_all
from estimators.did import estimate_did
from estimators.event_study import estimate_event_study
from robustness_engine.robustness import run_robustness_battery
from robustness_engine.stress_test import run_stress_test
from simulation_engine.dgp import VirtualWorldConfig, generate
from simulation_engine.monte_carlo import run_monte_carlo
from utils.i18n import t
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
if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None

lang = st.session_state.lang


def L(key: str) -> str:
    return t(key, lang)


def active_df() -> pd.DataFrame | None:
    """Whichever dataset is currently loaded: an uploaded real-world
    dataset takes priority over the simulated Virtual World data."""
    if st.session_state.uploaded_df is not None:
        return st.session_state.uploaded_df
    return st.session_state.virtual_df


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

    page = st.radio(
        "Navigation",
        [
            L("nav.dashboard"), L("nav.research_question"), L("nav.diagnosis"),
            L("nav.recommendation"), L("nav.virtual_lab"), L("nav.estimation"),
            L("nav.break_my_design"), L("nav.robustness"), L("nav.code"),
            L("nav.settings"),
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.caption(f"🔒 {L('settings.local_mode_note')}")

# --------------------------------------------------------------------------
# DASHBOARD
# --------------------------------------------------------------------------
if page == L("nav.dashboard"):
    st.title(f"🔬 {L('app.title')}")
    st.subheader(L("app.subtitle"))
    st.markdown(f"**{L('app.tagline')}**")
    st.markdown(
        "> CAUSAL LAB does not simply estimate causal effects. It helps "
        "researchers determine whether their research design can "
        "credibly identify them."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Research question set", "Yes" if st.session_state.design.research_question else "No")
    c2.metric("Diagnosis run", "Yes" if st.session_state.diagnosis else "No")
    c3.metric("Recommendations", len(st.session_state.recommendations) if st.session_state.recommendations else 0)
    c4.metric("Dataset loaded", "Yes" if active_df() is not None else "No")

    st.divider()
    cols = st.columns(3)
    if cols[0].button(f"📝 {L('home.start_project')}", use_container_width=True):
        st.session_state["_go_to"] = L("nav.research_question")
    if cols[1].button(f"🧪 {L('home.start_experiment')}", use_container_width=True):
        st.session_state["_go_to"] = L("nav.virtual_lab")
    if cols[2].button(f"💥 {L('home.diagnose')}", use_container_width=True):
        st.session_state["_go_to"] = L("nav.break_my_design")

# --------------------------------------------------------------------------
# STEP 1-5: RESEARCH QUESTION WIZARD
# --------------------------------------------------------------------------
elif page == L("nav.research_question"):
    st.title(f"📝 {L('nav.research_question')}")
    d = st.session_state.design

    st.subheader(L("step1.title"))
    d.research_question = st.text_area(
        L("step1.question"), value=d.research_question, height=100,
        placeholder=("What is the effect of mining exposure on child health "
                     "in neighboring territories?"),
    )

    st.subheader(L("step2.title"))
    c1, c2, c3 = st.columns(3)
    d.treatment_type = c1.selectbox("Treatment type", ["binary", "continuous", "multiple"],
                                     index=["binary", "continuous", "multiple"].index(d.treatment_type))
    d.treatment_timing = c2.selectbox("Treatment timing",
                                       ["single_date", "staggered", "continuous_time"],
                                       index=["single_date", "staggered", "continuous_time"].index(d.treatment_timing))
    d.assignment_mechanism = c3.selectbox(
        "Assignment mechanism",
        ["random", "policy", "geographic", "self_selected", "threshold"],
        index=["random", "policy", "geographic", "self_selected", "threshold"].index(d.assignment_mechanism))

    st.subheader(L("step3.title"))
    d.outcome_type = st.selectbox(
        "Outcome type",
        ["continuous", "binary", "count", "survival", "categorical"],
        index=["continuous", "binary", "count", "survival", "categorical"].index(d.outcome_type))

    st.subheader(L("step4.title"))
    d.unit_of_analysis = st.selectbox(
        "Unit of analysis",
        ["individual", "household", "firm", "municipality", "territory",
         "district", "country", "region", "spatial_cell", "time_series"],
        index=0 if d.unit_of_analysis not in
        ["individual", "household", "firm", "municipality", "territory",
         "district", "country", "region", "spatial_cell", "time_series"]
        else ["individual", "household", "firm", "municipality", "territory",
              "district", "country", "region", "spatial_cell", "time_series"].index(d.unit_of_analysis))

    st.subheader(L("step5.title"))
    c1, c2 = st.columns(2)
    d.data_structure = c1.selectbox(
        "Data structure",
        ["cross_section", "panel", "repeated_cross_section", "time_series",
         "spatial", "spatio_temporal_panel", "experimental", "survey", "administrative"],
        index=["cross_section", "panel", "repeated_cross_section", "time_series",
               "spatial", "spatio_temporal_panel", "experimental", "survey",
               "administrative"].index(d.data_structure))
    d.has_spatial_component = c2.checkbox("Has a spatial component", value=d.has_spatial_component)

    c1, c2, c3 = st.columns(3)
    d.has_pre_treatment_periods = c1.checkbox("Pre-treatment periods available", value=d.has_pre_treatment_periods)
    d.n_pre_periods = c2.number_input("Number of pre-treatment periods", min_value=0, value=d.n_pre_periods)
    d.n_post_periods = c3.number_input("Number of post-treatment periods", min_value=0, value=d.n_post_periods)

    st.session_state.design = d

    if st.button("➡️ Run Causal Diagnosis", type="primary"):
        st.session_state.diagnosis = diagnose(d)
        st.session_state.recommendations = recommend(d, st.session_state.diagnosis)
        st.success("Diagnosis complete — see 'Causal Diagnosis' and 'Method Recommendation' pages.")

# --------------------------------------------------------------------------
# CAUSAL DIAGNOSIS ENGINE
# --------------------------------------------------------------------------
elif page == L("nav.diagnosis"):
    st.title(f"🧠 {L('diagnosis.title')}")

    if st.session_state.diagnosis is None:
        st.info("No diagnosis yet. Fill in the Research Question wizard first.")
    else:
        diag: DiagnosisResult = st.session_state.diagnosis
        cols = st.columns(4)
        table = diag.as_table()
        for i, (name, level) in enumerate(table):
            with cols[i % 4]:
                st.metric(name, f"{LEVEL_COLOR[Level(level)]} {level}")

        if diag.notes:
            st.subheader("Notes")
            for note in diag.notes:
                st.warning(note)

# --------------------------------------------------------------------------
# METHOD RECOMMENDATION ENGINE
# --------------------------------------------------------------------------
elif page == L("nav.recommendation"):
    st.title(f"🧪 {L('recommendation.title')}")

    if not st.session_state.recommendations:
        st.info("No recommendation yet. Fill in the Research Question wizard first.")
    else:
        recs: list[MethodScore] = st.session_state.recommendations
        best = recs[0]

        st.markdown(f"### {L('recommendation.primary_method')}: **{best.method}**")
        st.markdown(f"**{L('recommendation.confidence')}: {best.confidence}**")
        for r in best.rationale:
            st.write("— " + r)
        c1, c2 = st.columns(2)
        c1.info(f"**Main assumption:** {best.main_assumption}")
        c2.warning(f"**Main concern:** {best.main_concern}")

        st.divider()
        st.subheader("CAUSAL LAB Method Suitability Score — all candidates")

        fig = go.Figure(go.Bar(
            x=[r.overall for r in recs],
            y=[r.method for r in recs],
            orientation="h",
            marker_color=["#2E86AB" if r is best else "#A9C9DE" for r in recs],
        ))
        fig.update_layout(xaxis_title="Suitability score (0-100)", yaxis_title="",
                           height=350, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        for r in recs:
            with st.expander(f"{r.method} — {r.overall:.0f}/100 ({r.confidence})"):
                st.table(pd.DataFrame(list(r.components.items()), columns=["Component", "Score"]))
                for note in r.rationale:
                    st.write("— " + note)
                st.caption(f"Main assumption: {r.main_assumption}")
                st.caption(f"Main concern: {r.main_concern}")

        st.caption(
            "This score is a transparent, explainable heuristic — the "
            "CAUSAL LAB Method Suitability Score — not a guarantee of "
            "causal identification."
        )

# --------------------------------------------------------------------------
# VIRTUAL WORLD
# --------------------------------------------------------------------------
elif page == L("nav.virtual_lab"):
    st.title(f"🧫 {L('virtual.title')}")
    st.caption("Build a synthetic world with a known ground-truth effect, "
               "then see how well an estimator recovers it.")

    cfg = st.session_state.vw_config
    c1, c2, c3 = st.columns(3)
    cfg.n_units = c1.number_input("Population (units)", 20, 2000, cfg.n_units, step=10)
    cfg.n_periods = c2.number_input("Time periods", 4, 60, cfg.n_periods)
    cfg.treatment_period = c3.number_input("Treatment period", 1, cfg.n_periods - 1, min(cfg.treatment_period, cfg.n_periods - 1))

    c1, c2, c3 = st.columns(3)
    cfg.share_treated = c1.slider("Share of treated units", 0.05, 0.9, cfg.share_treated)
    cfg.true_att = c2.number_input("True average treatment effect (design value)", value=cfg.true_att, step=0.1)
    cfg.noise_sd = c3.number_input("Noise (std. dev.)", 0.1, 5.0, cfg.noise_sd)

    st.subheader("Causal Threats Generator")
    levels = ["none", "low", "medium", "high", "severe"]
    c1, c2, c3 = st.columns(3)
    cfg.confounding = c1.select_slider("Confounding", levels, value=cfg.confounding)
    cfg.spillovers = c2.select_slider("Spillovers", levels, value=cfg.spillovers)
    cfg.serial_correlation = c3.select_slider("Serial correlation", levels, value=cfg.serial_correlation)
    c1, c2 = st.columns(2)
    cfg.staggered_adoption = c1.checkbox("Staggered adoption", value=cfg.staggered_adoption)
    cfg.treatment_heterogeneity = c2.select_slider("Treatment-effect heterogeneity", levels,
                                                     value=cfg.treatment_heterogeneity)
    cfg.seed = st.number_input("Random seed", value=cfg.seed or 42)

    st.session_state.vw_config = cfg

    if st.button("⚗️ Generate Virtual World", type="primary"):
        df, truth = generate(cfg)
        st.session_state.virtual_df = df
        st.session_state.virtual_truth = truth
        st.session_state.uploaded_df = None
        st.success(f"Virtual World generated: {cfg.n_units} units × {cfg.n_periods} periods "
                   f"({len(df)} rows). True ATT (realized) = {truth['true_att']:.4f}")

    st.divider()
    st.subheader("Upload real-world data instead (Real World Mode)")
    uploaded = st.file_uploader(
        "CSV with columns matching: unit, period, D (treatment), Y (outcome), treated_unit",
        type=["csv"])
    if uploaded is not None:
        try:
            up_df = pd.read_csv(uploaded)
        except Exception as exc:
            st.error(f"Could not read file: {exc}")
        else:
            missing = missing_required_columns(up_df)
            if missing:
                st.error(
                    f"Uploaded CSV is missing required column(s): {', '.join(missing)}. "
                    f"Expected columns: {', '.join(REQUIRED_COLUMNS)}."
                )
            else:
                st.session_state.uploaded_df = up_df
                st.session_state.virtual_df = None
                st.success(f"Loaded {len(up_df)} rows. Columns detected: {list(up_df.columns)}")

    if active_df() is not None:
        st.dataframe(active_df().head(20), use_container_width=True)

    if st.session_state.virtual_df is not None:
        st.divider()
        st.subheader("Monte Carlo Simulation")
        n_reps = st.select_slider("Replications", [100, 500, 1000, 5000], value=500)
        if st.button("🎲 Run Monte Carlo"):
            with st.spinner("Running replications..."):
                summary = run_monte_carlo(cfg, n_reps=n_reps)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Bias", f"{summary.bias:+.4f}")
            c2.metric("RMSE", f"{summary.rmse:.4f}")
            c3.metric("Coverage (95% CI)", f"{summary.coverage:.0%}")
            c4.metric("Avg. CI length", f"{summary.avg_ci_length:.3f}")
            fig = go.Figure(go.Histogram(x=summary.estimates, nbinsx=40))
            fig.add_vline(x=summary.true_att, line_color="red", line_dash="dash",
                           annotation_text="True ATT")
            fig.update_layout(title="Distribution of DiD estimates across replications",
                               xaxis_title="Estimated ATT", height=350)
            st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------------------------------
# ESTIMATION
# --------------------------------------------------------------------------
elif page == L("nav.estimation"):
    st.title(f"📈 {L('estimation.title')}")
    df = active_df()
    if df is None:
        st.info("No dataset loaded. Generate a Virtual World or upload data first.")
    else:
        tab1, tab2 = st.tabs(["Difference-in-Differences", "Event Study"])

        with tab1:
            result = estimate_did(df)
            c1, c2, c3 = st.columns(3)
            c1.metric("Estimated ATT", f"{result.att:.4f}")
            c2.metric("Cluster-robust SE", f"{result.se:.4f}")
            c3.metric("95% CI", f"[{result.ci_low:.3f}, {result.ci_high:.3f}]")

            if st.session_state.virtual_truth is not None:
                true_att = st.session_state.virtual_truth["true_att"]
                bias = result.att - true_att
                st.markdown("#### Ground truth comparison (Virtual World only)")
                c1, c2, c3 = st.columns(3)
                c1.metric("Estimated ATT", f"{result.att:.4f}")
                c2.metric("True ATT", f"{true_att:.4f}")
                c3.metric("Bias", f"{bias:+.4f}")

            st.code(result.summary_text, language="text")

        with tab2:
            treatment_period = st.session_state.vw_config.treatment_period if st.session_state.virtual_df is not None else int(df["period"].median())
            es = estimate_event_study(df, fixed_treatment_period=treatment_period)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=es.coefficients["rel_period"], y=es.coefficients["estimate"],
                error_y=dict(type="data",
                              array=1.96 * es.coefficients["se"],
                              visible=True),
                mode="markers+lines", name="Estimate"))
            fig.add_hline(y=0, line_dash="dot", line_color="gray")
            fig.add_vline(x=-0.5, line_dash="dash", line_color="red",
                          annotation_text="Treatment")
            fig.update_layout(title="Event study: dynamic treatment effects",
                               xaxis_title="Periods relative to treatment",
                               yaxis_title="Effect estimate", height=400)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Pre-treatment coefficients (k < -1) should be close to zero "
                       "if the parallel-trends assumption holds.")

# --------------------------------------------------------------------------
# BREAK MY DESIGN
# --------------------------------------------------------------------------
elif page == L("nav.break_my_design"):
    st.title(f"💥 {L('break.title')}")
    df = active_df()
    if df is None:
        st.info("No dataset loaded. Generate a Virtual World or upload data first.")
    else:
        treatment_period = (st.session_state.vw_config.treatment_period
                             if st.session_state.virtual_df is not None
                             else int(df["period"].median()))
        report = run_stress_test(df, treatment_period=treatment_period)

        st.subheader("Stress Test Results")
        for check in report.checks:
            icon = "✓" if check.verdict == "PASS" else "⚠"
            color = "success" if check.verdict == "PASS" else "warning"
            getattr(st, color)(f"**{check.name}** {icon} {check.verdict} — {check.detail}")

        st.divider()
        st.subheader("Identification Strength")
        st.progress(report.identification_strength / 100)
        st.markdown(f"### {report.identification_strength:.0f} / 100")
        st.caption("This is a diagnostic heuristic based on the checks above, "
                   "not a formal proof of causal identification.")

# --------------------------------------------------------------------------
# ROBUSTNESS
# --------------------------------------------------------------------------
elif page == L("nav.robustness"):
    st.title(f"🧯 {L('robustness.title')}")
    df = active_df()
    if df is None:
        st.info("No dataset loaded. Generate a Virtual World or upload data first.")
    else:
        treatment_period = (st.session_state.vw_config.treatment_period
                             if st.session_state.virtual_df is not None
                             else int(df["period"].median()))
        rows = run_robustness_battery(df, treatment_period=treatment_period)
        table = pd.DataFrame([{
            "Specification": r.specification, "ATT": round(r.att, 4),
            "SE": round(r.se, 4), "N": r.n_obs, "Note": r.note,
        } for r in rows])
        st.dataframe(table, use_container_width=True)

        fig = go.Figure(go.Scatter(
            x=table["ATT"], y=table["Specification"], mode="markers",
            error_x=dict(type="data", array=table["SE"] * 1.96, visible=True),
            marker=dict(size=10),
        ))
        fig.add_vline(x=rows[0].att, line_dash="dot", line_color="gray",
                      annotation_text="Baseline")
        fig.update_layout(height=350, xaxis_title="Estimated ATT", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------------------------------
# CODE GENERATOR
# --------------------------------------------------------------------------
elif page == L("nav.code"):
    st.title(f"💻 {L('code.title')}")
    c1, c2 = st.columns(2)
    data_path = c1.text_input("Data file path (for the generated script)", value="data.csv")
    cluster_col = c2.text_input("Cluster variable", value="unit")
    params = CodeGenParams(data_path=data_path, cluster_col=cluster_col)
    code = generate_all(params)

    tab1, tab2, tab3 = st.tabs(["Python", "R", "Stata"])
    with tab1:
        st.code(code["python"], language="python")
        st.download_button("Download Python script", code["python"], "causal_lab_did.py")
    with tab2:
        st.code(code["r"], language="r")
        st.download_button("Download R script", code["r"], "causal_lab_did.R")
    with tab3:
        st.code(code["stata"], language="stata")
        st.download_button("Download Stata script", code["stata"], "causal_lab_did.do")

# --------------------------------------------------------------------------
# SETTINGS
# --------------------------------------------------------------------------
elif page == L("nav.settings"):
    st.title(f"⚙️ {L('settings.language')}")
    st.write(f"Current language: **{st.session_state.lang.upper()}**")
    st.info(L("settings.local_mode_note"))
    st.caption("CAUSAL LAB v0.1 — MVP build. All computation runs locally "
               "in this Python process; no data is sent anywhere.")
