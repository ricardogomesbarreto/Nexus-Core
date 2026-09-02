from dataclasses import dataclass

from nexus.core.runtime import RuntimeMode


@dataclass
class HealthStatus:
    """
    Representa o estado de saúde dos principais
    componentes do Nexus Core.
    """

    core: bool = False
    configuration: bool = False
    database: bool = False
    logger: bool = False
    event_bus: bool = False
    security_gate: bool = False
    tool_registry: bool = False
    terminal_sandbox: bool = False

    network_online: bool = False
    runtime_mode: RuntimeMode = RuntimeMode.OFFLINE
    runtime_reason: str | None = None

    @property
    def ready(self) -> bool:
        """
        Indica se todos os componentes essenciais
        estão operacionais.

        A conectividade externa não é considerada
        um requisito para o Nexus operar localmente.
        """

        return all(
            [
                self.core,
                self.configuration,
                self.database,
                self.logger,
                self.event_bus,
                self.security_gate,
                self.tool_registry,
                self.terminal_sandbox,
            ]
        )
