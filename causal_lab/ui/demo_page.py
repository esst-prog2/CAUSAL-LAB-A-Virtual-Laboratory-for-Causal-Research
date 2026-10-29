"""
Guided demo: the app's main claim, demonstrated as a short paper.

1. Question and design of the simulation study.
2. One world with parallel trends and one without (live, seed 42).
3. The simulation study over 1000 worlds per level of diverging pre-trends
   (stored by spike/demo_study.py; 100 of them can be re-run live and are
   checked against the stored values).
4. Replication of Card & Krueger (1994), Table 3.
5. What this does not show.

Every number on the page comes from an engine or from the stored study;
none is typed in a text. Numbers follow the interface language's
conventions (decimal comma and a space before % in French).
"""
from __future__ import annotations

from dataclasses import replace

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from estimators.did import estimate_did
from robustness_engine.stress_test import _check_parallel_trends
from simulation_engine.demo_study import (CARD_KRUEGER_TABLE3, LEVELS, design, load_study, replicate_card_krueger,
                                          run_level, same, summarize)
from simulation_engine.dgp import generate
from ui.page_text import F, lang, references_caption
from utils.real_data import load_card_krueger

ONE_WORLD = 42                    # the seed of the single-world illustration (README section 1)
LIVE_REPS = 100


# --------------------------------------------------------------------------
# Numbers in the interface language
# --------------------------------------------------------------------------
def num(x: float, digits: int = 3, sign: bool = False) -> str:
    text = f"{x:+.{digits}f}" if sign else f"{x:.{digits}f}"
    text = text.replace("-", "−")                                     # typographic minus
    return text.replace(".", ",") if lang() == "fr" else text


def pct(x: float | None, digits: int = 1) -> str:
    if x is None:
        return "—"
    text = f"{100 * x:.{digits}f}"
    return text.replace(".", ",") + " %" if lang() == "fr" else text + "%"


# --------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _one_world(level: str):
    cfg = replace(design(level), seed=ONE_WORLD)
    df, truth = generate(cfg)
    did = estimate_did(df)
    pre = _check_parallel_trends(df, "Y", "unit", "period", "treated_unit", cfg.treatment_period)
    return truth["true_att"], did, pre


@st.cache_data(show_spinner=False)
def _study():
    return load_study()


@st.cache_data(show_spinner=False)
def _replication():
    return replicate_card_krueger(load_card_krueger())


def render(L) -> None:
    st.title(f"🎓 {L('demo.title')}")
    st.caption(L("demo.intro"))

    # 1. Question and design
    st.header(L("demo.s1"))
    cfg = design("none")
    st.markdown(L("demo.question"))
    st.markdown(F("demo.design", units=cfg.n_units, periods=cfg.n_periods, tp=cfg.treatment_period,
                  share=pct(cfg.share_treated, 0), att=num(cfg.true_att, 2, sign=True), sd=num(cfg.noise_sd, 1)))

    # 2. One world each way
    st.header(L("demo.s2"))
    rows = []
    for level in ("none", "severe"):
        truth, did, pre = _one_world(level)
        rows.append({L("demo.col.pretrends"): L(f"intensity.{level}"), L("common.true_att"): num(truth),
                     L("common.estimated_att"): num(did.att),
                     L("common.ci95"): f"[{num(did.ci_low)} ; {num(did.ci_high)}]" if lang() == "fr"
                     else f"[{num(did.ci_low)}, {num(did.ci_high)}]",
                     L("demo.col.covers"): L("common.yes") if did.ci_low <= truth <= did.ci_high else L("common.no"),
                     L("demo.col.pretest"): f"{L(f'verdict.{pre.verdict}')} (p = {num(pre.p_value)})"})
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.caption(F("demo.one_world_caption", seed=ONE_WORLD))

    # 3. Simulation study
    st.header(L("demo.s3"))
    stored = _study()
    if stored is None:
        st.info(L("demo.no_study"))
    else:
        meta, reps = stored
        summaries = {level: summarize(level, reps[level]) for level in LEVELS}
        _study_table(summaries, L)
        _study_figure(summaries, L)
        st.caption(F("demo.provenance", reps=meta["replications_per_level"], seed=meta["seed_base"],
                     date=meta["computed_at"][:10], script=meta["script"]))
        _reading(summaries, L)
        _live_rerun(reps, L)

    # 4. Replication
    st.header(L("demo.s4"))
    _replication_table(L)

    # 5. Limits
    st.header(L("demo.s5"))
    st.markdown(L("demo.limits"))
    references_caption("demo_study", "demo_replication")


