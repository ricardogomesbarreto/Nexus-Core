"""v0.9.5: stop one spoken reply without changing future voice settings."""
from test_conversation_audio_reliability import spin, ui


def test_shortcut_is_inert_without_current_speech(ui):
    root, window, recognizer, speaker, app = ui
    assert root.bind("<Control-Shift-S>")
    window.input.insert("1.0", "Texto preservado")

    assert window._shortcut_stop_speaking() == "break"
    assert speaker.stopped == 0
    assert window.speech_enabled.get()
    assert window.input.get("1.0", "end-1c") == "Texto preservado"


def test_shortcut_stops_only_current_reply_and_ignores_late_event(ui):
    root, window, recognizer, speaker, app = ui
    spin(root, lambda: len(recognizer.started) == 1)
    window.input.insert("1.0", "Primeira pergunta")
    window._send()
    spin(root, lambda: len(speaker.started) == 1)
    old_generation = window._speak_generation

    assert window._shortcut_stop_speaking() == "break"
    assert speaker.stopped == 1
    assert not window._speaking
    assert window.speech_enabled.get()
    assert window.status.cget("text") == "Leitura em voz interrompida"
    spin(root, lambda: len(recognizer.started) == 2)

    window._audio_events.put(("speak_done", "", old_generation))
    root.update()
    assert not window._speaking
    assert window._speak_generation == old_generation + 1

    speaker.started[0].set()
    window.input.insert("1.0", "Segunda pergunta")
    window._send()
    spin(root, lambda: len(speaker.started) == 2)
    assert speaker.spoken[-1] == ("Resposta de teste", "Feminina")
    speaker.started[1].set()


def test_shortcut_keeps_user_paused_microphone_paused(ui):
    root, window, recognizer, speaker, app = ui
    spin(root, lambda: len(recognizer.started) == 1)
    window._toggle_listening()
    spin(root, lambda: not window._listening)
    assert window._say_response("Resposta com microfone pausado")
    spin(root, lambda: len(speaker.started) == 1)

    assert window._shortcut_stop_speaking() == "break"
    assert not window._voice_active
    assert not window._speaking
    assert window.speech_enabled.get()
    root.update()
    assert len(recognizer.started) == 1
    speaker.started[0].set()
