"""
Structural estimation on the Theoretical Model page: the logit QRE
precision of a matrix game by maximum likelihood, and the parameters of a
continuous game by GMM on its first-order conditions
(theory_engine/estimation.py).
"""
from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from theory_engine.estimation import LEVEL, fit_logit_qre, gmm_first_order_conditions
from theory_engine.finite_games import BimatrixGame
from theory_engine.game import Game
from ui.page_text import F, R, error_text, references_caption
from utils.i18n import LocalizedError


def _fmt(value: float | None, digits: int = 4) -> str:
    if value is None:
        return "—"
    return "∞" if np.isinf(value) else f"{value:.{digits}f}"


# --------------------------------------------------------------------------
# Logit QRE by maximum likelihood (matrix games)
# --------------------------------------------------------------------------
def _counts_from_data(game: BimatrixGame, L) -> tuple[np.ndarray, np.ndarray] | None:
    from ui.theory_page import _data_sources
    sources = _data_sources(L)
    if not sources:
        st.info(L("est.no_dataset"))
        return None
    name = st.selectbox(L("theory.data_source"), list(sources), key="mx_est_data")
    df = sources[name]
    c1, c2 = st.columns(2)
    row_col = c1.selectbox(F("est.choice_column", player=R(game.row_player)), list(df.columns), key="mx_est_rcol")
    col_col = c2.selectbox(F("est.choice_column", player=R(game.col_player)), list(df.columns), key="mx_est_ccol")
    counts, ignored = [], 0
    for column, actions in ((row_col, game.row_actions), (col_col, game.col_actions)):
        labels = [str(R(a)).strip().lower() for a in actions]
        values = df[column].dropna().astype(str).str.strip().str.lower()
        counts.append(np.array([(values == label).sum() for label in labels], dtype=float))
        ignored += int((~values.isin(labels)).sum())
    if ignored:
        st.warning(F("est.ignored_choices", n=ignored))
    return counts[0], counts[1]


def _typed_counts(game: BimatrixGame, shape: str, L) -> tuple[np.ndarray, np.ndarray]:
    out = []
    for player, actions, tag in ((game.row_player, game.row_actions, "r"), (game.col_player, game.col_actions, "c")):
        st.markdown(f"**{F('est.counts_of', player=R(player))}**")
        cols = st.columns(len(actions))
        out.append(np.array([cols[i].number_input(R(a), min_value=0, value=0, step=1, key=f"mx_est_{tag}{i}_{shape}")
                             for i, a in enumerate(actions)], dtype=float))
    return out[0], out[1]


def render_qre_estimation(game: BimatrixGame, L) -> None:
    st.subheader(L("est.qre_title"))
    st.caption(L("est.qre_intro"))
    shape = f"{len(game.row_actions)}x{len(game.col_actions)}"
    mode = st.radio(L("est.counts_source"), ["typed", "data"], horizontal=True, key="mx_est_mode",
                    format_func=lambda m: L(f"est.counts.{m}"))
    counts = _typed_counts(game, shape, L) if mode == "typed" else _counts_from_data(game, L)
    if counts is None:
        return
    digest = hashlib.sha1(np.r_[game.row_payoffs.ravel(), game.col_payoffs.ravel(), *counts].tobytes()).hexdigest()
    if st.button(f"📐 {L('est.qre_run')}", key="mx_est_run"):
        try:
            with st.spinner(L("est.running")):
                st.session_state["mx_est"] = (digest, fit_logit_qre(game, *counts))
        except LocalizedError as exc:
            st.error(error_text(exc))
            return
    stored = st.session_state.get("mx_est")
    if stored is None or stored[0] != digest:
        return
    fit = stored[1]
    a, b, c, d = st.columns(4)
    if fit.at_bound:
        a.metric("λ", F("est.at_least", value=_fmt(fit.ci_low, 3)))
        st.warning(L("est.qre_at_bound"))
    else:
        a.metric("λ", _fmt(fit.lam))
        b.metric(L("est.se"), _fmt(fit.se))
        c.metric(F("est.ci", level=int(LEVEL * 100)), f"[{_fmt(fit.ci_low, 3)}, {_fmt(fit.ci_high, 3)}]")
    d.metric(L("est.loglik"), _fmt(fit.log_likelihood, 3))
    st.caption(F("est.qre_vs_random", lr=fit.lr_random, p=fit.p_random, n=fit.n_obs))
    rows = []
    for player, actions, fitted, observed in ((game.row_player, game.row_actions, fit.row, counts[0]),
                                              (game.col_player, game.col_actions, fit.col, counts[1])):
        total = observed.sum()
        for action, p, k in zip(actions, fitted, observed):
            rows.append({L("est.col.player"): R(player), L("est.col.action"): R(action),
                         L("est.col.observed"): round(k / total, 4) if total else None,
                         L("est.col.fitted"): round(float(p), 4)})
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    lams, values = zip(*fit.curve)
    fig = go.Figure([go.Scatter(x=lams, y=values, mode="lines", name=L("est.loglik"))])
    fig.add_hline(y=fit.log_likelihood - 1.920729, line=dict(dash="dot"),
                  annotation_text=F("est.ci", level=int(LEVEL * 100)))
    fig.add_vline(x=fit.lam, line=dict(dash="dash"))
    fig.update_layout(xaxis_title="λ", yaxis_title=L("est.loglik"), height=320, margin=dict(t=30, b=30))
    st.plotly_chart(fig, width="stretch")
    st.caption(L("est.qre_method"))
    references_caption("qre")


