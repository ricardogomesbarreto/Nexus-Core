from dataclasses import dataclass


@dataclass
class HealthStatus:
    core: bool = False
    configuration: bool = False
    database: bool = False
    logger: bool = False

    @property
    def ready(self) -> bool:
        return all(
            [
                self.core,
                self.configuration,
                self.database,
                self.logger,
            ]
        )
