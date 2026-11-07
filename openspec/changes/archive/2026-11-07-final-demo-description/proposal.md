## Why

The last point to change the demo before the presentation on 1 or 8 December. Section 1 of the README no longer did what the assignment asks: it had grown to a long report on the DiD study, and it did not show the research question analysis, which the author now presents as the project's contribution (`PLANNING_LOG.md`, 2026-11-03; scope pending the professor's confirmation, `docs/SCOPE_CLARIFICATION.md`). The presentation is five minutes of screenshots along one path through the program, and the audience scores the program.

## What Changes

- Section 1 of the README becomes five sentences in the present tense, along one path, each screen and number checked in a browser on 2026-11-07:
  - **Research Question:** an ambiguous question gets a question back, not a method.
  - **Research Question:** the scholarship question is read as causal, with the cutoff labelled an inference.
  - **Method Recommendation:** Regression Discontinuity, and why not difference-in-differences.
  - **Guided Demo:** the stored DiD study and its finding: bias of 47% of the effect, coverage 31.3%, pre-trend test warning in 14.2% of worlds.
- The earlier text moves unchanged to `docs/DEMO_DETAILS.md`, apart from two intervals given to three decimals.

The path keeps the DiD study from the first version of the demo, and puts the question analysis before it.

## Found while checking the path

In a browser, a second edit of a form field was lost: typing a second question put the first one back. The widgets took their default from the value they had set, which changed their identity. Fixed with stable keys (`bound` in `causal_lab/app.py`), for the research question form and the Virtual Lab.

## Capabilities

### Modified Capabilities
- `guided-demo`: the README describes the demo's path.
