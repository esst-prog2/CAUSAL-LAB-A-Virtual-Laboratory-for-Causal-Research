"""
Sequential games on the Theoretical Model page: Stackelberg leadership in
the continuous catalogue models, and bargaining (Nash solution, Rubinstein).
"""
from __future__ import annotations

import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from theory_engine.bargaining import nash_bargaining, rubinstein_finite, rubinstein_share
from theory_engine.catalogue import CATALOGUE, build
from theory_engine.sequential import solve_stackelberg
from ui.page_text import F, R, error_text
from utils.i18n import LocalizedError

# Models with at least two agents and smooth payoffs: leadership is meaningful there.
STACKELBERG_MODELS = ("cournot", "bertrand", "tullock", "public_good", "probabilistic_voting")


def render_stackelberg(L) -> None:
    st.caption(L("seq.stackelberg_intro"))
    key = st.selectbox(L("theory.model"), STACKELBERG_MODELS, key="seq_model",
                       format_func=lambda k: f"{R(CATALOGUE[k].category)} — {R(CATALOGUE[k].label)}")
    entry = CATALOGUE[key]
    n = st.slider(L("theory.n_agents"), *entry.n_range, entry.n_range[0], key=f"seq_n_{key}") if entry.n_range else None
    game = build(key, n)
    cols = st.columns(4)
    values = {name: cols[i % 4].number_input(R(game.parameter_info.get(name, name)), value=float(default),
                                             key=f"seq_{key}_{n}_{name}")
              for i, (name, default) in enumerate(game.parameters.items())}
    leader = st.selectbox(L("seq.leader"), range(len(game.agents)), format_func=lambda i: R(game.agents[i].name),
                          key=f"seq_leader_{key}_{n}")
    signature = (key, n, leader, tuple(sorted(values.items())))
    if st.button(f"⚖️ {L('seq.solve')}", type="primary", key="seq_solve"):
        with st.spinner(L("seq.solving")):
            try:
                st.session_state["seq_result"] = (signature, solve_stackelberg(game, values, leader))
            except LocalizedError as exc:
                st.error(error_text(exc))
                return
    stored = st.session_state.get("seq_result")
    if stored is None or stored[0] != signature:          # nothing solved yet for these settings
        return
    result = stored[1]
    sim = result.simultaneous
    rows = []
    for agent in game.agents:
        s = str(agent.strategy)
        rows.append({L("seq.col.agent"): R(agent.name), L("seq.col.strategy"): s,
                     L("seq.col.stackelberg"): round(result.strategies[s], 4),
                     L("seq.col.simultaneous"): round(sim.strategies[s], 4) if sim else None,
                     L("seq.col.utility_stackelberg"): round(result.utilities[agent.name], 4),
                     L("seq.col.utility_simultaneous"): round(sim.utilities[agent.name], 4) if sim else None})
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    if result.outcomes:
        st.dataframe(pd.DataFrame([{L("seq.col.outcome"): R(k), L("seq.col.stackelberg"): round(v, 4),
                                    L("seq.col.simultaneous"): round(sim.outcomes[k], 4) if sim else None}
                                   for k, v in result.outcomes.items()]), width="stretch", hide_index=True)
    if sim:
        gain = result.utilities[result.leader] - sim.utilities[result.leader]
        st.info(F("seq.first_mover", leader=R(result.leader), gain=gain))
    st.caption(L("seq.stackelberg_method"))


def render_bargaining(L) -> None:
    st.subheader(L("seq.nbs_title"))
    st.caption(L("seq.nbs_intro"))
    c1, c2, c3, c4 = st.columns(4)
    surplus = c1.number_input(L("seq.surplus"), 0.01, 1e9, 100.0, key="bg_surplus")
    alpha = c2.slider(L("seq.alpha"), 0.01, 0.99, 0.5, 0.01, key="bg_alpha")
    d1 = c3.number_input(L("seq.d1"), value=0.0, key="bg_d1")
    d2 = c4.number_input(L("seq.d2"), value=0.0, key="bg_d2")
    c1, c2 = st.columns(2)
    u1 = c1.text_input(L("seq.u1"), "m", key="bg_u1")
    u2 = c2.text_input(L("seq.u2"), "m", key="bg_u2")
    try:
        nbs = nash_bargaining(surplus, alpha, d1, d2, u1, u2)
    except LocalizedError as exc:
        st.error(error_text(exc))
    else:
        a, b, c = st.columns(3)
        a.metric(L("seq.share_1"), f"{nbs.share_1:.4f}")
        b.metric(L("seq.payoff_1"), f"{nbs.payoff_1:.4f}")
        c.metric(L("seq.payoff_2"), f"{nbs.payoff_2:.4f}")

    st.subheader(L("seq.rubinstein_title"))
    st.caption(L("seq.rubinstein_intro"))
    c1, c2, c3 = st.columns(3)
    delta_1 = c1.slider(L("seq.delta1"), 0.0, 0.99, 0.9, 0.01, key="bg_delta1")
    delta_2 = c2.slider(L("seq.delta2"), 0.0, 0.99, 0.8, 0.01, key="bg_delta2")
    rounds = c3.slider(L("seq.rounds"), 1, 60, 20, key="bg_rounds")
    try:
        share = rubinstein_share(delta_1, delta_2)
        path = rubinstein_finite(delta_1, delta_2, rounds)
    except LocalizedError as exc:
        st.error(error_text(exc))
        return
    st.metric(L("seq.rubinstein_share"), f"{share:.4f}")
    fig = go.Figure([go.Scatter(x=list(range(1, rounds + 1)), y=path, mode="lines+markers", name=L("seq.finite")),
                     go.Scatter(x=[1, rounds], y=[share, share], mode="lines", line=dict(dash="dash"),
                                name=L("seq.infinite"))])
    fig.update_layout(xaxis_title=L("seq.rounds"), yaxis_title=L("seq.share_1"), height=320, margin=dict(t=30, b=30))
    st.plotly_chart(fig, width="stretch")
    if 0 < delta_1 < 1 and 0 < delta_2 < 1:
        # Binmore-Rubinstein-Wolinsky: with short periods the Rubinstein split equals the Nash
        # solution with bargaining power log(delta2) / (log(delta1) + log(delta2)).
        power = math.log(delta_2) / (math.log(delta_1) + math.log(delta_2))
        st.caption(F("seq.brw", power=power, nbs=nash_bargaining(1.0, power).share_1, share=share))
