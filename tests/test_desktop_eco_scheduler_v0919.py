"""Idle desktop should not waste CPU polling while voice stays responsive."""
import pytest

from nexus.desktop.eco_scheduler import next_desktop_poll_ms


def test_idle_desktop_polls_without_high_frequency_spin():
    idle = next_desktop_poll_ms(
        busy=False, listening=False, speaking=False,
        camera=False, closing=False, pending_voice=False,
    )
    assert idle == 250
    assert idle > 80


@pytest.mark.parametrize("active", [
    "busy", "listening", "speaking", "camera", "closing", "pending_voice",
])
def test_active_desktop_preserves_fast_voice_and_camera_replies(active):
    flags = dict(busy=False, listening=False, speaking=False,
                 camera=False, closing=False, pending_voice=False)
    flags[active] = True
    assert next_desktop_poll_ms(**flags) == 80


@pytest.mark.skipif(not __import__("os").environ.get("DISPLAY"),
                    reason="Tk/Xvfb não disponível")
def test_window_uses_idle_poll_after_regular_initialization(monkeypatch):
    import tkinter as tk
    from nexus.agent import AgentOutcome
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow

    class App:
        def __init__(self):
            self.agent = self
        def run(self, *args, **kwargs):
            return AgentOutcome(True, content="Ok")
        def shutdown(self):
            return None

    class Speaker:
        def speak(self, *a, **kw): return None
        def stop(self): return None

    class Recognizer:
        def recognize_continuous(self, cancelled): return ""
        def stop(self): return None

    root = tk.Tk()
    confirmation = DesktopConfirmation()
    try:
        app = App()
        window = DesktopWindow(
            root, app, confirmation,
            speaker=Speaker(), recognizer=Recognizer(),
        )
        monkeypatch.setattr(window, "_refresh_network_status",
                            lambda: None)
        assert next_desktop_poll_ms(
            busy=window._busy, listening=window._listening,
            speaking=window._speaking, camera=window._live_camera is not None,
            closing=window._closing,
            pending_voice=bool(window._listen_pending_generations),
        ) == 250
        window._close()
        root.update()
    finally:
        confirmation.close()
        try: root.destroy()
        except tk.TclError: pass
