from nexus.config.settings import settings
from nexus.agent import AgentPlanner
from nexus.core.connectivity import ConnectivityManager
from nexus.core.connectivity_monitor import ConnectivityMonitor
from nexus.core.logger import setup_logger
from nexus.core.runtime import RuntimeMode
from nexus.core.runtime_state import RuntimeStateController
from nexus.database.database import Database
from nexus.devices import DeviceRegistry
from nexus.events import EventBus, EventType
from nexus.monitoring.health import HealthStatus
from nexus.models.model_factory import (
    build_model_router,
)
from nexus.security import ConfirmationHandler, SecurityGate
from nexus.tools import (
    ListDirectoryTool,
    ReadFileTool,
    FileMetadataTool,
    SystemInfoTool,
    TerminalSandboxTool,
    DesktopWindowInfoTool, DesktopTypeTextTool, DesktopNavigateTool,
    ToolExecutor,
    ToolRegistry,
)


class NexusApplication:
    """
    Aplicação principal do Nexus Core.
    """

    def __init__(
        self,
        database: Database,
        confirmation_handler: ConfirmationHandler | None = None,
    ):
        self.logger = setup_logger()

        self.database = database

        self.event_bus = EventBus()

        # Inert local declarations only: never discover or contact hardware.
        self.device_registry = DeviceRegistry()

        self.security_gate = SecurityGate()

        self.tool_registry = ToolRegistry()

        for tool in (
            SystemInfoTool(), ListDirectoryTool(), ReadFileTool(),
            FileMetadataTool(),
            TerminalSandboxTool(),
            DesktopWindowInfoTool(), DesktopTypeTextTool(), DesktopNavigateTool(),
        ):
            self.tool_registry.register(tool)

        self.tool_executor = ToolExecutor(
            registry=self.tool_registry,
            security_gate=self.security_gate,
            confirmation_handler=confirmation_handler,
        )

        self.connectivity_manager = ConnectivityManager()

        self.connectivity_monitor: ConnectivityMonitor | None = None

        self.health = HealthStatus()

        self.runtime_state = RuntimeStateController()

        self._model_router = None
        self._agent = None

        self._initialized = False
        self._shutdown_complete = False

    @property
    def model_router(self):
        if self._model_router is None:
            self._model_router = (
                build_model_router(
                    settings
                )
            )

        return self._model_router

    @property
    def local_model_client(self):
        return self.model_router.resolve(
            "ollama"
        )

    @property
    def agent(self):
        if self._agent is None:
            self._agent = AgentPlanner(
                model_router=self.model_router,
                registry=self.tool_registry,
                executor=self.tool_executor,
            )
        return self._agent

    def initialize(self):
        if self._initialized:
            raise RuntimeError(
                "NexusApplication já foi inicializada"
            )

        self.logger.info("Inicializando Nexus Core")

        self.health.core = True
        self.health.configuration = True
        self.health.logger = True
        self.health.event_bus = True
        self.health.security_gate = True
        self.health.tool_registry = True
        self.health.model_layer = True

        self.database.initialize()
        self.health.database = True

        self.health.terminal_sandbox = (
            self.tool_registry.exists(
                "terminal_sandbox"
            )
        )

        if settings.offline_mode:
            self.runtime_state = RuntimeStateController(
                initial_mode=RuntimeMode.OFFLINE,
                initial_reason=(
                    "Modo offline forçado pela configuração"
                ),
            )

            self.health.update_runtime(
                network_online=False,
                runtime_mode=self.runtime_state.mode,
                runtime_reason=self.runtime_state.reason,
            )

        else:
            connectivity = (
                self.connectivity_manager.check()
            )

            if connectivity.online:
                self.runtime_state = RuntimeStateController(
                    initial_mode=RuntimeMode.ONLINE,
                    initial_reason=(
                        "Conectividade externa disponível"
                    ),
                )

                self.event_bus.publish(
                    EventType.NETWORK_ONLINE,
                    {
                        "endpoint": connectivity.endpoint,
                        "latency_ms": (
                            connectivity.latency_ms
                        ),
                    },
                )

            else:
                self.runtime_state = RuntimeStateController(
                    initial_mode=RuntimeMode.OFFLINE,
                    initial_reason=(
                        "Conectividade externa indisponível"
                    ),
                )

                self.event_bus.publish(
                    EventType.NETWORK_OFFLINE,
                    {
                        "endpoint": connectivity.endpoint,
                        "latency_ms": (
                            connectivity.latency_ms
                        ),
                    },
                )

            self.health.update_runtime(
                network_online=connectivity.online,
                runtime_mode=self.runtime_state.mode,
                runtime_reason=self.runtime_state.reason,
            )

        self.event_bus.publish(
            EventType.RUNTIME_MODE_CHANGED,
            {
                "mode": self.runtime_state.mode.value,
                "reason": self.runtime_state.reason,
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

        if not settings.offline_mode:
            self.connectivity_monitor = ConnectivityMonitor(
                connectivity_manager=self.connectivity_manager,
                runtime_state=self.runtime_state,
                event_bus=self.event_bus,
                health=self.health,
                initial_network_online=connectivity.online,
                interval=(
                    settings.connectivity_monitor_interval
                ),
                logger=self.logger,
                confirmation_threshold=(
                    settings.connectivity_confirmation_threshold
                ),
            )

            self.connectivity_monitor.start()

        self._initialized = True

        self.logger.info("Nexus Core inicializado")

    def status(self):
        return self.health

    def shutdown(self):
        if self._shutdown_complete:
            return

        if self.connectivity_monitor is not None:
            self.connectivity_monitor.stop()

        self.event_bus.publish(
            EventType.SYSTEM_STOP
        )

        self.database.close()

        self._shutdown_complete = True

        self.logger.info("Nexus Core finalizado")
