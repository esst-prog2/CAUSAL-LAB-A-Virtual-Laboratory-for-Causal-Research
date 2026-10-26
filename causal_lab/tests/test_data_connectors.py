"""Data connectors, offline: a fake HTTP session replays responses recorded from
the live DHS, geoBoundaries and WorldPop APIs on 2026-10-25 (tests/connector_fixtures).
ACLED replies are built from its API documentation (no account to record them).
Set CAUSAL_LAB_LIVE=1 to also run one live request per public service."""
import json
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

import data_connectors.acled as acled
from data_connectors.common import parse_json
from data_connectors.dhs import fetch_dhs_indicators
from data_connectors.worldpop import fetch_worldpop_population
from utils.i18n import LocalizedError

FIXTURES = Path(__file__).resolve().parent / "connector_fixtures"
APP = str(Path(__file__).resolve().parent.parent / "app.py")


class Reply:
    def __init__(self, text, status=200):
        self.text, self.status_code = text, status


class FakeSession:
    """Routes requests to handlers; records every call."""
    def __init__(self, handler):
        self.handler, self.calls = handler, []

    def get(self, url, **kwargs):
        self.calls.append(("get", url, kwargs))
        return self.handler("get", url, kwargs)

    def post(self, url, **kwargs):
        self.calls.append(("post", url, kwargs))
        return self.handler("post", url, kwargs)


