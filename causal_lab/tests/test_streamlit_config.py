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


def test_server_listens_on_this_machine_only_and_sends_no_usage_statistics():
    config = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    assert config["server"]["address"] == "localhost"
    assert config["browser"]["gatherUsageStats"] is False
    # Only these two settings are overridden; the others stay at Streamlit's defaults.
    assert config == {"server": {"address": "localhost"}, "browser": {"gatherUsageStats": False}}


def test_the_promises_these_settings_protect_are_still_made():
    # If these texts change, the reason for the settings above must be revisited.
    assert "local" in t("settings.local_mode_note", "en")
    assert "no data is sent anywhere" in t("settings.build_note", "en")


if __name__ == "__main__":
    test_server_listens_on_this_machine_only_and_sends_no_usage_statistics()
    test_the_promises_these_settings_protect_are_still_made()
    print("test_streamlit_config: OK")
