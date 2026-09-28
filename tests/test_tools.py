import shutil
import subprocess
from pathlib import Path

import pytest

from nexus.security import (
    AuditLogger,
    PermissionDecision,
    RiskLevel,
    SecurityGate,
)
from nexus.tools import (
    ListDirectoryTool,
    ReadFileTool,
    SystemInfoTool,
    TerminalSandboxTool,
    ToolExecutor,
    ToolRegistry,
)


def create_executor(log_path=None):
    registry = ToolRegistry()

    registry.register(
        SystemInfoTool()
    )

    registry.register(
        ListDirectoryTool()
    )

    registry.register(
        ReadFileTool()
    )

    audit_logger = AuditLogger(
        log_path=log_path
    )

    security_gate = SecurityGate(
        audit_logger=audit_logger
    )

    return ToolExecutor(
        registry=registry,
        security_gate=security_gate,
    )


def create_sandbox():
    return TerminalSandboxTool()


@pytest.fixture(scope="module")
def docker_runtime():
    if shutil.which("docker") is None:
        pytest.skip("Docker não está instalado neste ambiente")

    try:
        status = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        pytest.skip("Daemon Docker indisponível")

    if status.returncode != 0:
        pytest.skip("Daemon Docker indisponível")


# =========================================================
# TOOL REGISTRY
# =========================================================

def test_tool_registry():
    registry = ToolRegistry()

    registry.register(
        SystemInfoTool()
    )

    assert registry.exists("system_info")
    assert "system_info" in registry.list_tools()


# =========================================================
# SYSTEM INFO
# =========================================================

def test_system_info_tool():
    executor = create_executor()

    result = executor.execute(
        "system_info"
    )

    assert result.success
    assert result.tool_name == "system_info"
    assert result.data["system"] == "Linux"


# =========================================================
# LIST DIRECTORY
# =========================================================

def test_list_directory_tool():
    executor = create_executor()

    result = executor.execute(
        "list_directory",
        path=".",
    )

    assert result.success
    assert result.tool_name == "list_directory"
    assert "items" in result.data


# =========================================================
# READ FILE
# =========================================================

def test_read_file_tool():
    executor = create_executor()

    test_file = Path(
        "tests/test_read_file.txt"
    )

    test_file.write_text(
        "NEXUS TEST FILE",
        encoding="utf-8",
    )

    try:
        result = executor.execute(
            "read_file",
            path=str(test_file),
        )

        assert result.success
        assert result.tool_name == "read_file"
        assert (
            result.data["content"]
            == "NEXUS TEST FILE"
        )

    finally:
        if test_file.exists():
            test_file.unlink()


def test_read_file_protected_path():
    executor = create_executor()

    result = executor.execute(
        "read_file",
        path="/etc/passwd",
    )

    assert not result.success
    assert "protegido" in result.error.lower()


def test_read_file_outside_home():
    executor = create_executor()

    result = executor.execute(
        "read_file",
        path="/tmp",
    )

    assert not result.success
    assert (
        "fora da área autorizada"
        in result.error.lower()
    )


def test_read_file_not_found():
    executor = create_executor()

    path = (
        Path.home()
        / "Nexus"
        / "arquivo_que_nao_existe.txt"
    )

    result = executor.execute(
        "read_file",
        path=str(path),
    )

    assert not result.success
    assert (
        "não encontrado"
        in result.error.lower()
    )


def test_read_directory_as_file():
    executor = create_executor()

    result = executor.execute(
        "read_file",
        path=str(
            Path.home() / "Nexus Core"
        ),
    )

    assert not result.success
    assert (
        "não é um arquivo"
        in result.error.lower()
    )


def test_read_file_through_executor():
    executor = create_executor()

    test_file = Path(
        "tests/integration_test.txt"
    )

    test_file.write_text(
        "NEXUS SECURITY TEST",
        encoding="utf-8",
    )

    try:
        result = executor.execute(
            "read_file",
            path=str(test_file),
        )

        assert result.success
        assert (
            result.data["content"]
            == "NEXUS SECURITY TEST"
        )

    finally:
        if test_file.exists():
            test_file.unlink()


