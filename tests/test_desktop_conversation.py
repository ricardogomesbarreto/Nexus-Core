import json

import pytest

from nexus.agent import AgentOutcome
from nexus.desktop.conversation import ChatSession
from nexus.tools import ToolResult


class FakeAgent:
    def __init__(self, outcomes):
        self.outcomes = iter(outcomes)
        self.requests = []

    def run(self, prompt, is_cancelled=None):
        self.requests.append((json.loads(prompt), is_cancelled))
        return next(self.outcomes)


def test_conversation_remembers_previous_exchange_without_persistence():
    agent = FakeAgent([
        AgentOutcome(True, content="Olá!"),
        AgentOutcome(True, content="Posso explicar."),
    ])
    session = ChatSession(agent)
    assert session.ask("Oi").text == "Olá!"
    assert session.ask("Pode explicar?").text == "Posso explicar."
    assert agent.requests[0][0] == {"historico": [], "mensagem_atual": "Oi"}
    assert agent.requests[1][0]["historico"] == [
        {"usuario": "Oi", "assistente": "Olá!"}
    ]
    session.close()
    assert agent.requests[1][1]() is True
    with pytest.raises(RuntimeError):
        session.ask("mais")


def test_history_is_bounded_to_six_short_exchanges():
    agent = FakeAgent([AgentOutcome(True, content="x" * 1300)] * 8)
    session = ChatSession(agent)
    for index in range(8):
        session.ask(f"mensagem {index}")
    assert len(session.history) == 6
    assert session.history[0][0] == "mensagem 2"
    assert len(session.history[0][1]) == ChatSession.MAX_CONTEXT_ITEM
    assert agent.requests[-1][0]["historico"][0]["usuario"] == "mensagem 1"


@pytest.mark.parametrize("message", ["", "  ", "x" * 4001, None])
def test_invalid_message_is_rejected_before_model(message):
    agent = FakeAgent([])
    with pytest.raises(ValueError):
        ChatSession(agent).ask(message)
    assert agent.requests == []


def test_tool_output_and_failure_are_visible_in_conversation():
    agent = FakeAgent([
        AgentOutcome(True, tool_result=ToolResult(
            True, "terminal_sandbox", data={"stdout": "ok\n", "stderr": ""}
        )),
        AgentOutcome(False, tool_result=ToolResult(
            False, "terminal_sandbox", error="Autorização recusada",
            error_code="CONFIRMATION_REJECTED"
        )),
    ])
    session = ChatSession(agent)
    assert session.ask("faça").text == "terminal_sandbox executada.\nok\n"
    assert "Autorização recusada" in session.ask("de novo").text


def test_long_tool_output_is_truncated_for_display_and_history():
    agent = FakeAgent([AgentOutcome(True, tool_result=ToolResult(
        True, "read_file", data={"content": "a" * 5000}
    ))])
    session = ChatSession(agent)
    reply = session.ask("ler")
    assert "saída abreviada" in reply.text
    assert len(session.history[0][1]) == ChatSession.MAX_CONTEXT_ITEM
