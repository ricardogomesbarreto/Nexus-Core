from nexus.security.permissions import PermissionDecision
from nexus.security.risk import RiskLevel


class SecurityPolicy:
    """
    Define como a Nexus deve tratar operações
    de acordo com seu nível de risco.
    """

    def __init__(
        self,
        maximum_allowed_risk: RiskLevel = RiskLevel.LOW,
    ):
        self.maximum_allowed_risk = maximum_allowed_risk

    def evaluate(
        self,
        risk_level: RiskLevel,
    ) -> PermissionDecision:

        if risk_level <= self.maximum_allowed_risk:
            return PermissionDecision.ALLOW

        if risk_level == RiskLevel.MEDIUM:
            return PermissionDecision.CONFIRM

        return PermissionDecision.DENY
