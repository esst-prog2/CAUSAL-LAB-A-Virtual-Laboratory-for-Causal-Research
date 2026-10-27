## Why

Before putting the app online (user request, 2026-10-27), every entry point was fed odd but plausible input. Online, any visitor can send any file.

The inputs:
- 19 panels through the CSV upload, each followed through every analysis page and the report;
- odd column mappings and tiny files through the six Causal Methods;
- odd files through the Theoretical Model page;
- hand-edited project files.

The app was also crawled in a real browser, in EN and FR, watching for console errors, exceptions and requests to other hosts. That crawl found none.

## What Changes

- **Upload:** rows with a missing unit, period or outcome are left out, with a message giving their number. Before, empty Y cells crashed Estimation, Break My Design, Robustness and the report.
- **Causal Methods:**
  - a mapped column that is entirely empty is refused by name;
  - IV refuses data with no residual degree of freedom (it crashed with a division by zero);
  - the RCT balance check is N/A on too few rows (statsmodels raised an error);
  - an unexpected library error is shown as a translated message with one line of technical detail, instead of raw library text or a crash.
- **Opening a project:** its panels are checked like an uploaded CSV, so a hand-edited file cannot bypass the upload checks.
- **Shared server:**
  - the cached results are bounded (16 per function);
  - `app.py` no longer rebinds the imported `style` module inside the Break My Design page.
- **Layout:** button labels wrap instead of being cut with "…". Four French dashboard buttons were cut at 1100 px.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `real-world-data-upload`: incomplete rows are left out.
- `project-persistence`: opened panels are validated.
- `causal-methods-lab`: empty columns are refused, and unexpected errors are translated.

## Impact

`tests/test_hardening.py` adds one regression test per finding. 6 of 6 mutants are caught.
