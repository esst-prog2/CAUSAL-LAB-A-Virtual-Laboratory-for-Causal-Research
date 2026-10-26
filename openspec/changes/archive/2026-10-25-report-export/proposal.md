## Why

Report export (PDF/Word/LaTeX) was listed under "Not this term" in README section 3. On 2026-10-25 the user decided to build it anyway, together with the other excluded features, knowing that this departs from the scope decision.

## What Changes

- New package `causal_lab/report_engine/`:
  - `builder.py` runs the engines on the session's data and collects a format-neutral list of headings, paragraphs, tables and code blocks;
  - `render.py` turns that list into Markdown, LaTeX, Word (python-docx) or PDF (reportlab).
- New Report page: choose a format, generate, download, and see a Markdown preview.
- New shared module `causal_lab/utils/session_data.py`, used by both the pages and the report: which data are active, their treatment timing, and the ground truth.
- New dependencies, both pure Python: `python-docx>=1.1` (MIT) and `reportlab>=4.0` (BSD).
- New messages in English and French.

## Capabilities

### New Capabilities
- `report-export`: the project report and its four formats.

### Modified Capabilities
(none)

## Impact

- **Not in the report:** charts (tables only) and the Theoretical Model page.
- **PDF fonts:** the PDF uses the standard Helvetica and Courier fonts, so no font file is added to the repository.
- **LaTeX:** compilation was checked with MiKTeX 2.9; the test skips it where no pdflatex is installed (CI).
- **Tests:** new `tests/test_report.py` (10 tests).
