"""The privacy notes follow where the app runs (spec: online-demo).

Locally the app promises that data stay on the machine; as the public online
demo it must say instead that uploads are processed on the hosting server.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from streamlit.testing.v1 import AppTest

import utils.deployment as deployment
from utils.i18n import t
from utils.deployment import is_online

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_local_addresses_are_not_online():
    for host in ("localhost:8501", "LOCALHOST", "127.0.0.1:8501", "[::1]:8501", "0.0.0.0:8501", "", None):
        assert not is_online(host), host
    for host in ("causal-lab.streamlit.app", "causal-lab.streamlit.app:443", "192.168.1.20:8501"):
        assert is_online(host), host


def _sidebar_captions(online: bool, lang: str = "en") -> list[str]:
    original = deployment.running_online
    deployment.running_online = lambda: online
    try:
        at = AppTest.from_file(APP, default_timeout=300)
        at.session_state["lang"] = lang
        at.run()
        assert not at.exception
        return [str(c.value) for c in at.sidebar.caption]
    finally:
        deployment.running_online = original


def test_the_sidebar_promise_follows_where_the_app_runs():
    local = " ".join(_sidebar_captions(False))
    assert t("settings.local_mode_note", "en") in local and t("online.sidebar_note", "en") not in local
    online = " ".join(_sidebar_captions(True, "fr"))
    assert t("online.sidebar_note", "fr") in online and t("settings.local_mode_note", "fr") not in online


def test_the_settings_page_no_longer_says_nothing_is_sent_when_online():
    original = deployment.running_online
    deployment.running_online = lambda: True
    try:
        at = AppTest.from_file(APP, default_timeout=300).run()
        at.sidebar.radio(key="page").set_value("settings").run()
        texts = " ".join(str(e.value) for e in [*at.warning, *at.info, *at.caption])
        assert t("online.settings_note", "en") in texts
        assert "no data is sent anywhere" not in texts
    finally:
        deployment.running_online = original


if __name__ == "__main__":
    test_local_addresses_are_not_online()
    test_the_sidebar_promise_follows_where_the_app_runs()
    test_the_settings_page_no_longer_says_nothing_is_sent_when_online()
    print("test_deployment: OK")
