from pathlib import Path

from nexus.security import (
    PathSecurity,
    PermissionDecision,
    RiskLevel,
    SecurityGate,
    SecurityRequest,
)


def test_home_is_allowed():
    security = PathSecurity()

    assert security.is_allowed(Path.home())


def test_nexus_directory_is_allowed():
    security = PathSecurity()

    nexus_path = Path.home() / "Nexus Core"

    assert security.is_allowed(nexus_path)


def test_etc_is_protected():
    security = PathSecurity()

    assert security.is_protected("/etc")


def test_boot_is_protected():
    security = PathSecurity()

    assert security.is_protected("/boot")


def test_usr_is_protected():
    security = PathSecurity()

    assert security.is_protected("/usr")


def test_root_is_protected():
    security = PathSecurity()

    assert security.is_protected("/root")


def test_path_outside_home_is_denied():
    security = PathSecurity()

    assert not security.is_allowed("/tmp")


def test_parent_traversal_is_denied():
    security = PathSecurity()

    malicious_path = (
        Path.home()
        / "Nexus"
        / ".."
        / ".."
        / "etc"
    )

    assert not security.is_allowed(malicious_path)


def test_security_gate_denies_protected_path():
    gate = SecurityGate()

    request = SecurityRequest(
        action="read_file",
        description="Ler arquivo",
        risk_level=RiskLevel.SAFE,
        path="/etc/passwd",
    )

    result = gate.evaluate(request)

    assert result.decision == PermissionDecision.DENY


def test_security_gate_allows_home_path():
    gate = SecurityGate()

    request = SecurityRequest(
        action="read_file",
        description="Ler arquivo",
        risk_level=RiskLevel.SAFE,
        path=str(Path.home() / "Nexus Core"),
    )

    result = gate.evaluate(request)

    assert result.decision == PermissionDecision.ALLOW


def test_ssh_is_protected():
    security = PathSecurity()

    ssh_path = Path.home() / ".ssh"

    assert security.is_protected(ssh_path)
    assert not security.is_allowed(ssh_path)


def test_gnupg_is_protected():
    security = PathSecurity()

    gnupg_path = Path.home() / ".gnupg"

    assert security.is_protected(gnupg_path)
    assert not security.is_allowed(gnupg_path)


def test_aws_is_protected():
    security = PathSecurity()

    aws_path = Path.home() / ".aws"

    assert security.is_protected(aws_path)
    assert not security.is_allowed(aws_path)


def test_docker_is_protected():
    security = PathSecurity()

    docker_path = Path.home() / ".docker"

    assert security.is_protected(docker_path)
    assert not security.is_allowed(docker_path)


def test_kube_is_protected():
    security = PathSecurity()

    kube_path = Path.home() / ".kube"

    assert security.is_protected(kube_path)
    assert not security.is_allowed(kube_path)


def test_config_is_protected():
    security = PathSecurity()

    config_path = Path.home() / ".config"

    assert security.is_protected(config_path)
    assert not security.is_allowed(config_path)


def test_keyrings_is_protected():
    security = PathSecurity()

    keyrings_path = (
        Path.home()
        / ".local"
        / "share"
        / "keyrings"
    )

    assert security.is_protected(keyrings_path)
    assert not security.is_allowed(keyrings_path)
