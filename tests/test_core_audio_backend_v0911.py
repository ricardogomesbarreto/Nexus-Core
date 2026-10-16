"""Select PipeWire/ALSA per NEXUS CORE recognizer, never system-wide."""

import os
from pathlib import Path

import pytest

from nexus.voice.local import LocalRecognizer, VoiceError
import nexus.voice.local as local


def test_audio_backend_selection_keeps_os_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setenv("NEXUS_AUDIO_INPUT", "alsa")
    original_env = os.environ["NEXUS_AUDIO_INPUT"]
    monkeypatch.setattr(local.shutil, "which", lambda binary: "/usr/bin/" + binary)
    monkeypatch.setattr(Path, "is_socket", lambda path: path.name == "pipewire-0")
    auto = LocalRecognizer.capture_command()
    pipewire = LocalRecognizer.capture_command(backend="pipewire")
    alsa = LocalRecognizer.capture_command(backend="alsa")
    assert "arecord" in auto[0]
    assert "pw-record" in pipewire[0]
    assert "--raw" in pipewire
    assert "arecord" in alsa[0]
    assert os.environ["NEXUS_AUDIO_INPUT"] == original_env


def test_requested_missing_pipewire_reports_actionable_error(monkeypatch):
    monkeypatch.setattr(local.shutil, "which", lambda binary: None)
    with pytest.raises(VoiceError, match="PipeWire não está disponível"):
        LocalRecognizer.capture_command(backend="pipewire")


@pytest.mark.parametrize("name", ["", "device1", "soundserver", "../etc"])
def test_backend_rejects_unknown_device_or_untrusted_command(name):
    with pytest.raises(VoiceError, match="automática"):
        LocalRecognizer.capture_command(backend=name)


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb")
def test_gui_mic_selector_changes_only_local_recognizer(monkeypatch):
    import tkinter as tk
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow

    class App:
        agent = object()
        closed = False
        def shutdown(self): self.closed = True
    class FakeSpeaker:
        def speak(self, text, voice): pass
        def stop(self): pass

    root = tk.Tk()
    confirmation = DesktopConfirmation()
    recognizer = LocalRecognizer(model_path="/nonexistent-vosk-test")
    app = App()
    try:
        window = DesktopWindow(root, app, confirmation,
                               speaker=FakeSpeaker(), recognizer=recognizer)
        assert window.audio_input_choice.get() == "Automático"
        window.audio_input_choice.set("ALSA")
        window._select_audio_input()
        assert recognizer.audio_backend == "alsa"
        window.audio_input_choice.set("PipeWire")
        window._select_audio_input()
        assert recognizer.audio_backend == "pipewire"
        assert "PipeWire" in window.status.cget("text")
        window._close()
    finally:
        confirmation.close()
        try: root.destroy()
        except tk.TclError: pass
