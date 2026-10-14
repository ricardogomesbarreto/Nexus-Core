"""v0.9.8: a window-local shortcut shares the speech checkbox policy."""

from test_conversation_audio_reliability import spin, ui


def toggle(root):
    root.update()
    root.event_generate("<Control-Shift-V>", when="tail")
    root.update()


def test_keyboard_toggle_preserves_microphone_and_draft(ui):
    root, window, recognizer, speaker, app = ui
    spin(root, lambda: len(recognizer.started) == 1)
    window.input.insert("1.0", "Rascunho preservado")
    assert root.bind("<Control-Shift-V>")

    toggle(root)
    assert not window.speech_enabled.get()
    assert not window.speech_toggle.instate(("selected",))
    assert window._voice_active and window._listening
    assert window.input.get("1.0", "end-1c") == "Rascunho preservado"
    assert window._privacy_labels[1].cget("text") == "Voz: desativada"
    assert speaker.stopped == 0

    toggle(root)
    assert window.speech_enabled.get()
    assert window._voice_active and window._listening
    assert window._privacy_labels[1].cget("text") == "Voz: habilitada"
    assert speaker.spoken == []


def test_keyboard_mute_stops_current_speech_without_replaying_it(ui):
    root, window, recognizer, speaker, app = ui
    spin(root, lambda: len(recognizer.started) == 1)
    window._toggle_listening()
    spin(root, lambda: not window._listening)
    assert window._say_response("Resposta anterior")
    spin(root, lambda: len(speaker.started) == 1)
    previous_generation = window._speak_generation

    toggle(root)
    assert not window.speech_enabled.get()
    assert not window._speaking
    assert speaker.stopped == 1
    assert window._speak_generation == previous_generation + 1
    assert not window._voice_active

    window._audio_events.put(("speak_done", "", previous_generation))
    root.update()
    assert not window._speaking
    speaker.started[0].set()
    toggle(root)
    assert window.speech_enabled.get()
    assert speaker.spoken == [("Resposta anterior", "Feminina")]
    assert not window._voice_active

    window.voice_choice.set("Masculina")
    assert window._say_response("Próxima resposta")
    spin(root, lambda: len(speaker.started) == 2)
    assert speaker.spoken[-1] == ("Próxima resposta", "Masculina")
    speaker.started[1].set()


def test_keyboard_mute_applies_to_pending_visual_reply(ui, monkeypatch):
    from tkinter import simpledialog
    from threading import Event

    root, window, recognizer, speaker, app = ui
    spin(root, lambda: len(recognizer.started) == 1)

    entered, release = Event(), Event()

    class Vision:
        def screen(self):
            return b"captura-efemera"

        def describe(self, image, *, question):
            entered.set()
            release.wait(timeout=4)
            return {"description": "Descrição visual local."}

    window.vision = Vision()
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "Descreva")
    monkeypatch.setattr(window.messagebox, "askyesno", lambda *a, **kw: True)
    window._vision_screen()
    assert window._busy
    spin(root, entered.is_set)
    toggle(root)
    release.set()
    spin(root, lambda: not window._busy)
    assert "Descrição visual local." in window.transcript.get("1.0", "end")
    assert speaker.spoken == []
    assert not window.speech_enabled.get()


def test_closing_window_does_not_toggle_speech(ui):
    root, window, recognizer, speaker, app = ui
    window._close()
    assert window._shortcut_toggle_speech() == "break"
    assert speaker.spoken == []
