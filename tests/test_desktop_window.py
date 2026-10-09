import os
import time

import pytest

from nexus.agent import AgentOutcome
from nexus.desktop.confirmation import DesktopConfirmation
from nexus.desktop.window import DesktopWindow
from nexus.security import RiskLevel, SecurityRequest


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer display Linux")
def test_desktop_conversation_and_confirmation_on_graphical_display():
    import tkinter as tk

    root = tk.Tk()
    confirmation = DesktopConfirmation()
    calls = []

    class FakeAgent:
        def run(self, prompt, is_cancelled=None):
            request = SecurityRequest(
                action="terminal_sandbox", description="Teste isolado",
                risk_level=RiskLevel.MEDIUM, tool_name="terminal_sandbox",
            )
            calls.append(confirmation.confirm(request))
            return AgentOutcome(True, content="Olá pela janela")

    class FakeApplication:
        agent = FakeAgent()

        def shutdown(self):
            calls.append("shutdown")

    class FakeSpeaker:
        def speak(self, text, voice):
            calls.append((text, voice))

        def stop(self):
            pass

    class FakeRecognizer:
        def recognize_continuous(self, cancelled):
            while not cancelled():
                time.sleep(0.01)
            return ""

        def stop(self):
            pass

    try:
        window = DesktopWindow(
            root, FakeApplication(), confirmation,
            speaker=FakeSpeaker(), recognizer=FakeRecognizer(),
        )
        window.voice_choice.set("Masculina")
        window._confirm = lambda request: True
        window.input.insert("1.0", "Olá")
        window._send()
        deadline = time.monotonic() + 5
        while window._busy and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert not window._busy
        assert calls[0] is True
        assert "Olá pela janela" in window.transcript.get("1.0", "end")
        while len(calls) < 2 and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert calls[1] == ("Olá pela janela", "Masculina")
        window._close()
        while "shutdown" not in calls and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert calls == [True, ("Olá pela janela", "Masculina"), "shutdown"]
    finally:
        confirmation.close()
        try:
            root.destroy()
        except tk.TclError:
            pass


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer display Linux")
def test_microphone_turn_uses_same_conversation_path():
    import tkinter as tk

    root = tk.Tk()
    confirmation = DesktopConfirmation()
    calls = []

    class FakeAgent:
        def run(self, prompt, is_cancelled=None):
            calls.append(prompt)
            return AgentOutcome(True, content="Entendi sua pergunta")

    class FakeApplication:
        agent = FakeAgent()

        def shutdown(self):
            pass

    class FakeRecognizer:
        said = False

        def recognize_continuous(self, cancelled):
            if not self.said and not cancelled():
                self.said = True
                return "Que horas são?"
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

    try:
        window = DesktopWindow(
            root, FakeApplication(), confirmation,
            speaker=FakeSpeaker(), recognizer=FakeRecognizer(),
        )
        window.speech_enabled.set(False)
        deadline = time.monotonic() + 5
        while (window._busy or not calls) and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert calls
        assert "Que horas são?" in window.transcript.get("1.0", "end")
        assert "Entendi sua pergunta" in window.transcript.get("1.0", "end")
        assert window._voice_active
        window._close()
        # Do not destroy the interpreter while voice workers are still
        # unwinding; the application owns the coordinated shutdown.
        deadline = time.monotonic() + 5
        destroyed = False
        while time.monotonic() < deadline:
            try:
                root.update()
                if not root.winfo_exists():
                    destroyed = True
                    break
            except tk.TclError:
                # Tk removes its `winfo` command when the root is destroyed.
                destroyed = True
                break
            time.sleep(0.01)
        assert destroyed
    finally:
        confirmation.close()
        try:
            root.destroy()
        except tk.TclError:
            pass


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer display Linux")
def test_voice_pause_command_and_button_resume_without_agent_request():
    import tkinter as tk

    root = tk.Tk()
    confirmation = DesktopConfirmation()
    calls = []

    class FakeAgent:
        def run(self, prompt, is_cancelled=None):
            calls.append(prompt)
            return AgentOutcome(True, content="Resposta")

    class FakeApplication:
        agent = FakeAgent()

        def shutdown(self):
            calls.append("shutdown")

    class FakeRecognizer:
        said = False

        def recognize_continuous(self, cancelled):
            if not self.said and not cancelled():
                self.said = True
                return "Nexus, pare de escutar"
            while not cancelled():
                time.sleep(0.01)
            return ""

        def stop(self):
            pass

    class FakeSpeaker:
        def speak(self, text, voice):
            calls.append((text, voice))

        def stop(self):
            pass

    try:
        window = DesktopWindow(root, FakeApplication(), confirmation,
                               speaker=FakeSpeaker(), recognizer=FakeRecognizer())
        deadline = time.monotonic() + 5
        while window._voice_active and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert not window._voice_active
        assert window.mic_button.cget("text") == "Retomar escuta"
        assert not calls
        window._toggle_listening()
        assert window._voice_active
        window._close()
        while "shutdown" not in calls and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert calls == ["shutdown"]
    finally:
        confirmation.close()
        try:
            root.destroy()
        except tk.TclError:
            pass


def test_spoken_shutdown_command_is_explicit():
    assert DesktopWindow._voice_command("Nexus, desligue o assistente") == "shutdown"
    assert DesktopWindow._voice_command("pause a escuta") == "pause"
    assert DesktopWindow._voice_command("Explique como desligar o assistente") is None
