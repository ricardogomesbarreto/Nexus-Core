import json

import pytest

from nexus.agent import AgentPlanner, ProposalError
from nexus.models.contracts import ModelProviderUnavailableError, ModelResponse
from nexus.security import AuditLogger, RiskLevel, SecurityGate
from nexus.tools import (
    FieldSpec, NexusTool, SystemInfoTool, ToolContract, ToolExecutor,
    ToolRegistry, ToolResult, ValueKind,
)


class FakeRouter:
    def __init__(self, content):
        self.content = content
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        if isinstance(self.content, Exception):
            raise self.content
        return ModelResponse(self.content, "test-model", True, 0, 0)


class MediumTool(NexusTool):
    name = "medium_action"
    description = "Ação de teste que exige autorização"
    risk_level = RiskLevel.MEDIUM
    contract = ToolContract(
        name, description, risk_level,
        inputs=(FieldSpec("value", ValueKind.STRING, nonempty=True),),
        outputs=(FieldSpec("value", ValueKind.STRING),),
    )

    def __init__(self):
        self.calls = []

    def sensitive_resources(self, **kwargs):
        return ()

    def execute(self, **kwargs):
        self.calls.append(kwargs)
        return ToolResult(True, self.name, data={"value": kwargs["value"]})


class Confirmation:
    def __init__(self, approve):
        self.approve = approve
        self.calls = []

    def confirm(self, request):
        self.calls.append(request)
        return self.approve


def planner(tmp_path, content, confirmation=None):
    registry = ToolRegistry()
    registry.register(SystemInfoTool())
    medium = MediumTool()
    registry.register(medium)
    executor = ToolExecutor(
        registry,
        SecurityGate(audit_logger=AuditLogger(tmp_path / "agent-audit.log")),
        confirmation_handler=confirmation,
    )
    router = FakeRouter(content)
    return AgentPlanner(router, registry, executor), router, medium


def proposal(name, arguments):
    return json.dumps({"type": "tool_call", "tool_name": name, "arguments": arguments})


def test_message_does_not_use_tool(tmp_path):
    agent, router, medium = planner(tmp_path, '{"type":"message","content":"Olá"}')
    outcome = agent.run("bom dia")
    assert outcome.success and outcome.content == "Olá"
    assert medium.calls == []
    assert router.requests[0].prompt == "bom dia"
    assert router.requests[0].json_mode is True
    assert router.requests[0].context_length == 4096
    assert len(router.requests[0].response_schema["oneOf"]) == 2
    assert "medium_action" in router.requests[0].system_prompt


def test_general_question_uses_plain_text_and_cannot_run_system_info(tmp_path):
    agent, router, _ = planner(tmp_path, proposal("system_info", {}))
    prompt = json.dumps({"historico": [{"usuario": "mostre meu sistema"}],
                         "mensagem_atual": "O que é uma IA?"})
    outcome = agent.run(prompt)
    assert outcome.error_code == "INVALID_PROPOSAL"
    assert router.requests[0].response_schema is None
    assert router.requests[0].json_mode is False
    assert router.requests[0].max_output_tokens == 192
    assert "Ferramentas disponíveis" not in router.requests[0].system_prompt
    assert "DECISION=DENY" in (tmp_path / "agent-audit.log").read_text()


def test_capability_question_does_not_trigger_tool_schema(tmp_path):
    agent, router, medium = planner(tmp_path, "Posso ajudar a organizar os arquivos.")
    outcome = agent.run(json.dumps({"mensagem_atual": "Vai poder arrumar meus arquivos?"}))
    assert outcome.success and outcome.content.startswith("Posso ajudar")
    assert not router.requests[0].json_mode
    assert not medium.calls


def test_explicit_computer_request_can_still_use_tool(tmp_path):
    agent, router, _ = planner(tmp_path, proposal("system_info", {}))
    outcome = agent.run(json.dumps({"mensagem_atual": "Mostre meu sistema"}))
    assert outcome.success and outcome.tool_result.tool_name == "system_info"
    assert "Ferramentas disponíveis" in router.requests[0].system_prompt


def test_safe_tool_runs_through_executor_and_is_audited(tmp_path):
    agent, _, medium = planner(tmp_path, proposal("system_info", {}))
    outcome = agent.run("sistema?")
    assert outcome.success and outcome.tool_result.data["system"]
    assert medium.calls == []
    assert "DECISION=ALLOW" in (tmp_path / "agent-audit.log").read_text()


@pytest.mark.parametrize("field", ["answer", "response", "content"])
def test_single_text_envelope_is_only_displayed_not_executed(tmp_path, field):
    agent, _, medium = planner(tmp_path, json.dumps({field: "Estou funcionando."}))
    outcome = agent.run("Você funciona?")
    assert outcome.success and outcome.content == "Estou funcionando."
    assert medium.calls == []


def test_medium_tool_requires_confirmation_for_each_call(tmp_path):
    confirmation = Confirmation(True)
    agent, _, medium = planner(
        tmp_path, proposal("medium_action", {"value": "x"}), confirmation
    )
    assert agent.run("agir").success
    assert agent.run("agir").success
    assert medium.calls == [{"value": "x"}, {"value": "x"}]
    assert len(confirmation.calls) == 2


@pytest.mark.parametrize("confirmation,code", [
    (None, "CONFIRMATION_REQUIRED"),
    (Confirmation(False), "CONFIRMATION_REJECTED"),
])
def test_medium_tool_fails_closed(tmp_path, confirmation, code):
    agent, _, medium = planner(
        tmp_path, proposal("medium_action", {"value": "x"}), confirmation
    )
    outcome = agent.run("agir")
    assert not outcome.success and outcome.error_code == code
    assert medium.calls == []


@pytest.mark.parametrize("content", [
    '{"type":"tool_call","tool_name":"medium_action","arguments":{"value":"x"},"approved":true}',
    '{"type":"tool_call","tool_name":"medium_action","arguments":{"value":"x","extra":1}}',
    '{"type":"tool_call","tool_name":"unknown","arguments":{}}',
    '{"type":"message","content":"ok","content":"duplicado"}',
    '[{"type":"message","content":"um"},{"type":"message","content":"dois"}]',
    '```json\n{"type":"message","content":"ok"}\n```',
    '{"type":"tool_call","tool_name":"medium_action","arguments":{"value":NaN}}',
    '{"type":"message","content":""}',
])
def test_invalid_model_proposals_are_denied_and_audited(tmp_path, content):
    agent, _, medium = planner(tmp_path, content)
    outcome = agent.run("agir")
    assert outcome.error_code == "INVALID_PROPOSAL"
    assert medium.calls == []
    assert "DECISION=DENY" in (tmp_path / "agent-audit.log").read_text()


def test_model_unavailable_does_not_execute(tmp_path):
    agent, _, medium = planner(tmp_path, ModelProviderUnavailableError("offline"))
    outcome = agent.run("agir")
    assert outcome.error_code == "MODEL_ERROR"
    assert "offline" not in (outcome.error or "")
    assert medium.calls == []


def test_incomplete_model_response_is_rejected(tmp_path):
    agent, router, _ = planner(tmp_path, "irrelevante")
    router.generate = lambda _: ModelResponse("{}", "test", False, 0, 0)
    with pytest.raises(ProposalError):
        agent.plan("agir")


def test_closing_session_cancels_model_proposed_tool(tmp_path):
    agent, _, medium = planner(tmp_path, proposal("medium_action", {"value": "x"}))
    outcome = agent.run("agir", is_cancelled=lambda: True)
    assert outcome.error_code == "CANCELLED"
    assert medium.calls == []