def _reading(summaries, L) -> None:
    none, high, severe = summaries["none"], summaries["high"], summaries["severe"]
    st.markdown(F("demo.reading_clean", coverage=pct(none.coverage), mcse=pct(none.coverage_mcse),
                  bias=num(none.bias, sign=True), bias_mcse=num(none.bias_mcse), rejection=pct(none.rejection),
                  false_alarm=pct(none.detection)))
    st.markdown(F("demo.reading_violated", coverage=pct(severe.coverage), bias=num(severe.bias, sign=True),
                  mean=num(severe.mean_estimate, sign=True), att=num(severe.true_att, sign=True),
                  wrong_sign=pct(severe.wrong_sign), detection=pct(severe.detection),
                  high_level=L("intensity.high"), high_detection=pct(high.detection)))
    # The violated level where the most worlds pass the pre-trend test.
    violated = [s for s in summaries.values() if s.level != "none" and s.coverage_given_pass is not None]
    if violated:
        s = max(violated, key=lambda s: s.n_pass)
        st.markdown(F("demo.reading_pretest", level=L(f"intensity.{s.level}"), n_pass=s.n_pass, reps=s.n_reps,
                      coverage_pass=pct(s.coverage_given_pass)))


def _study_table(summaries, L) -> None:
    # The columns the text discusses first; the rest of the Morris et al. (2019) set after them.
    rows = [{L("demo.col.pretrends"): L(f"intensity.{s.level}"),
             L("common.bias"): f"{num(s.bias, sign=True)} ({num(s.bias_mcse)})",
             L("demo.col.coverage"): f"{pct(s.coverage)} ({pct(s.coverage_mcse)})",
             L("demo.col.wrong_sign"): pct(s.wrong_sign),
             L("demo.col.detection"): f"{pct(s.detection)} ({pct(s.detection_mcse)})",
             L("demo.col.coverage_pass"): f"{pct(s.coverage_given_pass)} (n = {s.n_pass})",
             L("demo.col.mean"): num(s.mean_estimate),
             L("demo.col.emp_se"): f"{num(s.empirical_se)} / {num(s.mean_model_se)}",
             "RMSE": num(s.rmse),
             L("demo.col.rejection"): pct(s.rejection)}
            for s in summaries.values()]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.caption(L("demo.table_note"))


def _study_figure(summaries, L) -> None:
    x = [L(f"intensity.{level}") for level in summaries]
    fig = go.Figure()
    for attr, mcse, name in (("coverage", "coverage_mcse", L("demo.col.coverage")),
                             ("detection", "detection_mcse", L("demo.col.detection"))):
        fig.add_trace(go.Scatter(x=x, y=[getattr(s, attr) for s in summaries.values()], mode="lines+markers",
                                 name=name, error_y=dict(type="data", visible=True,
                                                         array=[1.96 * getattr(s, mcse) for s in summaries.values()])))
    fig.add_hline(y=0.95, line_dash="dot", annotation_text=L("demo.nominal"), annotation_position="bottom left")
    fig.update_layout(xaxis_title=L("demo.col.pretrends"), yaxis_title=L("demo.share"), yaxis_tickformat=".0%",
                      yaxis_range=[0, 1.02], height=360, margin=dict(t=30, b=40),
                      separators=", " if lang() == "fr" else ".,")
    st.plotly_chart(fig, width="stretch")


def _live_rerun(reps, L) -> None:
    with st.expander(F("demo.rerun_title", n=LIVE_REPS)):
        st.caption(F("demo.rerun_intro", n=LIVE_REPS))
        level = st.selectbox(L("demo.col.pretrends"), LEVELS, format_func=lambda v: L(f"intensity.{v}"),
                             key="demo_rerun_level")
        if st.button(f"🔁 {F('demo.rerun_button', n=LIVE_REPS)}", key="demo_rerun"):
            with st.spinner(L("demo.rerun_running")):
                live = run_level(level, LIVE_REPS)
            identical = all(same(a, b) for a, b in zip(live, reps[level][:LIVE_REPS], strict=True))
            s = summarize(level, live)
            st.write(F("demo.rerun_result", n=LIVE_REPS, coverage=pct(s.coverage), bias=num(s.bias, sign=True),
                       detection=pct(s.detection)))
            (st.success if identical else st.error)(L("demo.rerun_identical" if identical else "demo.rerun_differs"))


def _replication_table(L) -> None:
    ours = _replication()
    rows, agree, cells = [], 0, 0
    for row, published in CARD_KRUEGER_TABLE3.items():
        record = {L("demo.col.ck_row"): L(f"demo.ck.{row}")}
        for col in ("pa", "nj", "diff"):
            (pm, ps), (om, os_) = published[col], ours[row][col]
            record[L(f"demo.ck.{col}")] = f"{num(pm, 2)} ({num(ps, 2)}) · {num(om, 2)} ({num(os_, 2)})"
            agree += (f"{pm:.2f}" == f"{om:.2f}") + (f"{ps:.2f}" == f"{os_:.2f}")
            cells += 2
        rows.append(record)
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.caption(L("demo.ck_note"))
    st.markdown(F("demo.ck_agreement", agree=agree, cells=cells))
