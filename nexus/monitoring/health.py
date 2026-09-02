from dataclasses import dataclass


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

    @property
    def ready(self) -> bool:
        """
        Indica se todos os componentes essenciais
        estão operacionais.
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
