class FakeDatabase:
    """
    Fake determinístico do serviço Database para testes unitários.

    Não realiza I/O e não depende de PostgreSQL.
    """

    provider_id = "fake"

    def __init__(self):
        self.initialized = False
        self.closed = False
        self.events: list[tuple[str, str]] = []

    def initialize(self) -> None:
        self.initialized = True

    def healthcheck(self) -> bool:
        return self.initialized and not self.closed

    def add_event(
        self,
        event_type: str,
        message: str,
    ) -> None:
        self.events.append(
            (
                event_type,
                message,
            )
        )

    def close(self) -> None:
        self.closed = True
