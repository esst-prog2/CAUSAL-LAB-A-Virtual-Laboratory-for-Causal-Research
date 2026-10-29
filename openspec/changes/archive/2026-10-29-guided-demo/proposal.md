## Why

On 2026-10-29 the user asked for a demo that is rigorous and academic.

The README demo rests on single draws: one world with seed 42, then the same world with severe pre-trends. A single draw is an illustration, not evidence. A methods audience will ask three questions:
- How often does the interval cover the truth?
- How often does the pre-trend test catch the violation?
- Does the Card & Krueger number match the paper, or only its headline?

## What Changes

- **New "Guided Demo" page** (Start section), written like a short methods paper:
  1. the question and the design;
  2. one world each way (live, seed 42);
  3. a simulation study over the five levels of diverging pre-trends, 1,000 worlds each (described below);
  4. a replication of Card & Krueger (1994), Table 3, cell by cell against the published values;
  5. what the demo does not show.
- **The simulation study** reports, following Morris et al. (2019):
  - bias, empirical SE against mean model SE, RMSE, coverage of the 95% CI, rejection of H0: ATT = 0 and pre-trend detection, each with its Monte Carlo SE;
  - coverage among the worlds that pass the pre-trend test (Roth, 2022).
- **`simulation_engine/demo_study.py`:** the study and the replication. `spike/demo_study.py` computes the study and stores every replication (`data/demo_study/results.json`), with seeds, date and versions.
- **Live re-run:** the page re-runs 100 worlds of any level and checks them, value by value, against the stored ones.
- **Text:** every number in the page text comes from the stored study or the engines. Nothing is typed.
- **Bibliography:** Roth (2022) and Morris, White & Crowther (2019) are added, both checked against Crossref.

## Capabilities

### New Capabilities
- `guided-demo`

### Modified Capabilities
(none)

## Impact

New `tests/test_demo_study.py`:
- the replication, cell by cell;
- the stored study recomputed from its seeds;
- the summary statistics checked by hand;
- the claims made in words checked against the stored study;
- the page rendered in EN and FR.
