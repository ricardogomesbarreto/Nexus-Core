"""Ponte entre o worker do modelo e a confirmação na thread da janela."""

from dataclasses import dataclass, field
from queue import Empty, Queue
from threading import Event, Lock
from typing import Callable

from nexus.security import SecurityRequest


@dataclass
class _PendingConfirmation:
    request: SecurityRequest
    completed: Event = field(default_factory=Event)
    approved: bool = False


class DesktopConfirmation:
    """Uma autorização por chamada; fechar a janela recusa as pendentes."""

    def __init__(self):
        self._queue: Queue[_PendingConfirmation] = Queue()
        self._pending: list[_PendingConfirmation] = []
        self._lock = Lock()
        self._closed = False

    def confirm(self, request: SecurityRequest) -> bool:
        pending = _PendingConfirmation(request)
        with self._lock:
            if self._closed:
                return False
            self._pending.append(pending)
            self._queue.put(pending)
        completed = pending.completed.wait(timeout=300)
        with self._lock:
            if not completed:
                pending.completed.set()
            if pending in self._pending:
                self._pending.remove(pending)
            return pending.approved if completed and not self._closed else False

    def process(self, ask_user: Callable[[SecurityRequest], bool]) -> None:
        """Chamado exclusivamente pela thread da interface gráfica."""
        while True:
            try:
                pending = self._queue.get_nowait()
            except Empty:
                break
            with self._lock:
                if pending.completed.is_set() or self._closed:
                    pending.completed.set()
                    continue
            try:
                approved = ask_user(pending.request) is True
            except Exception:
                approved = False
            with self._lock:
                pending.approved = approved and not self._closed
                pending.completed.set()

    def close(self) -> None:
        with self._lock:
            self._closed = True
            for pending in self._pending:
                pending.completed.set()
