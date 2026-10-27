"""
Look of the app beyond the theme in .streamlit/config.toml: the sidebar's
workflow sections, metric cards, and the dashboard header and progress
cards. Colours are translucent so the same rules read well in the light
and the dark theme. Nothing is loaded from the network.
"""
from __future__ import annotations

from html import escape

import streamlit as st

# Sidebar sections, in workflow order: (section id, first page of the section).
NAV_SECTIONS = (
    ("start", "dashboard"),
    ("data", "virtual_lab"),
    ("analysis", "estimation"),
    ("stress", "break_my_design"),
    ("output", "code"),
)

# The icon each page's title uses, repeated in the sidebar.
PAGE_ICONS = {
    "dashboard": "🔬", "research_question": "📝", "diagnosis": "🧠", "recommendation": "🧪",
    "virtual_lab": "🧫", "data_sources": "🌍", "estimation": "📈", "methods": "🧭", "theory": "🧮",
    "break_my_design": "💥", "robustness": "🧯", "code": "💻", "report": "📄", "settings": "⚙️",
}

_BASE_CSS = """
.block-container { max-width: 1200px; padding-top: 2.6rem; }

/* Metrics as cards */
[data-testid="stMetric"] {
  background: rgba(127, 140, 170, 0.07);
  border: 1px solid rgba(127, 140, 170, 0.25);
  border-radius: 0.8rem;
  padding: 0.8rem 1rem;
}
[data-testid="stMetricLabel"] { opacity: 0.8; }

/* Button labels wrap instead of being cut with an ellipsis (long French labels) */
[data-testid="stMain"] button [data-testid="stMarkdownContainer"],
[data-testid="stMain"] button [data-testid="stMarkdownContainer"] p {
  white-space: normal !important; text-overflow: clip !important; overflow: visible !important;
}
[data-testid="stMain"] button { height: auto; min-height: 2.5rem; }

/* Sidebar navigation: a list of links, not radio buttons.
   In Streamlit 1.64 each option is a div with data-selected, holding the
   stRadioOption label. (No markup in these comments: st.html sanitizes it.) */
.st-key-nav [role="radiogroup"] { gap: 1px !important; row-gap: 1px !important; }
.st-key-nav [role="radiogroup"] > div { width: 100%; position: relative; }
.st-key-nav [data-testid="stRadioOption"] {
  width: 100%; margin: 0; padding: 0.32rem 0.6rem; border-radius: 0.5rem; cursor: pointer;
}
.st-key-nav [data-testid="stRadioOption"] > div > div:not([data-testid="stMarkdownContainer"]) { display: none; }
.st-key-nav [data-testid="stRadioOption"]:hover { background: rgba(127, 140, 170, 0.14); }
.st-key-nav [role="radiogroup"] > div[data-selected="true"] > [data-testid="stRadioOption"] {
  background: rgba(52, 81, 178, 0.14); box-shadow: inset 3px 0 0 #3451B2;
}
.st-key-nav [role="radiogroup"] > div[data-selected="true"] p { font-weight: 600; }

/* Dashboard header */
.cl-hero {
  padding: 1.7rem 1.9rem; border-radius: 1rem; color: #FFFFFF;
  background: linear-gradient(135deg, #2B3F94 0%, #3451B2 55%, #5B3FB8 100%);
}
.cl-hero .cl-title { font-size: 2.5rem; font-weight: 800; letter-spacing: 0.02em; line-height: 1.1; }
.cl-hero .cl-sub { font-size: 1.25rem; font-weight: 600; margin-top: 0.35rem; opacity: 0.95; }
.cl-hero .cl-tag {
  margin-top: 0.9rem; font-size: 0.82rem; font-weight: 700;
  letter-spacing: 0.12em; text-transform: uppercase; opacity: 0.8;
}
.cl-hero .cl-mission { margin-top: 0.6rem; max-width: 62ch; line-height: 1.5; opacity: 0.95; }

/* Dashboard progress cards */
.cl-steps-title { font-weight: 700; margin: 1.6rem 0 0.6rem; }
.cl-steps { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.8rem; }
@media (max-width: 1180px) { .cl-steps { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 520px) { .cl-steps { grid-template-columns: 1fr; } }
.cl-step {
  border: 1px solid rgba(127, 140, 170, 0.3); border-radius: 0.8rem; padding: 0.85rem 1rem;
}
.cl-step.done { border-color: rgba(46, 158, 131, 0.55); background: rgba(46, 158, 131, 0.06); }
.cl-step .cl-n { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.6; }
.cl-step .cl-label { font-weight: 600; margin: 0.2rem 0 0.55rem; }
.cl-badge {
  display: inline-block; padding: 0.12rem 0.6rem; border-radius: 999px;
  font-size: 0.8rem; font-weight: 600; background: rgba(127, 140, 170, 0.16);
}
.cl-step.done .cl-badge { background: rgba(46, 158, 131, 0.18); color: #2E9E83; }

@media (max-width: 640px) {
  .block-container { padding-top: 3.2rem; }
  .cl-hero { padding: 1.2rem 1.2rem; }
  .cl-hero .cl-title { font-size: 1.9rem; }
  .cl-hero .cl-sub { font-size: 1.05rem; }
}
"""


def _section_css(headings: dict[str, str], pages: list[str]) -> str:
    """Headings above the first page of each sidebar section."""
    rules = []
    for section, first_page in NAV_SECTIONS:
        n = pages.index(first_page) + 1
        text = headings[section].replace("\\", "\\\\").replace('"', '\\"')
        rules.append(
            f'.st-key-nav [role="radiogroup"] > div:nth-child({n}) {{ margin-top: {1.5 if n > 1 else 1.1}rem; }}\n'
            f'.st-key-nav [role="radiogroup"] > div:nth-child({n})::before {{\n'
            f'  content: "{text}"; position: absolute; left: 0.6rem; top: -1.15rem;\n'
            f'  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;\n'
            f'  opacity: 0.55; pointer-events: none;\n}}')
    return "\n".join(rules)


def inject(headings: dict[str, str], pages: list[str]) -> None:
    """Add the app's styles; `headings` maps each NAV_SECTIONS id to its label."""
    st.html(f"<style>{_BASE_CSS}\n{_section_css(headings, pages)}</style>")


def hero(title: str, subtitle: str, tagline: str, mission: str) -> None:
    st.html(f'<div class="cl-hero"><div class="cl-title">{escape(title)}</div>'
            f'<div class="cl-sub">{escape(subtitle)}</div><div class="cl-tag">{escape(tagline)}</div>'
            f'<div class="cl-mission">{escape(mission)}</div></div>')


def progress_cards(title: str, steps: list[tuple[str, str, bool, str]]) -> None:
    """One card per workflow step: (step label, name, done, status text)."""
    cards = "".join(
        f'<div class="cl-step {"done" if done else "todo"}"><div class="cl-n">{escape(n)}</div>'
        f'<div class="cl-label">{escape(name)}</div><span class="cl-badge">{escape(status)}</span></div>'
        for n, name, done, status in steps)
    st.html(f'<div class="cl-steps-title">{escape(title)}</div><div class="cl-steps">{cards}</div>')
