import platform

from nexus.security import RiskLevel
from nexus.tools.base import NexusTool, ToolResult
from nexus.tools.contracts import FieldSpec, ToolContract, ValueKind


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

    contract = ToolContract(
        name=name,
        description=description,
        permission=risk_level,
        outputs=tuple(
            FieldSpec(field, ValueKind.STRING)
            for field in ("system", "release", "version", "machine", "processor", "python")
        ),
    )

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
