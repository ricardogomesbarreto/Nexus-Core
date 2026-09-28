import platform

from nexus.security import RiskLevel
from nexus.tools.base import NexusTool, ToolResult


class SystemInfoTool(NexusTool):
    """
    Obtém informações básicas do sistema operacional.
    """

    name = "system_info"

    description = (
        "Obtém informações básicas do sistema "
        "operacional e hardware."
    )

    risk_level = RiskLevel.SAFE

    def sensitive_resources(self, **kwargs) -> tuple:
        return ()

    def execute(self, **kwargs) -> ToolResult:

        information = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": platform.python_version(),
        }

        return ToolResult(
            success=True,
            tool_name=self.name,
            data=information,
        )
