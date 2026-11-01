## Why

An Impeccable design critique of the app (2026-10-31) scored it 22/40 ("acceptable"). It combined two isolated assessments: a design review, and a run of the detector with browser measurements.

Its five priority issues were:
- empty pages that were dead ends;
- page titles that differed from their sidebar names, and a "Diagnose" shortcut that opened another page;
- an invisible keyboard focus in the sidebar, and text below WCAG AA contrast:
  - captions at 4.2:1;
  - inline code at 2.4:1;
  - the selected tab in the dark theme at 3.8:1;
  - the active-item stripe in the dark theme at 2.2:1;
- emoji as the icon system, and a generic gradient banner;
- charts with off-palette and hard-coded colours.

On 2026-11-01 the user asked for all five to be fixed, with a sober, academic dashboard.

## What Changes

- **Page titles and empty pages.**
  - Every page is titled with its sidebar name.
  - Empty pages state why they are empty. They offer buttons that lead out: open the Virtual Lab, load the Card & Krueger (1994) data, or open the Research Question form.
  - The Research Question form links to its results once it has run.
  - External Data links to Settings while the connectors are off.
  - "Pre-treatment periods" is disabled when the design has none.
- **Sidebar.**
  - Six sections, none with more than four pages: Start, Research design, Data, Analysis, Stress test, Output.
  - Material Symbols icons, bundled with Streamlit, replace the emoji.
  - Keyboard focus is visible.
  - The active page is marked by a background, not a coloured stripe.
  - The language switch has a text label.
- **Dashboard.**
  - A typographic header (title, subtitle, mission) replaces the gradient banner and the capitalised tagline.
  - The guided demo's main finding is shown, computed from the stored simulation study, with a primary "Open the guided demo" button.
  - "Diagnose My Research Design" becomes "Stress-test My Design", since it opens Break My Design.
  - Progress steps are numbered instead of carrying a "Step n" label.
- **Contrast, measured in both themes.**

  | Element | Light | Dark |
  |---|---|---|
  | Captions | 7.7:1 | 9.5:1 |
  | Inline code in captions | 7.5:1 | — |

  The selected tab takes the text colour and is underlined in the primary colour.
- **Readability.** Running text is limited to 78 characters per line.
- **Charts.**
  - One palette throughout.
  - Ordered threat levels use a sequential ramp.
  - Fixed roles have fixed colours: the true effect, the treatment date or cut-off, and reference lines.
  - The chart blue `#4F68DF` keeps 3:1 contrast on both backgrounds.
  - Diagnosis levels no longer rely on coloured dots.
- **Detector.** After the changes, the Impeccable detector finds no anti-pattern at 1440 px or at 390 px. It found one before.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `app-navigation`: sidebar sections, dashboard shortcuts and finding, page titles, empty states, accessibility.

## Impact

- `ui/style.py`, `app.py`, `ui/demo_page.py`, `ui/methods_page.py`, `ui/theory_page.py`, `ui/multidim_page.py`, `ui/estimation_page.py`, `ui/data_sources_page.py`, `.streamlit/config.toml`, and the EN and FR texts.
- `tests/test_app_flows.py` finds buttons by their text instead of their emoji. It has three new tests: page titles, empty-state exits, and the dashboard finding.
