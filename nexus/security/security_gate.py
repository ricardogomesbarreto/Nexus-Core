from dataclasses import dataclass
from typing import Any

from nexus.security.audit import AuditLogger
from nexus.security.permissions import PermissionDecision
from nexus.security.paths import PathSecurity
from nexus.security.policies import SecurityPolicy
from nexus.security.risk import RiskLevel
from nexus.security.tool_permissions import ToolPermissionPolicy


@dataclass(frozen=True)
class SecurityRequest:
    """
    Representa uma solicitação de operação feita
    por algum componente do Nexus.
    """

    action: str
    description: str
    risk_level: RiskLevel
    data: Any = None
    path: str | None = None
    tool_name: str | None = None


@dataclass(frozen=True)
class SecurityResult:
    """
    Resultado da avaliação de segurança.
    """

    decision: PermissionDecision
    request: SecurityRequest
    reason: str


class SecurityGate:
    """
    Camada central de segurança do Nexus.

    Toda operação que possa interagir com o sistema
    deverá passar por este componente.
    """

    def __init__(
        self,
        policy: SecurityPolicy | None = None,
        path_security: PathSecurity | None = None,
        tool_permissions: ToolPermissionPolicy | None = None,
        audit_logger: AuditLogger | None = None,
    ):
        self.policy = policy or SecurityPolicy()

        self.path_security = (
            path_security or PathSecurity()
        )

        self.tool_permissions = (
            tool_permissions
            or ToolPermissionPolicy()
        )

        self.audit_logger = (
            audit_logger
            or AuditLogger()
        )

    def evaluate(
        self,
        request: SecurityRequest,
    ) -> SecurityResult:

        # -------------------------------------------------
        # 1. Verificação da ferramenta
        # -------------------------------------------------

        if request.tool_name is not None:

            if not self.tool_permissions.is_registered(
                request.tool_name
            ):
                return self._deny(
                    request,
                    "Ferramenta não registrada "
                    "na política de segurança.",
                )

            if not self.tool_permissions.is_allowed(
                request.tool_name,
                request.risk_level,
            ):
                return self._deny(
                    request,
                    "O nível de risco solicitado "
                    "excede a permissão da ferramenta.",
                )

        # -------------------------------------------------
        # 2. Verificação do caminho
        # -------------------------------------------------

        if request.path is not None:

            if self.path_security.is_protected(
                request.path
            ):
                return self._deny(
                    request,
                    "Caminho protegido pela política "
                    "de segurança.",
                )

            if not self.path_security.is_allowed(
                request.path
            ):
                return self._deny(
                    request,
                    "Caminho fora da área autorizada "
                    "do Nexus.",
                )

        # -------------------------------------------------
        # 3. Política geral de risco
        # -------------------------------------------------

        decision = self.policy.evaluate(
            request.risk_level
        )

        if decision == PermissionDecision.ALLOW:

            reason = (
                "Operação permitida pela política."
            )

        elif decision == PermissionDecision.CONFIRM:

            reason = (
                "A operação requer confirmação "
                "explícita do usuário."
            )

        else:

            reason = (
                "Operação bloqueada pela política "
                "de segurança."
            )

        result = SecurityResult(
            decision=decision,
            request=request,
            reason=reason,
        )

        self._audit(result)

        return result

    def _deny(
        self,
        request: SecurityRequest,
        reason: str,
    ) -> SecurityResult:

        result = SecurityResult(
            decision=PermissionDecision.DENY,
            request=request,
            reason=reason,
        )

        self._audit(result)

        return result

    def _audit(
        self,
        result: SecurityResult,
    ) -> None:

        request = result.request

        self.audit_logger.record(
            tool_name=request.tool_name or "unknown",
            action=request.action,
            risk_level=request.risk_level.name,
            decision=result.decision.value,
            reason=result.reason,
            path=request.path,
        )
