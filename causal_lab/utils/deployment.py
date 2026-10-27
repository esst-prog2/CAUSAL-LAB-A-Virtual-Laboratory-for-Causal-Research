"""
Is the app running on the researcher's own machine, or as the public online
demo? The privacy notes differ: locally, every computation stays on the
machine; online, uploaded files are processed on the hosting server.

The answer comes from the address the browser used to reach the app, so no
setting has to be remembered when deploying.
"""
from __future__ import annotations

import streamlit as st

LOCAL_HOSTS = ("localhost", "127.0.0.1", "[::1]", "0.0.0.0")


def is_online(host: str | None) -> bool:
    """True when `host` (the HTTP Host header, possibly with a port) is not
    this machine. An unknown host counts as local: there is nothing to warn
    about when the app is driven without a browser (tests, scripts)."""
    if not host:
        return False
    name = host.strip().lower()
    name = name.rsplit(":", 1)[0] if not name.endswith("]") else name
    return name not in LOCAL_HOSTS


def running_online() -> bool:
    try:
        host = st.context.headers.get("Host")
    except Exception:                 # no browser session (bare script run)
        return False
    return is_online(host)
