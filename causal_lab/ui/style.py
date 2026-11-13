"""
Look of the app beyond the theme in .streamlit/config.toml: the sidebar's
workflow sections, metric cards, the dashboard header and progress
steps, and the colours of the charts. Colours are translucent where they
must read in the light and the dark theme alike, and every text colour
meets WCAG AA (4.5:1) in both. Nothing is loaded from the network: icons
are the Material Symbols font bundled with Streamlit.
"""
from __future__ import annotations

from html import escape

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# Sidebar sections, in workflow order: (section id, first page of the section).
NAV_SECTIONS = (
    ("start", "dashboard"),
    ("design", "research_question"),
    ("data", "virtual_lab"),
    ("analysis", "estimation"),
    ("stress", "break_my_design"),
    ("output", "code"),
)

# One icon per page, from the Material Symbols set bundled with Streamlit: in the
# sidebar, and on the buttons that lead to the page.
PAGE_ICONS = {
    "dashboard": ":material/home:", "demo": ":material/school:",
    "research_question": ":material/edit_note:", "diagnosis": ":material/troubleshoot:",
    "recommendation": ":material/recommend:", "virtual_lab": ":material/science:",
    "data_sources": ":material/public:", "estimation": ":material/query_stats:",
    "methods": ":material/account_tree:", "theory": ":material/function:",
    "break_my_design": ":material/bolt:", "robustness": ":material/shield:",
    "code": ":material/code:", "report": ":material/description:", "settings": ":material/settings:",
}

# Chart colours: the theme's categorical palette (config.toml), a sequential ramp
# from the primary colour for ordered levels (none -> severe), and fixed roles.
CATEGORICAL = ["#4F68DF", "#E07B39", "#2E9E83", "#C2416B", "#7A5AC8", "#8A94A6"]
SEQUENTIAL = ["#B4C0EC", "#8A9BE0", "#6177D2", "#3F57BC", "#24378A"]
PRIMARY, MUTED = "#4F68DF", "#8A94A6"  # 3.9:1 on the dark and 4.8:1 on the light background
TRUTH = "#2E9E83"           # the known true effect
MARKER = "#C2416B"          # treatment date, cut-off, decision thresholds

pio.templates["causal_lab"] = go.layout.Template(layout=go.Layout(colorway=CATEGORICAL))
pio.templates.default = "plotly+causal_lab"

