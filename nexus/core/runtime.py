from dataclasses import dataclass
from enum import Enum


class RuntimeMode(str, Enum):
    """
    Modos de operação do Nexus Core.
    """

    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"


@dataclass
class RuntimeStatus:
    """
    Representa o estado atual de execução do Nexus Core.
    """

    mode: RuntimeMode = RuntimeMode.OFFLINE
    reason: str | None = None
