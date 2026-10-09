"""Desktop wake-mode regression: words without prefix never reach the Agent."""
import json
import os
import time

import pytest

from nexus.agent import AgentOutcome
from nexus.desktop.confirmation import DesktopConfirmation
from nexus.desktop.window import DesktopWindow


def test_voice_check_cli_without_agent_or_audio_capture(monkeypatch, capsys):
    import nexus.main as module
    import nexus.voice.diagnostics as diag
    monkeypatch.setattr(module, "build_application",
                        lambda: pytest.fail("Voice diagnostics must not start the app"))
    monkeypatch.setattr(diag, "inspect_voice",
                        lambda: {"mode": "offline", "microphone_tested": False})
    module.cli(["--voice-check"])
    assert json.loads(capsys.readouterr().out) == {
        "mode": "offline", "microphone_tested": False
    }


@pytest.mark.parametrize("opts", [
    ["--voice-check", "--agent-prompt", "test"],
    ["--voice-check", "--memory-list"],
    ["--voice-check", "--knowledge-search", "test"],
])
def test_voice_check_rejects_combination_with_other_modes(opts):
    import nexus.main as module
    with pytest.raises(SystemExit) as error:
        module.cli(opts)
    assert error.value.code == 2


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requires virtual Linux display")
def test_optional_wake_gate_filters_ambient_speech_and_preserves_hands_free():
    import tkinter as tk

    root = tk.Tk()
    confirmation = DesktopConfirmation()
    requests = []

    class Agent:
        def run(self, prompt, is_cancelled=None):
            requests.append(json.loads(prompt))
            return AgentOutcome(True, content="Entendido")

    class App:
        agent = Agent()
        closed = False

        def shutdown(self):
            self.closed = True

    class Recognizer:
        calls = 0

        def recognize_continuous(self, cancelled):
            self.calls += 1
            if self.calls == 1:
                return "Esta pergunta não deve ativar"
            if self.calls == 2:
                return "Nexus, explique Python"
            while not cancelled():
                time.sleep(0.01)
            return ""

        def stop(self):
            pass

    class Speaker:
        def speak(self, text, voice):
            pass

        def stop(self):
            pass

    app = App()
    try:
        window = DesktopWindow(root, app, confirmation,
                               speaker=Speaker(), recognizer=Recognizer())
        window.speech_enabled.set(False)
        assert not window.wake_required.get()
        window.wake_required.set(True)
        assert window.wake_required.get()
        limit = time.monotonic() + 5
        while not requests and time.monotonic() < limit:
            root.update()
            time.sleep(0.01)
        assert len(requests) == 1
        assert requests[0]["mensagem_atual"] == "explique Python"
        assert "Esta pergunta não deve ativar" not in window.transcript.get("1.0", "end")
        window._close()
        while not app.closed and time.monotonic() < limit:
            try:
                root.update()
            except tk.TclError:
                break
            time.sleep(0.01)
        assert app.closed
    finally:
        confirmation.close()
        try:
            root.destroy()
        except tk.TclError:
            pass
