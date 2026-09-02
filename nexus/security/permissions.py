from enum import Enum


class PermissionDecision(str, Enum):
    """
    Decisão tomada pelo Security Gate.
    """

    ALLOW = "ALLOW"
    CONFIRM = "CONFIRM"
    DENY = "DENY"