def test_read_file_cannot_access_etc():
    executor = create_executor()

    result = executor.execute(
        "read_file",
        path="/etc/passwd",
    )

    assert not result.success
    assert (
        "protegido"
        in result.error.lower()
    )


def test_read_file_cannot_access_tmp():
    executor = create_executor()

    result = executor.execute(
        "read_file",
        path="/tmp",
    )

    assert not result.success
    assert (
        "fora da área autorizada"
        in result.error.lower()
    )


def test_read_file_cannot_access_ssh():
    executor = create_executor()

    ssh_path = Path.home() / ".ssh"

    result = executor.execute(
        "read_file",
        path=str(ssh_path),
    )

    assert not result.success
    assert (
        "protegido"
        in result.error.lower()
    )


def test_read_file_cannot_escape_home():
    executor = create_executor()

    malicious_path = (
        Path.home()
        / "Nexus"
        / ".."
        / ".."
        / "etc"
        / "passwd"
    )

    result = executor.execute(
        "read_file",
        path=str(malicious_path),
    )

    assert not result.success
    assert (
        "protegido"
        in result.error.lower()
        or "fora da área autorizada"
        in result.error.lower()
    )


# =========================================================
# READ FILE LIMITS
# =========================================================

def test_read_file_rejects_large_file():
    executor = create_executor()

    test_file = Path(
        "tests/large_test_file.txt"
    )

    test_file.write_bytes(
        b"A"
        * (
            ReadFileTool.MAX_FILE_SIZE
            + 1
        )
    )

    try:
        result = executor.execute(
            "read_file",
            path=str(test_file),
        )

        assert not result.success
        assert "1 MB" in result.error

    finally:
        if test_file.exists():
            test_file.unlink()


def test_read_file_rejects_binary_file():
    executor = create_executor()

    test_file = Path(
        "tests/binary_test_file.bin"
    )

    test_file.write_bytes(
        bytes(
            [0, 159, 146, 150, 255, 0, 1, 2]
        )
    )

    try:
        result = executor.execute(
            "read_file",
            path=str(test_file),
        )

        assert not result.success
        assert "UTF-8" in result.error

    finally:
        if test_file.exists():
            test_file.unlink()


# =========================================================
# TOOL EXECUTION AUDIT
# =========================================================

def test_successful_execution_is_audited(
    tmp_path,
):
    log_path = (
        tmp_path / "security.log"
    )

    executor = create_executor(
        log_path=log_path
    )

    test_file = Path(
        "tests/audit_success.txt"
    )

    test_file.write_text(
        "AUDIT SUCCESS",
        encoding="utf-8",
    )

    try:
        result = executor.execute(
            "read_file",
            path=str(test_file),
        )

        assert result.success

        log_content = log_path.read_text(
            encoding="utf-8"
        )

        assert (
            "TOOL=read_file"
            in log_content
        )

        assert (
            "OUTCOME=SUCCESS"
            in log_content
        )

        assert (
            "Ferramenta executada com sucesso."
            in log_content
        )

    finally:
        if test_file.exists():
            test_file.unlink()


def test_failed_execution_is_audited(
    tmp_path,
):
    log_path = (
        tmp_path / "security.log"
    )

    executor = create_executor(
        log_path=log_path
    )

    test_file = (
        Path.home()
        / "Nexus"
        / "arquivo_inexistente_audit.txt"
    )

    result = executor.execute(
        "read_file",
        path=str(test_file),
    )

    assert not result.success

    log_content = log_path.read_text(
        encoding="utf-8"
    )

    assert (
        "TOOL=read_file"
        in log_content
    )

    assert (
        "OUTCOME=ERROR"
        in log_content
    )

    assert (
        "Arquivo não encontrado."
        in log_content
    )


# =========================================================
# TERMINAL SANDBOX
# =========================================================

def test_terminal_sandbox_exists():
    tool = create_sandbox()

    assert tool.name == "terminal_sandbox"
    assert tool.risk_level == RiskLevel.MEDIUM


def test_terminal_sandbox_executes_command(docker_runtime):
    tool = create_sandbox()

    result = tool.execute(
        command="echo NEXUS_SANDBOX_OK"
    )

    assert result.success
    assert (
        result.tool_name
        == "terminal_sandbox"
    )

    assert (
        "NEXUS_SANDBOX_OK"
        in result.data["stdout"]
    )

    assert result.data["exit_code"] == 0


