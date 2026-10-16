"""Spoken startup greeting: single utterance, no mic feedback or false readiness."""

import os
import time
from threading import Event
from types import SimpleNamespace

import pytest

from nexus.desktop.welcome import desktop_spoken_welcome


def test_short_spoken_greeting_is_truthful_and_local():
    assert desktop_spoken_welcome("Ricardo") == "Bem-vindo ao Nexus Core, Ricardo."
    assert desktop_spoken_welcome("Nome <comando>") == "Bem-vindo ao Nexus Core."
    assert desktop_spoken_welcome("A" * 61) == "Bem-vindo ao Nexus Core."
    assert len(desktop_spoken_welcome()) <= 90


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb")
def test_spoken_welcome_uses_selected_voice_once_before_starting_microphone():
    import tkinter as tk
    from nexus.agent import AgentOutcome
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow

    calls = []
    release_speech = Event()

    class App:
        closed = False
        agent = None
        def __init__(self):
            self.agent = self
        def status(self):
            return SimpleNamespace(database=True)
        def run(self, prompt, **kwargs):
            calls.append("agent")
            return AgentOutcome(True, content="Resposta")
        def shutdown(self):
            self.closed = True

    class Speaker:
        def speak(self, text, voice):
            calls.append(("speak", text, voice))
            release_speech.wait(timeout=3)
        def stop(self):
            release_speech.set()

    class Recognizer:
        def recognize_continuous(self, cancelled):
            calls.append("listen")
            while not cancelled():
                time.sleep(0.01)
            return ""
        def stop(self):
            pass

    root = tk.Tk()
    confirmation = DesktopConfirmation()
    app = App()
    try:
        window = DesktopWindow(root, app, confirmation,
                               speaker=Speaker(), recognizer=Recognizer(),
                               startup_voice=True)
        window.voice_choice.set("Feminina")
        limit = time.monotonic() + 5
        while not any(isinstance(c, tuple) and c[0] == "speak" for c in calls) and time.monotonic() < limit:
            root.update()
            time.sleep(0.01)
        utterances = [c for c in calls if isinstance(c, tuple)]
        assert len(utterances) == 1
        assert utterances[0] == ("speak", desktop_spoken_welcome(), "Feminina")
        assert "listen" not in calls
        assert "agent" not in calls
        assert window._speaking
        release_speech.set()
        limit = time.monotonic() + 5
        while "listen" not in calls and time.monotonic() < limit:
            root.update()
            time.sleep(0.01)
        assert calls.index("listen") > calls.index(utterances[0])
        assert len([c for c in calls if isinstance(c, tuple)]) == 1
        window._close()
        limit = time.monotonic() + 5
        while not app.closed and time.monotonic() < limit:
            root.update()
            time.sleep(0.01)
        assert app.closed
    finally:
        release_speech.set()
        confirmation.close()
        try:
            root.destroy()
        except tk.TclError:
            pass


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb")
def test_muted_startup_never_speaks_but_can_listen():
    import tkinter as tk
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow

    calls = []

    class App:
        agent = object()
        closed = False
        def shutdown(self):
            self.closed = True

    class Speaker:
        def speak(self, text, voice):
            calls.append("tts")
        def stop(self):
            pass

    class Recognizer:
        def recognize_continuous(self, cancelled):
            calls.append("listen")
            while not cancelled():
                time.sleep(0.01)
            return ""
        def stop(self):
            pass

    root = tk.Tk()
    confirmation = DesktopConfirmation()
    app = App()
    try:
        window = DesktopWindow(root, app, confirmation,
                               speaker=Speaker(), recognizer=Recognizer(),
                               startup_voice=True)
        window.speech_enabled.set(False)
        end = time.monotonic() + 5
        while "listen" not in calls and time.monotonic() < end:
            root.update()
            time.sleep(0.01)
        assert "listen" in calls
        assert "tts" not in calls
        assert "Bem-vindo ao NEXUS CORE!" in window.transcript.get("1.0", "end")
        window._close()
        end = time.monotonic() + 5
        while not app.closed and time.monotonic() < end:
            root.update()
            time.sleep(0.01)
        assert app.closed
    finally:
        confirmation.close()
        try:
            root.destroy()
        except tk.TclError:
            pass


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb")
def test_spoken_welcome_tts_error_is_reported_and_listening_resumes():
    import tkinter as tk
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow
    from nexus.voice import VoiceError

    calls = []

    class App:
        agent = object()
        closed = False
        def shutdown(self):
            self.closed = True

    class Speaker:
        def speak(self, text, voice):
            calls.append("tts")
            raise VoiceError("Dispositivo de saída não disponível")
        def stop(self):
            pass

    class Recognizer:
        def recognize_continuous(self, cancelled):
            calls.append("listen")
            while not cancelled():
                time.sleep(0.01)
            return ""
        def stop(self):
            pass

    root = tk.Tk()
    confirmation = DesktopConfirmation()
    app = App()
    try:
        window = DesktopWindow(root, app, confirmation,
                               speaker=Speaker(), recognizer=Recognizer(),
                               startup_voice=True)
        end = time.monotonic() + 5
        while "listen" not in calls and time.monotonic() < end:
            root.update()
            time.sleep(0.01)
        assert calls.count("tts") == 1
        assert "listen" in calls
        assert "Não foi possível falar as boas-vindas" in window.transcript.get("1.0", "end")
        assert "Dispositivo de saída não disponível" in window.transcript.get("1.0", "end")
        window._close()
        end = time.monotonic() + 5
        while not app.closed and time.monotonic() < end:
            root.update()
            time.sleep(0.01)
        assert app.closed
    finally:
        confirmation.close()
        try:
            root.destroy()
        except tk.TclError:
            pass
