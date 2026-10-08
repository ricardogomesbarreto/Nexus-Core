import json

import pytest

from nexus.security import AuditLogger, RiskLevel, SecurityGate
from nexus.tools import (
    FieldSpec,
    ListDirectoryTool,
    NexusTool,
    ReadFileTool,
    ResourceSpec,
    SystemInfoTool,
    TerminalSandboxTool,
    ToolContract,
    ToolExecutor,
    ToolRegistry,
    ToolResult,
    ValueKind,
)


def executor_for(tmp_path, tool):
    registry = ToolRegistry()
    registry.register(tool)
    gate = SecurityGate(audit_logger=AuditLogger(tmp_path / "contract.log"))
    return ToolExecutor(registry, gate)


def test_builtin_contracts_are_machine_readable_and_precise():
    registry = ToolRegistry()
    for tool in (SystemInfoTool(), ListDirectoryTool(), ReadFileTool(), TerminalSandboxTool()):
        registry.register(tool)

    contracts = {entry["name"]: entry for entry in registry.contracts()}
    assert json.loads(json.dumps(contracts)) == contracts
    assert contracts["list_directory"]["inputs"]["properties"]["path"]["default"] == "."
    assert contracts["list_directory"]["inputs"]["properties"]["path"]["pattern"] == "\\S"
    assert contracts["read_file"]["inputs"]["required"] == ["path"]
    assert contracts["terminal_sandbox"]["permission"] == "MEDIUM"
    assert contracts["terminal_sandbox"]["resources"] == [
        {"name": "workspace", "input": "workspace"}
    ]
    assert contracts["system_info"]["inputs"]["additionalProperties"] is False
    assert contracts["system_info"]["outputs"]["required"] == [
        "system", "release", "version", "machine", "processor", "python"
    ]
    assert contracts["list_directory"]["outputs"]["properties"]["items"][
        "items"
    ]["required"] == ["name", "type"]


@pytest.mark.parametrize(
    ("name", "arguments"),
    [
        ("read_file", {}),
        ("read_file", {"path": 123}),
        ("read_file", {"path": "/etc/passwd", "extra": True}),
        ("list_directory", {"path": "  "}),
        ("terminal_sandbox", {"command": ""}),
        ("terminal_sandbox", {"command": "pwd", "workspace": 42}),
    ],
)
def test_invalid_inputs_denied_and_audited_before_security_or_execution(
    tmp_path, name, arguments
):
    tool = {
        "read_file": ReadFileTool,
        "list_directory": ListDirectoryTool,
        "terminal_sandbox": TerminalSandboxTool,
    }[name]()
    executor = executor_for(tmp_path, tool)
    result = executor.execute(name, **arguments)

    assert not result.success
    assert result.error_code == "INVALID_INPUT"
    assert "DECISION=DENY" in (tmp_path / "contract.log").read_text()
    assert "DECISION=ALLOW" not in (tmp_path / "contract.log").read_text()


class MissingResourceTool(NexusTool):
    name = "missing_resource"
    description = "Ferramenta que omite o recurso"
    risk_level = RiskLevel.SAFE
    contract = ToolContract(
        name, description, risk_level,
        inputs=(FieldSpec("path", ValueKind.STRING),),
        resources=(ResourceSpec("file", "path"),),
    )

    def sensitive_resources(self, **kwargs):
        return ()

    def execute(self, **kwargs):
        raise AssertionError("A ferramenta não pode ser executada")


def test_declared_resource_must_match_call_arguments(tmp_path):
    executor = executor_for(tmp_path, MissingResourceTool())
    result = executor.execute("missing_resource", path="/etc/passwd")

    assert result.error_code == "INVALID_RESOURCES"
    assert "DECISION=DENY" in (tmp_path / "contract.log").read_text()


class BadResultTool(NexusTool):
    name = "bad_result"
    description = "Ferramenta que retorna dados inválidos"
    risk_level = RiskLevel.SAFE
    contract = ToolContract(
        name, description, risk_level,
        outputs=(FieldSpec("count", ValueKind.INTEGER),),
    )

    def __init__(self, response):
        self.response = response

    def sensitive_resources(self, **kwargs):
        return ()

    def execute(self, **kwargs):
        return self.response


@pytest.mark.parametrize(
    "response",
    [
        {"count": 1},
        ToolResult(True, "other_tool", data={"count": 1}),
        ToolResult(True, "bad_result", data={"count": True}),
        ToolResult(True, "bad_result", data={"count": 1, "extra": 2}),
        ToolResult(False, "bad_result", error=""),
    ],
)
def test_invalid_result_is_not_exposed_and_is_audited(tmp_path, response):
    executor = executor_for(tmp_path, BadResultTool(response))
    result = executor.execute("bad_result")

    assert result.error_code == "INVALID_RESULT"
    assert result.data is None
    assert "OUTCOME=INVALID_RESULT" in (tmp_path / "contract.log").read_text()


def test_nested_directory_items_are_validated():
    contract = ListDirectoryTool.contract
    with pytest.raises(ValueError, match="Item inválido"):
        contract.validate_output({
            "path": "/home/user",
            "items": [{"name": "a", "type": "file", "extra": "unlisted"}],
        })


def test_result_serialization_has_stable_error_code():
    failed = ToolResult(False, "read_file", error="Arquivo não encontrado.")
    assert failed.as_dict() == {
        "success": False,
        "tool_name": "read_file",
        "data": None,
        "error": {"code": "TOOL_ERROR", "message": "Arquivo não encontrado."},
    }
    assert ToolResult(True, "system_info", data={"system": "Linux"}).as_dict()[
        "error"
    ] is None


def test_registry_rejects_absent_or_mismatched_contract():
    class NoContract(NexusTool):
        name = "no_contract"
        def execute(self, **kwargs):
            return ToolResult(True, self.name)

    with pytest.raises(ValueError, match="contrato"):
        ToolRegistry().register(NoContract())
    bad = MissingResourceTool()
    bad.risk_level = RiskLevel.HIGH
    with pytest.raises(ValueError, match="incompatível"):
        ToolRegistry().register(bad)


def test_contract_rejects_invalid_resource_mapping():
    with pytest.raises(ValueError, match="correspondente"):
        ToolContract(
            "bad", "Recurso sem entrada", RiskLevel.LOW,
            resources=(ResourceSpec("file", "path"),),
        )
