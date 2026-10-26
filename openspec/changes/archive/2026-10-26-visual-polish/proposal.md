## Why

The app works, but it still looks like an unstyled Streamlit script:
- red default radio buttons and a "Deploy" button that does nothing for a local app;
- a flat list of 14 pages in the sidebar;
- a dashboard that shows "No / No / 0 / No" in large type.

The demo audience sees only the screen (session 7, "A real interface"). On 2026-10-26 the user asked for a better layout.

## What Changes

- **Theme** (`.streamlit/config.toml`):
  - one indigo accent instead of Streamlit's red;
  - light and dark variants;
  - smaller metric values, chart colours that match the theme, and no "Deploy" button (`toolbarMode = "minimal"`).
  - It uses only fonts bundled with Streamlit: nothing is loaded from the network, so the "data remain local" promise still holds.
- **Sidebar:** the pages are grouped into workflow sections (Start, Data, Analysis, Stress test, Output), with section headings in the interface language. Each page has the icon its title uses, and the selected page is highlighted. The language switch shows "EN" / "FR".
- **Dashboard:**
  - a header block with the title, tagline and mission;
  - four progress cards (research question, diagnosis, recommendations, dataset) marked done or not yet, instead of bare Yes/No metrics.
- **Global styles** (`ui/style.py`): metrics in cards, a readable content width, and spacing that works on a phone.
- **`tests/test_streamlit_config.py`:**
  - it still pins the two privacy settings;
  - it now also checks that the config loads nothing from outside the machine.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `app-navigation`: grouped sidebar sections and dashboard progress cards.

## Impact

UI only: no engine changes. Page ids, widget keys and the sidebar radio key `page` stay the same, so the existing app tests still drive the app.