_BASE_CSS = """
/* Room for the toolbar the online host draws above the page (Fork, GitHub) */
.block-container { max-width: 1200px; padding-top: 4rem; }

/* Running text keeps a readable measure, even in the wide layout */
[data-testid="stMain"] [data-testid="stMarkdownContainer"] > p,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] > ul,
[data-testid="stMain"] [data-testid="stMarkdownContainer"] > ol,
[data-testid="stMain"] [data-testid="stCaptionContainer"] { max-width: 78ch; }
[data-testid="stMain"] [data-testid="stMarkdownContainer"] p { text-wrap: pretty; }

/* Captions: Streamlit draws them at 60% opacity, under 4.5:1 in the light
   theme; inline code in a caption takes the caption's colour. */
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p { color: inherit !important; }
[data-testid="stCaptionContainer"] { opacity: 0.78 !important; }
[data-testid="stCaptionContainer"] code { color: inherit; }

/* Selected tab: the text colour, underlined in the primary colour (the primary
   colour as text is under 4.5:1 on the dark background). */
[data-baseweb="tab-list"] [aria-selected="true"] p { color: inherit; font-weight: 600; }

/* Metrics as cards */
[data-testid="stMetric"] {
  background: rgba(127, 140, 170, 0.07);
  border: 1px solid rgba(127, 140, 170, 0.25);
  border-radius: 0.8rem;
  padding: 0.8rem 1rem;
}
[data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }

/* Button labels wrap instead of being cut with an ellipsis (long French labels) */
[data-testid="stMain"] button [data-testid="stMarkdownContainer"],
[data-testid="stMain"] button [data-testid="stMarkdownContainer"] p {
  white-space: normal !important; text-overflow: clip !important; overflow: visible !important;
}
[data-testid="stMain"] button { height: auto; min-height: 2.5rem; }

::selection { background: rgba(52, 81, 178, 0.28); }

/* Type scale: page title, section, sub-section, each a clear step down
   (Streamlit's defaults, 44, 36 and 28 px, are too close to read as levels). */
[data-testid="stMain"] [data-testid="stHeading"] h1 {
  font-size: 2.2rem; font-weight: 750; letter-spacing: -0.01em; line-height: 1.15; padding-bottom: 0.2rem;
}
[data-testid="stMain"] [data-testid="stHeading"] h2 {
  font-size: 1.5rem; font-weight: 700; line-height: 1.25; padding-top: 1.4rem; margin-top: 0.6rem;
  border-top: 1px solid rgba(127, 140, 170, 0.28);
}
[data-testid="stMain"] [data-testid="stHeading"] h3 { font-size: 1.2rem; font-weight: 650; line-height: 1.3; }

/* The sentence under a page title reads as its lead, not as a footnote. */
[data-testid="stMain"] .stElementContainer:has([data-testid="stHeading"] h1)
  + .stElementContainer [data-testid="stCaptionContainer"] {
  font-size: 1.05rem; line-height: 1.55; opacity: 0.9 !important;
}

/* Tables: figures line up in their columns. */
[data-testid="stDataFrame"], [data-testid="stTable"] { font-variant-numeric: tabular-nums; }

/* Wizard steps: a numbered rail, so the researcher sees where they are. */
.cl-wstep { display: flex; align-items: center; gap: 0.75rem; margin: 1.6rem 0 0.2rem; }
.cl-wstep .cl-n {
  flex: none; width: 2rem; height: 2rem; border-radius: 999px; display: inline-flex;
  align-items: center; justify-content: center; font-weight: 700; font-size: 0.95rem;
  background: #3451B2; color: #FFFFFF; font-variant-numeric: tabular-nums;
}
.cl-wstep h3 { margin: 0; padding: 0; font-size: 1.25rem; font-weight: 650; line-height: 1.3; }
.cl-wstep .cl-of { margin-left: auto; font-size: 0.85rem; font-weight: 600; opacity: 0.75; font-variant-numeric: tabular-nums; }

/* Sidebar brand */
.cl-brand { font-size: 1.15rem; font-weight: 700; letter-spacing: 0.04em; line-height: 1.2; }

/* Sidebar navigation: a list of links, not radio buttons.
   In Streamlit 1.64 each option is a div with data-selected, holding the
   stRadioOption label. (No markup in these comments: st.html sanitizes it.) */
.st-key-nav .stElementContainer,
.st-key-nav [data-testid="stRadio"], .st-key-nav [data-testid="stRadio"] > div { width: 100% !important; }
.st-key-nav [role="radiogroup"] { gap: 2px !important; row-gap: 2px !important; width: 100%; }
.st-key-nav [role="radiogroup"] > div { width: 100%; position: relative; }
.st-key-nav [data-testid="stRadioOption"] {
  width: 100%; margin: 0; padding: 0.38rem 0.6rem; border-radius: 0.5rem; cursor: pointer;
}
.st-key-nav [data-testid="stRadioOption"] > div > div:not([data-testid="stMarkdownContainer"]) { display: none; }
.st-key-nav [data-testid="stRadioOption"] [data-testid="stIconMaterial"] { opacity: 0.72; }
.st-key-nav [data-testid="stRadioOption"]:hover { background: rgba(127, 140, 170, 0.14); }
.st-key-nav [role="radiogroup"] > div[data-selected="true"] > [data-testid="stRadioOption"] {
  background: rgba(79, 104, 223, 0.16); box-shadow: inset 3px 0 0 #4F68DF;
}
.st-key-nav [role="radiogroup"] > div[data-selected="true"] p { font-weight: 650; }
.st-key-nav [role="radiogroup"] > div[data-selected="true"] [data-testid="stIconMaterial"] { opacity: 1; }
/* The radio input itself is hidden: show keyboard focus on its row. */
.st-key-nav [data-testid="stRadioOption"]:has(input:focus-visible) {
  outline: 2px solid #5B74E8; outline-offset: -2px;
}

/* Dashboard header: typographic, no banner */
.cl-head { padding: 0.4rem 0 0.2rem; }
.cl-head h1 {
  font-size: 2.6rem; font-weight: 750; letter-spacing: 0.02em; line-height: 1.1; margin: 0; padding: 0;
}
.cl-head .cl-sub { font-size: 1.2rem; font-weight: 600; margin-top: 0.4rem; }
.cl-head .cl-mission { margin: 0.7rem 0 0; max-width: 64ch; line-height: 1.55; font-size: 1.05rem; }

/* Dashboard: the demo's main finding */
.cl-finding {
  margin: 0.2rem 0 0.4rem; padding: 1rem 1.2rem; border-radius: 0.8rem;
  background: rgba(79, 104, 223, 0.08); border: 1px solid rgba(79, 104, 223, 0.28);
  max-width: 78ch; line-height: 1.55;
}
.cl-finding .cl-finding-title { font-weight: 700; margin-bottom: 0.3rem; }

/* Dashboard progress steps */
.cl-steps-title { font-weight: 700; font-size: 1.05rem; margin: 1.6rem 0 0.6rem; }
.cl-steps { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.8rem; }
@media (max-width: 1180px) { .cl-steps { grid-template-columns: repeat(2, 1fr); } }
.cl-step {
  border: 1px solid rgba(127, 140, 170, 0.3); border-radius: 0.8rem; padding: 0.8rem 1rem;
  display: flex; flex-direction: column; gap: 0.5rem; align-items: flex-start;
}
.cl-step.done { border-color: rgba(46, 158, 131, 0.55); background: rgba(46, 158, 131, 0.06); }
.cl-step .cl-label { font-weight: 600; display: flex; gap: 0.55rem; align-items: baseline; }
.cl-step .cl-n {
  flex: none; width: 1.5rem; height: 1.5rem; border-radius: 999px; display: inline-flex;
  align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 700;
  border: 1px solid rgba(127, 140, 170, 0.6); font-variant-numeric: tabular-nums;
}
.cl-step.done .cl-n { border-color: #2E9E83; background: #2E9E83; color: #FFFFFF; }
.cl-badge {
  display: inline-block; padding: 0.12rem 0.6rem; border-radius: 999px;
  font-size: 0.85rem; font-weight: 600; background: rgba(127, 140, 170, 0.16);
}
.cl-step.done .cl-badge { background: rgba(46, 158, 131, 0.18); }

@media (max-width: 640px) {
  .block-container { padding-top: 3.6rem; }
  .cl-head h1 { font-size: 2rem; }
  .cl-head .cl-sub { font-size: 1.05rem; }
  .cl-head .cl-mission { font-size: 1rem; }
  .cl-step { padding: 0.65rem 0.8rem; }
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
            f'  content: "{text}"; position: absolute; left: 0.6rem; top: -1.2rem;\n'
            f'  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;\n'
            f'  opacity: 0.8; pointer-events: none;\n}}')
    return "\n".join(rules)


def inject(headings: dict[str, str], pages: list[str]) -> None:
    """Add the app's styles; `headings` maps each NAV_SECTIONS id to its label."""
    st.html(f"<style>{_BASE_CSS}\n{_section_css(headings, pages)}</style>")


