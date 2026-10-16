"""Microphone activity sprite: packaged image, Tk-only animation and safety."""

import os
import struct
import time

import pytest

from nexus.desktop.microphone_indicator import (
    DISPLAY_SUBSAMPLE,
    FRAME_COUNT,
    FRAME_PIXELS,
    SPRITE_PATH,
    MicrophoneIndicator,
    microphone_frame_for_peak,
)


@pytest.mark.parametrize("level,frame", [
    (-100, 0), (0, 0), (2, 0), (3, 0), (4, 1), (12, 1),
    (19, 1), (20, 2), (42, 2), (49, 2), (50, 3),
    (86, 3), (100, 3), (200, 3),
    (None, 0), (True, 0), ("86", 0),
])
def test_microphone_frames_follow_pcm_peak_only(level, frame):
    assert microphone_frame_for_peak(level) == frame


def test_microphone_sprite_is_packaged_valid_png_with_four_frames():
    assert SPRITE_PATH.is_file()
    payload = SPRITE_PATH.read_bytes()
    assert payload.startswith(b"\x89PNG\r\n\x1a\n")
    width, height = struct.unpack(">II", payload[16:24])
    assert (width, height) == (FRAME_PIXELS * FRAME_COUNT, FRAME_PIXELS)
    assert DISPLAY_SUBSAMPLE == 2


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb Linux")
def test_tk_sprite_renders_four_levels_and_pauses():
    import tkinter as tk

    root = tk.Tk()
    indicator = None
    try:
        indicator = MicrophoneIndicator(root)
        indicator.widget.pack()
        root.update_idletasks()
        assert len(indicator.frames) == 4, "PNG must be usable by Tk without Pillow"
        assert indicator.frames[0].width() == 40
        assert indicator.frames[0].height() == 40
        idle_photo = str(indicator.widget.cget("image"))
        for peak, expected in ((8, 1), (36, 2), (86, 3), (0, 0)):
            indicator.show_peak(peak, listening=True)
            assert indicator.frame_index == expected
            assert str(indicator.widget.cget("image")) == str(indicator.frames[expected])
        indicator.show_peak(95, listening=True)
        indicator.show_peak(95, listening=False)
        assert indicator.frame_index == 0
        assert str(indicator.widget.cget("image")) == idle_photo
    finally:
        if indicator is not None:
            indicator.release()
        root.destroy()


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb Linux")
def test_missing_sprite_falls_back_without_disabling_chat(tmp_path):
    import tkinter as tk

    root = tk.Tk()
    try:
        indicator = MicrophoneIndicator(root, sprite_path=tmp_path / "absent.png")
        indicator.widget.pack()
        indicator.show_peak(86, listening=True)
        assert indicator.frames == []
        assert indicator.widget.cget("text")
        indicator.release()
    finally:
        root.destroy()


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb Linux")
def test_live_gui_consumes_only_current_audio_generation_and_pauses():
    import tkinter as tk

    from nexus.agent import AgentOutcome
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow

    class App:
        def __init__(self):
            self.agent = self
            self.closed = False

        def run(self, prompt, **kwargs):
            return AgentOutcome(True, content="Ok")

        def shutdown(self):
            self.closed = True

    class Recognizer:
        def recognize_continuous(self, cancelled):
            while not cancelled():
                time.sleep(0.01)
            return ""

        def stop(self):
            pass

    class Speaker:
        def speak(self, text, voice):
            pass

        def stop(self):
            pass

    root = tk.Tk()
    confirmation = DesktopConfirmation()
    app = App()
    try:
        window = DesktopWindow(
            root, app, confirmation,
            recognizer=Recognizer(), speaker=Speaker(),
        )
        deadline = time.monotonic() + 5
        while not window._listening and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert window._listening
        generation = window._listen_generation
        window._audio_events.put(("input_level", "86", generation - 1))
        root.update()
        assert window.microphone_indicator.frame_index == 0
        window._audio_events.put(("input_level", "86", generation))
        deadline = time.monotonic() + 5
        while window.microphone_indicator.frame_index != 3 and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert window.microphone_indicator.frame_index == 3
        window._toggle_listening()
        assert not window._voice_active
        assert window.microphone_indicator.frame_index == 0
        window._audio_events.put(("input_level", "90", generation))
        root.update()
        assert window.microphone_indicator.frame_index == 0
        window._close()
        deadline = time.monotonic() + 5
        while not app.closed and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert app.closed
    finally:
        confirmation.close()
        try:
            root.destroy()
        except tk.TclError:
            pass
