"""Nexus-owned preview is bounded and cannot read outside the tool policy."""

import os
import time
from types import SimpleNamespace

import pytest
from PIL import Image, PngImagePlugin

from nexus.desktop.image_preview import load_image_preview
from nexus.security.paths import PathSecurity
from nexus.tools.base import ToolResult


def policy_for(tmp_path):
    policy = PathSecurity()
    policy.home = tmp_path / "home"
    policy.home.mkdir()
    policy.protected_paths = [policy.home / ".ssh"]
    return policy


def test_preview_is_thumbnail_and_does_not_keep_source_metadata(tmp_path):
    policy = policy_for(tmp_path)
    path = policy.home / "nova.png"
    info = PngImagePlugin.PngInfo()
    info.add_text("GPSInfo", "private")
    Image.new("RGBA", (900, 600), (120, 30, 50, 100)).save(path, pnginfo=info)
    before = path.read_bytes()
    image = load_image_preview(str(path), policy)
    assert image.size == (720, 480)
    assert image.mode == "RGBA"
    assert image.getpixel((2, 2))[3] == 100
    assert "GPSInfo" not in image.info
    assert path.read_bytes() == before


def test_preview_refuses_symlink_outside_and_invalid_image(tmp_path):
    policy = policy_for(tmp_path)
    outside = tmp_path / "outside.png"
    Image.new("RGB", (10, 10)).save(outside)
    link = policy.home / "link.png"
    link.symlink_to(outside)
    with pytest.raises(PermissionError):
        load_image_preview(str(link), policy)
    with pytest.raises(PermissionError):
        load_image_preview(str(outside), policy)
    invalid = policy.home / "invalid.png"
    invalid.write_bytes(b"not an image")
    with pytest.raises(OSError):
        load_image_preview(str(invalid), policy)
    with pytest.raises(ValueError):
        load_image_preview(str(invalid.with_suffix(".svg")), policy)


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb")
def test_preview_button_only_for_successful_created_image(tmp_path):
    import tkinter as tk

    from nexus.agent import AgentOutcome
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow

    policy = policy_for(tmp_path)
    path = policy.home / "criada.png"
    Image.new("RGB", (120, 80), "#722F37").save(path)

    class App:
        security_gate = SimpleNamespace(path_security=policy)
        agent = SimpleNamespace(run=lambda *args, **kwargs: AgentOutcome(True, content="Ok"))
        closed = False

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
        ui = DesktopWindow(root, app, confirmation,
                           speaker=Speaker(), recognizer=Recognizer())
        root.geometry("770x570")
        root.update()
        assert str(ui.preview_image_button.cget("state")) == "disabled"
        ui._remember_created_image(ToolResult(False, "edit_image_local",
                                    data={"path": str(path)}))
        assert str(ui.preview_image_button.cget("state")) == "disabled"
        ui._remember_created_image(ToolResult(True, "create_directory",
                                    data={"path": str(path)}))
        assert str(ui.preview_image_button.cget("state")) == "disabled"
        ui._remember_created_image(ToolResult(True, "image_geometry_local",
                                    data={"path": str(path)}))
        assert str(ui.preview_image_button.cget("state")) == "normal"
        assert ui.preview_image_button.winfo_rootx() + ui.preview_image_button.winfo_width() <= (
            root.winfo_rootx() + root.winfo_width() + 2)
        ui._show_created_image()
        root.update()
        assert ui._created_image_window is not None
        assert ui._created_image_photo is not None
        ui._close_created_image()
        assert ui._created_image_window is None
        ui._close()
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
