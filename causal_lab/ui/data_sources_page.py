"""
External data page: DHS indicators, WorldPop population and ACLED events.

Off until the researcher enables the connectors in Settings
(st.session_state.connectors_enabled). A fetched dataset can be downloaded
as CSV or sent to a Causal Methods page as if it had been uploaded there,
where its columns are mapped as usual.
"""
from __future__ import annotations

import streamlit as st

from data_connectors.acled import access_token, aggregate_events, fetch_acled_events
from data_connectors.common import new_session
from data_connectors.dhs import COMMON_INDICATORS, fetch_dhs_indicators
from data_connectors.worldpop import LEVELS, YEARS, fetch_worldpop_population
from estimators.registry import METHOD_KEYS
from ui.page_text import F, error_text
from utils.i18n import LocalizedError

SECONDS_PER_WORLDPOP_REQUEST = 6        # measured: 10 requests, 4 at a time, 58 s


def _store() -> dict:
    return st.session_state.setdefault("connector_data", {})


def _result(source: str, L) -> None:
    df = _store().get(source)
    if df is None:
        return
    st.success(F("sources.fetched", rows=len(df), units=df["unit"].nunique(), periods=df["period"].nunique()))
    st.dataframe(df.head(50), width="stretch")
    c1, c2, c3 = st.columns([2, 2, 1])
    c1.download_button(F("code.download", language="CSV"), df.to_csv(index=False), f"causal_lab_{source}.csv",
                       key=f"src_{source}_csv")
    c2.selectbox(L("sources.send_to"), METHOD_KEYS, format_func=lambda k: L(f"method.{k}"),
                 key=f"src_{source}_method")
    c3.button(L("sources.send"), key=f"src_{source}_send", on_click=_send, args=(source,))


def _send(source: str) -> None:
    """Button callback (runs before the page, so it may change page): hand the
    dataset to a Causal Methods page as an uploaded file, to be mapped there."""
    method = st.session_state[f"src_{source}_method"]
    store = st.session_state.setdefault("method_data", {})
    entry = store.setdefault(method, {"df": None, "truth": None, "mapping": None, "options": {},
                                      "source": None, "result": None, "error": None, "dropped": 0,
                                      "file_id": None})
    entry.update(raw=_store()[source].copy(), file_id=f"connector:{source}", result=None, error=None, source=None)
    st.session_state[f"mw_{method}_source"] = "upload"
    st.session_state["methods_choice"] = method
    st.session_state.page = "methods"


def _run(fetch, source: str) -> None:
    try:
        _store()[source] = fetch()
    except LocalizedError as exc:
        st.error(error_text(exc))


def render(L) -> None:
    st.title(f"🌍 {L('sources.title')}")
    st.caption(L("sources.intro"))
    if not st.session_state.get("connectors_enabled"):
        st.info(L("sources.disabled"))
        return
    st.warning(L("sources.network_note"))
    tab_dhs, tab_wp, tab_acled = st.tabs(["DHS", "WorldPop", "ACLED"])

    with tab_dhs:
        st.caption(L("sources.dhs.intro"))
        c1, c2 = st.columns(2)
        countries = c1.text_input(L("sources.dhs.countries"), value="CD", key="src_dhs_countries")
        chosen = c2.multiselect(L("sources.dhs.indicators"), list(COMMON_INDICATORS), default=["CM_ECMR_C_U5M"],
                                format_func=lambda k: f"{COMMON_INDICATORS[k]} ({k})", key="src_dhs_indicators")
        extra = st.text_input(L("sources.dhs.other_indicators"), value="", key="src_dhs_extra")
        subnational = st.checkbox(L("sources.dhs.subnational"), key="src_dhs_sub")
        if st.button(f"⬇️ {L('sources.fetch')}", type="primary", key="src_dhs_fetch"):
            codes = [c.strip().upper() for c in countries.split(",") if c.strip()]
            ids = chosen + [i.strip() for i in extra.split(",") if i.strip()]
            with st.spinner(L("sources.fetching")):
                _run(lambda: fetch_dhs_indicators(new_session(), codes, ids, subnational), "dhs")
        if subnational:
            st.caption(L("sources.dhs.unbalanced"))
        _result("dhs", L)

    with tab_wp:
        st.caption(L("sources.worldpop.intro"))
        c1, c2, c3 = st.columns(3)
        iso3 = c1.text_input(L("sources.worldpop.iso3"), value="RWA", key="src_wp_iso3")
        level = c2.selectbox(L("sources.worldpop.level"), LEVELS, index=1, key="src_wp_level")
        years = c3.multiselect(L("sources.worldpop.years"), list(YEARS), default=[2010, 2020], key="src_wp_years")
        st.caption(F("sources.worldpop.time", seconds=SECONDS_PER_WORLDPOP_REQUEST * max(len(years), 1)))
        if st.button(f"⬇️ {L('sources.fetch')}", type="primary", key="src_wp_fetch"):
            bar = st.progress(0.0)
            _run(lambda: fetch_worldpop_population(new_session(), iso3.strip(), years, level,
                                                   progress=lambda d, n: bar.progress(d / n)), "worldpop")
        _result("worldpop", L)

    with tab_acled:
        st.caption(L("sources.acled.intro"))
        c1, c2 = st.columns(2)
        email = c1.text_input(L("sources.acled.email"), key="src_acled_email")
        password = c2.text_input(L("sources.acled.password"), type="password", key="src_acled_password")
        c1, c2, c3, c4 = st.columns(4)
        country = c1.text_input(L("sources.acled.country"), value="Democratic Republic of Congo",
                                key="src_acled_country")
        first, last = c2.number_input(L("sources.acled.first_year"), 1997, 2030, 2018, key="src_acled_first"), \
            c3.number_input(L("sources.acled.last_year"), 1997, 2030, 2022, key="src_acled_last")
        level = c4.selectbox(L("sources.acled.level"), ["admin1", "country"], key="src_acled_level")
        frequency = st.radio(L("sources.acled.frequency"), ["year", "month"], horizontal=True,
                             format_func=lambda f: L(f"sources.acled.frequency.{f}"), key="src_acled_freq")
        if st.button(f"⬇️ {L('sources.fetch')}", type="primary", key="src_acled_fetch"):
            def fetch():
                session = new_session()
                token = access_token(session, email.strip(), password)
                events = fetch_acled_events(session, token, country.strip(), list(range(int(first), int(last) + 1)))
                return aggregate_events(events, level, frequency)
            with st.spinner(L("sources.fetching")):
                _run(fetch, "acled")
        st.caption(L("sources.acled.untested"))
        _result("acled", L)
