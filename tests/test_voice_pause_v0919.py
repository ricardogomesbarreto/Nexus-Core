"""Process-owned Linux pause/resume semantics; no audio hardware required."""
import signal

from nexus.voice.local import LocalSpeaker
from nexus.desktop.window import DesktopWindow


class FakeProcess:
    def __init__(self):
        self.active = True
        self.events = []

    def poll(self):
        return None if self.active else 0

    def send_signal(self, sig):
        self.events.append(sig)

    def terminate(self):
        self.events.append("terminate")
        self.active = False


def test_pause_resume_only_active_owned_process():
    speaker = LocalSpeaker()
    assert speaker.pause() is False
    assert speaker.resume() is False
    process = FakeProcess()
    speaker._set_process(process)
    assert speaker.pause()
    assert process.events == [signal.SIGSTOP]
    assert not speaker.pause()
    assert speaker.resume()
    assert process.events == [signal.SIGSTOP, signal.SIGCONT]
    assert not speaker.resume()
    speaker.stop()
    assert process.events[-1] == "terminate"
    speaker._clear_process(process)
    assert not speaker.pause()


def test_stop_resumes_stopped_process_before_termination():
    speaker = LocalSpeaker()
    process = FakeProcess()
    speaker._set_process(process)
    assert speaker.pause()
    speaker.stop()
    assert process.events == [signal.SIGSTOP, signal.SIGCONT, "terminate"]
    assert not speaker.resume()


def test_finished_process_cannot_receive_pause_signals():
    speaker = LocalSpeaker()
    process = FakeProcess()
    process.active = False
    speaker._set_process(process)
    assert speaker.pause() is False
    assert speaker.resume() is False
    assert process.events == []


def test_main_window_pause_resume_uses_injected_speaker_only():
    calls = []

    class Speaker:
        def pause(self):
            calls.append("pause")
            return True
        def resume(self):
            calls.append("resume")
            return True
        def stop(self):
            calls.append("stop")

    class Status:
        def configure(self, **kwargs):
            calls.append(kwargs["text"])

    ui = DesktopWindow.__new__(DesktopWindow)
    ui._speaking = True
    ui._voice_paused = False
    ui.speaker = Speaker()
    ui.status = Status()
    ui._toggle_pause_voice()
    assert ui._voice_paused is True
    ui._toggle_pause_voice()
    assert ui._voice_paused is False
    assert calls[0] == "pause"
    assert calls[2] == "resume"
    ui._speaking = False
    ui._toggle_pause_voice()
    assert "Nenhuma fala ativa" in calls[-1]
