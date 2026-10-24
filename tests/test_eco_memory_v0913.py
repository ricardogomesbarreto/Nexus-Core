"""Limites de memória do desktop sem reduzir o conteúdo do modelo."""

from io import BytesIO
import os

import pytest
from PIL import Image
from PIL.JpegImagePlugin import JpegImageFile

from nexus.vision.local import LocalVision


def test_large_jpeg_uses_reduced_decoder_before_rgb(monkeypatch):
    image = Image.new("RGB", (3000, 2400), "#722f37")
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    calls = []
    original = JpegImageFile.draft

    def tracked(self, mode, size):
        calls.append((mode, size, self.size))
        return original(self, mode, size)

    monkeypatch.setattr(JpegImageFile, "draft", tracked)
    normalized = LocalVision._normalize_image(buffer.getvalue(), max_edge=768)
    assert calls == [("RGB", (768, 768), (3000, 2400))]
    with Image.open(BytesIO(normalized)) as output:
        assert max(output.size) <= 768
        assert output.convert("RGB").getpixel((2, 2))[0] > 100
        assert not output.info


def test_reduced_jpeg_preserves_exif_orientation_without_copying_metadata():
    image = Image.new("RGB", (2400, 1600), "#722f37")
    exif = Image.Exif()
    exif[274] = 6  # Rotate 90 degrees for correct display.
    exif[270] = "private image description"
    buffer = BytesIO()
    image.save(buffer, format="JPEG", exif=exif)
    normalized = LocalVision._normalize_image(buffer.getvalue(), max_edge=768)
    with Image.open(BytesIO(normalized)) as output:
        assert output.height > output.width
        assert max(output.size) <= 768
        assert not output.getexif()
        assert b"private image description" not in normalized


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb")
def test_desktop_transcript_keeps_recent_text_with_a_fixed_cap():
    import tkinter as tk
    from nexus.desktop.window import DesktopWindow

    root = tk.Tk()
    try:
        window = DesktopWindow.__new__(DesktopWindow)
        window.transcript = tk.Text(root, state="disabled")
        for number in range(180):
            window._append("Nexus Core", f"resposta-{number}:" + "x" * 300, "assistant")
        visible = window.transcript.get("1.0", "end-1c")
        assert len(visible) <= window.MAX_VISIBLE_TRANSCRIPT_CHARS
        assert "resposta-0:" not in visible
        assert "resposta-179:" in visible
        window._append("Nexus Core", "y" * 40_000, "assistant")
        assert len(window.transcript.get("1.0", "end-1c")) <= window.MAX_VISIBLE_TRANSCRIPT_CHARS
        assert window.transcript.get("end-2c", "end-1c") == "\n"
    finally:
        root.destroy()
