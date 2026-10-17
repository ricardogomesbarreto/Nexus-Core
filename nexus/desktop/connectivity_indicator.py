"""Passive Internet indicator for the Ubuntu desktop.

NetworkManager already tracks connectivity. Query its last known state; never
request a fresh check or contact an endpoint from the forced offline runtime.
"""

import subprocess
from threading import Event, Thread
from typing import Callable


def passive_internet_status() -> str:
    """Return online, offline or unknown without initiating a network probe."""
    try:
        result = subprocess.run(
            ["nmcli", "networking", "connectivity"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            timeout=2, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    if result.returncode != 0:
        return "unknown"
    state = result.stdout.strip().lower()
    if state == "full":
        return "online"
    if state in ("none", "limited", "portal"):
        return "offline"
    return "unknown"


class PassiveConnectivityWatcher:
    """Poll the OS state off the Tk thread and publish transitions only."""

    def __init__(self, publish: Callable[[str], None], *,
                 probe: Callable[[], str] = passive_internet_status,
                 interval: float = 10.0):
        self.publish = publish
        self.probe = probe
        self.interval = interval
        self._stop = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = Thread(target=self._run, name="Nexus-DesktopConnectivity", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        previous = None
        while not self._stop.is_set():
            try:
                state = self.probe()
            except Exception:
                state = "unknown"
            if state not in ("online", "offline", "unknown"):
                state = "unknown"
            if state != previous and not self._stop.is_set():
                self.publish(state)
                previous = state
            self._stop.wait(self.interval)
