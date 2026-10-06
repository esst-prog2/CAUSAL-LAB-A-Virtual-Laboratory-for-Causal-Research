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
model's signature, so switching models never reuses stale inputs.
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

DEFAULT_EDITOR_AGENT = {
    1: dict(name="Lobby A", strategy="x1", lower="0", upper="V", utility="V*x1/(x1+x2) - x1"),
    2: dict(name="Lobby B", strategy="x2", lower="0", upper="V", utility="V*x2/(x1+x2) - x2"),
}
VERDICT_STYLE = {"consistent": st.success, "magnitude differs": st.warning, "sign contradicts": st.error}


def _state() -> dict:
    return st.session_state.setdefault("theory", {"signature": None, "game": None})


def _reset_downstream(state: dict) -> None:
    for k in ("values", "baseline", "equilibria", "table", "prediction", "curve", "solve_message"):
        state.pop(k, None)


def _tex_name(name: str) -> str:
    return r"\text{" + name.replace("_", r"\_") + "}"


# --------------------------------------------------------------------------
# Step 1 — model
# --------------------------------------------------------------------------
def _parse_parameters(text: str) -> dict[str, float]:
    params: dict[str, float] = {}
    for chunk in [c.strip() for c in text.replace("\n", ",").split(",") if c.strip()]:
        if "=" not in chunk:
            raise ValueError(f"Parameter '{chunk}' needs a default value, e.g. {chunk}=1.")
        name, value = (p.strip() for p in chunk.split("=", 1))
        try:
            params[name] = float(value)
        except ValueError:
            raise ValueError(f"Default value of parameter '{name}' must be a number.") from None
    return params


def _parse_outcomes(text: str) -> dict[str, str]:
    outcomes = {}
    for line in [l.strip() for l in text.splitlines() if l.strip()]:
        if "=" not in line:
            raise ValueError(f"Outcome line '{line}' must look like: name = expression.")
        name, expr = (p.strip() for p in line.split("=", 1))
        outcomes[name] = expr
    return outcomes


def _model_step(state: dict, L) -> None:
    mode = st.radio(L("theory.source"), ["catalogue", "editor"], horizontal=True, key="th_mode",
                    format_func=lambda m: L("theory.catalogue") if m == "catalogue" else L("theory.editor"))
    if mode == "catalogue":
        key = st.selectbox(L("theory.model"), list(CATALOGUE), key="th_model",
                           format_func=lambda k: f"{CATALOGUE[k].category} — {CATALOGUE[k].label}")
        entry = CATALOGUE[key]
        n = None
        if entry.n_range:
            n = st.slider(L("theory.n_agents"), entry.n_range[0], entry.n_range[1], entry.n_range[0], key=f"th_n_{key}")
        signature = f"cat:{key}:{n}"
        if state["signature"] != signature:
            state.update(signature=signature, game=build(key, n))
            _reset_downstream(state)
    else:
        n_agents = st.number_input(L("theory.n_agents"), 1, 6, 2, key="th_ed_n")
        params_text = st.text_input(L("theory.parameters_input"), "V=10", key="th_ed_params")
        agents = []
        for i in range(1, int(n_agents) + 1):
            default = DEFAULT_EDITOR_AGENT.get(i, dict(name=f"Agent {i}", strategy=f"s{i}", lower="0", upper="1",
                                                       utility=f"s{i}"))
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            agent = dict(name=c1.text_input(f"Agent {i}", default["name"], key=f"th_ed_name_{i}"),
                         strategy=c2.text_input("Strategy", default["strategy"], key=f"th_ed_strat_{i}"),
                         lower=c3.text_input("Lower", default["lower"], key=f"th_ed_lo_{i}"),
                         upper=c4.text_input("Upper", default["upper"], key=f"th_ed_hi_{i}"))
            agent["utility"] = st.text_input(f"Utility of agent {i}", default["utility"], key=f"th_ed_u_{i}")
            agents.append(agent)
        outcomes_text = st.text_area(L("theory.outcomes_input"), "total effort = x1 + x2", key="th_ed_outcomes")
        if st.button(f"🛠️ {L('theory.build')}", key="th_ed_build"):
            try:
                game = build_custom_game("Custom model", _parse_parameters(params_text), agents,
                                         _parse_outcomes(outcomes_text))
            except ValueError as exc:
                st.error(str(exc))
            else:
                state.update(signature=f"custom:{st.session_state.get('th_ed_counter', 0)}", game=game)
                st.session_state["th_ed_counter"] = st.session_state.get("th_ed_counter", 0) + 1
                _reset_downstream(state)
                st.success("Model built.")
        if state["game"] is None or not str(state["signature"]).startswith("custom"):
            st.info("Write the model, then click the build button.")
            return

    game: Game = state["game"]
    _show_equations(game, L)


