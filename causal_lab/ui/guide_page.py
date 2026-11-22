"""
Method Guide page: what each design estimates, what it rests on, what Causal
Lab does with it, when it fails, and its key readings.

The explanations are long-form text, one Markdown file per design and
language, in locales/guide/<lang>/<method>.md (a test keeps both languages
complete). The readings are indicative, for whoever wants to read further:
reference books and peer-reviewed journal articles from utils/references.py
(GENERAL_READINGS, METHOD_READINGS), each checked against Crossref or, for a
book without a DOI, its ISBN record.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Callable

import streamlit as st

from utils.references import GENERAL_READINGS, METHOD_READINGS, REFERENCES, reference_list

GUIDE_DIR = Path(__file__).resolve().parent.parent / "locales" / "guide"
# The eight designs of the recommendation, in its order, then double machine learning.
GUIDE_METHODS = ("rct", "rdd", "did", "event_study", "synthetic_control", "iv", "its", "matching", "dml")


@lru_cache(maxsize=None)
def guide_text(method: str, lang: str) -> str:
    return (GUIDE_DIR / lang / f"{method}.md").read_text(encoding="utf-8")


def _linked(entry: str, doi: str) -> str:
    """An APA entry with its DOI as a Markdown link."""
    url = f"https://doi.org/{doi}"
    return entry.replace(url, f"[{url}]({url})") if doi else entry


def _entries(keys) -> str:
    """APA entries of `keys` as a Markdown list, DOIs as links."""
    doi = {REFERENCES[k].full(): REFERENCES[k].doi for k in keys}
    return "\n".join(f"- {_linked(entry, doi[entry])}" for entry in reference_list(keys))


def render(L: Callable[[str], str], lang: str) -> None:
    st.caption(L("guide.intro"))
    with st.expander(L("guide.general")):
        st.markdown(_entries(GENERAL_READINGS))
    method = st.selectbox(L("guide.choose"), GUIDE_METHODS, format_func=lambda m: L(f"method.{m}"),
                          key="guide_method")
    st.header(L(f"method.{method}"), anchor=False)
    with st.container(key="guide"):        # its section titles sit one step under the design's name
        st.markdown(guide_text(method, lang))

    st.subheader(L("guide.readings"), anchor=False)
    st.caption(L("guide.readings_note"))
    keys = METHOD_READINGS[method]
    books = [k for k in keys if REFERENCES[k].kind == "book"]
    articles = [k for k in keys if REFERENCES[k].kind == "article"]
    if books:
        st.markdown(f"**{L('guide.books')}**")
        st.markdown(_entries(books))
    st.markdown(f"**{L('guide.articles')}**")
    st.markdown(_entries(articles))