def brand(title: str) -> None:
    st.html(f'<div class="cl-brand">{escape(title)}</div>')


def header(title: str, subtitle: str, mission: str) -> None:
    st.html(f'<div class="cl-head"><h1>{escape(title)}</h1>'
            f'<div class="cl-sub">{escape(subtitle)}</div><p class="cl-mission">{escape(mission)}</p></div>')


def finding(title: str, text: str) -> None:
    """A short result in a quiet panel; `text` may hold **bold** spans."""
    parts = escape(text).split("**")
    body = "".join(f"<strong>{p}</strong>" if i % 2 else p for i, p in enumerate(parts))
    st.html(f'<div class="cl-finding"><div class="cl-finding-title">{escape(title)}</div>{body}</div>')


def wizard_step(n: int, total: int, title: str) -> None:
    """A wizard step heading: its number in a disc, its name, and "n / total".
    `title` is the translated "Step n — name"; the number is drawn, not repeated."""
    name = title.split(" — ", 1)[-1]
    st.html(f'<div class="cl-wstep"><span class="cl-n" aria-hidden="true">{n}</span>'
            f'<h3>{escape(title if name == title else name)}</h3>'
            f'<span class="cl-of">{n} / {total}</span></div>')


def progress_cards(title: str, steps: list[tuple[str, str, bool, str]]) -> None:
    """One card per workflow step: (step number, name, done, status text)."""
    cards = "".join(
        f'<div class="cl-step {"done" if done else "todo"}">'
        f'<div class="cl-label"><span class="cl-n">{escape(n)}</span><span>{escape(name)}</span></div>'
        f'<span class="cl-badge">{escape(status)}</span></div>'
        for n, name, done, status in steps)
    st.html(f'<div class="cl-steps-title">{escape(title)}</div><div class="cl-steps">{cards}</div>')
