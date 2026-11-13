# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

The app: Python and Streamlit (`causal_lab/app.py`), deployed on Streamlit Community Cloud from the author's fork. The promo page and the slides: static HTML/CSS, no build step, served by GitHub Pages from `/docs` (author's choice, 2026-11-13).

## Users

Students and researchers in statistics and economics (MSc level) who have a causal question and must choose a method, often with a panel dataset and a treatment date. Secondary readers of the promo page: classmates, the course teacher, and strangers who have never heard of the project.

## Product Purpose

Causal Lab helps a researcher choose and understand a causal design. It reads the research question first, recommends a method only once the question is causal and the form is answered, explains the assumptions, and lets the researcher see on simulated worlds with a known effect where a design breaks. It is an MSc project (ELTE, Advanced Programming), defended in December 2026.

## Positioning

Method-choice tools usually start from a design the student already knows ("do you have a threshold?"). Causal Lab starts from the question as the student wrote it, abstains while that question is unclear, and only then picks a method. It then shows, on a world whose true effect is known, how badly a plausible design can fail. The main contribution, decided by the professor on 2026-11-09, is the difference-in-differences bias study; the question analysis is an extension.

## Operating Context

A student types a research question on the Research Question screen, confirms the form, gets a Method Recommendation, then uses Break My Design, the robustness battery, and the Guided Demo (a stored simulation study). The app is available in English and in French. It is presented at demo days on 1 and 8 December 2026, five minutes, five slides, from a shared computer.

## Capabilities and Constraints

- Eight methods in the recommendation (`METHOD_KEYS` in `causal_lab/causal_engine/recommendation.py`).
- Never describe the app as establishing causal identification: identification rests on assumptions data can sometimes refute and never prove.
- No numerical credibility score on methods; the order is argued.
- Wherever the question analyser is presented, its numbers come together as `AGENTS.md` lists them, never one alone.
- The live app serves the fork's `main`; it is not called up to date until the author has synchronised and rebooted it.

## Brand Commitments

Name: Causal Lab. Author: Thierry Z. Barhame, MSc Statistics and Data Analytics, ELTE. Voice: plain, exact, every number with its source, failures reported alongside successes. No logo exists.

## Evidence on Hand

- The DiD simulation study: 4 threats × 5 levels × 1,000 worlds, every replication with its seed (`causal_lab/data/demo_study/results.json`, `docs/DEMO_DETAILS.md`).
- Four frozen evaluations of the question analyser on 230 published article titles (`docs/evaluation/`).
- The test suite, run in CI on every push and pull request (`.github/workflows/`).
- The demo path (`README.md`, section 1).
- No user testimonials, no user-test results, and no second-rater agreement exist yet: none may be invented.

## Product Principles

1. Ask before answering: no method for a question the app does not understand.
2. Show the failure, not only the success: a design is judged on worlds where the truth is known.
3. Every number has a source a reader can open.
4. The app helps choose and understand a design; it never claims to prove causation.
