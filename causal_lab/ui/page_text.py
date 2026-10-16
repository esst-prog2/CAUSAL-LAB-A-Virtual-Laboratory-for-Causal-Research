"""
Language helpers shared by the page modules (hw6 review 4).

They used to be copied into each page, each with a module-level `_LANG`
set at the start of its render. Module globals are shared by every
Streamlit session of the server process, so two visitors using different
languages could see each other's language. The language is now read from
the visitor's own session state each time.
"""
from __future__ import annotations

import streamlit as st

from utils.i18n import DEFAULT_LANGUAGE, LocalizedError, render as render_message, tf


def lang() -> str:
    return st.session_state.get("lang", DEFAULT_LANGUAGE)


def F(key: str, **params) -> str:
    return tf(key, lang(), **params)


def R(message) -> str:
    return render_message(message, lang())


def error_text(exc: Exception) -> str:
    return exc.render(lang()) if isinstance(exc, LocalizedError) else str(exc)
