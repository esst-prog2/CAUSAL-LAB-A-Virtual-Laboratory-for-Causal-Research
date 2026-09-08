# CAUSAL LAB — v0.1 (MVP)

**A Virtual Laboratory for Causal Research**

This is the first working MVP of CAUSAL LAB, implementing the ten
Version 0.1 modules defined in the project specification:

1. Research Question (wizard)
2. Causal Diagnosis Engine
3. Method Recommendation Engine
4. Virtual World (synthetic data generator with known ground truth)
5. Difference-in-Differences estimator
6. Event Study estimator
7. Break My Design (stress-test module)
8. Robustness Engine
9. Code Generator (R / Python / Stata)
10. Bilingual interface (EN / FR)

## Design principle

The software separates the **AI / heuristic reasoning layer** (which
proposes diagnoses and recommendations) from the **statistical engine**
(which produces actual numbers). The reasoning layer never invents a
result — every number shown in the app comes from an actual computation
on actual data (simulated or uploaded).

```
Reasoning layer (diagnosis, recommendation, explanations)
        |
Statistical engine (estimators, simulation, robustness)
        |
Numerical results
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens in your browser at http://localhost:8501

## Project layout

```
causal_lab/
├── app.py                     # Streamlit entry point / page router
├── locales/                   # i18n dictionaries (en.json, fr.json)
├── utils/
│   └── i18n.py                 # translation helper
├── causal_engine/
│   ├── diagnosis.py            # Causal Diagnosis Engine
│   └── recommendation.py       # Method Suitability Score engine
├── simulation_engine/
│   ├── dgp.py                  # Virtual World data-generating process
│   └── monte_carlo.py          # Monte Carlo simulation runner
├── estimators/
│   ├── did.py                  # Two-way fixed effects DiD estimator
│   └── event_study.py          # Event-study (leads/lags) estimator
├── robustness_engine/
│   ├── stress_test.py          # "Break My Design" stress tests
│   └── robustness.py           # Robustness checks (leave-one-out, windows)
├── code_generator/
│   └── generator.py            # R / Python / Stata code generation
└── tests/                      # unit tests for the non-UI logic
```

## What v0.1 does NOT include yet (see spec §48–52)

RCT, Matching, IV, RDD, Synthetic Control, spatial econometrics,
Causal ML / DML, DAG builder with automatic backdoor-path detection,
PDF/Word/LaTeX report export, project persistence (JSON project files),
and the full connectors to external data sources (DHS, ACLED, WorldPop,
etc.). These are planned for v0.2–v1.0 per the roadmap.

## Language

All code, comments and in-app explanatory text are written in English.
The interface labels are already wired through the i18n system
(`locales/en.json`, `locales/fr.json`) so a full French UI can be
completed by filling in `locales/fr.json` without touching any code.
