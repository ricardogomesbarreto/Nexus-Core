"""PipeWire recorder must remain cancellable and recover from interruptions."""

import io
import json
import os
import sys
import time
import types

import pytest

from nexus.voice import LocalRecognizer
import nexus.voice.local as voice


def fake_vosk(monkeypatch):
    class Decoder:
        def __init__(self, model, rate):
            assert rate == 16000

        def AcceptWaveform(self, frames):
            assert frames
            return True

        def Result(self):
            return json.dumps({"text": "olá nexus"})

    monkeypatch.setitem(sys.modules, "vosk", types.SimpleNamespace(
        Model=lambda path: object(), KaldiRecognizer=Decoder,
    ))


def test_recognizer_polls_real_pcm_fd_and_produces_words(monkeypatch, tmp_path):
    model_dir = tmp_path / "vosk"
    model_dir.mkdir()
    fake_vosk(monkeypatch)
    read_fd, write_fd = os.pipe()
    os.write(write_fd, b"\x00\x10" * 2048)
    os.close(write_fd)

    class Process:
        stdout = os.fdopen(read_fd, "rb", buffering=0)
        stopped = False
        def poll(self):
            return 0 if self.stopped else None
        def terminate(self):
            self.stopped = True
        def wait(self, timeout=None):
            return 0
        def kill(self):
            self.stopped = True

    proc = Process()
    monkeypatch.setattr(voice.subprocess, "Popen", lambda args, **kwargs: proc)
    recognizer = LocalRecognizer(model_dir)
    assert recognizer.recognize_continuous() == "olá nexus"
    assert proc.stopped
    proc.stdout.close()


def test_no_pcm_data_does_not_hold_voice_worker_after_pause(monkeypatch, tmp_path):
    model_dir = tmp_path / "vosk"
    model_dir.mkdir()
    fake_vosk(monkeypatch)

    class Reader:
        def fileno(self): return 109  # Only passed to mocked select
    class Process:
        stdout = Reader()
        stopped = False
        def poll(self): return 0 if self.stopped else None
        def terminate(self): self.stopped = True
        def wait(self, timeout=None): return 0
        def kill(self): self.stopped = True

    proc = Process()
    monkeypatch.setattr(voice.subprocess, "Popen", lambda args, **kwargs: proc)
    polls = []
    def waiting(*args):
        polls.append(args)
        return [], [], []
    monkeypatch.setattr(voice.select, "select", waiting)
    recognizer = LocalRecognizer(model_dir)
    assert recognizer.recognize_continuous(cancelled=lambda: len(polls) >= 2) == ""
    assert len(polls) == 2
    assert polls[0][-1] == .25
    assert proc.stopped


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb")
def test_transient_recording_error_restarts_listening_at_most_twice():
    import tkinter as tk
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow

    class App:
        agent = object()
        closed = False
        def shutdown(self): self.closed = True

    class Recognizer:
        def recognize_continuous(self, cancelled):
            from nexus.voice.local import VoiceError
            raise VoiceError("Não foi possível capturar áudio do microfone.")
        def stop(self): pass

    class Speaker:
        def speak(self, text, voice): pass
        def stop(self): pass

    root = tk.Tk()
    confirmation = DesktopConfirmation()
    app = App()
    try:
        window = DesktopWindow(root, app, confirmation,
                               recognizer=Recognizer(), speaker=Speaker())
        deadline = time.monotonic() + 6
        while window._voice_active and time.monotonic() < deadline:
            root.update()
            time.sleep(.02)
        assert not window._voice_active
        assert window._listen_retries == 2
        assert "Teste PipeWire ou ALSA" in window.transcript.get("1.0", "end")
        assert window.mic_button.cget("text") == "Retomar escuta"
        window._close()
        deadline = time.monotonic() + 5
        while not app.closed and time.monotonic() < deadline:
            root.update()
            time.sleep(.01)
        assert app.closed
    finally:
        confirmation.close()
        try: root.destroy()
        except tk.TclError: pass
