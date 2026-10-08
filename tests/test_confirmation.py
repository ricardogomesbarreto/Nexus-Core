import io
from pathlib import Path

from nexus.security import (
    AuditLogger,
    ConsoleConfirmation,
    PathSecurity,
    RiskLevel,
    SecurityGate,
    SecurityRequest,
    SensitiveResource,
)
from nexus.tools import (
    FieldSpec, NexusTool, ResourceSpec, ToolContract, ToolExecutor,
    ToolRegistry, ToolResult, ValueKind,
)


class ConfirmTool(NexusTool):
    name = "confirmation_test"
    description = "Executa operação de teste"
    risk_level = RiskLevel.MEDIUM
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(FieldSpec("path", ValueKind.STRING, required=False),),
        resources=(ResourceSpec("path", "path"),),
    )

    def __init__(self):
        self.calls = 0

    def sensitive_resources(self, **kwargs):
        path = kwargs.get("path")
        return (SensitiveResource("path", path),) if path else ()

    def execute(self, **kwargs):
        self.calls += 1
        return ToolResult(True, self.name)


class HighRiskTool(ConfirmTool):
    name = "high_risk_test"
    risk_level = RiskLevel.HIGH
    contract = ToolContract(
        name=name, description=ConfirmTool.description, permission=risk_level,
        inputs=ConfirmTool.contract.inputs,
        resources=ConfirmTool.contract.resources,
    )


class FakeConfirmation:
    def __init__(self, response=True, callback=None):
        self.response = response
        self.callback = callback
        self.requests = []

    def confirm(self, request):
        self.requests.append(request)
        if self.callback:
            self.callback()
        return self.response


def make_executor(tmp_path, tool, handler):
    home = tmp_path / "home"
    home.mkdir()
    paths = PathSecurity()
    paths.home = home
    paths.protected_paths = [Path("/etc")]
    gate = SecurityGate(
        path_security=paths,
        audit_logger=AuditLogger(tmp_path / "audit.log"),
    )
    registry = ToolRegistry()
    registry.register(tool)
    return ToolExecutor(registry, gate, handler), home


def test_confirmation_approves_exactly_one_operation_and_audits(tmp_path):
    tool = ConfirmTool()
    handler = FakeConfirmation()
    executor, home = make_executor(tmp_path, tool, handler)

    result = executor.execute(tool.name, path=str(home))

    assert result.success
    assert tool.calls == 1
    assert len(handler.requests) == 1
    audit = (tmp_path / "audit.log").read_text()
    assert "DECISION=CONFIRM" in audit
    assert "OUTCOME=APPROVED" in audit
    assert "OUTCOME=SUCCESS" in audit


def test_rejection_and_non_boolean_response_fail_closed(tmp_path):
    tool = ConfirmTool()
    handler = FakeConfirmation(response=False)
    executor, _ = make_executor(tmp_path, tool, handler)

    assert not executor.execute(tool.name).success
    handler.response = "sim"
    assert not executor.execute(tool.name).success
    assert tool.calls == 0
    assert (tmp_path / "audit.log").read_text().count(
        "OUTCOME=REJECTED"
    ) == 2


def test_absent_or_failing_handler_never_executes(tmp_path):
    tool = ConfirmTool()
    executor, _ = make_executor(tmp_path, tool, None)
    assert not executor.execute(tool.name).success

    handler = FakeConfirmation(callback=lambda: 1 / 0)
    executor.confirmation_handler = handler
    result = executor.execute(tool.name)
    assert not result.success
    assert tool.calls == 0
    audit = (tmp_path / "audit.log").read_text()
    assert "OUTCOME=UNAVAILABLE" in audit
    assert "OUTCOME=ERROR" in audit


def test_high_risk_denial_does_not_ask_for_confirmation(tmp_path):
    tool = HighRiskTool()
    handler = FakeConfirmation()
    executor, _ = make_executor(tmp_path, tool, handler)

    assert not executor.execute(tool.name).success
    assert not handler.requests
    assert tool.calls == 0


def test_symlink_changed_during_confirmation_is_denied(tmp_path):
    tool = ConfirmTool()
    executor, home = make_executor(tmp_path, tool, None)
    target = home / "target"
    target.mkdir()
    link = home / "link"
    link.symlink_to(target, target_is_directory=True)

    def change_target():
        link.unlink()
        link.symlink_to("/etc", target_is_directory=True)

    executor.confirmation_handler = FakeConfirmation(callback=change_target)
    result = executor.execute(tool.name, path=str(link))

    assert not result.success
    assert tool.calls == 0
    assert "DECISION=DENY" in (tmp_path / "audit.log").read_text()


class TTYInput(io.StringIO):
    def isatty(self):
        return True


class TTYOutput(io.StringIO):
    def isatty(self):
        return True


def test_console_requires_tty_and_exact_explicit_response():
    request = SecurityRequest(
        action="terminal_sandbox",
        description="Comando isolado",
        risk_level=RiskLevel.MEDIUM,
        tool_name="terminal_sandbox",
        data={"command": "echo hello\nworld"},
    )
    output = TTYOutput()
    assert not ConsoleConfirmation(io.StringIO("sim\n"), output).confirm(
        request
    )
    assert output.getvalue() == ""

    handler = ConsoleConfirmation(TTYInput("SIM\n"), output)
    assert handler.confirm(request) is True
    assert "echo hello\\u000aworld" in output.getvalue()
    assert not ConsoleConfirmation(TTYInput("s\n"), TTYOutput()).confirm(
        request
    )
    assert not ConsoleConfirmation(TTYInput("sim\n"), io.StringIO()).confirm(
        request
    )


def test_audit_fields_cannot_inject_extra_records(tmp_path):
    log_path = tmp_path / "security.log"
    AuditLogger(log_path).record(
        tool_name="tool\nDECISION=ALLOW",
        action="run|override",
        risk_level="MEDIUM",
        decision="CONFIRM",
        reason="line one\nline two",
        path="/home/user\r/other",
    )

    content = log_path.read_text()
    assert len(content.splitlines()) == 1
    assert "tool\\nDECISION=ALLOW" in content
    assert "run\\|override" in content
    assert "line one\\nline two" in content
