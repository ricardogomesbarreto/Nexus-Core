from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from nexus.security import RiskLevel


@dataclass(frozen=True)
class ToolResult:
    """
    Resultado da execução de uma ferramenta.
    """

    success: bool
    tool_name: str
    data: Any = None
    error: str | None = None


class NexusTool(ABC):
    """
    Interface base para todas as ferramentas do Nexus.
    """

    name: str = ""
    description: str = ""
    risk_level: RiskLevel = RiskLevel.SAFE

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Executa a ferramenta.
        """
        raise NotImplementedError
