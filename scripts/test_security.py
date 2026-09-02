from nexus.security import (
    SecurityGate,
    SecurityRequest,
    RiskLevel,
)


def show_operation(
    gate,
    action,
    description,
    risk,
):
    request = SecurityRequest(
        action=action,
        description=description,
        risk_level=risk,
    )

    result = gate.evaluate(request)

    print()
    print("=" * 60)
    print(f"Ação:       {request.action}")
    print(f"Descrição:  {request.description}")
    print(f"Risco:      {request.risk_level.name}")
    print(f"Decisão:    {result.decision.value}")
    print(f"Motivo:     {result.reason}")


def main():
    gate = SecurityGate()

    show_operation(
        gate,
        "open_browser",
        "Abrir navegador",
        RiskLevel.LOW,
    )

    show_operation(
        gate,
        "move_file",
        "Mover arquivo",
        RiskLevel.MEDIUM,
    )

    show_operation(
        gate,
        "modify_system",
        "Modificar configuração do sistema",
        RiskLevel.HIGH,
    )

    show_operation(
        gate,
        "delete_system",
        "Excluir arquivos críticos do sistema",
        RiskLevel.CRITICAL,
    )


if __name__ == "__main__":
    main()
