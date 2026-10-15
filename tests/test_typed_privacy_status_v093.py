"""v0.9.3: typed status questions use the same bounded local reply."""
import pytest

from test_multimodal_privacy_status_v090 import desktop, spin


def type_and_send(window, text):
    window.input.insert("1.0", text)
    assert window._send() == "break"


def test_typed_status_works_with_paused_microphone_and_speech_off(desktop, monkeypatch):
    root, window, app, vision = desktop
    window._shortcut_toggle_listening()
    window.speech_enabled.set(False)
    monkeypatch.setattr(window.session, "prepare_turn",
                        lambda: pytest.fail("Local status must not start an agent turn"))
    monkeypatch.setattr(window.speaker, "speak", lambda *args: pytest.fail("Speech is off"))

    type_and_send(window, "Qual é o estado da privacidade?")

    transcript = window.transcript.get("1.0", "end")
    assert "Escuta: pausada" in transcript
    assert "Voz: desativada" in transcript
    assert "Visão: sem captura" in transcript
    assert "não verificam hardware" in transcript
    assert window.input.get("1.0", "end-1c") == ""
    assert window._voice_active is False
    assert not window._busy
    assert app.agent.calls == []
    assert vision.captures == 0


def test_typed_status_stops_listening_before_local_speech(desktop, monkeypatch):
    root, window, app, vision = desktop
    spoken = []
    monkeypatch.setattr(window.speaker, "speak", lambda text, voice: spoken.append((text, voice)))
    window.voice_choice.set("Feminina")
    spin(root, lambda: bool(window._listen_pending_generations))
    previous_generation = window._listen_generation

    type_and_send(window, "Como está minha privacidade?")
    spin(root, lambda: bool(spoken))

    assert window._listen_generation > previous_generation
    assert "Visão: sem captura" in spoken[0][0]
    assert spoken[0][1] == "Feminina"
    assert app.agent.calls == []
    assert vision.captures == 0


def test_other_typed_question_still_goes_to_normal_conversation(desktop):
    root, window, app, vision = desktop
    window.speech_enabled.set(False)

    type_and_send(window, "Explique o estado da privacidade")
    spin(root, lambda: "Resposta local" in window.transcript.get("1.0", "end"))

    assert len(app.agent.calls) == 1
    assert vision.captures == 0


def test_busy_window_keeps_typed_status_for_later(desktop):
    root, window, app, vision = desktop
    window._busy = True
    window.input.insert("1.0", "Qual o estado da privacidade")

    assert window._send() == "break"
    assert window.input.get("1.0", "end-1c") == "Qual o estado da privacidade"
    assert app.agent.calls == []
    assert vision.captures == 0
    window._busy = False
