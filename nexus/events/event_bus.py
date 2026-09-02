from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable


@dataclass(frozen=True)
class NexusEvent:
    """
    Representa um evento interno do Nexus.
    """

    event_type: str
    data: Any = None
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


EventHandler = Callable[[NexusEvent], None]


class EventBus:
    """
    Barramento interno de eventos do Nexus.

    Permite que diferentes componentes do Nexus
    publiquem e recebam eventos sem depender
    diretamente uns dos outros.
    """

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._lock = RLock()

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """
        Inscreve um handler para determinado tipo de evento.
        """

        with self._lock:
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)

    def unsubscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """
        Remove um handler de determinado tipo de evento.
        """

        with self._lock:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)

    def publish(
        self,
        event_type: str,
        data: Any = None,
    ) -> NexusEvent:
        """
        Publica um evento para todos os handlers inscritos.
        """

        event = NexusEvent(
            event_type=event_type,
            data=data,
        )

        with self._lock:
            handlers = list(self._handlers.get(event_type, []))

        for handler in handlers:
            handler(event)

        return event

    def clear(self) -> None:
        """
        Remove todos os handlers registrados.
        """

        with self._lock:
            self._handlers.clear()

    def handler_count(
        self,
        event_type: str,
    ) -> int:
        """
        Retorna a quantidade de handlers
        registrados para determinado evento.
        """

        with self._lock:
            return len(self._handlers.get(event_type, []))
