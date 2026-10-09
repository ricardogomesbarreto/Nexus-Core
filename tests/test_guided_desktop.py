"""Tk guided suggestions, cooperative cancel and visual-response suppression."""
import json
import os
import time
from threading import Event

import pytest

from nexus.agent import AgentOutcome
from nexus.desktop.confirmation import DesktopConfirmation
from nexus.desktop.window import DesktopWindow


def spin(root, until):
    end = time.monotonic() + 5
    while not until() and time.monotonic() < end:
        root.update()
        time.sleep(0.01)
    assert until()


class FakeAgent:
    def __init__(self):
        self.calls = []
        self.started = Event()
        self.release = Event()
        self.block = False

    def run(self, prompt, is_cancelled=None, *, allow_tools=True):
        self.calls.append((json.loads(prompt), allow_tools))
        self.started.set()
        if self.block:
            self.release.wait(3)
        return AgentOutcome(True, content="Sugiro testar seu projeto primeiro.")


class FakeApp:
    def __init__(self):
        self.agent = FakeAgent()
        self.closed = False

    def shutdown(self):
        self.closed = True


class FakeSpeaker:
    def __init__(self):
        self.calls = []

    def speak(self, text, voice):
        self.calls.append((text, voice))

    def stop(self):
        pass


class FakeRecognizer:
    def recognize_continuous(self, cancelled):
        while not cancelled():
            time.sleep(0.01)
        return ""

    def stop(self):
        pass


class BlockingVision:
    def __init__(self):
        self.started = Event()
        self.release = Event()

    def screen(self):
        return b"mocked-screenshot"

    def describe(self, image, *, question):
        self.started.set()
        self.release.wait(3)
        return {"description": "Resultado da tela não deve ser apresentado."}


@pytest.fixture
def ui():
    if not os.environ.get("DISPLAY"):
        pytest.skip("Tk display required")
    import tkinter as tk
    root = tk.Tk()
    app = FakeApp()
    confirmation = DesktopConfirmation()
    speaker = FakeSpeaker()
    vision = BlockingVision()
    w = DesktopWindow(root, app, confirmation,
                      recognizer=FakeRecognizer(), speaker=speaker, vision=vision)
    yield root, w, app, speaker, vision
    app.agent.release.set()
    vision.release.set()
    if not app.closed:
        w._close()
        spin(root, lambda: app.closed)
    confirmation.close()
    try:
        root.destroy()
    except tk.TclError:
        pass


def test_suggest_button_produces_advice_without_tools(ui):
    root, w, app, speaker, vision = ui
    w.speech_enabled.set(False)
    w._suggest()
    spin(root, lambda: not w._busy)
    assert len(app.agent.calls) == 1
    prompt, allow_tools = app.agent.calls[0]
    assert allow_tools is False
    assert prompt["modo"] == "sugestao_sem_ferramentas"
    assert "Sugiro testar" in w.transcript.get("1.0", "end")
    assert str(w.suggest_button.cget("state")) == "normal"


def test_cancel_chat_drops_reply_and_does_not_read_out_loud(ui):
    root, w, app, speaker, vision = ui
    app.agent.block = True
    w.input.insert("1.0", "Explique a arquitetura")
    w._send()
    assert app.agent.started.wait(2)
    w._cancel_current()
    assert w._cancel_requested
    app.agent.release.set()
    spin(root, lambda: not w._busy)
    assert not w.session.history
    assert "Solicitação cancelada." in w.transcript.get("1.0", "end")
    assert "Sugiro testar" not in w.transcript.get("1.0", "end")
    assert speaker.calls == []
    assert str(w.cancel_button.cget("state")) == "disabled"


def test_cancel_visual_request_drops_description_and_speech(ui, monkeypatch):
    from tkinter import simpledialog
    root, w, app, speaker, vision = ui
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "Explique a tela")
    monkeypatch.setattr(w.messagebox, "askyesno", lambda *a, **kw: True)
    w._vision_screen()
    assert vision.started.wait(2)
    w._cancel_current()
    vision.release.set()
    spin(root, lambda: not w._busy)
    transcript = w.transcript.get("1.0", "end")
    assert "Análise visual cancelada." in transcript
    assert "Resultado da tela não deve ser apresentado" not in transcript
    assert speaker.calls == []
    assert w.session.history == []
    assert str(w.send_button.cget("state")) == "normal"
