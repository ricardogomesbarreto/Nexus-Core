"""Safe, opt-in release staging while the desktop app remains running."""
import logging
import os
from threading import Event, Thread

from .manager import autoupdate_enabled, managed_home, stage_latest, UpdateError


class AutoUpdateWatcher:
    """Hourly background download only; installation belongs to launcher."""

    INTERVAL_SECONDS = 3600

    def __init__(self, version: str, *, logger=None, interval: float | None = None):
        self.version = version
        self.logger = logger or logging.getLogger(__name__)
        self.interval = self.INTERVAL_SECONDS if interval is None else interval
        if not 60 <= self.interval <= 86400:
            raise ValueError("Intervalo de atualização inválido.")
        self._stop = Event()
        self._worker: Thread | None = None

    def check_once(self) -> bool:
        home = managed_home()
        if not autoupdate_enabled(home):
            return False
        try:
            release = stage_latest(self.version, home)
            return release is not None
        except (UpdateError, OSError):
            # Network errors never break speech, model, Tk or local data.
            self.logger.info("Consulta de atualização indisponível.")
            return False

    def start(self) -> bool:
        # Only the explicit installer may enable managed updating. Running
        # Python directly or development/CI must not create network workers.
        if (
            os.environ.get("NEXUS_RUNNING_MANAGED") != "1"
            or not autoupdate_enabled()
        ):
            return False
        if self._worker is not None and self._worker.is_alive():
            return True
        self._stop.clear()
        self._worker = Thread(
            target=self._run, name="Nexus-UpdateChecker", daemon=True,
        )
        self._worker.start()
        return True

    def _run(self) -> None:
        while not self._stop.is_set():
            self.check_once()
            if self._stop.wait(self.interval):
                return

    def stop(self) -> None:
        self._stop.set()
        if self._worker is not None:
            self._worker.join(timeout=1)
