## Why

On the live server (Streamlit Community Cloud, free tier), re-running 100 worlds of the Guided Demo took 105 seconds, against about 20 on a laptop. That is too long to wait for during a presentation.

## What Changes

- The presenter chooses how many stored worlds to re-run: 20, 50 or 100. The default is 20, about 20 seconds online.
- The page says how long each world takes.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `guided-demo`: the size of the live re-run is chosen.

## Impact

`ui/demo_page.py`, its texts (EN, FR), README section 1.
