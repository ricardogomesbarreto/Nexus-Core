"""Regression: authorized Imagem, Tela and Câmera answer using chosen local voice."""
import os
import time

import pytest

from nexus.agent import AgentOutcome
from nexus.desktop.confirmation import DesktopConfirmation
from nexus.desktop.window import DesktopWindow


class Agent:
    def run(self, prompt, is_cancelled=None, **kw):
        return AgentOutcome(True, content="Uma recomendação.")


class App:
    agent = Agent()
    closed = False

    def shutdown(self):
        self.closed = True


class Recognizer:
    def recognize_continuous(self, cancelled):
        while not cancelled():
            time.sleep(0.01)
        return ""

    def stop(self):
        pass


class Speaker:
    def __init__(self):
        self.spoken = []

    def speak(self, text, voice):
        self.spoken.append((text, voice))

    def stop(self):
        pass


class Vision:
    def __init__(self):
        self.calls = []

    def image_from_file(self, path):
        self.calls.append(("image", path))
        return b"file-bytes"

    def screen(self):
        self.calls.append(("screen",))
        return b"screen-bytes"

    def camera(self, index):
        self.calls.append(("camera", index))
        return b"camera-bytes"

    def describe(self, image, *, question):
        self.calls.append(("describe", image, question))
        return {"description": "Vejo um esquema elétrico com três componentes."}


def pump(root, until, timeout=5):
    end = time.monotonic() + timeout
    while not until() and time.monotonic() < end:
        root.update()
        time.sleep(0.01)
    assert until()


@pytest.fixture
def ui():
    if not os.environ.get("DISPLAY"):
        pytest.skip("Requer Xvfb")
    import tkinter as tk
    root = tk.Tk()
    confirmation = DesktopConfirmation()
    speaker = Speaker()
    service = Vision()
    app = App()
    app.closed = False
    window = DesktopWindow(root, app, confirmation,
                           recognizer=Recognizer(), speaker=speaker, vision=service)
    yield root, window, service, speaker, app
    if not app.closed:
        window._close()
        pump(root, lambda: app.closed)
    confirmation.close()
    try:
        root.destroy()
    except tk.TclError:
        pass


@pytest.mark.parametrize("source,voice,expected_source", [
    ("file", "Feminina", "image"),
    ("screen", "Masculina", "screen"),
    ("camera", "Feminina", "camera"),
])
def test_each_visual_source_produces_spoken_reply(ui, monkeypatch, source, voice, expected_source):
    from tkinter import filedialog, simpledialog
    root, window, service, speaker, _ = ui
    assert window.speech_enabled.get(), "Responses should be spoken by default"
    window.voice_choice.set(voice)
    monkeypatch.setattr(filedialog, "askopenfilename", lambda *a, **kw: "/home/user/figura.png")
    monkeypatch.setattr(simpledialog, "askinteger", lambda *a, **kw: 1)
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "Explique a imagem")
    monkeypatch.setattr(window.messagebox, "askyesno", lambda *a, **kw: True)
    window._request_vision(source)
    pump(root, lambda: bool(speaker.spoken) and not window._busy)
    assert speaker.spoken == [("Vejo um esquema elétrico com três componentes.", voice)]
    assert service.calls[0][0] == expected_source
    assert service.calls[1][0] == "describe"
    assert "Vejo um esquema elétrico" in window.transcript.get("1.0", "end")


@pytest.mark.parametrize("source", ["file", "screen", "camera"])
def test_visual_reply_is_silent_when_user_disables_speech(ui, monkeypatch, source):
    from tkinter import filedialog, simpledialog
    root, window, service, speaker, _ = ui
    window.speech_enabled.set(False)
    monkeypatch.setattr(filedialog, "askopenfilename", lambda *a, **kw: "/home/user/figura.png")
    monkeypatch.setattr(simpledialog, "askinteger", lambda *a, **kw: 0)
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "Explique")
    monkeypatch.setattr(window.messagebox, "askyesno", lambda *a, **kw: True)
    window._request_vision(source)
    pump(root, lambda: not window._busy)
    assert service.calls[-1][0] == "describe"
    assert speaker.spoken == []
    assert "Vejo um esquema elétrico" in window.transcript.get("1.0", "end")


def test_denied_visual_capture_never_speaks_or_reads_hardware(ui, monkeypatch):
    from tkinter import simpledialog
    root, window, service, speaker, _ = ui
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "O que vê?")
    monkeypatch.setattr(window.messagebox, "askyesno", lambda *a, **kw: False)
    window._vision_screen()
    root.update()
    assert service.calls == []
    assert speaker.spoken == []
