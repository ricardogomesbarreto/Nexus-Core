from nexus.security import (
    ConfirmationHandler,
    PermissionDecision,
    SecurityGate,
    SecurityRequest,
    SensitiveResource,
)

from nexus.tools.base import ToolResult
from nexus.tools.contracts import ContractViolation
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
        confirmation_handler: ConfirmationHandler | None = None,
    ):
        self.registry = registry

        self.security_gate = (
            security_gate or SecurityGate()
        )
        self.confirmation_handler = confirmation_handler

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
                tool.contract.permission,
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
                error_code="NOT_FOUND",
            )

        try:
            parameters = tool.contract.validate_inputs(kwargs)
        except ContractViolation as exc:
            reason = str(exc)
            self._audit_contract_denial(tool, reason)
            return ToolResult(
                False, tool_name, error=reason, error_code="INVALID_INPUT"
            )

        try:
            expected_resources = tool.contract.expected_resources(parameters)
            resources = tool.sensitive_resources(**parameters)
            if (
                not isinstance(resources, tuple)
                or any(
                    not isinstance(resource, SensitiveResource)
                    for resource in resources
                )
                or resources != expected_resources
            ):
                raise ValueError("Declaração de recursos inválida")
        except Exception:
            reason = "Recursos sensíveis não declarados ou inválidos."
            self._audit_contract_denial(tool, reason)
            return ToolResult(
                success=False,
                tool_name=tool_name,
                error=reason,
                error_code="INVALID_RESOURCES",
            )

        # 2. Criar solicitação de segurança
        request = SecurityRequest(
            action=tool.name,
            description=tool.description,
            risk_level=tool.contract.permission,
            data=parameters,
            tool_name=tool.name,
            resources=resources,
        )

        audit_path = self.security_gate.audit_path(request)

        # 3. Security Gate
        security_result = (
            self.security_gate.evaluate(
                request
            )
        )

        if security_result.decision == PermissionDecision.CONFIRM:
            if self.confirmation_handler is None:
                self._audit_confirmation(request, "UNAVAILABLE")
                return ToolResult(
                    success=False,
                    tool_name=tool_name,
                    error=security_result.reason,
                    error_code="CONFIRMATION_REQUIRED",
                )

            try:
                approved = self.confirmation_handler.confirm(request)
            except Exception:
                self._audit_confirmation(request, "ERROR")
                return ToolResult(
                    success=False,
                    tool_name=tool_name,
                    error="Não foi possível obter confirmação do usuário.",
                    error_code="CONFIRMATION_ERROR",
                )

            if approved is not True:
                self._audit_confirmation(request, "REJECTED")
                return ToolResult(
                    success=False,
                    tool_name=tool_name,
                    error="Operação não autorizada pelo usuário.",
                    error_code="CONFIRMATION_REJECTED",
                )

            # A autorização vale somente para esta chamada. Revalida os
            # recursos e a política após o tempo gasto na confirmação.
            try:
                current_resources = tool.sensitive_resources(**parameters)
            except Exception:
                current_resources = None

            if current_resources != expected_resources:
                self._audit_confirmation(request, "INVALIDATED")
                return ToolResult(
                    success=False,
                    tool_name=tool_name,
                    error="Recursos alterados durante a confirmação.",
                    error_code="RESOURCES_CHANGED",
                )

            rechecked = self.security_gate.evaluate(request)
            if rechecked.decision != PermissionDecision.CONFIRM:
                self._audit_confirmation(request, "INVALIDATED")
                return ToolResult(
                    success=False,
                    tool_name=tool_name,
                    error="Autorização invalidada pela política de segurança.",
                    error_code="POLICY_CHANGED",
                )

            self._audit_confirmation(request, "APPROVED")

        elif security_result.decision != PermissionDecision.ALLOW:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                error=security_result.reason,
                error_code="DENIED",
            )

        # 4. Executar ferramenta
        try:
            result = tool.execute(**parameters)

            try:
                self._validate_result(tool, result)
            except ContractViolation as exc:
                self.security_gate.audit_logger.record_execution(
                    tool_name=tool.name,
                    action=tool.name,
                    outcome="INVALID_RESULT",
                    reason=str(exc),
                    path=audit_path,
                )
                return ToolResult(
                    False,
                    tool_name,
                    error="Resultado da ferramenta não obedece ao contrato.",
                    error_code="INVALID_RESULT",
                )

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
                path=audit_path,
            )

            return result

        except Exception as exc:

            self.security_gate.audit_logger.record_execution(
                tool_name=tool.name,
                action=tool.name,
                outcome="EXCEPTION",
                reason=str(exc),
                path=audit_path,
            )

            return ToolResult(
                success=False,
                tool_name=tool_name,
                error=str(exc),
                error_code="EXECUTION_ERROR",
            )

    def _audit_contract_denial(self, tool, reason: str) -> None:
        self.security_gate.audit_logger.record(
            tool_name=tool.name,
            action=tool.name,
            risk_level=tool.contract.permission.name,
            decision=PermissionDecision.DENY.value,
            reason=reason,
        )

    @staticmethod
    def _validate_result(tool, result) -> None:
        if not isinstance(result, ToolResult) or type(result.success) is not bool:
            raise ContractViolation("Tipo de resultado inválido.")
        if result.tool_name != tool.name:
            raise ContractViolation("Resultado pertence a outra ferramenta.")
        if result.success and result.error is not None:
            raise ContractViolation("Resultado de sucesso contém erro.")
        if not result.success and (
            not isinstance(result.error, str) or not result.error.strip()
        ):
            raise ContractViolation("Resultado de falha sem mensagem de erro.")
        if result.error_code is not None and (
            not isinstance(result.error_code, str)
            or not result.error_code.isidentifier()
        ):
            raise ContractViolation("Código de erro inválido.")
        if result.success or result.data is not None:
            tool.contract.validate_output(result.data)

    def _audit_confirmation(
        self,
        request: SecurityRequest,
        outcome: str,
    ) -> None:
        self.security_gate.audit_logger.record(
            tool_name=request.tool_name or "unknown",
            action=request.action,
            risk_level=request.risk_level.name,
            decision=PermissionDecision.CONFIRM.value,
            reason="Resultado da confirmação humana.",
            path=self.security_gate.audit_path(request),
            outcome=outcome,
        )
