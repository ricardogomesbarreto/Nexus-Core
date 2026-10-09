"""Guided autonomy forbids tool execution in advisor mode and supports cancel."""
import json
from threading import Event, Thread

from nexus.agent import AgentOutcome
from nexus.desktop.conversation import ChatSession


class FakeAgent:
    def __init__(self, gate=None):
        self.calls = []
        self.gate = gate

    def run(self, prompt, is_cancelled=None, *, allow_tools=True):
        self.calls.append((json.loads(prompt), allow_tools))
        if self.gate:
            self.gate.wait(timeout=3)
        return AgentOutcome(True, content="Sugiro testar primeiro em ambiente local.")


def test_advisory_mode_is_explicit_and_keeps_conversation_context():
    agent = FakeAgent()
    chat = ChatSession(agent)
    chat.prepare_turn()
    suggestion = chat.ask("Quais próximos passos?", advisory_only=True)
    assert suggestion.outcome.success
    assert agent.calls[0][1] is False
    assert agent.calls[0][0]["modo"] == "sugestao_sem_ferramentas"
    assert agent.calls[0][0]["historico"] == []
    chat.prepare_turn()
    reply = chat.ask("Explique a sugestão")
    assert reply.outcome.success
    assert agent.calls[1][1] is True
    assert "Sugiro testar" in agent.calls[1][0]["historico"][0]["assistente"]


def test_cancel_discards_pending_model_response_and_history():
    barrier = Event()
    agent = FakeAgent(gate=barrier)
    chat = ChatSession(agent)
    output = []
    chat.prepare_turn()
    worker = Thread(target=lambda: output.append(chat.ask("Pode sugerir?", advisory_only=True)))
    worker.start()
    for _ in range(300000):
        if agent.calls:
            break
    assert agent.calls
    chat.cancel_current()
    barrier.set()
    worker.join(timeout=3)
    assert not worker.is_alive()
    assert output[0].outcome.error_code == "CANCELLED"
    assert chat.history == []
    chat.prepare_turn()
    reply = chat.ask("Continuar")
    assert reply.outcome.success
    assert len(chat.history) == 1


def test_closed_session_does_not_restart_after_cancel():
    chat = ChatSession(FakeAgent())
    chat.close()
    try:
        chat.prepare_turn()
    except RuntimeError:
        pass
    else:
        raise AssertionError("Closed ChatSession was reactivated")


def test_agent_planner_rejects_tool_calls_in_suggestion_mode(tmp_path):
    from tests.test_agent_planner import planner, proposal
    agent, router, medium = planner(
        tmp_path, proposal("medium_action", {"value": "danger"}),
    )
    outcome = agent.run("sugira apenas", allow_tools=False)
    assert not outcome.success
    assert outcome.error_code == "ADVISORY_ONLY"
    assert medium.calls == []


def test_agent_planner_cancellation_preempts_tool_execution(tmp_path):
    from tests.test_agent_planner import planner, proposal
    agent, _, medium = planner(
        tmp_path, proposal("medium_action", {"value": "danger"}),
    )
    original_plan = agent.plan

    def cancel_during_plan(prompt):
        proposal = original_plan(prompt)
        state["cancelled"] = True
        return proposal

    state = {"cancelled": False}
    agent.plan = cancel_during_plan
    outcome = agent.run("agir?", is_cancelled=lambda: state["cancelled"])
    assert outcome.error_code == "CANCELLED"
    assert medium.calls == []
