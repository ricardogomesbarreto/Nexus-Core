"""Ephemeral vision-derived context follows normal short chat limits."""
import json

import pytest

from nexus.agent import AgentOutcome
from nexus.desktop.conversation import ChatSession


class Agent:
    def __init__(self):
        self.prompts = []

    def run(self, prompt, is_cancelled=None):
        self.prompts.append(json.loads(prompt))
        return AgentOutcome(True, content="Sugestão facultativa")


def test_visual_context_does_not_store_image_and_is_used_on_follow_up():
    agent = Agent()
    session = ChatSession(agent)
    session.note_visual("Qual figura?", "Vejo uma placa Arduino")
    assert len(session.history) == 1
    reply = session.ask("Qual seria o próximo teste?")
    assert reply.text == "Sugestão facultativa"
    assert "Arduino" in agent.prompts[0]["historico"][0]["assistente"]
    assert session.history[-1][0] == "Qual seria o próximo teste?"


def test_visual_context_is_bounded_ephemeral_and_closed_session_ignores_changes():
    agent = Agent()
    session = ChatSession(agent)
    for i in range(12):
        session.note_visual("pergunta-" + str(i), "y" * 4000)
    assert len(session.history) == ChatSession.MAX_TURNS
    assert all(len(answer) <= ChatSession.MAX_CONTEXT_ITEM
               for _, answer in session.history)
    session.close()
    previous = session.history[:]
    session.note_visual("nova pergunta", "novo resultado")
    assert session.history == previous


@pytest.mark.parametrize("question,description", [
    (None, "texto"), ("texto", None), (1, "texto"), ("texto", 2)
])
def test_visual_context_rejects_non_text(question, description):
    with pytest.raises(ValueError):
        ChatSession(Agent()).note_visual(question, description)
