from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from nexus.security import RiskLevel, SensitiveResource
from nexus.tools.contracts import ToolContract


@dataclass(frozen=True)
class ToolResult:
    """
    Resultado da execução de uma ferramenta.
    """

    success: bool
    tool_name: str
    data: Any = None
    error: str | None = None
    error_code: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Retorno estável para clientes sem expor exceções internas."""
        return {
            "success": self.success,
            "tool_name": self.tool_name,
            "data": self.data,
            "error": (
                {"code": self.error_code or "TOOL_ERROR", "message": self.error}
                if not self.success else None
            ),
        }


class NexusTool(ABC):
    """
    Interface base para todas as ferramentas do Nexus.
    """

    name: str = ""
    description: str = ""
    risk_level: RiskLevel = RiskLevel.SAFE
    contract: ToolContract | None = None

    def sensitive_resources(
        self,
        **kwargs,
    ) -> tuple[SensitiveResource, ...]:
        """
        Declara todos os caminhos do host usados por esta execução.

        Ferramentas sem recursos devem retornar explicitamente ().
        A ausência de declaração bloqueia a execução pelo ToolExecutor.
        """
        raise NotImplementedError(
            "A ferramenta precisa declarar seus recursos sensíveis"
        )

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Executa a ferramenta.
        """
        raise NotImplementedError
