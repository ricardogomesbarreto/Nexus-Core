from nexus.tools.base import NexusTool


class ToolRegistry:
    """
    Registro central das ferramentas disponíveis no Nexus.
    """

    def __init__(self):
        self._tools: dict[str, NexusTool] = {}

    def register(self, tool: NexusTool) -> None:
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

    def clear(self) -> None:
        self._tools.clear()
