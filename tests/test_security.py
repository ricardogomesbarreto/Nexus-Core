from nexus.security import (
    PermissionDecision,
    RiskLevel,
    SecurityGate,
    SecurityRequest,
)


def create_request(
    action: str,
    risk: RiskLevel,
):
    return SecurityRequest(
        action=action,
        description=f"Teste: {action}",
        risk_level=risk,
    )


def test_safe_operation_is_allowed():
    gate = SecurityGate()

    request = create_request(
        "read_file",
        RiskLevel.SAFE,
    )

    result = gate.evaluate(request)

    assert result.decision == PermissionDecision.ALLOW


def test_low_risk_operation_is_allowed():
    gate = SecurityGate()

    request = create_request(
        "open_application",
        RiskLevel.LOW,
    )

    result = gate.evaluate(request)

    assert result.decision == PermissionDecision.ALLOW


def test_medium_risk_requires_confirmation():
    gate = SecurityGate()

    request = create_request(
        "move_file",
        RiskLevel.MEDIUM,
    )

    result = gate.evaluate(request)

    assert result.decision == PermissionDecision.CONFIRM


def test_high_risk_is_denied():
    gate = SecurityGate()

    request = create_request(
        "modify_system",
        RiskLevel.HIGH,
    )

    result = gate.evaluate(request)

    assert result.decision == PermissionDecision.DENY


def test_critical_risk_is_denied():
    gate = SecurityGate()

    request = create_request(
        "delete_system_files",
        RiskLevel.CRITICAL,
    )

    result = gate.evaluate(request)

    assert result.decision == PermissionDecision.DENY
