"""Offline fresh-turn safety and natural, symbol-free local speech."""

import json
import os
import time

import pytest

from nexus.agent import AgentOutcome
from nexus.desktop.conversation import ChatSession
from nexus.voice.speech_text import readable_model_text, speech_from_model_text


@pytest.mark.parametrize("raw,expected", [
    ("**A câmera** mostra *uma mesa*.", "A câmera mostra uma mesa."),
    ("### Resultado\n- **Um computador**\n- **Dois monitores**",
     "Resultado\nUm computador\nDois monitores"),
    ("**Resumo:** Vejo objetos. ******", "Resumo: Vejo objetos."),
    ("Veja [o diagrama](https://example.invalid) e `roteador`.",
     "Veja o diagrama e roteador."),
    ("**Texto** com acentos: **São Luís**.", "Texto com acentos: São Luís."),
])
def test_displayed_visual_prose_removes_markdown(raw, expected):
    assert readable_model_text(raw) == expected


def test_spoken_camera_description_never_says_markdown_asterisks():
    raw = "## Análise\n- **Imagem:** Há *dois* computadores.\n- **Tela:** Um código Python."
    speech = speech_from_model_text(raw)
    assert speech == "Análise. Imagem: Há dois computadores. Tela: Um código Python."
    assert "*" not in speech
    assert "#" not in speech
    assert not speech.startswith("hífen")


def test_speech_is_bounded_and_does_not_read_long_code_blocks():
    raw = "```python\n" + "print('secret')\n" + "```\n**Tudo certo.**"
    rendered = speech_from_model_text(raw)
    assert "print(" not in rendered
    assert "trecho de código" in rendered
    assert "Tudo certo." in rendered
    very_long = speech_from_model_text("palavra " * 2000)
    assert len(very_long) < 2700
    assert very_long.endswith("Consulte o restante na conversa.")


class SequenceAgent:
    def __init__(self, outcomes):
        self.outcomes = iter(outcomes)
        self.calls = []

    def run(self, prompt, is_cancelled=None, **kwargs):
        self.calls.append((json.loads(prompt), kwargs))
        return next(self.outcomes)


def test_distinct_questions_do_not_reuse_previous_response():
    repeated = "O roteador conecta computadores em uma rede."
    agent = SequenceAgent([
        AgentOutcome(True, content=repeated),
        AgentOutcome(True, content=repeated),  # small local model echoes history
        AgentOutcome(True, content="Um switch conecta dispositivos na mesma LAN."),
    ])
    session = ChatSession(agent)
    assert session.ask("O que é um roteador?").text == repeated
    second = session.ask("O que é um switch?")
    assert second.text == "Um switch conecta dispositivos na mesma LAN."
    assert len(agent.calls) == 3
    assert agent.calls[-1][0]["historico"] == []
    assert agent.calls[-1][0]["mensagem_atual"] == "O que é um switch?"
    assert agent.calls[-1][1]["allow_tools"] is False
    assert session.history[-1][0] == "O que é um switch?"


def test_same_stale_answer_twice_is_reported_not_pretended():
    old = "Resposta anterior sobre redes de computadores."
    agent = SequenceAgent([AgentOutcome(True, content=old)] * 3)
    session = ChatSession(agent)
    assert session.ask("Como funciona uma rede?").outcome.success
    later = session.ask("Explique a memória RAM.")
    assert later.outcome.error_code == "STALE_REPLY"
    assert "não produziu uma resposta nova" in later.text
    assert later.text != old
    assert len(session.history) == 1
    assert all(call[1].get("allow_tools") is False for call in agent.calls[2:])


def test_same_question_may_give_same_answer_without_second_inference():
    old = "Uma rede conecta dispositivos para trocar dados."
    agent = SequenceAgent([AgentOutcome(True, content=old)] * 2)
    session = ChatSession(agent)
    session.ask("Defina rede.")
    assert session.ask("Defina rede.").text == old
    assert len(agent.calls) == 2


def test_offline_model_failure_does_not_fall_back_to_cached_reply():
    agent = SequenceAgent([
        AgentOutcome(True, content="A RAM mantém dados temporários."),
        AgentOutcome(False, error="O Ollama local está indisponível.",
                     error_code="MODEL_ERROR"),
    ])
    session = ChatSession(agent)
    first = session.ask("O que é RAM?")
    other = session.ask("O que é GPU?")
    assert first.outcome.success
    assert not other.outcome.success
    assert other.text == "O Ollama local está indisponível."
    assert other.text != first.text
    assert len(session.history) == 1


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb Linux")
def test_tk_speaks_plain_portuguese_and_shows_clean_visual_reply():
    import tkinter as tk
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow

    spoken = []

    class App:
        agent = object()
        closed = False
        def shutdown(self):
            self.closed = True

    class Recognizer:
        def recognize_continuous(self, cancelled):
            while not cancelled():
                time.sleep(.01)
            return ""
        def stop(self):
            pass

    class Speaker:
        def speak(self, content, voice):
            spoken.append((content, voice))
        def stop(self):
            pass

    root = tk.Tk()
    confirmation = DesktopConfirmation()
    app = App()
    try:
        window = DesktopWindow(root, app, confirmation,
                               recognizer=Recognizer(), speaker=Speaker())
        window._vision_events.put((
            "success", "O que aparece?",
            "### Visão\n- **Uma mesa** com *um notebook*.\n- **Duas cadeiras**."
        ))
        deadline = time.monotonic() + 5
        while not spoken and time.monotonic() < deadline:
            root.update()
            time.sleep(.01)
        assert len(spoken) == 1
        assert spoken[0][0] == (
            "Visão. Uma mesa com um notebook. Duas cadeiras."
        )
        assert "*" not in spoken[0][0]
        display = window.transcript.get("1.0", "end")
        assert "Uma mesa com um notebook." in display
        assert "**" not in display
        window._close()
        deadline = time.monotonic() + 5
        while not app.closed and time.monotonic() < deadline:
            root.update()
            time.sleep(.01)
        assert app.closed
    finally:
        confirmation.close()
        try:
            root.destroy()
        except tk.TclError:
            pass
