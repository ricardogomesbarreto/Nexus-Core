from nexus.tools.base import NexusTool
from nexus.tools.contracts import ToolContract


class ToolRegistry:
    """
    Registro central das ferramentas disponíveis no Nexus.
    """

    def __init__(self):
        self._tools: dict[str, NexusTool] = {}

    def register(self, tool: NexusTool) -> None:
        if not isinstance(tool, NexusTool) or not isinstance(tool.contract, ToolContract):
            raise ValueError("Ferramenta precisa de contrato estruturado")
        if (
            tool.contract.name != tool.name
            or tool.contract.description != tool.description
            or tool.contract.permission != tool.risk_level
        ):
            raise ValueError("Contrato incompatível com a ferramenta")
        if tool.name in self._tools:
            raise ValueError(
                f"Tool já registrada: {tool.name}"
            )

        self._tools[tool.name] = tool

    def get(self, name: str) -> NexusTool | None:
        return self._tools.get(name)

    def exists(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> list[str]:
        return sorted(self._tools.keys())

    def contracts(self) -> list[dict]:
        return [self._tools[name].contract.schema() for name in self.list_tools()]

    def clear(self) -> None:
        self._tools.clear()
