"""Desktop integration: settings and local history survive Tk restarts."""

import os
import time

import pytest

from nexus.agent import AgentOutcome
from nexus.desktop.chat_archive import ChatArchive
from nexus.desktop.preferences import DesktopPreferenceStore, DesktopPreferences


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb Linux")
def test_voice_and_mic_preferences_survive_full_desktop_restart(tmp_path):
    import tkinter as tk
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow

    pref = DesktopPreferenceStore(tmp_path / "config" / "prefs.json")
    archive = ChatArchive(tmp_path / "state" / "chat.json")

    class App:
        def __init__(self):
            self.agent = self
            self.closed = False
            self.calls = []
        def run(self, prompt, **kwargs):
            self.calls.append(prompt)
            return AgentOutcome(True, content="Uma explicação do Nexus Core.")
        def shutdown(self):
            self.closed = True

    class Recognizer:
        def recognize_continuous(self, cancelled):
            while not cancelled():
                time.sleep(0.01)
            return ""
        def stop(self): pass

    class Speaker:
        def speak(self, text, voice): pass
        def stop(self): pass

    root = tk.Tk()
    confirmation = DesktopConfirmation()
    app = App()
    try:
        window = DesktopWindow(
            root, app, confirmation, speaker=Speaker(),
            recognizer=Recognizer(), preference_store=pref,
            chat_archive=archive,
        )
        assert window.archive_enabled.get()
        window.voice_choice.set("Masculina")
        window._save_desktop_preferences()
        window.speech_enabled.set(False)
        window._toggle_speech()
        window.wake_required.set(True)
        window._toggle_wake()
        window.audio_input_choice.set("ALSA")
        window._select_audio_input()
        window._toggle_listening()  # User pauses mic; persist privacy state.
        assert not window._voice_active
        root.geometry("930x660")
        root.update()
        window.session.ask("Explique computadores")
        window._close()
        deadline = time.monotonic() + 5
        while not app.closed and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert app.closed
    finally:
        confirmation.close()
        try: root.destroy()
        except tk.TclError: pass

    actual = pref.load()
    assert actual == DesktopPreferences(
        voice="Masculina", speech_enabled=False, wake_required=True,
        audio_backend="alsa", listening_enabled=False,
        geometry="930x660", remember_history=True,
    )
    assert len(archive.load()) == 1

    second_root = tk.Tk()
    second_confirmation = DesktopConfirmation()
    second_app = App()
    try:
        second = DesktopWindow(
            second_root, second_app, second_confirmation,
            speaker=Speaker(), recognizer=Recognizer(),
            preference_store=pref, chat_archive=archive,
        )
        second_root.update()
        assert second.voice_choice.get() == "Masculina"
        assert not second.speech_enabled.get()
        assert second.wake_required.get()
        assert second.audio_input_choice.get() == "ALSA"
        assert not second._voice_active
        assert second.mic_button.cget("text") == "Retomar escuta"
        assert second_root.geometry().startswith("930x660")
        assert second.archive_enabled.get()
        assert "Explique computadores" in second.transcript.get("1.0", "end")
        assert "Uma explicação do Nexus Core" in second.transcript.get("1.0", "end")
        assert not second_app.calls  # Restoring preferences never invokes Ollama.
        second._close()
        deadline = time.monotonic() + 5
        while not second_app.closed and time.monotonic() < deadline:
            second_root.update()
            time.sleep(0.01)
        assert second_app.closed
    finally:
        second_confirmation.close()
        try: second_root.destroy()
        except tk.TclError: pass


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb Linux")
def test_history_can_be_disabled_and_cleared_with_confirmation(tmp_path, monkeypatch):
    import tkinter as tk
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow

    class App:
        agent = None
        closed = False
        def __init__(self): self.agent = self
        def run(self, prompt, **kwargs):
            return AgentOutcome(True, content="Resposta local sem ferramentas.")
        def shutdown(self): self.closed = True

    class Recognizer:
        def recognize_continuous(self, cancelled):
            while not cancelled(): time.sleep(0.01)
            return ""
        def stop(self): pass

    class Speaker:
        def speak(self, text, voice): pass
        def stop(self): pass

    pref = DesktopPreferenceStore(tmp_path / "config" / "prefs.json")
    archive = ChatArchive(tmp_path / "state" / "archive.json")
    archive.append("Anterior", "Resposta anterior")
    root = tk.Tk()
    confirmation = DesktopConfirmation()
    app = App()
    try:
        window = DesktopWindow(
            root, app, confirmation, speaker=Speaker(),
            recognizer=Recognizer(), preference_store=pref,
            chat_archive=archive,
        )
        window.archive_enabled.set(False)
        window._toggle_archive()
        assert not window.archive_enabled.get()
        assert not pref.load().remember_history
        window.session.ask("Nova conversa")
        assert len(archive.load()) == 1
        monkeypatch.setattr(window.messagebox, "askyesno", lambda *a, **kw: False)
        window._clear_saved_history()
        assert len(archive.load()) == 1
        monkeypatch.setattr(window.messagebox, "askyesno", lambda *a, **kw: True)
        window._clear_saved_history()
        assert archive.load() == []
        assert window.session.history == []
        window._close()
        deadline = time.monotonic() + 5
        while not app.closed and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert app.closed
    finally:
        confirmation.close()
        try: root.destroy()
        except tk.TclError: pass
