"""NEXUS CORE microphone activity indicator (four-frame branded PNG).

The indicator is presentation-only. It never opens microphones, stores audio,
interprets speech, or grants permission to any operation. Tk images are created
and updated exclusively on the desktop GUI thread.
"""

from pathlib import Path

FRAME_PIXELS = 80
FRAME_COUNT = 4
DISPLAY_SUBSAMPLE = 2
SPRITE_PATH = Path(__file__).resolve().parents[1] / "assets" / "ui" / "microphone_speaking.png"


def microphone_frame_for_peak(percent: int) -> int:
    """Map the measured PCM peak percentage to idle/low/medium/high frames.

    A nonzero sound level indicates audio activity, NOT successful speech
    transcription. Thresholds damp small background hum in normal rooms.
    """
    if not isinstance(percent, int) or isinstance(percent, bool):
        return 0
    peak = max(0, min(100, percent))
    if peak < 4:
        return 0
    if peak < 20:
        return 1
    if peak < 50:
        return 2
    return 3


class MicrophoneIndicator:
    """Small Tk label using packaged sprite frames; never animates by itself."""

    def __init__(self, parent, *, sprite_path: Path = SPRITE_PATH):
        import tkinter as tk

        self.frames = []
        self.frame_index = 0
        self._label = None

        try:
            # Tk supports PNG directly. Pillow is not needed by voice-only
            # installations and no external files or network are accessed.
            sprite = tk.PhotoImage(master=parent, file=str(sprite_path))
            if (sprite.width(), sprite.height()) != (
                FRAME_PIXELS * FRAME_COUNT, FRAME_PIXELS
            ):
                raise ValueError("Invalid microphone sprite dimensions")

            for index in range(FRAME_COUNT):
                region = tk.PhotoImage(
                    master=parent, width=FRAME_PIXELS, height=FRAME_PIXELS
                )
                region.tk.call(
                    str(region), "copy", str(sprite), "-from",
                    index * FRAME_PIXELS, 0,
                    (index + 1) * FRAME_PIXELS, FRAME_PIXELS,
                    "-to", 0, 0,
                )
                self.frames.append(region.subsample(DISPLAY_SUBSAMPLE))

            self._label = tk.Label(
                parent,
                image=self.frames[0],
                background="#f7f4f5",
                borderwidth=0,
                highlightthickness=0,
                width=FRAME_PIXELS // DISPLAY_SUBSAMPLE,
                height=FRAME_PIXELS // DISPLAY_SUBSAMPLE,
            )
        except (OSError, tk.TclError, ValueError):
            # A corrupt/missing asset must never prevent conversation or audio.
            self.frames = []
            self._label = tk.Label(
                parent, text="🎙", background="#f7f4f5",
                borderwidth=0, font=("Sans", 16),
            )

    @property
    def widget(self):
        return self._label

    def show_peak(self, peak_percent: int, *, listening: bool) -> None:
        """UI-thread only; return to the idle frame whenever listening stops."""
        index = microphone_frame_for_peak(peak_percent) if listening else 0
        if index == self.frame_index:
            return
        self.frame_index = index
        if self.frames:
            self._label.configure(image=self.frames[index])

    def release(self) -> None:
        """Drop references on the Tk thread before destroying the root."""
        if self.frames:
            self._label.configure(image="")
            self.frames.clear()
        self.frame_index = 0
