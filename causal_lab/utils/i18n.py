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
