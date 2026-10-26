"""
Games with multidimensional strategies on the Theoretical Model page:
catalogue models (2-D probabilistic voting, multimarket Cournot, two-prize
contest) and a free editor where each agent chooses several variables.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import sympy as sp
import streamlit as st

from theory_engine.multidim import VectorGame, build_vector_game, closed_form_values, solve_vector_equilibrium
from theory_engine.vector_catalogue import VECTOR_CATALOGUE, build_vector
from ui.page_text import F, R, error_text
from ui.theory_page import _parse_outcomes, _parse_parameters    # theory_page imports this page lazily
from utils.i18n import LocalizedError

EDITOR_DEFAULTS = {
    1: dict(name="A", strategies="xA, yA", lower="0", upper="1",
            utility="-((xA - 0.3)^2 + (yA - 0.7)^2) - k*((xA - xB)^2 + (yA - yB)^2)"),
    2: dict(name="B", strategies="xB, yB", lower="0", upper="1",
            utility="-((xB - 0.8)^2 + (yB - 0.4)^2) - k*((xA - xB)^2 + (yA - yB)^2)"),
}


def _catalogue(L) -> tuple[VectorGame, dict[str, float], tuple]:
    key = st.selectbox(L("theory.model"), list(VECTOR_CATALOGUE), key="md_model",
                       format_func=lambda k: R(VECTOR_CATALOGUE[k].label))
    entry = VECTOR_CATALOGUE[key]
    n = st.slider(L("theory.n_agents"), *entry.n_range, entry.n_range[0], key=f"md_n_{key}") if entry.n_range else None
    game = build_vector(key, n)
    cols = st.columns(4)
    values = {name: cols[i % 4].number_input(R(game.parameter_info.get(name, name)), value=float(default),
                                             key=f"md_{key}_{n}_{name}")
              for i, (name, default) in enumerate(game.parameters.items())}
    return game, values, ("cat", key, n, tuple(sorted(values.items())))


def _editor(L) -> tuple[VectorGame, dict[str, float], tuple] | None:
    st.caption(L("md.editor_intro"))
    n_agents = st.number_input(L("theory.n_agents"), 1, 6, 2, key="md_ed_n")
    params_text = st.text_input(L("theory.parameters_input"), "k=0.5", key="md_ed_params")
    agents = []
    for i in range(1, int(n_agents) + 1):
        default = EDITOR_DEFAULTS.get(i, dict(name=F("theory.default_agent", i=i), strategies=f"s{i}, t{i}",
                                              lower="0", upper="1", utility=f"-(s{i} - 0.5)^2 - (t{i} - 0.5)^2"))
        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
        agent = dict(name=c1.text_input(F("theory.agent_label", i=i), default["name"], key=f"md_ed_name_{i}"),
                     strategies=c2.text_input(L("md.strategies"), default["strategies"], key=f"md_ed_strat_{i}"),
                     lower=c3.text_input(L("theory.lower"), default["lower"], key=f"md_ed_lo_{i}"),
                     upper=c4.text_input(L("theory.upper"), default["upper"], key=f"md_ed_hi_{i}"))
        agent["utility"] = st.text_input(F("theory.utility_label", i=i), default["utility"], key=f"md_ed_u_{i}")
        agents.append(agent)
    outcomes_text = st.text_area(L("theory.outcomes_input"), L("md.default_outcome"), key="md_ed_outcomes")
    if st.button(f"🛠️ {L('theory.build')}", key="md_ed_build"):
        try:
            game = build_vector_game(L("theory.custom_name"), _parse_parameters(params_text), agents,
                                     _parse_outcomes(outcomes_text))
        except ValueError as exc:
            st.error(error_text(exc))
        else:
            counter = st.session_state.get("md_ed_counter", 0) + 1
            st.session_state.update(md_ed_counter=counter, md_custom=game)
            st.success(L("theory.built"))
    game = st.session_state.get("md_custom")
    if game is None:
        st.info(L("theory.editor_hint"))
        return None
    return game, dict(game.parameters), ("custom", st.session_state.get("md_ed_counter", 0))


def _show_equations(game: VectorGame, L) -> None:
    st.subheader(R(game.name))
    if game.description:
        st.write(R(game.description))
    for agent in game.agents:
        own = ", ".join(sp.latex(s) for s in agent.strategies)
        st.latex(rf"\max_{{{own}}}\; {sp.latex(agent.utility)}")
    if game.references:
        st.caption(F("md.references", refs=game.references))


def _voting_chart(game: VectorGame, values: dict[str, float], strategies: dict[str, float], L) -> None:
    merged = {**game.parameters, **values}
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[merged[f"bx{g}"] for g in (1, 2, 3)], y=[merged[f"by{g}"] for g in (1, 2, 3)],
                             mode="markers+text", text=[F("md.group", g=g) for g in (1, 2, 3)],
                             textposition="top center", name=L("md.ideal_points"),
                             marker=dict(size=[8 + 0.4 * merged[f"n{g}"] for g in (1, 2, 3)], opacity=0.6)))
    fig.add_trace(go.Scatter(x=[strategies["xA"], strategies["xB"]], y=[strategies["yA"], strategies["yB"]],
                             mode="markers", name=L("md.platforms"), marker=dict(symbol="x", size=16)))
    fig.update_layout(xaxis_title=L("md.issue_1"), yaxis_title=L("md.issue_2"), height=380,
                      margin=dict(t=30, b=30), yaxis=dict(scaleanchor="x"))
    st.plotly_chart(fig, width="stretch")


def render(L) -> None:
    st.caption(L("md.intro"))
    mode = st.radio(L("theory.source"), ["catalogue", "editor"], horizontal=True, key="md_mode",
                    format_func=lambda m: L("theory.catalogue") if m == "catalogue" else L("theory.editor"))
    picked = _catalogue(L) if mode == "catalogue" else _editor(L)
    if picked is None:
        return
    game, values, signature = picked
    _show_equations(game, L)
    if st.button(f"⚖️ {L('md.solve')}", type="primary", key="md_solve"):
        with st.spinner(L("md.solving")):
            try:
                st.session_state["md_result"] = (signature, solve_vector_equilibrium(game, values))
            except LocalizedError as exc:
                st.error(error_text(exc))
                return
    stored = st.session_state.get("md_result")
    if stored is None or stored[0] != signature:           # nothing solved yet for these settings
        return
    result = stored[1]
    st.info(R(result.message))
    try:
        closed = closed_form_values(game, values)
    except LocalizedError:
        closed = None
    for k, eq in enumerate(result.equilibria, start=1):
        if len(result.equilibria) > 1:
            st.markdown(f"**{F('md.equilibrium_n', k=k)}**")
        rows = []
        for agent in game.agents:
            for s in agent.strategies:
                row = {L("seq.col.agent"): R(agent.name), L("seq.col.strategy"): str(s),
                       L("md.col.value"): round(eq.strategies[str(s)], 6)}
                if closed is not None:
                    row[L("md.col.closed_form")] = round(closed[str(s)], 6)
                rows.append(row)
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.dataframe(pd.DataFrame([{L("seq.col.agent"): R(a.name), L("md.col.utility"): round(eq.utilities[a.name], 6)}
                                   for a in game.agents]), width="stretch", hide_index=True)
        if eq.outcomes:
            st.dataframe(pd.DataFrame([{L("seq.col.outcome"): R(name), L("md.col.value"): round(v, 6)}
                                       for name, v in eq.outcomes.items()]), width="stretch", hide_index=True)
        if signature[0] == "cat" and signature[1] == "md_voting":
            _voting_chart(game, values, eq.strategies, L)
    st.caption(L("md.method"))
