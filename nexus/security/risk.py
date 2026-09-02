from enum import IntEnum


class RiskLevel(IntEnum):
    """
    Níveis de risco das operações executadas pela Nexus.
    """

    SAFE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
