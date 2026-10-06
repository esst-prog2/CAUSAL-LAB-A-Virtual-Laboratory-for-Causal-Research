"""
Theoretical Model page (CAUSAL LAB spec: theory-lab-page).

Three steps:
  1. Model                 catalogue or free editor; utilities, first-order
                           conditions and best responses as equations.
  2. Equilibrium & data    parameter sources (manual / column statistic /
                           regression), detected data structure, scope
                           (pooled / per group / per period), equilibrium
                           table, path chart and outcome curve.
  3. Predictions           treatment as a parameter shift, comparative
                           statics, and comparison with a causal estimate.

State lives in `st.session_state.theory`; every widget key carries the
model's signature, so switching models never reuses stale inputs. All
text goes through the i18n layer (keys theory.*, plus the engines'
message keys rendered with `R`).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sympy as sp
import streamlit as st

from theory_engine.calibration import (STATISTICS, CalibrationError, ParameterSource, calibrate,
                                       default_scope, detect_structure, solve_by_scope)
from theory_engine.catalogue import CATALOGUE, build
from theory_engine.game import (Equilibrium, Game, best_responses, build_custom_game, first_order_conditions,
                                solve_equilibrium)
from theory_engine.predictions import compare_with_estimate, delta_from_data, predict_shift
from utils.i18n import LocalizedError, render as render_message, tf

VERDICT_STYLE = {"consistent": st.success, "magnitude differs": st.warning, "sign contradicts": st.error}
VERDICT_KEY = {"consistent": "consistent", "magnitude differs": "magnitude", "sign contradicts": "sign"}


_LANG = "en"   # set at the start of each render; read by format_func closures


def _lang() -> str:
    return _LANG


def F(key: str, **params) -> str:
    return tf(key, _lang(), **params)


def R(message) -> str:
    return render_message(message, _lang())


def _state() -> dict:
    return st.session_state.setdefault("theory", {"signature": None, "game": None})


def _reset_downstream(state: dict) -> None:
    for k in ("values", "baseline", "equilibria", "table", "prediction", "curve", "solve_message"):
        state.pop(k, None)


def _tex_name(name: str) -> str:
    return r"\text{" + name.replace("_", r"\_") + "}"


def _error_text(exc: Exception) -> str:
    return exc.render(_lang()) if isinstance(exc, LocalizedError) else str(exc)


# --------------------------------------------------------------------------
# Step 1 — model
# --------------------------------------------------------------------------
def _parse_parameters(text: str) -> dict[str, float]:
    params: dict[str, float] = {}
    for chunk in [c.strip() for c in text.replace("\n", ",").split(",") if c.strip()]:
        if "=" not in chunk:
            raise ValueError(F("theory.err.param_default", chunk=chunk))
        name, value = (p.strip() for p in chunk.split("=", 1))
        try:
            params[name] = float(value)
        except ValueError:
            raise ValueError(F("theory.err.param_number", name=name)) from None
    return params


def _parse_outcomes(text: str) -> dict[str, str]:
    outcomes = {}
    for line in [l.strip() for l in text.splitlines() if l.strip()]:
        if "=" not in line:
            raise ValueError(F("theory.err.outcome_line", line=line))
        name, expr = (p.strip() for p in line.split("=", 1))
        outcomes[name] = expr
    return outcomes


def _editor_defaults() -> dict[int, dict]:
    return {
        1: dict(name=F("theory.default_lobby", label="A"), strategy="x1", lower="0", upper="V",
                utility="V*x1/(x1+x2) - x1"),
        2: dict(name=F("theory.default_lobby", label="B"), strategy="x2", lower="0", upper="V",
                utility="V*x2/(x1+x2) - x2"),
    }


def _model_step(state: dict, L) -> None:
    mode = st.radio(L("theory.source"), ["catalogue", "editor"], horizontal=True, key="th_mode",
                    format_func=lambda m: L("theory.catalogue") if m == "catalogue" else L("theory.editor"))
    if mode == "catalogue":
        key = st.selectbox(L("theory.model"), list(CATALOGUE), key="th_model",
                           format_func=lambda k: f"{R(CATALOGUE[k].category)} — {R(CATALOGUE[k].label)}")
        entry = CATALOGUE[key]
        n = None
        if entry.n_range:
            n = st.slider(L("theory.n_agents"), entry.n_range[0], entry.n_range[1], entry.n_range[0], key=f"th_n_{key}")
        signature = f"cat:{key}:{n}"
        if state["signature"] != signature:
            state.update(signature=signature, game=build(key, n))
            _reset_downstream(state)
    else:
        defaults = _editor_defaults()
        n_agents = st.number_input(L("theory.n_agents"), 1, 6, 2, key="th_ed_n")
        params_text = st.text_input(L("theory.parameters_input"), "V=10", key="th_ed_params")
        agents = []
        for i in range(1, int(n_agents) + 1):
            default = defaults.get(i, dict(name=F("theory.default_agent", i=i), strategy=f"s{i}", lower="0",
                                           upper="1", utility=f"s{i}"))
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            agent = dict(name=c1.text_input(F("theory.agent_label", i=i), default["name"], key=f"th_ed_name_{i}"),
                         strategy=c2.text_input(L("theory.strategy"), default["strategy"], key=f"th_ed_strat_{i}"),
                         lower=c3.text_input(L("theory.lower"), default["lower"], key=f"th_ed_lo_{i}"),
                         upper=c4.text_input(L("theory.upper"), default["upper"], key=f"th_ed_hi_{i}"))
            agent["utility"] = st.text_input(F("theory.utility_label", i=i), default["utility"], key=f"th_ed_u_{i}")
            agents.append(agent)
        outcomes_text = st.text_area(L("theory.outcomes_input"), L("theory.default_outcome"), key="th_ed_outcomes")
        if st.button(f"🛠️ {L('theory.build')}", key="th_ed_build"):
            try:
                game = build_custom_game(L("theory.custom_name"), _parse_parameters(params_text), agents,
                                         _parse_outcomes(outcomes_text))
            except ValueError as exc:
                st.error(_error_text(exc))
            else:
                state.update(signature=f"custom:{st.session_state.get('th_ed_counter', 0)}", game=game)
                st.session_state["th_ed_counter"] = st.session_state.get("th_ed_counter", 0) + 1
                _reset_downstream(state)
                st.success(L("theory.built"))
        if state["game"] is None or not str(state["signature"]).startswith("custom"):
            st.info(L("theory.editor_hint"))
            return

    _show_equations(state["game"], L)


def _show_equations(game: Game, L) -> None:
    st.subheader(R(game.name))
    if game.description:
        st.write(R(game.description))
    if game.references:
        st.caption(F("theory.references", refs=game.references))

    st.markdown(f"**{L('theory.equations')}**")
    focs = first_order_conditions(game)
    brs = best_responses(game) if focs else {}
    for agent in game.agents:
        s = sp.latex(agent.strategy)
        st.markdown(F("theory.agent_chooses", agent=R(agent.name),
                      space=f"${s} \\in [{sp.latex(agent.lower)},\\ {sp.latex(agent.upper)}]$"))
        st.latex(rf"U_{{{_tex_name(R(agent.name))}}} = {sp.latex(agent.utility)}")
        if focs:
            st.latex(rf"\frac{{\partial U}}{{\partial {s}}} = {sp.latex(focs[agent.name])} = 0")
            roots = brs.get(agent.name)
            if roots:
                st.latex(rf"BR({s}) \in \left\{{ {', '.join(sp.latex(r) for r in roots)} \right\}}")
            else:
                st.caption(L("theory.no_closed_br"))
    if not focs:
        st.caption(L("theory.non_smooth"))
    if game.closed_form:
        st.markdown(f"**{L('theory.closed_form')}**")
        for k, expr in game.closed_form.items():
            st.latex(rf"{sp.latex(sp.Symbol(k))}^* = {sp.latex(expr)}")
    if game.outcomes:
        st.markdown(f"**{L('theory.outcomes')}**")
        for k, expr in game.outcomes.items():
            st.latex(rf"{_tex_name(R(k))} = {sp.latex(expr)}")
    st.dataframe(pd.DataFrame([{L("theory.col.parameter"): k, L("theory.col.default"): v,
                                L("theory.col.meaning"): R(game.parameter_info.get(k, ""))}
                               for k, v in game.parameters.items()]), width="stretch", hide_index=True)


# --------------------------------------------------------------------------
# Step 2 — equilibrium & data
# --------------------------------------------------------------------------
def _data_sources(L) -> dict[str, pd.DataFrame]:
    sources: dict[str, pd.DataFrame] = {}
    lab = st.session_state.get("uploaded_df")
    if lab is None:
        lab = st.session_state.get("virtual_df")
    if lab is not None:
        sources[L("theory.source_virtual_lab")] = lab
    for method, data in st.session_state.get("method_data", {}).items():
        if data.get("df") is not None:
            sources[F("theory.source_methods", method=L(f"method.{method}"))] = data["df"]
    return sources


def _pick_dataset(state: dict, sig: str, L) -> pd.DataFrame | None:
    sources = _data_sources(L)
    options = ["none"] + list(sources) + ["upload"]
    labels = {"none": L("theory.no_data"), "upload": L("theory.upload")}
    choice = st.selectbox(L("theory.data_source"), options, key=f"th_{sig}_data",
                          format_func=lambda o: labels.get(o, o))
    if choice == "none":
        return None
    if choice == "upload":
        uploaded = st.file_uploader("CSV", type=["csv"], key=f"th_{sig}_upload")
        if uploaded is None:
            return None
        if state.get("upload_id") != uploaded.file_id:
            try:
                state["upload_df"] = pd.read_csv(uploaded)
                state["upload_id"] = uploaded.file_id
            except Exception as exc:
                st.error(F("common.read_error", error=exc))
                return None
        return state.get("upload_df")
    return sources[choice]


def _source_widgets(game: Game, df: pd.DataFrame | None, sig: str, L) -> dict[str, ParameterSource]:
    numeric_cols = [] if df is None else [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    all_cols = [] if df is None else list(df.columns)
    kinds = ["manual"] if df is None else ["manual", "statistic", "regression"]
    all_rows = "__all__"
    sources = {}
    for name, default in game.parameters.items():
        p = f"th_{sig}_src_{name}"
        cols = st.columns([1.2, 1, 1.2, 1.2, 1.2])
        cols[0].markdown(f"**{name}**  \n<small>{R(game.parameter_info.get(name, ''))}</small>",
                         unsafe_allow_html=True)
        kind = cols[1].selectbox(L("theory.src.kind"), kinds, key=f"{p}_kind", label_visibility="collapsed",
                                 format_func=lambda k: L(f"theory.src.{k}"))
        if kind == "manual":
            sources[name] = ParameterSource("manual", value=cols[2].number_input(
                L("theory.src.value"), value=float(default), key=f"{p}_value", format="%.4f",
                label_visibility="collapsed"))
        elif kind == "statistic":
            stat = cols[2].selectbox(L("theory.src.statistic"), STATISTICS, key=f"{p}_stat",
                                     label_visibility="collapsed", format_func=lambda s: L(f"stat.{s}"))
            column = cols[3].selectbox(L("theory.src.column"), numeric_cols or ["—"], key=f"{p}_col",
                                       label_visibility="collapsed")
            fcol = cols[4].selectbox(L("theory.src.filter"), [all_rows] + all_cols, key=f"{p}_fcol",
                                     label_visibility="collapsed",
                                     format_func=lambda c: L("theory.src.all_rows") if c == all_rows else c)
            fval = None
            if fcol != all_rows:
                values = sorted(df[fcol].dropna().astype(str).unique().tolist())
                fval = cols[4].selectbox(L("theory.src.equals"), values, key=f"{p}_fval")
            sources[name] = ParameterSource("statistic", statistic=stat, column=column,
                                            filter_column=None if fcol == all_rows else fcol, filter_value=fval)
        else:
            y = cols[2].selectbox("y", numeric_cols or ["—"], key=f"{p}_y")
            x = cols[3].selectbox("x", numeric_cols or ["—"], key=f"{p}_x")
            coef = cols[4].selectbox(L("theory.src.coefficient"), ["slope", "intercept"], key=f"{p}_coef",
                                     format_func=lambda c: L(f"coef.{c}"))
            sources[name] = ParameterSource("regression", y=y, x=x, coefficient=coef)
    return sources


def _variable_label(game: Game, key: str) -> str:
    """Display name of an equilibrium variable (strategy symbol or outcome)."""
    for outcome in game.outcomes:
        if str(outcome) == str(key):
            return R(outcome)
    return str(key)


def _equilibrium_table(eq: Equilibrium, L) -> pd.DataFrame:
    col_var, col_kind, col_value = L("theory.col.variable"), L("theory.col.kind"), L("theory.col.value")
    rows = [{col_var: k, col_kind: L("theory.kind.strategy"), col_value: v} for k, v in eq.strategies.items()]
    rows += [{col_var: R(k), col_kind: L("theory.kind.utility"), col_value: v} for k, v in eq.utilities.items()]
    rows += [{col_var: R(k), col_kind: L("theory.kind.outcome"), col_value: v} for k, v in eq.outcomes.items()]
    return pd.DataFrame(rows)


def _translate_unit_table(game: Game, table: pd.DataFrame, L) -> pd.DataFrame:
    shown = table.copy()
    if "status" in shown:
        shown["status"] = shown["status"].map(lambda s: R(s) if isinstance(s, str) else s)

    def rename(col: str) -> str:
        if col.startswith("param:"):
            return F("theory.col.param", name=col[6:])
        if col.startswith("strategy:"):
            return F("theory.col.strategy", name=col[9:])
        if col.startswith("outcome:"):
            return _variable_label(game, col[8:])
        return L(f"theory.col.{col}")

    return shown.rename(columns=rename)


def _series_label(game: Game, col: str) -> str:
    return F("theory.col.strategy", name=col[9:]) if col.startswith("strategy:") else _variable_label(game, col[8:])


def _equilibrium_step(state: dict, L) -> None:
    game: Game | None = state.get("game")
    if game is None:
        st.info(L("theory.need_model"))
        return
    sig = state["signature"].replace(":", "_")
    df = _pick_dataset(state, sig, L)
    state["df"] = df

    scope, scope_col = "pooled", None
    none = "__none__"
    if df is not None:
        cols = list(df.columns)
        c1, c2 = st.columns(2)
        unit_col = c1.selectbox(L("theory.unit_column"), [none] + cols, key=f"th_{sig}_unit",
                                index=(cols.index("unit") + 1) if "unit" in cols else 0,
                                format_func=lambda c: L("theory.none_option") if c == none else c)
        period_col = c2.selectbox(L("theory.period_column"), [none] + cols, key=f"th_{sig}_period",
                                  index=(cols.index("period") + 1) if "period" in cols else 0,
                                  format_func=lambda c: L("theory.none_option") if c == none else c)
        unit_col = None if unit_col == none else unit_col
        period_col = None if period_col == none else period_col
        structure = detect_structure(df, unit_col, period_col)
        st.info(F("theory.structure_info", label=L("theory.structure"), structure=L(f"structure.{structure}"),
                  rows=len(df)))
        scopes = ["pooled", "group", "period"] if period_col else ["pooled", "group"]
        default = default_scope(structure)
        scope = st.radio(L("theory.scope"), scopes, horizontal=True, key=f"th_{sig}_scope",
                         index=scopes.index(default) if default in scopes else 0,
                         format_func=lambda s: L(f"theory.scope.{s}"))
        if scope == "group":
            scope_col = st.selectbox(L("theory.group_column"), [c for c in cols if c != period_col],
                                     key=f"th_{sig}_group")
        elif scope == "period":
            scope_col = period_col

    st.markdown(f"**{L('theory.parameter_sources')}**")
    sources = _source_widgets(game, df, sig, L)

    if st.button(f"⚖️ {L('theory.solve')}", type="primary", key=f"th_{sig}_solve"):
        _reset_downstream(state)
        try:
            values = calibrate(df, sources)
            result = solve_equilibrium(game, values)
            state.update(values=values, sources=sources, solve_message=result.message,
                         equilibria=result.equilibria)
            if scope != "pooled" and df is not None:
                with st.spinner(L("theory.solving_units")):
                    state["table"] = solve_by_scope(game, df, sources, scope, scope_col)
                    state["table_scope"] = scope
        except (CalibrationError, ValueError) as exc:
            st.error(_error_text(exc))

    if "values" not in state:
        return
    st.caption(F("theory.calibrated", values=", ".join(
        f"{k} = {v:.4g} [{R(state['sources'][k].describe())}]" for k, v in state["values"].items())))
    equilibria = state.get("equilibria") or []
    (st.success if equilibria else st.error)(R(state["solve_message"]))
    if equilibria:
        idx = 0
        if len(equilibria) > 1:
            idx = st.selectbox(L("theory.eq_for_predictions"), range(len(equilibria)), key=f"th_{sig}_eqidx",
                               format_func=lambda i: F("theory.eq_number", i=i + 1))
        eq = equilibria[idx]
        state["baseline"] = eq
        st.dataframe(_equilibrium_table(eq, L).round(6), width="stretch", hide_index=True)
        method = L("theory.method.closed") if eq.method == "closed form" else L("theory.method.numeric")
        st.caption(F("theory.method_caption", method=method, gain=eq.max_gain))

    table = state.get("table")
    if table is not None:
        st.markdown(f"**{L('theory.by_unit')}**")
        st.dataframe(_translate_unit_table(game, table, L), width="stretch", hide_index=True)
        value_cols = [c for c in table.columns if c.startswith(("strategy:", "outcome:"))]
        if value_cols:
            shown = st.multiselect(L("theory.plot"), value_cols, default=value_cols[: min(3, len(value_cols))],
                                   key=f"th_{sig}_pathcols", format_func=lambda c: _series_label(game, c))
            fig = go.Figure()
            for c in shown:
                if state.get("table_scope") == "period":
                    fig.add_trace(go.Scatter(x=table["unit"], y=table[c], mode="lines+markers",
                                             name=_series_label(game, c)))
                else:
                    fig.add_trace(go.Bar(x=table["unit"].astype(str), y=table[c], name=_series_label(game, c)))
            fig.update_layout(height=380, xaxis_title=scope_col, title=L("theory.by_unit_chart"))
            st.plotly_chart(fig, width="stretch")

    if state.get("baseline") is not None:
        _outcome_curve(state, game, sig, L)


def _outcome_curve(state: dict, game: Game, sig: str, L) -> None:
    st.markdown(f"**{L('theory.curve')}**")
    base = state["baseline"]
    variables = list(base.strategies) + list(base.outcomes)
    c1, c2 = st.columns(2)
    var = c1.selectbox(L("theory.eq_variable"), variables, key=f"th_{sig}_curve_var",
                       format_func=lambda v: _variable_label(game, v))
    param = c2.selectbox(L("theory.parameter"), list(game.parameters), key=f"th_{sig}_curve_param")
    if st.button(L("theory.plot_curve"), key=f"th_{sig}_curve_btn"):
        theta = state["values"][param]
        span = 0.5 * abs(theta) if theta else 1.0
        grid = np.linspace(theta - span, theta + span, 21)
        ys, start = [], base.strategies
        for g in grid:
            try:
                res = solve_equilibrium(game, {**state["values"], param: g}, start=start)
            except ValueError:
                res = None
            if res is None or not res.found:
                ys.append(np.nan)
                continue
            eq = res.equilibria[0]
            start = eq.strategies
            ys.append({**eq.strategies, **eq.outcomes}[var])
        state["curve"] = (param, var, grid, ys, theta)
    if state.get("curve"):
        param, var, grid, ys, theta = state["curve"]
        label = _variable_label(game, var)
        fig = go.Figure(go.Scatter(x=grid, y=ys, mode="lines+markers"))
        fig.add_vline(x=theta, line_dash="dot", line_color="gray", annotation_text=L("theory.calibrated_mark"))
        fig.update_layout(height=340, xaxis_title=param, yaxis_title=label,
                          title=F("theory.curve_title", variable=label, parameter=param))
        st.plotly_chart(fig, width="stretch")


# --------------------------------------------------------------------------
# Step 3 — predictions
# --------------------------------------------------------------------------
def _causal_estimates(L) -> dict[str, tuple[float, float, float]]:
    out = {}
    for method, data in st.session_state.get("method_data", {}).items():
        r = data.get("result")
        if r is not None and r.ci_low is not None:
            out[f"{L(f'method.{method}')} — {R(r.estimand)}"] = (r.estimate, r.ci_low, r.ci_high)
    return out


def _predictions_step(state: dict, L) -> None:
    game: Game | None = state.get("game")
    if game is None or state.get("baseline") is None:
        st.info(L("theory.need_equilibrium"))
        return
    sig = state["signature"].replace(":", "_")
    df = state.get("df")
    c1, c2 = st.columns(2)
    param = c1.selectbox(L("theory.shifted_parameter"), list(game.parameters), key=f"th_{sig}_pred_param")
    modes = ["manual"] + (["data"] if df is not None else [])
    mode = c2.radio(L("theory.delta_source"), modes, horizontal=True, key=f"th_{sig}_pred_mode",
                    format_func=lambda m: L(f"theory.delta.{m}"))
    delta = None
    if mode == "manual":
        delta = st.number_input("Δ", value=1.0, key=f"th_{sig}_pred_delta", format="%.4f")
    else:
        treat_col = st.selectbox(L("theory.treatment_column"), list(df.columns),
                                 index=list(df.columns).index("D") if "D" in df.columns else 0,
                                 key=f"th_{sig}_pred_treat")
        try:
            delta = delta_from_data(df, state["sources"][param], treat_col, param)
            st.info(F("theory.delta_measured", delta=delta, source=R(state["sources"][param].describe())))
        except CalibrationError as exc:
            st.error(_error_text(exc))

    if delta is not None and st.button(f"🔮 {L('theory.predict')}", type="primary", key=f"th_{sig}_pred_btn"):
        try:
            state["prediction"] = predict_shift(game, state["values"], param, float(delta), state["baseline"])
        except ValueError as exc:
            st.error(_error_text(exc))
            state.pop("prediction", None)

    pred = state.get("prediction")
    if pred is None:
        return
    rows = []
    for k in pred.effects:
        base = {**pred.baseline.strategies, **pred.baseline.outcomes}[k]
        shifted = {**pred.shifted.strategies, **pred.shifted.outcomes}[k]
        rows.append({L("theory.col.variable"): _variable_label(game, k), L("theory.col.baseline"): base,
                     L("theory.col.after_shift"): shifted, L("theory.col.predicted_effect"): pred.effects[k],
                     f"d/d{pred.parameter}": pred.derivatives.get(k, np.nan)})
    st.markdown(f"**{F('theory.prediction_title', parameter=pred.parameter, delta=pred.delta)}**")
    st.dataframe(pd.DataFrame(rows).round(6), width="stretch", hide_index=True)

    st.markdown(f"**{L('theory.compare')}**")
    variable = st.selectbox(L("theory.predicted_variable"), list(pred.effects), key=f"th_{sig}_cmp_var",
                            format_func=lambda v: _variable_label(game, v))
    estimates = _causal_estimates(L)
    choice = st.selectbox(L("theory.causal_estimate"), list(estimates) + ["manual"], key=f"th_{sig}_cmp_src",
                          format_func=lambda o: L("theory.enter_manually") if o == "manual" else o)
    if choice == "manual":
        c1, c2, c3 = st.columns(3)
        est = c1.number_input(L("common.estimate"), value=0.0, key=f"th_{sig}_cmp_est", format="%.4f")
        lo = c2.number_input(L("theory.ci_low"), value=-1.0, key=f"th_{sig}_cmp_lo", format="%.4f")
        hi = c3.number_input(L("theory.ci_high"), value=1.0, key=f"th_{sig}_cmp_hi", format="%.4f")
    else:
        est, lo, hi = estimates[choice]
    predicted = pred.effects[variable]
    verdict = compare_with_estimate(predicted, est, lo, hi)
    VERDICT_STYLE[verdict](F("theory.verdict_text", label=L("theory.verdict"),
                             verdict=L(f"theory.verdict.{VERDICT_KEY[verdict]}"),
                             variable=_variable_label(game, variable), predicted=predicted, est=est, lo=lo, hi=hi))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[est], y=[L("theory.causal_estimate")], mode="markers", marker=dict(size=12),
                             error_x=dict(type="data", symmetric=False, array=[hi - est], arrayminus=[est - lo])))
    fig.add_trace(go.Scatter(x=[predicted], y=[L("theory.prediction")], mode="markers",
                             marker=dict(size=14, symbol="diamond")))
    fig.add_vline(x=0, line_dash="dot", line_color="gray")
    fig.update_layout(height=240, showlegend=False, xaxis_title=L("methods.effect"))
    st.plotly_chart(fig, width="stretch")
    st.caption(L("theory.same_units"))


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------
def render(L) -> None:
    global _LANG
    _LANG = st.session_state.get("lang", "en")
    st.title(f"🧮 {L('theory.title')}")
    st.caption(L("theory.intro"))
    state = _state()
    tab1, tab2, tab3 = st.tabs([L("theory.tab_model"), L("theory.tab_equilibrium"), L("theory.tab_predictions")])
    with tab1:
        _model_step(state, L)
    with tab2:
        _equilibrium_step(state, L)
    with tab3:
        _predictions_step(state, L)
