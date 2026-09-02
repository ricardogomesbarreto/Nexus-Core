from nexus.security.risk import RiskLevel


class ToolPermissionPolicy:
    """
    Define permissões individuais para as ferramentas
    disponíveis no Nexus.
    """

    def __init__(self):
        self._permissions: dict[str, RiskLevel] = {}

    def register(
        self,
        tool_name: str,
        maximum_risk: RiskLevel,
    ) -> None:
        """
        Registra o nível máximo permitido para uma Tool.
        """

        self._permissions[tool_name] = maximum_risk

    def get_maximum_risk(
        self,
        tool_name: str,
    ) -> RiskLevel | None:
        """
        Retorna o nível máximo permitido para uma Tool.
        """

        return self._permissions.get(tool_name)

    def is_registered(
        self,
        tool_name: str,
    ) -> bool:
        return tool_name in self._permissions

    def is_allowed(
        self,
        tool_name: str,
        requested_risk: RiskLevel,
    ) -> bool:
        """
        Verifica se uma ferramenta está registrada
        e se o risco solicitado está dentro do limite
        definido para ela.
        """

        maximum_risk = self.get_maximum_risk(
            tool_name
        )

        if maximum_risk is None:
            return False

        return requested_risk <= maximum_risk

    def clear(self) -> None:
        self._permissions.clear()
