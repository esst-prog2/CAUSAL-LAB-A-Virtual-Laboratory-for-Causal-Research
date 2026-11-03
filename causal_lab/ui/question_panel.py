"""
The analysis of the research question, shown on the Research Question form
(as the question is written) and at the top of the Recommendation page:
each element of the question's causal structure, whether it is stated,
inferred or unknown, the follow-up questions, and what the question implies
for the form.
"""
from __future__ import annotations

import streamlit as st

from causal_engine.question_analysis import ELEMENTS, QuestionAnalysis
from ui.page_text import F, R

# Fields of the form the question can imply, with how their value is shown.
IMPLIED_FIELDS = {"assignment_mechanism": "wizard.assignment_mechanism", "treatment_timing": "wizard.treatment_timing",
                  "n_treated_units": "wizard.n_treated", "instrument": "wizard.instrument"}


def _differences(analysis: QuestionAnalysis, design) -> dict:
    return {f: v for f, v in analysis.inferred.items() if f in IMPLIED_FIELDS and getattr(design, f) != v}


def _apply(analysis: QuestionAnalysis) -> None:
    design = st.session_state.design
    changed = _differences(analysis, design)
    for name, value in changed.items():
        setattr(design, name, value)
    st.session_state.design = design
    st.session_state.qa_applied = list(changed)


def render(analysis: QuestionAnalysis | None, design, L, editable: bool = False) -> None:
    st.subheader(L("qa.title"))
    if analysis is None:
        st.info(L("qa.no_question"))
        return
    st.caption(L("qa.intro"))
    # A Markdown table, so that long inferences wrap instead of being cut.
    lines = [f"| {L('qa.col.element')} | {L('qa.col.status')} | {L('qa.col.analysis')} |", "|---|---|---|"]
    for name in ELEMENTS:
        element = analysis.elements[name]
        text = R(element.text) if element.text else f"*{L('qa.unknown')}*"
        lines.append(f"| **{L(f'qa.element.{name}')}** | {L(f'qa.status.{element.status}')} | "
                     f"{text.replace('|', '/')} |")
    st.markdown("\n".join(lines))
    if analysis.blocking:
        for reason in analysis.blocking:
            st.warning(R(reason))
    if analysis.follow_up:
        st.markdown(f"**{L('qa.follow_up')}**")
        st.markdown("\n".join(f"{i}. {R(q)}" for i, q in enumerate(analysis.follow_up, start=1)))
    differences = _differences(analysis, design)
    if differences:
        fields = "; ".join(F("qa.difference", field=L(IMPLIED_FIELDS[f]), question=L(f"opt.{v}"),
                               form=L(f"opt.{getattr(design, f)}")) for f, v in differences.items())
        st.caption(F("qa.form_differs", fields=fields))
        if editable:
            st.button(L("qa.apply"), icon=":material/input:", on_click=_apply, args=(analysis,), key="qa_apply")
    applied = st.session_state.pop("qa_applied", None) if editable else None
    if applied:
        st.success(F("qa.applied", fields=", ".join(L(IMPLIED_FIELDS[f]) for f in applied)))
