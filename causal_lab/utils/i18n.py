"""
Minimal i18n helper for CAUSAL LAB.

Loads the JSON translation dictionaries from /locales and exposes a
single `t(key, lang)` lookup function used throughout the Streamlit
app. This keeps the principle from the spec: no UI text is hard-coded
inside components, it is always looked up through this module.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
SUPPORTED_LANGUAGES = ("en", "fr")
DEFAULT_LANGUAGE = "en"


@lru_cache(maxsize=None)
def _load(lang: str) -> dict:
    path = LOCALES_DIR / f"{lang}.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def t(key: str, lang: str = DEFAULT_LANGUAGE) -> str:
    """Translate `key` into `lang`, falling back to English, then to
    the raw key itself if nothing is found (so missing translations
    are visible instead of crashing the app)."""
    lang = lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    data = _load(lang)
    if key in data:
        return data[key]
    fallback = _load(DEFAULT_LANGUAGE)
    return fallback.get(key, key)


def tf(key: str, lang: str = DEFAULT_LANGUAGE, **params) -> str:
    """Translate `key` and fill its `{placeholders}` with `params`.
    Falls back to the English template if the translation's
    placeholders do not match."""
    # A parameter may itself be a Msg (e.g. a translated option label).
    params = {k: (v.render(lang) if isinstance(v, Msg) else v) for k, v in params.items()}
    template = t(key, lang)
    try:
        return template.format(**params)
    except (KeyError, IndexError, ValueError):
        return t(key, DEFAULT_LANGUAGE).format(**params)


def _rebuild_msg(key: str, params: dict) -> "Msg":
    return Msg(key, **params)


class Msg(str):
    """A translatable message produced by an engine: a locale key plus
    the values for its placeholders. It *is* a str whose value is the
    English text, so engines, tests and any string operation keep
    working unchanged; the UI calls `msg.render(lang)`."""

    def __new__(cls, key: str, **params):
        obj = super().__new__(cls, tf(key, DEFAULT_LANGUAGE, **params))
        obj.key = key
        obj.params = params
        return obj

    def render(self, lang: str = DEFAULT_LANGUAGE) -> str:
        return tf(self.key, lang, **self.params)

    def __repr__(self) -> str:
        return f"Msg({self.key!r}, {self.params!r})"

    def __reduce__(self):            # pickling (st.cache_data) keeps key and params
        return _rebuild_msg, (self.key, self.params)


class LocalizedError(ValueError):
    """A ValueError whose message can be rendered in any language."""

    def __init__(self, key: str, **params):
        self.msg = Msg(key, **params)
        super().__init__(str(self.msg))

    def render(self, lang: str = DEFAULT_LANGUAGE) -> str:
        return self.msg.render(lang)


def render(message, lang: str = DEFAULT_LANGUAGE) -> str:
    """Render a Msg, a LocalizedError, or fall back to str()."""
    if isinstance(message, (Msg, LocalizedError)):
        return message.render(lang)
    return str(message)