# --------------------------------------------------------------------------
# GMM on first-order conditions (continuous games)
# --------------------------------------------------------------------------
ROLES = ("fixed", "observed", "estimate")


def render_gmm(state: dict, L) -> None:
    from ui.theory_page import _pick_dataset
    game: Game | None = state.get("game")
    if game is None:
        st.info(L("theory.need_model"))
        return
    st.caption(L("est.gmm_intro"))
    if not game.smooth:
        st.info(L("est.gmm_not_smooth"))
        return
    sig = state["signature"].replace(":", "_") + "_est"
    df = _pick_dataset(state, sig, L)
    if df is None:
        st.info(L("est.gmm_need_data"))
        return
    numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if not numeric:
        st.error(L("est.no_numeric"))
        return

    st.markdown(f"**{L('est.strategies_title')}**")
    cols = st.columns(min(4, len(game.agents)))
    strategy_columns = {}
    for i, agent in enumerate(game.agents):
        s = str(agent.strategy)
        default = numeric.index(s) if s in numeric else min(i, len(numeric) - 1)
        strategy_columns[s] = cols[i % len(cols)].selectbox(F("est.strategy_column", strategy=s, agent=R(agent.name)),
                                                            numeric, index=default, key=f"th_{sig}_s_{s}")

    st.markdown(f"**{L('est.parameters_title')}**")
    estimate, observed, fixed = {}, {}, {}
    for name, default in game.parameters.items():
        c = st.columns([1.3, 1, 1.3])
        c[0].markdown(f"**{name}**  \n<small>{R(game.parameter_info.get(name, ''))}</small>", unsafe_allow_html=True)
        role = c[1].selectbox(L("est.role"), ROLES, index=2, key=f"th_{sig}_role_{name}",
                              label_visibility="collapsed", format_func=lambda r: L(f"est.role.{r}"))
        if role == "observed":
            observed[name] = c[2].selectbox(L("theory.src.column"), numeric, key=f"th_{sig}_col_{name}",
                                            label_visibility="collapsed")
        else:
            value = c[2].number_input(L(f"est.value.{role}"), value=float(default), key=f"th_{sig}_val_{role}_{name}",
                                      format="%.4f")
            (estimate if role == "estimate" else fixed)[name] = value

    c1, c2 = st.columns(2)
    agents = c1.multiselect(L("est.agents"), list(range(len(game.agents))), default=list(range(len(game.agents))),
                            format_func=lambda i: R(game.agents[i].name), key=f"th_{sig}_agents")
    taken = set(strategy_columns.values())
    instruments = c2.multiselect(L("est.instruments"), [c for c in numeric if c not in taken], key=f"th_{sig}_iv")
    st.caption(F("est.moment_count", moments=len(agents) * (1 + len(instruments)), parameters=len(estimate)))

    run_sig = (sig, tuple(sorted(strategy_columns.items())), tuple(sorted(estimate.items())),
               tuple(sorted(observed.items())), tuple(sorted(fixed.items())), tuple(agents), tuple(instruments), id(df))
    if st.button(f"📐 {L('est.gmm_run')}", type="primary", key=f"th_{sig}_run"):
        try:
            with st.spinner(L("est.running")):
                fit = gmm_first_order_conditions(game, df, strategy_columns, estimate, instruments,
                                                 observed=observed, fixed=fixed, agents=agents)
            state["gmm"] = (run_sig, fit)
        except LocalizedError as exc:
            st.error(error_text(exc))
            return
    stored = state.get("gmm")
    if stored is None or stored[0] != run_sig:
        return
    fit = stored[1]
    if not fit.converged:
        st.warning(L("est.not_converged"))
    level = int(LEVEL * 100)
    st.dataframe(pd.DataFrame([{L("est.col.parameter"): name, L("est.col.estimate"): round(float(v), 6),
                                L("est.se"): round(float(s), 6),
                                F("est.col.ci_low", level=level): round(float(lo), 6),
                                F("est.col.ci_high", level=level): round(float(hi), 6)}
                               for name, v, s, lo, hi in zip(fit.names, fit.estimates, fit.se, fit.ci_low,
                                                             fit.ci_high)]), width="stretch", hide_index=True)
    st.caption(F("est.gmm_sample", n=fit.n, dropped=fit.n_dropped, moments=fit.n_moments))
    if fit.j_stat is None:
        st.info(L("est.j_exact"))
    elif fit.j_p < 0.05:
        st.warning(F("est.j_reject", j=fit.j_stat, df=fit.j_df, p=fit.j_p))
    else:
        st.success(F("est.j_ok", j=fit.j_stat, df=fit.j_df, p=fit.j_p))
    st.caption(L("est.gmm_method"))
    references_caption("gmm")
