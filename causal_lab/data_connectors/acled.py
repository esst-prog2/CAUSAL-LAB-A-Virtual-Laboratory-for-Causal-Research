"""
ACLED conflict events, aggregated to a panel.

ACLED requires an account: the researcher's e-mail (username) and password
are exchanged for an access token (OAuth password grant at
acleddata.com/oauth/token), which then authorizes the event requests
(acleddata.com/api/acled/read). The credentials go to ACLED only and are
never stored by Causal Lab. Events are fetched page by page and aggregated
to events and fatalities per country or first-level unit (admin1) and year
or month.

Written to ACLED's documented API (2025). It could not be tried against the
live service without an account: the tests use responses built from that
documentation. ACLED's terms of use apply to the data.
"""
from __future__ import annotations

import pandas as pd

from data_connectors.common import get_json, parse_json, request
from utils.i18n import LocalizedError

TOKEN_URL = "https://acleddata.com/oauth/token"
READ_URL = "https://acleddata.com/api/acled/read"
SERVICE = "ACLED"
PAGE_SIZE = 5000
FIELDS = "event_date|year|country|admin1|event_type|fatalities"


def access_token(session, email: str, password: str) -> str:
    if not email or not password:
        raise LocalizedError("err.acled_credentials")
    text = request(session, "post", SERVICE, TOKEN_URL, data={
        "username": email, "password": password, "grant_type": "password", "client_id": "acled"})
    reply = parse_json(SERVICE, text)
    token = reply.get("access_token") if isinstance(reply, dict) else None
    if not token:
        raise LocalizedError("err.acled_credentials")
    return token


def fetch_acled_events(session, token: str, country: str, years: list[int]) -> pd.DataFrame:
    """Raw events (one row each) for `country` and `years`."""
    events = []
    for year in sorted(set(int(y) for y in years)):
        page = 1
        while True:
            reply = get_json(session, SERVICE, READ_URL, headers={"Authorization": f"Bearer {token}"}, params={
                "_format": "json", "country": country, "year": year, "fields": FIELDS,
                "limit": PAGE_SIZE, "page": page})
            if not isinstance(reply, dict) or reply.get("success") is False:
                raise LocalizedError("err.connector_parse", service=SERVICE)
            batch = reply.get("data") or []
            events.extend(batch)
            if len(batch) < PAGE_SIZE:
                break
            page += 1
    return pd.DataFrame(events, columns=FIELDS.split("|"))


def aggregate_events(events: pd.DataFrame, level: str = "admin1", frequency: str = "year") -> pd.DataFrame:
    """Events and fatalities per unit and period; unit-periods without events are
    not in ACLED's data, so they are filled with zeros over the units and periods seen."""
    if level not in ("country", "admin1") or frequency not in ("year", "month"):
        raise LocalizedError("err.acled_aggregation")
    if events.empty:
        raise LocalizedError("err.acled_no_events")
    data = events.copy()
    data["fatalities"] = pd.to_numeric(data["fatalities"], errors="coerce").fillna(0)
    data["period"] = (pd.to_numeric(data["year"]).astype(int) if frequency == "year"
                      else pd.to_datetime(data["event_date"]).dt.strftime("%Y-%m"))
    data["unit"] = data[level].fillna("")
    panel = data.groupby(["unit", "period"]).agg(events=("event_type", "size"),
                                                 fatalities=("fatalities", "sum")).reset_index()
    full = pd.MultiIndex.from_product([sorted(panel["unit"].unique()), sorted(panel["period"].unique())],
                                      names=["unit", "period"])
    return panel.set_index(["unit", "period"]).reindex(full, fill_value=0).reset_index()
