from pathlib import Path

from nexus.security import (
    PathSecurity,
    PermissionDecision,
    RiskLevel,
    SecurityGate,
    SecurityRequest,
)


def check_path(
    gate,
    path,
):
    request = SecurityRequest(
        action="read_file",
        description=f"Testar acesso a {path}",
        risk_level=RiskLevel.SAFE,
        path=str(path),
    )

    result = gate.evaluate(request)

    print()
    print("=" * 60)
    print(f"Caminho:   {path}")
    print(f"Decisão:   {result.decision.value}")
    print(f"Motivo:    {result.reason}")


def main():

    gate = SecurityGate()

    check_path(
        gate,
        Path.home() / "Nexus Core",
    )

    check_path(
        gate,
        Path.home(),
    )

    check_path(
        gate,
        "/etc/passwd",
    )

    check_path(
        gate,
        "/boot",
    )

    check_path(
        gate,
        "/usr/bin",
    )

    check_path(
        gate,
        "/tmp",
    )


if __name__ == "__main__":
    main()
