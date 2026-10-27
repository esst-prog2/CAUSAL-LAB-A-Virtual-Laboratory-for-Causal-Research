"""The Streamlit settings keep the promises the app makes to its user.

The sidebar says "Your data remain local", the Settings page says "no data is
sent anywhere", and the README opens the app at http://localhost:8501.
Streamlit's defaults contradict both: it listens on every network interface
and sends browser usage statistics to Streamlit. Checked by hand on
2026-10-20: with the default, the server listened on 0.0.0.0:8501; with this
file, on 127.0.0.1 only, and was unreachable from the machine's LAN address.
"""
import sys
import tomllib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.i18n import t

APP_DIR = Path(__file__).resolve().parent.parent
CONFIG = APP_DIR / ".streamlit" / "config.toml"
ONLINE_CONFIG = APP_DIR.parent / ".streamlit" / "config.toml"     # read by Streamlit Community Cloud


def test_server_listens_on_this_machine_only_and_sends_no_usage_statistics():
    config = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    # Server and browser: only these two settings are overridden.
    assert config["server"] == {"address": "localhost"}
    assert config["browser"] == {"gatherUsageStats": False}
    # Everything else is appearance: no toolbar, and the theme.
    assert set(config) == {"server", "browser", "client", "theme"}
    assert config["client"] == {"toolbarMode": "minimal"}


def _values(node):
    if isinstance(node, dict):
        for value in node.values():
            yield from _values(value)
    elif isinstance(node, list):
        for value in node:
            yield from _values(value)
    else:
        yield node


def test_the_theme_loads_nothing_from_the_network():
    # A font or image given by URL would make every visitor's browser fetch it,
    # contradicting "no data is sent anywhere". Only bundled fonts are used.
    config = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    assert not [v for v in _values(config) if isinstance(v, str) and "://" in v]
    assert "font" not in config["theme"] and "fontFaces" not in config["theme"]


def test_the_promises_these_settings_protect_are_still_made():
    # If these texts change, the reason for the settings above must be revisited.
    assert "local" in t("settings.local_mode_note", "en")
    assert "no data is sent anywhere" in t("settings.build_note", "en")



def test_the_online_demo_looks_the_same_and_loads_nothing_from_the_network():
    # Community Cloud reads only the repository-root config. It must give the
    # online demo the same appearance, and add nothing else: no server or
    # browser settings (the host sets those) and no URL.
    app = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    online = tomllib.loads(ONLINE_CONFIG.read_text(encoding="utf-8"))
    assert set(online) == {"client", "theme"}
    assert online["client"] == app["client"] and online["theme"] == app["theme"]
    assert not [v for v in _values(online) if isinstance(v, str) and "://" in v]


if __name__ == "__main__":
    test_server_listens_on_this_machine_only_and_sends_no_usage_statistics()
    test_the_theme_loads_nothing_from_the_network()
    test_the_online_demo_looks_the_same_and_loads_nothing_from_the_network()
    test_the_promises_these_settings_protect_are_still_made()
    print("test_streamlit_config: OK")
