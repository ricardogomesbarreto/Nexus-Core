import os
import subprocess
from pathlib import Path

from nexus.security import (
    AuditLogger,
    PathSecurity,
    RiskLevel,
    SecurityGate,
    SecurityPolicy,
    SensitiveResource,
)
from nexus.tools import (
    FieldSpec,
    ListDirectoryTool,
    NexusTool,
    ResourceSpec,
    TerminalSandboxTool,
    ToolContract,
    ToolExecutor,
    ToolRegistry,
    ToolResult,
    ValueKind,
)


def make_executor(tmp_path, tool):
    home = tmp_path / "home"
    home.mkdir()

    paths = PathSecurity()
    paths.home = home
    paths.protected_paths = [home / ".ssh", Path("/etc")]

    gate = SecurityGate(
        path_security=paths,
        policy=SecurityPolicy(maximum_allowed_risk=RiskLevel.MEDIUM),
        audit_logger=AuditLogger(tmp_path / "security.log"),
    )
    registry = ToolRegistry()
    registry.register(tool)
    return ToolExecutor(registry, gate), home


def test_implicit_directory_is_mediated(tmp_path, monkeypatch):
    executor, home = make_executor(tmp_path, ListDirectoryTool())
    monkeypatch.chdir(home)

    result = executor.execute("list_directory")

    assert result.success
    assert result.data["path"] == str(home)
    assert "PATH=." in (tmp_path / "security.log").read_text()


def test_implicit_directory_outside_home_is_denied(tmp_path, monkeypatch):
    executor, _ = make_executor(tmp_path, ListDirectoryTool())
    monkeypatch.chdir(tmp_path)

    result = executor.execute("list_directory")

    assert not result.success
    assert "fora da área" in result.error


def test_symlink_outside_home_is_denied(tmp_path):
    executor, home = make_executor(tmp_path, ListDirectoryTool())
    link = home / "escape"
    link.symlink_to(tmp_path, target_is_directory=True)

    result = executor.execute("list_directory", path=str(link))

    assert not result.success
    assert "fora da área" in result.error


def test_terminal_workspace_is_checked_before_docker(tmp_path, monkeypatch):
    executor, home = make_executor(tmp_path, TerminalSandboxTool())

    def unexpected_run(*args, **kwargs):
        raise AssertionError("Docker não deveria ser chamado")

    monkeypatch.setattr(subprocess, "run", unexpected_run)
    result = executor.execute(
        "terminal_sandbox",
        command="pwd",
        workspace="/etc",
    )

    assert not result.success
    assert "protegido" in result.error
    assert "PATH=/etc" in (tmp_path / "security.log").read_text()


def test_terminal_workspace_allowed_and_read_only(tmp_path, monkeypatch):
    executor, home = make_executor(tmp_path, TerminalSandboxTool())
    commands = []
    mounted_sources = []

    def fake_run(command, **kwargs):
        commands.append(command)
        mounts = [part for part in command if "src=" in part]
        assert len(mounts) == 1
        source = Path(mounts[0].split("src=", 1)[1].split(",", 1)[0])
        assert source.is_dir()  # the temporary snapshot is present while Docker starts
        mounted_sources.append(source)
        return subprocess.CompletedProcess(command, 0, "OK", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = executor.execute(
        "terminal_sandbox",
        command="pwd",
        workspace=str(home),
    )

    assert result.success
    assert len(commands) == 1
    sources = [
        value.split("src=", 1)[1].split(",", 1)[0]
        for value in commands[0] if "src=" in value
    ]
    assert len(sources) == 1
    assert sources[0] != str(home)
    assert mounted_sources and str(mounted_sources[0]) == sources[0]
    # The descriptor must be open during subprocess invocation, not just
    # revalidated by a mutable host pathname.
    assert any("dst=/workspace,readonly" in value for value in commands[0])


class UndeclaredTool(NexusTool):
    name = "undeclared"
    description = "Não declara recursos"
    risk_level = RiskLevel.SAFE
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(FieldSpec("path", ValueKind.STRING),),
        resources=(ResourceSpec("path", "path"),),
    )

    def execute(self, **kwargs):
        raise AssertionError("Ferramenta não deve executar")


def test_missing_resource_declaration_fails_closed(tmp_path):
    executor, _ = make_executor(tmp_path, UndeclaredTool())

    result = executor.execute("undeclared", path="/etc/passwd")

    assert not result.success
    assert "não declarados" in result.error
    assert "DECISION=DENY" in (
        tmp_path / "security.log"
    ).read_text()


class MultiResourceTool(NexusTool):
    name = "multi_resource"
    description = "Dois caminhos"
    risk_level = RiskLevel.SAFE
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(
            FieldSpec("source", ValueKind.STRING),
            FieldSpec("destination", ValueKind.STRING),
        ),
        resources=(
            ResourceSpec("input", "source"),
            ResourceSpec("output", "destination"),
        ),
    )

    def sensitive_resources(self, **kwargs):
        return (
            SensitiveResource("input", kwargs["source"]),
            SensitiveResource("output", kwargs["destination"]),
        )

    def execute(self, **kwargs):
        raise AssertionError("Ferramenta não deve executar")


def test_all_declared_resources_are_checked(tmp_path):
    executor, home = make_executor(tmp_path, MultiResourceTool())

    result = executor.execute(
        "multi_resource",
        source=str(home),
        destination="/etc/passwd",
    )

    assert not result.success
    assert "protegido" in result.error
    log = (tmp_path / "security.log").read_text()
    assert str(home) in log
    assert "/etc/passwd" in log


def test_invalid_resource_path_fails_closed(tmp_path):
    executor, _ = make_executor(tmp_path, ListDirectoryTool())

    result = executor.execute("list_directory", path="")

    assert not result.success
    assert result.error_code == "INVALID_INPUT"
