from nexus.config.settings import settings
from nexus.core.connectivity import ConnectivityManager
from nexus.core.logger import setup_logger
from nexus.core.runtime import RuntimeMode
from nexus.database.database import Database
from nexus.events import EventBus, EventType
from nexus.monitoring.health import HealthStatus
from nexus.security import SecurityGate
from nexus.tools import (
    TerminalSandboxTool,
    ToolExecutor,
    ToolRegistry,
)


class NexusApplication:
    """
    Aplicação principal do Nexus Core.
    """

    def __init__(self):
        self.logger = setup_logger()

        self.database = Database()

        self.event_bus = EventBus()

        self.security_gate = SecurityGate()

        self.tool_registry = ToolRegistry()

        self.tool_registry.register(
            TerminalSandboxTool()
        )

        self.tool_executor = ToolExecutor(
            registry=self.tool_registry,
            security_gate=self.security_gate,
        )

        self.connectivity_manager = ConnectivityManager()

        self.health = HealthStatus()

    def initialize(self):
        self.logger.info("Inicializando Nexus Core")

        self.health.core = True
        self.health.configuration = True
        self.health.logger = True
        self.health.event_bus = True
        self.health.security_gate = True
        self.health.tool_registry = True

        self.database.initialize()
        self.health.database = True

        self.health.terminal_sandbox = (
            self.tool_registry.exists(
                "terminal_sandbox"
            )
        )

        if settings.offline_mode:
            self.health.network_online = False
            self.health.runtime_mode = RuntimeMode.OFFLINE
            self.health.runtime_reason = (
                "Modo offline forçado pela configuração"
            )

            self.event_bus.publish(
                EventType.RUNTIME_MODE_CHANGED,
                {
                    "mode": RuntimeMode.OFFLINE.value,
                    "reason": self.health.runtime_reason,
                },
            )

        else:
            connectivity = self.connectivity_manager.check()

            self.health.network_online = connectivity.online

            if connectivity.online:
                self.health.runtime_mode = RuntimeMode.ONLINE
                self.health.runtime_reason = (
                    "Conectividade externa disponível"
                )

                self.event_bus.publish(
                    EventType.NETWORK_ONLINE,
                    {
                        "endpoint": connectivity.endpoint,
                        "latency_ms": connectivity.latency_ms,
                    },
                )

                self.event_bus.publish(
                    EventType.RUNTIME_MODE_CHANGED,
                    {
                        "mode": RuntimeMode.ONLINE.value,
                        "reason": self.health.runtime_reason,
                    },
                )

            else:
                self.health.runtime_mode = RuntimeMode.OFFLINE
                self.health.runtime_reason = (
                    "Conectividade externa indisponível"
                )

                self.event_bus.publish(
                    EventType.NETWORK_OFFLINE,
                    {
                        "endpoint": connectivity.endpoint,
                        "latency_ms": connectivity.latency_ms,
                    },
                )

                self.event_bus.publish(
                    EventType.RUNTIME_MODE_CHANGED,
                    {
                        "mode": RuntimeMode.OFFLINE.value,
                        "reason": self.health.runtime_reason,
                    },
                )

        self.event_bus.publish(
            EventType.SYSTEM_START,
            {
                "version": settings.version,
                "node": settings.node_name,
            },
        )

        self.database.add_event(
            EventType.SYSTEM_START,
            "Nexus Core inicializado",
        )

        self.logger.info("Nexus Core inicializado")

    def status(self):
        return self.health

    def shutdown(self):
        self.event_bus.publish(
            EventType.SYSTEM_STOP
        )

        self.database.close()

        self.logger.info("Nexus Core finalizado")
