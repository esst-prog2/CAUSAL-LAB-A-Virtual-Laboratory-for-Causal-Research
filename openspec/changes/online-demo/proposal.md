## Why

On 2026-10-27 the user asked to put the app online, after the hardening pass (2026-10-27-harden-before-online). Session 7 lists "Put it online: anyone can try it on their own phone", which lets the demo audience use the app.

Two things stood in the way.
- **The app's promises:** it tells every visitor "Your data remain local" and "no data is sent anywhere". On a hosted server those statements are false.
- **The configuration:** Streamlit Community Cloud reads only the repository-root `.streamlit/config.toml`, so the theme in `causal_lab/.streamlit/` would be lost online.

## What Changes

- **`utils/deployment.py`:** it detects the online demo from the Host header the browser sent: any host other than localhost, 127.0.0.1 or [::1] counts as online. No deployment setting has to be remembered.
- **Online notes:** when online, the sidebar, the Settings page and the External Data page say that uploads are processed on the hosting server and that connector requests (ACLED credentials included) pass through it. They point to running the app locally for confidential data. Locally, nothing changes.
- **Repository-root `.streamlit/config.toml`:** the same theme and toolbar, and nothing else; a test keeps the two copies the same.
- **README section 6:** how to deploy, what changes online, and the limits of the free tier.

## Capabilities

### New Capabilities
- `online-demo`

### Modified Capabilities
(none)

## Impact

New `tests/test_deployment.py`; a new check in `tests/test_streamlit_config.py`. The deployment itself is done by the repository owner at share.streamlit.io, which requires their account.