def test_terminal_sandbox_runs_as_non_root(docker_runtime):
    tool = create_sandbox()

    result = tool.execute(
        command="id"
    )

    assert result.success
    assert "uid=1000" in result.data["stdout"]
    assert "uid=0" not in result.data["stdout"]


def test_terminal_sandbox_network_is_disabled(docker_runtime):
    tool = create_sandbox()

    result = tool.execute(
        command=(
            'bash -c '
            '"echo > /dev/tcp/1.1.1.1/80"'
        )
    )

    assert not result.success

    assert (
        result.data["exit_code"] != 0
    )

    assert (
        "Network is unreachable"
        in result.data["stderr"]
    )


def test_terminal_sandbox_root_filesystem_is_read_only(docker_runtime):
    tool = create_sandbox()

    result = tool.execute(
        command="touch /nexus_test.txt"
    )

    assert not result.success

    assert (
        "Read-only file system"
        in result.data["stderr"]
    )


def test_terminal_sandbox_tmp_is_writable(docker_runtime):
    tool = create_sandbox()

    result = tool.execute(
        command=(
            "echo NEXUS_TMP_OK "
            "> /tmp/nexus_test.txt "
            "&& cat /tmp/nexus_test.txt"
        )
    )

    assert result.success

    assert (
        "NEXUS_TMP_OK"
        in result.data["stdout"]
    )


def test_terminal_sandbox_empty_command():
    tool = create_sandbox()

    result = tool.execute(
        command=""
    )

    assert not result.success

    assert (
        "Comando não informado."
        in result.error
    )


def test_terminal_sandbox_invalid_workspace():
    tool = create_sandbox()

    result = tool.execute(
        command="pwd",
        workspace="/caminho/inexistente",
    )

    assert not result.success

    assert (
        "Workspace não encontrado."
        in result.error
    )


def test_terminal_sandbox_workspace_must_be_directory(
    tmp_path,
):
    test_file = (
        tmp_path / "arquivo.txt"
    )

    test_file.write_text(
        "NEXUS",
        encoding="utf-8",
    )

    tool = create_sandbox()

    result = tool.execute(
        command="pwd",
        workspace=str(test_file),
    )

    assert not result.success

    assert (
        "Workspace não é um diretório."
        in result.error
    )


def test_terminal_sandbox_workspace_is_read_only(
    tmp_path,
    docker_runtime,
):
    workspace = (
        tmp_path / "workspace"
    )

    workspace.mkdir()

    tool = create_sandbox()

    result = tool.execute(
        command="touch /workspace/teste.txt",
        workspace=str(workspace),
    )

    assert not result.success

    assert (
        "Read-only file system"
        in result.data["stderr"]
    )


def test_terminal_sandbox_workspace_is_mounted(
    tmp_path,
    docker_runtime,
):
    workspace = (
        tmp_path / "workspace"
    )

    workspace.mkdir()

    test_file = (
        workspace / "teste.txt"
    )

    test_file.write_text(
        "NEXUS_WORKSPACE",
        encoding="utf-8",
    )

    tool = create_sandbox()

    result = tool.execute(
        command="cat /workspace/teste.txt",
        workspace=str(workspace),
    )

    assert result.success

    assert (
        "NEXUS_WORKSPACE"
        in result.data["stdout"]
    )


# =========================================================
# TOOL EXECUTOR + SECURITY GATE
# =========================================================

def test_terminal_sandbox_requires_confirmation():
    registry = ToolRegistry()

    registry.register(
        TerminalSandboxTool()
    )

    security_gate = SecurityGate()

    executor = ToolExecutor(
        registry=registry,
        security_gate=security_gate,
    )

    result = executor.execute(
        "terminal_sandbox",
        command="echo SHOULD_NOT_RUN",
    )

    assert not result.success

    assert (
        "confirmação"
        in result.error.lower()
    )


def test_unknown_tool_is_rejected():
    executor = create_executor()

    result = executor.execute(
        "delete_everything"
    )

    assert not result.success

    assert (
        "não encontrada"
        in result.error
    )
