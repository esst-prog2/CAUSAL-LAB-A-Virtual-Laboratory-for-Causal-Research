"""HTTP helpers shared by the connectors."""
from __future__ import annotations

import json
import re

from utils.i18n import LocalizedError

TIMEOUT_SECONDS = 120
USER_AGENT = "CausalLab/0.1 (research software; data connectors)"


def new_session():
    """A requests session with Causal Lab's user agent (requests ships with Streamlit)."""
    import requests

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    return session


def get_json(session, service: str, url: str, **kwargs):
    return parse_json(service, request(session, "get", service, url, **kwargs))


def request(session, method: str, service: str, url: str, **kwargs) -> str:
    """Response text, or a LocalizedError naming the service and the problem."""
    try:
        response = getattr(session, method)(url, timeout=TIMEOUT_SECONDS, **kwargs)
    except Exception as exc:             # requests raises many types (connection, timeout, SSL...)
        raise LocalizedError("err.connector_network", service=service, detail=type(exc).__name__) from None
    if response.status_code in (401, 403):
        raise LocalizedError("err.connector_denied", service=service, status=response.status_code)
    if response.status_code >= 400:
        raise LocalizedError("err.connector_http", service=service, status=response.status_code)
    return response.text


def parse_json(service: str, text: str):
    """The first JSON object or array in `text`. WorldPop's API prefixes its
    JSON with PHP deprecation notices in HTML, so plain json.loads fails."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    cleaned = re.sub(r"<[^>]+>", "", text)
    decoder = json.JSONDecoder()
    for match in re.finditer(r"[{\[]", cleaned):
        try:
            return decoder.raw_decode(cleaned[match.start():])[0]
        except json.JSONDecodeError:
            continue
    raise LocalizedError("err.connector_parse", service=service)
