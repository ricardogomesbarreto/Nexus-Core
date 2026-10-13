"""v0.9.2: explicit privacy questions stay in the local desktop state path."""
import pytest

from nexus.desktop.window import DesktopWindow

from test_multimodal_privacy_status_v090 import desktop, spin


def recognize_once(window, monkeypatch, phrase):
    """Complete one recognizer request, then keep later requests cancellable."""
    original = window.recognizer.recognize_continuous
    calls = []

    def recognize(cancelled):
        calls.append(True)
        if len(calls) == 1:
            return phrase
        return original(cancelled)

    monkeypatch.setattr(window.recognizer, "recognize_continuous", recognize)
    return calls


@pytest.mark.parametrize("phrase", [
    "Qual é o estado da privacidade?",
    "Nexus, qual o estado da privacidade",
    "Como está minha privacidade?",
    "Informe o estado da privacidade.",
])
def test_only_exact_privacy_requests_are_commands(phrase):
    assert DesktopWindow._voice_command(phrase) == "privacy_status"
    assert DesktopWindow._voice_command("Explique o estado da privacidade") is None
    assert DesktopWindow._voice_command("Qual o estado da privacidade de outro app") is None


def test_spoken_privacy_request_uses_current_state_without_agent_or_vision(desktop, monkeypatch):
    root, window, app, vision = desktop
    spoken = []
    monkeypatch.setattr(window.speaker, "speak", lambda text, voice: spoken.append((text, voice)))
    window.voice_choice.set("Masculina")
    recognize_once(window, monkeypatch, "Qual é o estado da privacidade?")
    spin(root, lambda: bool(spoken))
    response, voice = spoken[0]
    assert voice == "Masculina"
    assert "Visão: sem captura" in response
    assert "não verificam hardware" in response
    assert "Qual é o estado da privacidade?" in window.transcript.get("1.0", "end")
    assert app.agent.calls == []
    assert vision.captures == 0
    assert not window._busy


def test_privacy_voice_request_respects_disabled_speech_and_mic_pause(desktop, monkeypatch):
    root, window, app, vision = desktop
    monkeypatch.setattr(window.speaker, "speak", lambda *args: pytest.fail("Voice is off"))
    window.speech_enabled.set(False)
    recognize_once(window, monkeypatch, "Como está minha privacidade?")
    spin(root, lambda: "Voz: desativada" in window.transcript.get("1.0", "end"))
    assert app.agent.calls == []
    assert vision.captures == 0
    window._shortcut_toggle_listening()
    assert window._voice_active is False
    assert window._voice_command("Qual o estado da privacidade") == "privacy_status"
    # The command parser never starts the microphone; paused state remains paused.
    assert window._voice_active is False


def test_wake_gate_does_not_bypass_existing_utterance_filter(desktop, monkeypatch):
    root, window, app, vision = desktop
    window.wake_required.set(True)
    calls = recognize_once(window, monkeypatch, "Qual o estado da privacidade")
    spin(root, lambda: len(calls) >= 2)
    assert "Estados do aplicativo;" not in window.transcript.get("1.0", "end")
    assert app.agent.calls == []
    assert vision.captures == 0


def test_privacy_query_with_wake_word_is_answered_locally(desktop, monkeypatch):
    root, window, app, vision = desktop
    window.wake_required.set(True)
    window.speech_enabled.set(False)
    recognize_once(window, monkeypatch, "Nexus, qual é o estado da privacidade?")
    spin(root, lambda: "Estados do aplicativo;" in window.transcript.get("1.0", "end"))
    assert "Visão: sem captura" in window.transcript.get("1.0", "end")
    assert app.agent.calls == []
    assert vision.captures == 0
