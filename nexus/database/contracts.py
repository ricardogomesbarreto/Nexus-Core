from typing import Protocol


class DatabaseProvider(Protocol):
    """
    Contrato de infraestrutura para providers de database
    do Nexus Core.

    O Core depende deste contrato, não de um driver específico.
    """

    @property
    def provider_id(self) -> str:
        """
        Identificador estável do provider.
        """
        ...

    def initialize(self) -> None:
        """
        Inicializa conexão e infraestrutura mínima do provider.
        """
        ...

    def healthcheck(self) -> bool:
        """
        Verifica se o database está operacional.
        """
        ...

    def add_event(
        self,
        event_type: str,
        message: str,
    ) -> None:
        """
        Persiste um evento estrutural do sistema.
        """
        ...

    def close(self) -> None:
        """
        Libera os recursos mantidos pelo provider.
        """
        ...
