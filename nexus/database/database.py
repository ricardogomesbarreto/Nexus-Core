from nexus.database.contracts import DatabaseProvider
from nexus.database.errors import DatabaseConnectionError


class Database:
    """
    Serviço de database do Nexus Core.

    O serviço depende exclusivamente do contrato DatabaseProvider
    e não conhece drivers, conexões ou SQL específicos.
    """

    def __init__(
        self,
        provider: DatabaseProvider,
    ):
        self._provider = provider

    @property
    def provider_id(self) -> str:
        return self._provider.provider_id

    def initialize(self) -> None:
        self._provider.initialize()

        if not self._provider.healthcheck():
            raise DatabaseConnectionError(
                "Database provider falhou no healthcheck de inicialização"
            )

    def healthcheck(self) -> bool:
        return self._provider.healthcheck()

    def add_event(
        self,
        event_type: str,
        message: str,
    ) -> None:
        self._provider.add_event(
            event_type,
            message,
        )

    def close(self) -> None:
        self._provider.close()
