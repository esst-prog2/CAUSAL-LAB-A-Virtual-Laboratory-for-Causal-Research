## 1. Implementation

- [x] 1.1 Share the active-data logic between the pages and the report (`utils/session_data.py`).
- [x] 1.2 Write the report builder and the four renderers.
- [x] 1.3 Add the Report page and the EN and FR messages, and add python-docx and reportlab to `requirements.txt`.

## 2. Verification

- [x] 2.1 Write `tests/test_report.py`:
  - section content checked against the engines;
  - language, no-data and real-data cases;
  - Markdown and LaTeX escaping;
  - LaTeX compilation;
  - Word headings and tables;
  - PDF validity and character mapping;
  - the Report page generating a download.
- [x] 2.2 Check the PDFs and Word files by extracting their text and reopening them; check the minimum dependency versions.
- [x] 2.3 Add the `report-export` spec. Verify with `openspec validate report-export --strict`.