def _show_equations(game: Game, L) -> None:
    st.subheader(game.name)
    if game.description:
        st.write(game.description)
    if game.references:
        st.caption(f"References: {game.references}")

    st.markdown(f"**{L('theory.equations')}**")
    focs = first_order_conditions(game)
    brs = best_responses(game) if focs else {}
    for agent in game.agents:
        s = sp.latex(agent.strategy)
        st.markdown(f"*{agent.name}* chooses ${s} \\in [{sp.latex(agent.lower)},\\ {sp.latex(agent.upper)}]$")
        st.latex(rf"U_{{{_tex_name(agent.name)}}} = {sp.latex(agent.utility)}")
        if focs:
            st.latex(rf"\frac{{\partial U}}{{\partial {s}}} = {sp.latex(focs[agent.name])} = 0")
            roots = brs.get(agent.name)
            if roots:
                st.latex(rf"BR({s}) \in \left\{{ {', '.join(sp.latex(r) for r in roots)} \right\}}")
            else:
                st.caption("No closed-form best response: it is computed numerically.")
    if not focs:
        st.caption("Payoffs are not differentiable: the equilibrium comes from the model's closed form, "
                   "then checked against every unilateral deviation.")
    if game.closed_form:
        st.markdown("**Closed-form equilibrium (literature)**")
        for k, expr in game.closed_form.items():
            st.latex(rf"{sp.latex(sp.Symbol(k))}^* = {sp.latex(expr)}")
    if game.outcomes:
        st.markdown("**Outcomes**")
        for k, expr in game.outcomes.items():
            st.latex(rf"{_tex_name(k)} = {sp.latex(expr)}")
    st.dataframe(pd.DataFrame([{"parameter": k, "default": v, "meaning": game.parameter_info.get(k, "")}
                               for k, v in game.parameters.items()]), use_container_width=True, hide_index=True)


# --------------------------------------------------------------------------
# Step 2 — equilibrium & data
# --------------------------------------------------------------------------
def _data_sources() -> dict[str, pd.DataFrame]:
    sources: dict[str, pd.DataFrame] = {}
    lab = st.session_state.get("uploaded_df")
    if lab is None:
        lab = st.session_state.get("virtual_df")
    if lab is not None:
        sources["Virtual Lab dataset"] = lab
    for method, data in st.session_state.get("method_data", {}).items():
        if data.get("df") is not None:
            sources[f"Causal Methods — {method}"] = data["df"]
    return sources


def _pick_dataset(state: dict, sig: str, L) -> pd.DataFrame | None:
    sources = _data_sources()
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
                st.error(f"Could not read file: {exc}")
                return None
        return state.get("upload_df")
    return sources[choice]


