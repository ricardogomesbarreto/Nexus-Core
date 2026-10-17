"""The badge follows OS transitions without launching active Internet checks."""

import os
import subprocess
import time

import pytest

from nexus.desktop.connectivity_indicator import (
    PassiveConnectivityWatcher, passive_internet_status,
)


@pytest.mark.parametrize("nm_state,expected", [
    ("full\n", "online"), ("none\n", "offline"),
    ("limited\n", "offline"), ("portal\n", "offline"),
    ("unknown\n", "unknown"),
])
def test_cached_networkmanager_state_is_bounded(monkeypatch, nm_state, expected):
    def run(command, **kwargs):
        assert command == ["nmcli", "networking", "connectivity"]
        assert kwargs["timeout"] == 2
        assert kwargs["stdin"] is subprocess.DEVNULL
        return subprocess.CompletedProcess(command, 0, nm_state, "")

    monkeypatch.setattr(subprocess, "run", run)
    assert passive_internet_status() == expected


def test_missing_networkmanager_remains_unverified(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: (_ for _ in ()).throw(FileNotFoundError()))
    assert passive_internet_status() == "unknown"


def test_watcher_publishes_only_changes_and_stops():
    states = iter(["offline", "offline", "online", "unknown"])
    published = []
    watcher = PassiveConnectivityWatcher(published.append,
                                         probe=lambda: next(states, "unknown"), interval=0.005)
    watcher.start()
    end = time.monotonic() + 1
    while len(published) < 3 and time.monotonic() < end:
        time.sleep(0.005)
    watcher.stop()
    assert published == ["offline", "online", "unknown"]


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer display Linux")
def test_badge_updates_on_tk_thread_from_queued_state(desktop, caplog):
    import logging
    caplog.set_level(logging.INFO, logger="nexus.desktop_runtime")
    root, _, window, _ = desktop
    assert window.network_badge.cget("text") == "● NÃO VERIFICADO"
    window._network_events.put("online")
    root.update()
    assert window.network_badge.cget("text") == "● ONLINE"
    assert window.network_badge.cget("style") == "Nexus.NetworkOnline.TLabel"
    window._network_events.put("offline")
    root.update()
    assert window.network_badge.cget("text") == "● OFFLINE"
    assert "TESTE-LOCAL evento=rede estado=offline" in caplog.text

    class Health:
        network_online = True
        def runtime_snapshot(self):
            return self

    app = window.app
    app.connectivity_monitor = object()
    app.status = lambda: Health()
    window._refresh_network_status()
    assert window.network_badge.cget("text") == "● ONLINE"


from test_vision_desktop_integration import desktop  # noqa: E402
