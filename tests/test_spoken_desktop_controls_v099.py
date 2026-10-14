"""v0.9.9: voice commands use local controls and per-shot vision consent."""

import os
from queue import Empty, Queue
import time

import pytest

from nexus.agent import AgentOutcome
from nexus.desktop.confirmation import DesktopConfirmation
from nexus.desktop.window import DesktopWindow


class Agent:
    def __init__(self):
        self.requests = []

    def run(self, prompt, is_cancelled=None, **kwargs):
        self.requests.append(prompt)
        return AgentOutcome(True, content="Resposta do modelo")


class App:
    def __init__(self):
        self.agent = Agent()
        self.closed = False

    def shutdown(self):
        self.closed = True


class Recognizer:
    def __init__(self):
        self.transcripts = Queue()
        self.calls = 0

    def recognize_continuous(self, cancelled):
        self.calls += 1
        while not cancelled():
            try:
                return self.transcripts.get(timeout=0.01)
            except Empty:
                pass
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
        self.calls.append(("file", path))
        return b"private-file"

    def screen(self):
        self.calls.append(("screen",))
        return b"private-screen"

    def camera(self, index):
        self.calls.append(("camera", index))
        return b"private-camera"

    def describe(self, image, *, question):
        self.calls.append(("describe", image, question))
        return {"description": "Uma descrição local."}


def spin(root, predicate, timeout=5):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        root.update()
        time.sleep(0.01)
    assert predicate()


@pytest.fixture
def desktop():
    if not os.environ.get("DISPLAY"):
        pytest.skip("Requer Xvfb")
    import tkinter as tk

    root = tk.Tk()
    app, recognizer, speaker, vision = App(), Recognizer(), Speaker(), Vision()
    confirmation = DesktopConfirmation()
    window = DesktopWindow(root, app, confirmation, recognizer=recognizer,
                           speaker=speaker, vision=vision)
    yield root, app, window, recognizer, speaker, vision
    if not app.closed:
        window._close()
        spin(root, lambda: app.closed)
    confirmation.close()
    try:
        root.destroy()
    except tk.TclError:
        pass


@pytest.mark.parametrize("spoken,command", [
    ("Nexus, analise a tela", "vision_screen"),
    ("analisar imagem", "vision_file"),
    ("analise a câmera", "vision_camera"),
    ("Desative a voz!", "speech_off"),
    ("Ligue a voz", "speech_on"),
])
def test_exact_spoken_commands(spoken, command):
    assert DesktopWindow._voice_command(spoken) == command


@pytest.mark.parametrize("spoken", [
    "A imagem contém uma tela", "A câmera está ligada?",
    "Explique como analisar a tela", "analisar tela e executar comando",
])
def test_ordinary_questions_are_not_control_commands(spoken):
    assert DesktopWindow._voice_command(spoken) is None


@pytest.mark.parametrize("spoken", [
    "analisar imagem", "analisar tela", "analisar câmera",
])
def test_spoken_visual_request_still_requires_consent_and_resumes_on_refusal(
    desktop, monkeypatch, spoken
):
    from tkinter import filedialog, simpledialog

    root, app, window, recognizer, speaker, vision = desktop
    monkeypatch.setattr(filedialog, "askopenfilename", lambda *a, **kw: "/home/user/a.png")
    monkeypatch.setattr(simpledialog, "askinteger", lambda *a, **kw: 2)
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "O que aparece?")
    consents = []
    monkeypatch.setattr(window.messagebox, "askyesno",
                        lambda title, message, **kw: consents.append(message) or False)

    recognizer.transcripts.put(spoken)
    spin(root, lambda: len(consents) == 1 and recognizer.calls >= 2)
    assert "UMA captura/leitura" in consents[0]
    assert vision.calls == []
    assert speaker.spoken == []
    assert app.agent.requests == []
    assert window._voice_active and not window._busy


def test_spoken_screen_request_captures_once_and_answers_by_voice(desktop, monkeypatch):
    from tkinter import simpledialog

    root, app, window, recognizer, speaker, vision = desktop
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "Descreva")
    monkeypatch.setattr(window.messagebox, "askyesno", lambda *a, **kw: True)

    recognizer.transcripts.put("Nexus, analise a tela")
    spin(root, lambda: bool(speaker.spoken) and not window._busy)
    assert vision.calls == [
        ("screen",), ("describe", b"private-screen", "Descreva"),
    ]
    assert speaker.spoken == [("Uma descrição local.", "Feminina")]
    assert app.agent.requests == []


@pytest.mark.parametrize("spoken", ["analisar imagem", "analisar câmera"])
def test_spoken_visual_selection_cancellation_resumes_listening(
    desktop, monkeypatch, spoken
):
    from tkinter import filedialog, simpledialog

    root, app, window, recognizer, speaker, vision = desktop
    monkeypatch.setattr(filedialog, "askopenfilename", lambda *a, **kw: "")
    monkeypatch.setattr(simpledialog, "askinteger", lambda *a, **kw: None)
    monkeypatch.setattr(window.messagebox, "askyesno",
                        lambda *a, **kw: pytest.fail("No consent expected"))
    recognizer.transcripts.put(spoken)
    spin(root, lambda: recognizer.calls >= 2)
    assert vision.calls == []
    assert window._voice_active and not window._busy
    assert app.agent.requests == []


def test_spoken_settings_obey_optional_wake_gate_without_agent(desktop):
    root, app, window, recognizer, speaker, vision = desktop
    window.wake_required.set(True)
    recognizer.transcripts.put("desative a voz")
    spin(root, lambda: recognizer.calls >= 2)
    assert window.speech_enabled.get()

    recognizer.transcripts.put("Nexus, desative a voz")
    spin(root, lambda: not window.speech_enabled.get())
    assert speaker.spoken == []
    assert window._privacy_labels[1].cget("text") == "Voz: desativada"
    assert window._voice_active

    recognizer.transcripts.put("Nexus, ative a voz")
    spin(root, lambda: speaker.spoken == [("Leitura em voz ativada.", "Feminina")])
    assert window.speech_enabled.get()
    assert app.agent.requests == []
    assert vision.calls == []