def _source_widgets(game: Game, df: pd.DataFrame | None, sig: str) -> dict[str, ParameterSource]:
    numeric_cols = [] if df is None else [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    all_cols = [] if df is None else list(df.columns)
    kinds = ["manual"] if df is None else ["manual", "statistic", "regression"]
    sources = {}
    for name, default in game.parameters.items():
        p = f"th_{sig}_src_{name}"
        cols = st.columns([1.2, 1, 1.2, 1.2, 1.2])
        cols[0].markdown(f"**{name}**  \n<small>{game.parameter_info.get(name, '')}</small>", unsafe_allow_html=True)
        kind = cols[1].selectbox("Source", kinds, key=f"{p}_kind", label_visibility="collapsed")
        if kind == "manual":
            sources[name] = ParameterSource("manual", value=cols[2].number_input(
                "Value", value=float(default), key=f"{p}_value", format="%.4f", label_visibility="collapsed"))
        elif kind == "statistic":
            stat = cols[2].selectbox("Statistic", STATISTICS, key=f"{p}_stat", label_visibility="collapsed")
            column = cols[3].selectbox("Column", numeric_cols or ["—"], key=f"{p}_col", label_visibility="collapsed")
            fcol = cols[4].selectbox("Filter", ["(all rows)"] + all_cols, key=f"{p}_fcol", label_visibility="collapsed")
            fval = None
            if fcol != "(all rows)":
                values = sorted(df[fcol].dropna().astype(str).unique().tolist())
                fval = cols[4].selectbox("equals", values, key=f"{p}_fval")
            sources[name] = ParameterSource("statistic", statistic=stat, column=column,
                                            filter_column=None if fcol == "(all rows)" else fcol, filter_value=fval)
        else:
            y = cols[2].selectbox("y", numeric_cols or ["—"], key=f"{p}_y")
            x = cols[3].selectbox("x", numeric_cols or ["—"], key=f"{p}_x")
            coef = cols[4].selectbox("Coefficient", ["slope", "intercept"], key=f"{p}_coef")
            sources[name] = ParameterSource("regression", y=y, x=x, coefficient=coef)
    return sources


def _equilibrium_table(eq: Equilibrium) -> pd.DataFrame:
    rows = [{"variable": k, "kind": "strategy", "value": v} for k, v in eq.strategies.items()]
    rows += [{"variable": k, "kind": "utility", "value": v} for k, v in eq.utilities.items()]
    rows += [{"variable": k, "kind": "outcome", "value": v} for k, v in eq.outcomes.items()]
    return pd.DataFrame(rows)


def _equilibrium_step(state: dict, L) -> None:
    game: Game | None = state.get("game")
    if game is None:
        st.info("Choose or build a model in step 1 first.")
        return
    sig = state["signature"].replace(":", "_")
    df = _pick_dataset(state, sig, L)
    state["df"] = df

    scope, scope_col = "pooled", None
    if df is not None:
        cols = list(df.columns)
        c1, c2 = st.columns(2)
        unit_col = c1.selectbox("Unit column", ["(none)"] + cols, key=f"th_{sig}_unit",
                                index=(cols.index("unit") + 1) if "unit" in cols else 0)
        period_col = c2.selectbox("Period column", ["(none)"] + cols, key=f"th_{sig}_period",
                                  index=(cols.index("period") + 1) if "period" in cols else 0)
        unit_col = None if unit_col == "(none)" else unit_col
        period_col = None if period_col == "(none)" else period_col
        structure = detect_structure(df, unit_col, period_col)
        st.info(f"**{L('theory.structure')}:** {structure} ({len(df)} rows)")
        scopes = ["pooled", "group", "period"] if period_col else ["pooled", "group"]
        default = default_scope(structure)
        scope = st.radio(L("theory.scope"), scopes, horizontal=True, key=f"th_{sig}_scope",
                         index=scopes.index(default) if default in scopes else 0,
                         format_func=lambda s: {"pooled": "Pooled sample", "group": "One equilibrium per group",
                                                "period": "One equilibrium per period (path)"}[s])
        if scope == "group":
            scope_col = st.selectbox("Group column", [c for c in cols if c != period_col], key=f"th_{sig}_group")
        elif scope == "period":
            scope_col = period_col

    st.markdown(f"**{L('theory.parameter_sources')}**")
    sources = _source_widgets(game, df, sig)

    if st.button(f"⚖️ {L('theory.solve')}", type="primary", key=f"th_{sig}_solve"):
        _reset_downstream(state)
        try:
            values = calibrate(df, sources)
            result = solve_equilibrium(game, values)
            state.update(values=values, sources=sources, solve_message=result.message,
                         equilibria=result.equilibria)
            if scope != "pooled" and df is not None:
                with st.spinner("Solving one equilibrium per unit..."):
                    state["table"] = solve_by_scope(game, df, sources, scope, scope_col)
                    state["table_scope"] = scope
        except (CalibrationError, ValueError) as exc:
            st.error(str(exc))

    if "values" not in state:
        return
    st.caption("Calibrated parameters: " + ", ".join(
        f"{k} = {v:.4g} [{state['sources'][k].describe()}]" for k, v in state["values"].items()))
    equilibria = state.get("equilibria") or []
    (st.success if equilibria else st.error)(state["solve_message"])
    if equilibria:
        idx = 0
        if len(equilibria) > 1:
            idx = st.selectbox("Equilibrium used for predictions", range(len(equilibria)), key=f"th_{sig}_eqidx",
                               format_func=lambda i: f"Equilibrium {i + 1}")
        state["baseline"] = equilibria[idx]
        st.dataframe(_equilibrium_table(equilibria[idx]).round(6), use_container_width=True, hide_index=True)
        st.caption(f"Method: {equilibria[idx].method}; largest relative gain from a unilateral deviation = "
                   f"{equilibria[idx].max_gain:.2e}.")

    table = state.get("table")
    if table is not None:
        st.markdown(f"**{L('theory.by_unit')}**")
        st.dataframe(table, use_container_width=True, hide_index=True)
        value_cols = [c for c in table.columns if c.startswith(("strategy:", "outcome:"))]
        if value_cols:
            shown = st.multiselect("Plot", value_cols, default=value_cols[: min(3, len(value_cols))],
                                   key=f"th_{sig}_pathcols")
            fig = go.Figure()
            for c in shown:
                if state.get("table_scope") == "period":
                    fig.add_trace(go.Scatter(x=table["unit"], y=table[c], mode="lines+markers", name=c))
                else:
                    fig.add_trace(go.Bar(x=table["unit"].astype(str), y=table[c], name=c))
            fig.update_layout(height=380, xaxis_title=scope_col, title="Equilibrium by unit of computation")
            st.plotly_chart(fig, use_container_width=True)

    if state.get("baseline") is not None:
        _outcome_curve(state, game, sig, L)


def _outcome_curve(state: dict, game: Game, sig: str, L) -> None:
    st.markdown(f"**{L('theory.curve')}**")
    base = state["baseline"]
    variables = list(base.strategies) + list(base.outcomes)
    c1, c2 = st.columns(2)
    var = c1.selectbox("Equilibrium variable", variables, key=f"th_{sig}_curve_var")
    param = c2.selectbox("Parameter", list(game.parameters), key=f"th_{sig}_curve_param")
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
        fig = go.Figure(go.Scatter(x=grid, y=ys, mode="lines+markers"))
        fig.add_vline(x=theta, line_dash="dot", line_color="gray", annotation_text="calibrated")
        fig.update_layout(height=340, xaxis_title=param, yaxis_title=var,
                          title=f"Equilibrium {var} as a function of {param}")
        st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------------------------------
# Step 3 — predictions
# --------------------------------------------------------------------------
def _causal_estimates() -> dict[str, tuple[float, float, float]]:
    out = {}
    for method, data in st.session_state.get("method_data", {}).items():
        r = data.get("result")
        if r is not None and r.ci_low is not None:
            out[f"{r.method} — {r.estimand}"] = (r.estimate, r.ci_low, r.ci_high)
    return out


def _predictions_step(state: dict, L) -> None:
    game: Game | None = state.get("game")
    if game is None or state.get("baseline") is None:
        st.info("Solve the equilibrium in step 2 first.")
        return
    sig = state["signature"].replace(":", "_")
    df = state.get("df")
    c1, c2 = st.columns(2)
    param = c1.selectbox(L("theory.shifted_parameter"), list(game.parameters), key=f"th_{sig}_pred_param")
    modes = ["manual"] + (["data"] if df is not None else [])
    mode = c2.radio(L("theory.delta_source"), modes, horizontal=True, key=f"th_{sig}_pred_mode",
                    format_func=lambda m: "Enter Δ" if m == "manual" else "Treated − control in the data")
    delta = None
    if mode == "manual":
        delta = st.number_input("Δ", value=1.0, key=f"th_{sig}_pred_delta", format="%.4f")
    else:
        treat_col = st.selectbox("Treatment column (0/1)", list(df.columns),
                                 index=list(df.columns).index("D") if "D" in df.columns else 0,
                                 key=f"th_{sig}_pred_treat")
        try:
            delta = delta_from_data(df, state["sources"][param], treat_col, param)
            st.info(f"Δ measured in the data = {delta:.4g}  ({state['sources'][param].describe()}: treated − control)")
        except CalibrationError as exc:
            st.error(str(exc))

    if delta is not None and st.button(f"🔮 {L('theory.predict')}", type="primary", key=f"th_{sig}_pred_btn"):
        try:
            state["prediction"] = predict_shift(game, state["values"], param, float(delta), state["baseline"])
        except ValueError as exc:
            st.error(str(exc))
            state.pop("prediction", None)

    pred = state.get("prediction")
    if pred is None:
        return
    rows = []
    for k in pred.effects:
        base = {**pred.baseline.strategies, **pred.baseline.outcomes}[k]
        shifted = {**pred.shifted.strategies, **pred.shifted.outcomes}[k]
        rows.append({"variable": k, "baseline": base, "after shift": shifted, "predicted effect": pred.effects[k],
                     f"d/d{pred.parameter}": pred.derivatives.get(k, np.nan)})
    st.markdown(f"**Predicted effect of {pred.parameter} → {pred.parameter} {pred.delta:+.4g}**")
    st.dataframe(pd.DataFrame(rows).round(6), use_container_width=True, hide_index=True)

    st.markdown(f"**{L('theory.compare')}**")
    variable = st.selectbox("Predicted variable", list(pred.effects), key=f"th_{sig}_cmp_var")
    estimates = _causal_estimates()
    choice = st.selectbox("Causal estimate", list(estimates) + ["manual"], key=f"th_{sig}_cmp_src",
                          format_func=lambda o: "Enter manually" if o == "manual" else o)
    if choice == "manual":
        c1, c2, c3 = st.columns(3)
        est = c1.number_input("Estimate", value=0.0, key=f"th_{sig}_cmp_est", format="%.4f")
        lo = c2.number_input("95% CI low", value=-1.0, key=f"th_{sig}_cmp_lo", format="%.4f")
        hi = c3.number_input("95% CI high", value=1.0, key=f"th_{sig}_cmp_hi", format="%.4f")
    else:
        est, lo, hi = estimates[choice]
    predicted = pred.effects[variable]
    verdict = compare_with_estimate(predicted, est, lo, hi)
    VERDICT_STYLE[verdict](f"**{L('theory.verdict')}: {verdict}** — predicted {variable} effect = {predicted:+.4g}; "
                           f"causal estimate = {est:+.4g}, 95% CI [{lo:.4g}, {hi:.4g}].")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[est], y=["Causal estimate"], mode="markers", marker=dict(size=12),
                             error_x=dict(type="data", symmetric=False, array=[hi - est], arrayminus=[est - lo])))
    fig.add_trace(go.Scatter(x=[predicted], y=["Theory prediction"], mode="markers",
                             marker=dict(size=14, symbol="diamond")))
    fig.add_vline(x=0, line_dash="dot", line_color="gray")
    fig.update_layout(height=240, showlegend=False, xaxis_title="Effect")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("The prediction and the causal estimate must refer to the same outcome, measured in the same units, "
               "for this comparison to be meaningful.")


# --------------------------------------------------------------------------
# Page
# --------------------------------------------------------------------------
def render(L) -> None:
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
