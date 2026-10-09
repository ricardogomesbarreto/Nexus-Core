"""Tk audio concurrency regressions and outdated generation safety."""
import os
import time
from threading import Event

import pytest

from nexus.agent import AgentOutcome
from nexus.desktop.confirmation import DesktopConfirmation
from nexus.desktop.window import DesktopWindow


class Agent:
    def run(self, prompt, is_cancelled=None, **kwargs):
        return AgentOutcome(True, content="Resposta de teste")


class App:
    agent = Agent()
    stopped = False

    def shutdown(self):
        self.stopped = True


class ControlledRecognizer:
    def __init__(self):
        self.started = []
        self.stopped = 0

    def recognize_continuous(self, cancelled):
        flag = Event()
        self.started.append(flag)
        while not cancelled() and not flag.is_set():
            time.sleep(0.003)
        return ""

    def stop(self):
        self.stopped += 1


class ControlledSpeaker:
    def __init__(self):
        self.started = []
        self.spoken = []
        self.stopped = 0

    def speak(self, text, voice):
        done = Event()
        self.started.append(done)
        self.spoken.append((text, voice))
        done.wait(timeout=4)

    def stop(self):
        self.stopped += 1


def spin(root, predicate, timeout=5):
    end = time.monotonic() + timeout
    while not predicate() and time.monotonic() < end:
        root.update()
        time.sleep(0.005)
    assert predicate()


@pytest.fixture
def ui():
    if not os.environ.get("DISPLAY"):
        pytest.skip("Tk requires Xvfb")
    import tkinter as tk
    root = tk.Tk()
    app, recognizer, speaker = App(), ControlledRecognizer(), ControlledSpeaker()
    confirm = DesktopConfirmation()
    window = DesktopWindow(root, app, confirm, speaker=speaker, recognizer=recognizer)
    yield root, window, recognizer, speaker, app
    for done in speaker.started:
        done.set()
    for done in recognizer.started:
        done.set()
    if not app.stopped:
        window._close()
        spin(root, lambda: app.stopped)
    confirm.close()
    try:
        root.destroy()
    except tk.TclError:
        pass


def test_paused_then_resumed_audio_never_overlaps_recorder_workers(ui):
    root, window, recognizer, speaker, _ = ui
    spin(root, lambda: len(recognizer.started) == 1)
    previous_generation = window._listen_generation
    window._toggle_listening()
    window._toggle_listening()
    # A cancelled recognizer is still unwinding. Do not launch a second
    # recorder before it reports completion to the GUI thread.
    assert len(recognizer.started) == 1
    spin(root, lambda: len(recognizer.started) == 2)
    active_generation = window._listen_generation
    assert active_generation != previous_generation
    assert window._listening
    # Duplicate, delayed completion from the old generation cannot start
    # a third capture or disarm the one currently active.
    window._audio_events.put(("silence", "", previous_generation))
    root.update()
    assert len(recognizer.started) == 2
    assert window._listening
    assert window._listen_pending_generations == {active_generation}


def test_stale_speech_completion_does_not_unset_new_speaking_state(ui):
    root, window, recognizer, speaker, _ = ui
    spin(root, lambda: len(recognizer.started) == 1)
    window._toggle_listening()
    spin(root, lambda: not window._listening)
    assert window._say_response("Resposta anterior")
    spin(root, lambda: len(speaker.started) == 1)
    previous_generation = window._speak_generation
    window._stop_speaking()
    assert window._say_response("Resposta atual")
    spin(root, lambda: len(speaker.started) == 2)
    # Synthesize delayed completion deterministically, without timing races.
    window._audio_events.put(("speak_done", "", previous_generation))
    root.update()
    assert window._speaking
    speaker.started[0].set()
    assert speaker.spoken == [
        ("Resposta anterior", "Feminina"),
        ("Resposta atual", "Feminina"),
    ]
    speaker.started[1].set()
    spin(root, lambda: not window._speaking)


def test_silencing_mid_response_invalidates_late_tts_event(ui):
    root, window, recognizer, speaker, _ = ui
    spin(root, lambda: len(recognizer.started) == 1)
    window._toggle_listening()
    spin(root, lambda: not window._listening)
    assert window._say_response("Vai ser interrompido")
    spin(root, lambda: len(speaker.started) == 1)
    window.speech_enabled.set(False)
    window._toggle_speech()
    assert not window._speaking
    before = window._speak_generation
    window._audio_events.put(("speak_done", "", before - 1))
    root.update()
    speaker.started[0].set()
    assert window._speak_generation == before
    assert not window._speaking