def _raises_key(key, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except LocalizedError as exc:
        assert exc.msg.key == key, exc.msg.key
    else:
        raise AssertionError(f"expected {key}")


# --------------------------------------------------------------------------- DHS
def test_dhs_national_panel_keeps_the_preferred_estimates():
    raw = json.loads((FIXTURES / "dhs_national.json").read_text())
    session = FakeSession(lambda m, u, kw: Reply(json.dumps(raw)))
    panel = fetch_dhs_indicators(session, ["CD", "RW"], ["CM_ECMR_C_U5M", "CN_NUTS_C_HA2"])
    preferred = [r for r in raw["Data"] if r["IsPreferred"] == 1]
    assert len(panel) == len({(r["CountryName"], r["SurveyYear"]) for r in preferred})
    drc_2007 = panel[(panel["unit"] == "Congo Democratic Republic") & (panel["period"] == 2007)].iloc[0]
    expected = next(r["Value"] for r in preferred if r["SurveyId"] == "CD2007DHS" and r["IndicatorId"] == "CM_ECMR_C_U5M")
    assert drc_2007["CM_ECMR_C_U5M"] == expected == 148
    params = session.calls[0][2]["params"]
    assert params["countryIds"] == "CD,RW" and params["breakdown"] == "national" and params["f"] == "json"


def test_dhs_uses_the_preferred_row_even_when_another_comes_first():
    base = {"CountryName": "X", "SurveyYear": 2010, "SurveyId": "XX2010DHS", "IndicatorId": "CM_ECMR_C_U5M",
            "CharacteristicCategory": "Total", "CharacteristicLabel": "Total"}
    rows = [{**base, "Value": 99, "IsPreferred": 0, "ByVariableLabel": "Ten years preceding the survey"},
            {**base, "Value": 50, "IsPreferred": 1, "ByVariableLabel": "Five years preceding the survey"}]
    session = FakeSession(lambda m, u, kw: Reply(json.dumps({"TotalPages": 1, "Data": rows})))
    panel = fetch_dhs_indicators(session, ["XX"], ["CM_ECMR_C_U5M"])
    assert panel["CM_ECMR_C_U5M"].tolist() == [50]


def test_dhs_regions_are_named_without_the_indent_and_pages_are_followed():
    raw = json.loads((FIXTURES / "dhs_subnational.json").read_text())
    half = len(raw["Data"]) // 2
    pages = {1: {**raw, "TotalPages": 2, "Data": raw["Data"][:half]}, 2: {**raw, "TotalPages": 2, "Data": raw["Data"][half:]}}
    session = FakeSession(lambda m, u, kw: Reply(json.dumps(pages[kw["params"]["page"]])))
    panel = fetch_dhs_indicators(session, ["RW"], ["CM_ECMR_C_U5M"], subnational=True)
    assert len(session.calls) == 2 and len(panel) == len(raw["Data"])
    assert all(u.startswith("Rwanda / ") and ".." not in u for u in panel["unit"])


def test_dhs_errors_name_the_problem():
    empty = FakeSession(lambda m, u, kw: Reply(json.dumps({"TotalPages": 1, "Data": []})))
    _raises_key("err.dhs_no_data", fetch_dhs_indicators, empty, ["XX"], ["CM_ECMR_C_U5M"])
    _raises_key("err.dhs_needs_choice", fetch_dhs_indicators, empty, [], ["CM_ECMR_C_U5M"])

    def offline(m, u, kw):
        raise ConnectionError("no route")
    _raises_key("err.connector_network", fetch_dhs_indicators, FakeSession(offline), ["CD"], ["CM_ECMR_C_U5M"])
    _raises_key("err.connector_http", fetch_dhs_indicators, FakeSession(lambda m, u, kw: Reply("", 500)), ["CD"], ["X"])
    _raises_key("err.connector_parse", fetch_dhs_indicators, FakeSession(lambda m, u, kw: Reply("<html>down</html>")),
                ["CD"], ["X"])


# --------------------------------------------------------------------------- WorldPop
def _worldpop_session():
    meta = json.loads((FIXTURES / "geoboundaries_rwa_adm1_meta.json").read_text())
    shapes = json.loads((FIXTURES / "geoboundaries_rwa_adm1.geojson").read_text())
    replies = json.loads((FIXTURES / "worldpop_rwa_adm1_raw.json").read_text())
    geometries = [json.dumps(f["geometry"]) for f in shapes["features"]]

    def handler(method, url, kw):
        if method == "get" and url.startswith("https://www.geoboundaries.org/"):
            return Reply(json.dumps(meta))
        if method == "get" and url == meta["simplifiedGeometryGeoJSON"]:
            return Reply(json.dumps(shapes))
        if method == "post" and url == "https://api.worldpop.org/v1/services/stats":
            sent = json.loads(kw["data"]["geojson"])["features"][0]["geometry"]
            index = geometries.index(json.dumps(sent))
            return Reply(replies[f"{index}_{kw['data']['year']}"])
        raise AssertionError((method, url))
    return FakeSession(handler), shapes, replies


def test_worldpop_population_panel_from_the_recorded_replies():
    session, shapes, replies = _worldpop_session()
    seen = []
    panel = fetch_worldpop_population(session, "RWA", [2015, 2010], "ADM1", progress=lambda d, n: seen.append(n))
    assert len(panel) == 10 and set(panel["period"]) == {2010, 2015} and seen and set(seen) == {10}
    kigali = panel[(panel["unit"] == "City of Kigali") & (panel["period"] == 2015)]["population"].iloc[0]
    assert abs(kigali - parse_json("WorldPop", replies["0_2015"])["data"]["total_population"]) < 1e-6
    posts = [c for c in session.calls if c[0] == "post"]
    assert len(posts) == 10 and all(c[2]["data"]["dataset"] == "wpgppop" for c in posts)


def test_worldpop_replies_with_php_notices_are_parsed():
    noisy = "<br />\n<b>Deprecated</b>: something {not json\n" + '{"error": false, "data": {"total_population": 12.5}}'
    assert parse_json("WorldPop", noisy)["data"]["total_population"] == 12.5


def test_worldpop_rejects_years_and_levels_it_does_not_have():
    session, _, _ = _worldpop_session()
    _raises_key("err.worldpop_years", fetch_worldpop_population, session, "RWA", [1990])
    _raises_key("err.worldpop_level", fetch_worldpop_population, session, "RWA", [2010], "ADM9")


# --------------------------------------------------------------------------- ACLED
def _acled_session(events, page_size, token_status=200):
    def handler(method, url, kw):
        if method == "post" and url == acled.TOKEN_URL:
            if token_status != 200:
                return Reply('{"error": "invalid_grant"}', token_status)
            assert kw["data"]["grant_type"] == "password" and kw["data"]["username"] == "me@uni.edu"
            return Reply(json.dumps({"token_type": "Bearer", "access_token": "TOKEN", "expires_in": 86400}))
        if method == "get" and url == acled.READ_URL:
            assert kw["headers"]["Authorization"] == "Bearer TOKEN"
            p = kw["params"]
            rows = [e for e in events if e["year"] == str(p["year"])]
            chunk = rows[(p["page"] - 1) * page_size: p["page"] * page_size]
            return Reply(json.dumps({"status": 200, "success": True, "count": len(chunk), "data": chunk}))
        raise AssertionError((method, url))
    return FakeSession(handler)


EVENTS = ([{"event_date": "2019-03-02", "year": "2019", "country": "X", "admin1": "North", "event_type": "Battles",
            "fatalities": "3"}] * 3
          + [{"event_date": "2020-07-10", "year": "2020", "country": "X", "admin1": "South",
              "event_type": "Riots", "fatalities": "0"}])


def test_acled_pages_through_events_and_aggregates_with_zeros():
    saved, acled.PAGE_SIZE = acled.PAGE_SIZE, 2
    try:
        session = _acled_session(EVENTS, page_size=2)
        token = acled.access_token(session, "me@uni.edu", "secret")
        events = acled.fetch_acled_events(session, token, "X", [2019, 2020])
    finally:
        acled.PAGE_SIZE = saved
    assert len(events) == 4
    reads = [c for c in session.calls if c[1] == acled.READ_URL]
    assert [(c[2]["params"]["year"], c[2]["params"]["page"]) for c in reads] == [(2019, 1), (2019, 2), (2020, 1)]
    panel = acled.aggregate_events(events, "admin1", "year")
    assert len(panel) == 4                                   # 2 units x 2 years, missing ones filled
    north = panel.set_index(["unit", "period"]).loc[("North", 2019)]
    assert north["events"] == 3 and north["fatalities"] == 9
    assert panel.set_index(["unit", "period"]).loc[("North", 2020), "events"] == 0
    monthly = acled.aggregate_events(events, "country", "month")
    assert set(monthly["period"]) == {"2019-03", "2020-07"}


def test_acled_credentials_problems_are_reported():
    _raises_key("err.acled_credentials", acled.access_token, _acled_session([], 1), "", "")
    _raises_key("err.connector_denied", acled.access_token, _acled_session([], 1, token_status=401), "me@uni.edu", "x")
    _raises_key("err.acled_no_events", acled.aggregate_events, pd.DataFrame(columns=acled.FIELDS.split("|")))


# --------------------------------------------------------------------------- page
def test_the_page_is_off_by_default_and_sends_nothing():
    from streamlit.testing.v1 import AppTest
    import requests

    import data_connectors.common as common
    import ui.data_sources_page as page
    called = []

    def forbidden(*args, **kwargs):
        called.append(1)
        raise AssertionError("a network session was opened")
    saved = common.new_session, page.new_session, requests.Session
    common.new_session = page.new_session = requests.Session = forbidden
    try:
        at = AppTest.from_file(APP, default_timeout=120)
        at.session_state["page"] = "data_sources"
        at.run()
        for other in ("settings", "dashboard"):
            at.session_state["page"] = other
            at.run()
    finally:
        common.new_session, page.new_session, requests.Session = saved
        at.session_state["page"] = "data_sources"
        at.run()
    assert not at.exception and not called
    assert any("connectors are off" in i.value for i in at.info)
    assert not [b for b in at.button if "Fetch" in b.label]


def test_turning_the_connectors_on_survives_leaving_settings():
    # Found by running the app: the toggle's own key was dropped when Settings was
    # left, so the External Data page saw the connectors off again.
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["page"] = "settings"
    at.run()
    at.toggle(key="connectors_toggle").set_value(True).run()
    at.session_state["page"] = "data_sources"
    at.run()
    assert at.session_state["connectors_enabled"] is True
    assert [b for b in at.button if b.key == "src_dhs_fetch"]
    at.session_state["page"] = "settings"
    at.run()
    assert at.toggle(key="connectors_toggle").value is True          # still shown as on


def test_a_fetched_dataset_can_be_sent_to_a_causal_methods_page():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=120)
    at.session_state["page"] = "data_sources"
    at.session_state["connectors_enabled"] = True
    at.session_state["connector_data"] = {"dhs": pd.DataFrame({"unit": ["A", "A", "B", "B"], "period": [1, 2, 1, 2],
                                                                "CM_ECMR_C_U5M": [100.0, 90.0, 120.0, 80.0]})}
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    at.selectbox(key="src_dhs_method").set_value("dml").run()
    next(b for b in at.button if b.key == "src_dhs_send").click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.session_state["page"] == "methods"
    entry = at.session_state["method_data"]["dml"]
    assert entry["file_id"] == "connector:dhs" and list(entry["raw"].columns)[0] == "unit"


def test_live_public_services_when_asked():
    if os.environ.get("CAUSAL_LAB_LIVE") != "1":
        print("CAUSAL_LAB_LIVE not set: live requests skipped")
        return
    from data_connectors.common import new_session
    panel = fetch_dhs_indicators(new_session(), ["CD"], ["CM_ECMR_C_U5M"])
    assert (panel["period"] == 2007).any() and len(panel) >= 3
    pop = fetch_worldpop_population(new_session(), "RWA", [2020], "ADM1")
    assert len(pop) == 5 and pop["population"].sum() > 10e6


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
    print("test_data_connectors: OK")
