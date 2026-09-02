from nexus.config.settings import settings
from nexus.core.logger import setup_logger
from nexus.database.database import Database
from nexus.events import EventBus, EventType
from nexus.monitoring.health import HealthStatus


class NexusApplication:
    """
    Aplicação principal do Nexus.
    """

    def __init__(self):
        self.logger = setup_logger()

        self.database = Database()

        self.event_bus = EventBus()

        self.health = HealthStatus()

    def initialize(self):
        self.logger.info("Inicializando Nexus Core")

        self.health.core = True
        self.health.configuration = True
        self.health.logger = True

        self.database.initialize()
        self.health.database = True

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
