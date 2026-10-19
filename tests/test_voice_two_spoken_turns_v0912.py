"""A aprovação do teste de voz depende de resposta falada e nova escuta."""
import os
import time
from queue import Empty, Queue
from threading import Event

import pytest


def test_cancelled_voice_playback_cannot_complete_diagnostic(monkeypatch):
    from nexus.desktop import window as module
    events = []
    monkeypatch.setattr(module, "live_event", lambda kind, state, **kwargs:
                        events.append((kind, state)))
    ui = module.DesktopWindow.__new__(module.DesktopWindow)
    ui._speak_generation = 4
    ui._test_voice_speech_generation = 4
    ui._test_voice_turns_remaining = 2
    ui._speaking = True
    class Speaker:
        def stop(self): pass
    ui.speaker = Speaker()
    ui._stop_speaking()
    assert ui._test_voice_speech_generation is None
    assert ui._test_voice_turns_remaining == 2
    assert ("teste", "falhou") in events


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Exige Tk/Xvfb")
def test_two_turns_are_not_credited_until_speech_finishes_and_listening_resumes(monkeypatch):
    import tkinter as tk
    from nexus.agent import AgentOutcome
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop import window as module

    events = []
    monkeypatch.setattr(module, "live_event", lambda event, state, **kwargs:
                        events.append((event, state)))
    utterances = Queue()
    speech_release = Event()
    class Recognizer:
        def recognize_continuous(self, cancelled):
            while not cancelled():
                try: return utterances.get(timeout=0.01)
                except Empty: pass
            return ""
        def stop(self): pass
    class Speaker:
        def speak(self, text, voice):
            speech_release.wait(3)
        def stop(self): speech_release.set()
    class App:
        class Agent:
            def run(self, prompt, **kwargs): return AgentOutcome(True, content="Resposta local.")
        agent = Agent()
        def shutdown(self): pass
    root = tk.Tk()
    confirmation = DesktopConfirmation()
    try:
        ui = module.DesktopWindow(root, App(), confirmation,
                                  speaker=Speaker(), recognizer=Recognizer(),
                                  startup_voice=False)
        ui._start_voice_diagnostic()
        utterances.put("Qual o horário agora?")
        deadline = time.monotonic() + 5
        while not ui._speaking and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert ui._speaking
        assert ui._test_voice_turns_remaining == 2
        assert ("teste", "concluido") not in events
        speech_release.set()
        while ui._test_voice_turns_remaining == 2 and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert ui._test_voice_turns_remaining == 1 and ui._listening
        utterances.put("Que dia é hoje?")
        while ui._test_voice_turns_remaining == 1 and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert ui._test_voice_turns_remaining == 0 and ui._listening
        assert events.count(("teste", "concluido")) == 1
        ui._close()
        while ui._workers_running() and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
    finally:
        speech_release.set()
        confirmation.close()
        try:
            root.destroy()
        except tk.TclError:
            pass
