"""Voice profile: persisted safely, applied locally and opt-in."""
import json
from dataclasses import replace

import pytest

from nexus.desktop.preferences import DesktopPreferences, DesktopPreferenceStore, PreferenceStoreError
from nexus.voice.local import LocalSpeaker, VoiceError
import nexus.voice.local as local_voice


@pytest.mark.parametrize("updates", [
    {"voice_speed_percent": 74}, {"voice_speed_percent": 126},
    {"voice_speed_percent": True}, {"voice_speed_percent": "100"},
    {"voice_volume_percent": 49}, {"voice_volume_percent": 151},
    {"voice_volume_percent": 100.0}, {"voice_volume_percent": False},
])
def test_voice_profile_rejects_unsafe_values(updates):
    with pytest.raises(PreferenceStoreError):
        replace(DesktopPreferences(), **updates).validate()


def test_old_preferences_load_with_safe_defaults(tmp_path):
    path = tmp_path / "prefs.json"
    path.write_text(json.dumps({"version": 1, "preferences": {
        "voice": "Masculina", "speech_enabled": True,
        "wake_required": False, "audio_backend": "auto",
        "listening_enabled": True, "geometry": "980x720",
        "remember_history": True,
    }}), encoding="utf-8")
    old = DesktopPreferenceStore(path).load()
    assert old.voice_speed_percent == old.voice_volume_percent == 100
    old = replace(old, voice_speed_percent=125, voice_volume_percent=75)
    DesktopPreferenceStore(path).save(old)
    assert DesktopPreferenceStore(path).load() == old


def test_espeak_respects_requested_speed_volume_without_shell(monkeypatch):
    commands = []
    class Process:
        returncode = 0
        def poll(self): return 0
        def communicate(self, input=None, timeout=None): return b"", b""
    monkeypatch.setattr(LocalSpeaker, "female_voice_ready", staticmethod(lambda: False))
    monkeypatch.setattr(LocalSpeaker, "neural_voice_ready", classmethod(lambda cls: False))
    monkeypatch.setattr(local_voice.shutil, "which", lambda name: "/usr/bin/espeak-ng")
    def spawn(command, **kwargs):
        commands.append(command)
        return Process()
    monkeypatch.setattr(local_voice.subprocess, "Popen", spawn)
    speaker = LocalSpeaker()
    speaker.speak("Teste", "Feminina", speed=1.25, volume=75)
    assert commands[0][:6] == ["/usr/bin/espeak-ng", "-v", "pt-br+f3", "-b", "1", "--stdin"]
    assert commands[0][6:] == ["-s", "219", "-a", "75"]
    with pytest.raises(VoiceError):
        speaker.speak("Teste", speed=2.0)
    with pytest.raises(VoiceError):
        speaker.speak("Teste", volume=-1)


@pytest.mark.skipif(not __import__("os").environ.get("DISPLAY"),
                    reason="Requer Tk/Xvfb")
def test_profile_controls_persist_on_desktop(monkeypatch, tmp_path):
    import tkinter as tk
    from nexus.agent import AgentOutcome
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow

    class App:
        def __init__(self): self.agent = self
        def run(self, *a, **kw): return AgentOutcome(True, content="Ok")
        def shutdown(self): pass

    class Speaker:
        def speak(self, *a, **kw): pass
        def stop(self): pass

    class Recognizer:
        def recognize_continuous(self, cancelled): return ""
        def stop(self): pass

    prefs = DesktopPreferenceStore(tmp_path / "prefs.json")
    root = tk.Tk()
    confirmation = DesktopConfirmation()
    try:
        window = DesktopWindow(root, App(), confirmation, speaker=Speaker(),
                               recognizer=Recognizer(), preference_store=prefs)
        window.voice_speed_choice.set("125%")
        window.voice_volume_choice.set("75%")
        window._select_voice_profile()
        assert prefs.load().voice_speed_percent == 125
        assert prefs.load().voice_volume_percent == 75
        window._close()
        root.update()
    finally:
        confirmation.close()
        try: root.destroy()
        except tk.TclError: pass
