"""v0.6.1: real Tk dispatch with fake Linux audio/vision hardware."""
import json
import os
import time

import pytest

from nexus.agent import AgentOutcome
from nexus.desktop.confirmation import DesktopConfirmation
from nexus.desktop.window import DesktopWindow
from nexus.vision.local import VisionError


class FakeAgent:
    def __init__(self):
        self.requests = []

    def run(self, prompt, is_cancelled=None):
        self.requests.append(json.loads(prompt))
        return AgentOutcome(True, content="Sugiro revisar o próximo tópico.")


class FakeApp:
    def __init__(self):
        self.agent = FakeAgent()
        self.closed = False

    def shutdown(self):
        self.closed = True


class FakeRecognizer:
    def recognize_continuous(self, cancelled):
        while not cancelled():
            time.sleep(0.01)
        return ""

    def stop(self):
        pass


class FakeSpeaker:
    def speak(self, text, voice):
        pass

    def stop(self):
        pass


class FakeVision:
    def __init__(self):
        self.calls = []
        self.raise_error = False

    def image_from_file(self, path):
        self.calls.append(("file", path))
        return b"private-image"

    def screen(self):
        self.calls.append(("screen",))
        return b"private-screen"

    def camera(self, index):
        self.calls.append(("camera", index))
        return b"private-camera"

    def describe(self, image, *, question):
        self.calls.append(("describe", image, question))
        if self.raise_error:
            raise VisionError("Modelo visual local indisponível.")
        return {"model": "gemma3:4b", "description": "Um diagrama de redes."}


def spin(root, condition, timeout=6):
    end = time.monotonic() + timeout
    while not condition() and time.monotonic() < end:
        try:
            root.update()
        except Exception:
            break
        time.sleep(0.01)
    assert condition()


@pytest.fixture
def desktop():
    if not os.environ.get("DISPLAY"):
        pytest.skip("Requer Xvfb")
    import tkinter as tk

    root = tk.Tk()
    app = FakeApp()
    confirmation = DesktopConfirmation()
    vision = FakeVision()
    window = DesktopWindow(root, app, confirmation,
                           speaker=FakeSpeaker(), recognizer=FakeRecognizer(),
                           vision=vision)
    window.speech_enabled.set(False)
    yield root, app, window, vision
    if not app.closed:
        window._close()
        spin(root, lambda: app.closed)
    confirmation.close()
    try:
        root.destroy()
    except tk.TclError:
        pass


def test_vision_buttons_do_not_capture_until_explicit_consent(desktop, monkeypatch):
    from tkinter import simpledialog
    root, app, window, vision = desktop
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "Explique o gráfico")
    monkeypatch.setattr(window.messagebox, "askyesno", lambda *a, **kw: False)
    window._vision_screen()
    assert vision.calls == []
    assert not window._busy
    assert not app.agent.requests
    assert all(str(x.cget("state")) == "normal" for x in window._vision_buttons)


def test_approved_screenshot_is_single_shot_and_can_be_discussed(desktop, monkeypatch):
    from tkinter import simpledialog
    root, app, window, vision = desktop
    consent = []
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "Como funciona?")
    monkeypatch.setattr(window.messagebox, "askyesno",
                        lambda title, message, **kw: consent.append(message) or True)
    window._vision_screen()
    assert window._busy
    assert all(str(x.cget("state")) == "disabled" for x in window._vision_buttons)
    spin(root, lambda: not window._busy and len(vision.calls) == 2)
    assert vision.calls == [
        ("screen",), ("describe", b"private-screen", "Como funciona?")
    ]
    assert len(consent) == 1
    assert "Ollama local" in consent[0]
    assert "Um diagrama de redes." in window.transcript.get("1.0", "end")
    assert len(window.session.history) == 1
    assert "private-screen" not in str(window.session.history)
    assert not app.agent.requests
    window.input.insert("1.0", "Qual seria a próxima etapa?")
    window._send()
    spin(root, lambda: len(app.agent.requests) == 1 and not window._busy)
    assert "Um diagrama de redes" in app.agent.requests[0]["historico"][0]["assistente"]
    assert len([call for call in vision.calls if call[0] == "screen"]) == 1


@pytest.mark.parametrize("source", ["file", "camera"])
def test_file_and_camera_require_separate_consent(desktop, monkeypatch, source):
    from tkinter import simpledialog, filedialog
    root, app, window, vision = desktop
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "O que aparece?")
    monkeypatch.setattr(simpledialog, "askinteger", lambda *a, **kw: 2)
    monkeypatch.setattr(filedialog, "askopenfilename",
                        lambda *a, **kw: "/home/example/notes.png")
    monkeypatch.setattr(window.messagebox, "askyesno", lambda *a, **kw: True)
    window._request_vision(source)
    spin(root, lambda: not window._busy and len(vision.calls) == 2)
    assert vision.calls[0] == (
        ("file", "/home/example/notes.png") if source == "file"
        else ("camera", 2)
    )
    assert vision.calls[1][0] == "describe"


def test_dialog_cancellation_is_side_effect_free(desktop, monkeypatch):
    from tkinter import simpledialog, filedialog
    root, app, window, vision = desktop
    monkeypatch.setattr(filedialog, "askopenfilename", lambda *a, **kw: "")
    window._vision_file()
    monkeypatch.setattr(simpledialog, "askinteger", lambda *a, **kw: None)
    window._vision_camera()
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: None)
    window._vision_screen()
    assert vision.calls == []
    assert not window._busy


def test_local_vision_error_cannot_crash_gui_or_trigger_agent(desktop, monkeypatch):
    from tkinter import simpledialog
    root, app, window, vision = desktop
    vision.raise_error = True
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "Descreva")
    monkeypatch.setattr(window.messagebox, "askyesno", lambda *a, **kw: True)
    window._vision_screen()
    spin(root, lambda: not window._busy)
    assert "Modelo visual local indisponível" in window.transcript.get("1.0", "end")
    assert window.session.history == []
    assert not app.agent.requests


def test_closed_window_ignores_stale_vision_events(desktop):
    root, app, window, vision = desktop
    window._vision_events.put(("success", "teste", "texto não autorizado após fechar"))
    window._close()
    spin(root, lambda: app.closed)
    assert window.session.history == []
