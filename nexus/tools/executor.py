from nexus.security import (
    PermissionDecision,
    SecurityGate,
    SecurityRequest,
)

from nexus.tools.base import ToolResult
from nexus.tools.registry import ToolRegistry


class ToolExecutor:
    """
    Executa ferramentas somente após aprovação
    do SecurityGate.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        security_gate: SecurityGate | None = None,
    ):
        self.registry = registry

        self.security_gate = (
            security_gate or SecurityGate()
        )

        self._register_tools_permissions()

    def _register_tools_permissions(self) -> None:
        """
        Registra as ferramentas existentes no Registry
        na política de permissões do SecurityGate.
        """

        for tool_name in self.registry.list_tools():

            tool = self.registry.get(tool_name)

            if tool is None:
                continue

            self.security_gate.tool_permissions.register(
                tool.name,
                tool.risk_level,
            )

    def execute(
        self,
        tool_name: str,
        **kwargs,
    ) -> ToolResult:

        # 1. Localizar ferramenta
        tool = self.registry.get(tool_name)

        if tool is None:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                error=(
                    f"Ferramenta não encontrada: "
                    f"{tool_name}"
                ),
            )

        path = kwargs.get("path")

        # 2. Criar solicitação de segurança
        request = SecurityRequest(
            action=tool.name,
            description=tool.description,
            risk_level=tool.risk_level,
            data=kwargs,
            tool_name=tool.name,
            path=path,
        )

        # 3. Security Gate
        security_result = (
            self.security_gate.evaluate(
                request
            )
        )

        if (
            security_result.decision
            != PermissionDecision.ALLOW
        ):
            return ToolResult(
                success=False,
                tool_name=tool_name,
                error=security_result.reason,
            )

        # 4. Executar ferramenta
        try:
            result = tool.execute(**kwargs)

            # 5. Registrar resultado da execução
            outcome = (
                "SUCCESS"
                if result.success
                else "ERROR"
            )

            reason = (
                "Ferramenta executada com sucesso."
                if result.success
                else (
                    result.error
                    or "A ferramenta retornou erro."
                )
            )

            self.security_gate.audit_logger.record_execution(
                tool_name=tool.name,
                action=tool.name,
                outcome=outcome,
                reason=reason,
                path=path,
            )

            return result

        except Exception as exc:

            self.security_gate.audit_logger.record_execution(
                tool_name=tool.name,
                action=tool.name,
                outcome="EXCEPTION",
                reason=str(exc),
                path=path,
            )

            return ToolResult(
                success=False,
                tool_name=tool_name,
                error=str(exc),
            )
