"""v0.9.6: stopping TTS during process startup cannot play stale text."""
from queue import Queue

from nexus.desktop.window import DesktopWindow
from nexus.voice import LocalSpeaker
import nexus.voice.local as voice_module

from test_voice_local import FakeProcess


def test_cancelled_request_does_not_spawn_espeak(monkeypatch):
    monkeypatch.setattr(voice_module.subprocess, "Popen",
                        lambda *args, **kwargs: 1 / 0)
    LocalSpeaker().speak("Mensagem antiga", cancelled=lambda: True)


def test_window_stop_during_espeak_startup_terminates_without_sending_text(monkeypatch):
    window = object.__new__(DesktopWindow)
    window._closing = False
    window._speak_generation = 1
    window._audio_events = Queue()
    window.speaker = LocalSpeaker()
    processes = []
    monkeypatch.setattr(voice_module.shutil, "which", lambda name: "/usr/bin/espeak-ng")

    class PendingProcess(FakeProcess):
        def __init__(self, args, **kwargs):
            super().__init__(args, **kwargs)
            self.returncode = None

        def terminate(self):
            super().terminate()
            self.returncode = -15

    def spawn(args, **kwargs):
        process = PendingProcess(args, **kwargs)
        processes.append(process)
        # The UI requested stop after the worker's first generation check,
        # while Popen was starting and before _set_process could register it.
        window._speak_generation += 1
        window.speaker.stop()  # No registered process yet.
        return process

    monkeypatch.setattr(voice_module.subprocess, "Popen", spawn)
    window._speak("Mensagem antiga", "Feminina", 1)

    assert len(processes) == 1
    assert processes[0].terminated
    assert processes[0].input is None
    assert window.speaker._process is None
    assert window._audio_events.get_nowait() == ("speak_done", "", 1)
    assert window._speak_generation == 2
