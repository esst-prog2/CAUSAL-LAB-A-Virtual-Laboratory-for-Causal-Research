"""
Matrix games on the Theoretical Model page: catalogue or free payoff
matrices, every Nash equilibrium (pure and mixed), and the logit quantal
response equilibrium path, and the estimate of its precision lambda from
observed choices (ui/estimation_page.py).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from theory_engine.finite_games import MAX_ACTIONS, BimatrixGame, logit_qre, matrix_catalogue, nash_equilibria
from theory_engine.optimization import mangasarian_stone, zero_sum_solution
from ui.page_text import F, R, error_text, references_caption
from utils.i18n import LocalizedError
from utils.references import cite


def _labels(text: str, fallback: str) -> list[str]:
    names = [t.strip() for t in text.split(",") if t.strip()]
    return names or [fallback]


def _custom_game(L) -> BimatrixGame | None:
    c1, c2 = st.columns(2)
    rows = _labels(c1.text_input(L("matrix.row_actions"), "Up, Down", key="mx_rows"), "Up")[:MAX_ACTIONS]
    cols = _labels(c2.text_input(L("matrix.col_actions"), "Left, Right", key="mx_cols"), "Left")[:MAX_ACTIONS]
    st.caption(F("matrix.editor_hint", maximum=MAX_ACTIONS))
    shape_key = f"{len(rows)}x{len(cols)}"
    blank = pd.DataFrame(np.zeros((len(rows), len(cols))), index=rows, columns=cols)
    c1, c2 = st.columns(2)
    c1.markdown(f"**{L('matrix.row_payoffs')}**")
    a = c1.data_editor(blank, key=f"mx_a_{shape_key}", width="stretch")
    c2.markdown(f"**{L('matrix.col_payoffs')}**")
    b = c2.data_editor(blank, key=f"mx_b_{shape_key}", width="stretch")
    try:
        return BimatrixGame(L("matrix.custom_name"), rows, cols, a.to_numpy(float), b.to_numpy(float),
                            L("matrix.row_player_default"), L("matrix.col_player_default"))
    except (LocalizedError, ValueError) as exc:
        st.error(error_text(exc))
        return None


def _payoff_table(game: BimatrixGame) -> pd.DataFrame:
    cells = [[f"{game.row_payoffs[i, j]:g} , {game.col_payoffs[i, j]:g}" for j in range(len(game.col_actions))]
             for i in range(len(game.row_actions))]
    return pd.DataFrame(cells, index=[R(r) for r in game.row_actions], columns=[R(c) for c in game.col_actions])


def _mix(probabilities: np.ndarray, actions) -> str:
    return ", ".join(f"{R(a)} {p:.3f}" for a, p in zip(actions, probabilities) if p > 1e-12)


def _optimisation(game: BimatrixGame, n_enumerated: int, L) -> None:
    """Equilibria as the solutions of the Mangasarian-Stone quadratic program, and
    the linear program of a zero-sum game (theory_engine/optimization.py)."""
    st.subheader(L("matrix.opt_title"))
    st.caption(L("matrix.opt_intro"))
    st.latex(r"\max_{x,\,y,\,p,\,q}\; x^\top (A+B)\, y - p - q \quad \text{s.t.}\quad A y \le p\,\mathbf{1},\;"
             r" B^\top x \le q\,\mathbf{1},\; x \in \Delta_m,\; y \in \Delta_n")
    qp = mangasarian_stone(game)
    if qp.equilibria:
        st.dataframe(pd.DataFrame([{
            R(game.row_player): _mix(e.row, game.row_actions),
            R(game.col_player): _mix(e.col, game.col_actions),
            F("matrix.col.payoff", player=R(game.row_player)): round(e.row_payoff, 4),
            F("matrix.col.payoff", player=R(game.col_player)): round(e.col_payoff, 4),
            L("matrix.opt.objective"): f"{e.objective:.1e}",
            L("matrix.opt.gain"): f"{e.gain:.1e}",
        } for e in qp.equilibria]), width="stretch", hide_index=True)
    st.caption(F("matrix.opt_summary", found=len(qp.equilibria), enumerated=n_enumerated, converged=qp.converged,
                 starts=qp.starts))
    zs = zero_sum_solution(game)
    if zs is not None:
        st.markdown(f"**{L('matrix.zs_title')}**")
        st.latex(r"v = \max_{x \in \Delta_m} \min_{j}\, (x^\top A)_j = \min_{y \in \Delta_n} \max_{i}\, (A y)_i")
        st.markdown(F("matrix.zs_result", value=zs.value, row=_mix(zs.row, game.row_actions),
                      col=_mix(zs.col, game.col_actions), row_player=R(game.row_player),
                      col_player=R(game.col_player)))
    references_caption("mangasarian_stone", "zero_sum_lp")


def render(L) -> None:
    source = st.radio(L("theory.source"), ["catalogue", "editor"], horizontal=True, key="mx_source",
                      format_func=lambda m: L("theory.catalogue") if m == "catalogue" else L("theory.editor"))
    if source == "catalogue":
        catalogue = matrix_catalogue()
        key = st.selectbox(L("theory.model"), list(catalogue), format_func=lambda k: R(catalogue[k].name),
                           key="mx_model")
        game = catalogue[key]
        st.caption(R(game.description))
        if game.references:
            st.caption(F("theory.references", refs=cite(*game.references)))
    else:
        game = _custom_game(L)
        if game is None:
            return

    st.markdown(f"**{F('matrix.payoffs_title', row=R(game.row_player), col=R(game.col_player))}**")
    st.dataframe(_payoff_table(game), width="stretch")

    equilibria = nash_equilibria(game)
    st.subheader(L("matrix.equilibria"))
    st.caption(F("matrix.n_equilibria", n=len(equilibria)))
    st.dataframe(pd.DataFrame([{
        L("matrix.col.kind"): L("matrix.pure") if e.pure else L("matrix.mixed"),
        R(game.row_player): _mix(e.row, game.row_actions),
        R(game.col_player): _mix(e.col, game.col_actions),
        F("matrix.col.payoff", player=R(game.row_player)): round(e.row_payoff, 4),
        F("matrix.col.payoff", player=R(game.col_player)): round(e.col_payoff, 4),
    } for e in equilibria]), width="stretch", hide_index=True)
    st.caption(L("matrix.method_note"))
    references_caption("nash_enumeration", "qre")
    _optimisation(game, len(equilibria), L)

    st.subheader(L("matrix.qre_title"))
    st.caption(L("matrix.qre_intro"))
    lam_max = st.slider(L("matrix.qre_lambda"), 0.5, 50.0, 10.0, 0.5, key="mx_lam")
    grid = np.linspace(0, lam_max, 60)
    try:
        path = [logit_qre(game, lam) for lam in grid]
    except LocalizedError as exc:
        st.error(error_text(exc))
        return
    fig = go.Figure()
    for i, action in enumerate(game.row_actions):
        fig.add_trace(go.Scatter(x=grid, y=[p[0][i] for p in path], mode="lines",
                                 name=f"{R(game.row_player)}: {R(action)}"))
    for j, action in enumerate(game.col_actions):
        fig.add_trace(go.Scatter(x=grid, y=[p[1][j] for p in path], mode="lines", line=dict(dash="dash"),
                                 name=f"{R(game.col_player)}: {R(action)}"))
    fig.update_layout(xaxis_title="λ", yaxis_title=L("matrix.probability"), height=380, margin=dict(t=30, b=30))
    st.plotly_chart(fig, width="stretch")
    st.caption(L("matrix.qre_branch_note"))

    from ui.estimation_page import render_qre_estimation
    render_qre_estimation(game, L)
