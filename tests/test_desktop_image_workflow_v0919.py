"""The desktop image menu creates a real file only after the usual consent."""

import os
import time
from types import SimpleNamespace

import pytest
from PIL import Image


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb")
def test_desktop_image_menu_rejects_then_creates_private_copy(tmp_path, monkeypatch):
    import tkinter as tk
    from tkinter import filedialog, simpledialog

    from nexus.agent import AgentOutcome
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow
    from nexus.security import AuditLogger, PathSecurity, SecurityGate
    from nexus.tools import EditImageTool, CreateGraphicTool, ToolExecutor, ToolRegistry

    home = tmp_path / "home"
    home.mkdir()
    source = home / "original.png"
    destination = home / "editada.png"
    poster = home / "cartaz.png"
    Image.new("RGB", (24, 16), (80, 40, 20)).save(source)
    before = source.read_bytes()

    policy = PathSecurity()
    policy.home = home
    policy.protected_paths = [home / ".ssh"]
    gate = SecurityGate(path_security=policy, audit_logger=AuditLogger(tmp_path / "audit.log"))
    registry = ToolRegistry()
    registry.register(EditImageTool())
    registry.register(CreateGraphicTool())
    confirmation = DesktopConfirmation()
    executor = ToolExecutor(registry, gate, confirmation)

    class App:
        agent = SimpleNamespace(run=lambda *a, **kw: AgentOutcome(True, content="Ok"))
        security_gate = gate
        tool_executor = executor

        def shutdown(self):
            pass

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
    try:
        ui = DesktopWindow(root, App(), confirmation,
                           speaker=Speaker(), recognizer=Recognizer())
        ui._voice_active = False
        monkeypatch.setattr(filedialog, "askopenfilename", lambda **kw: str(source))
        monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "cinza")
        monkeypatch.setattr(filedialog, "asksaveasfilename", lambda **kw: str(destination))

        def finish():
            deadline = time.monotonic() + 10
            while ui._busy and time.monotonic() < deadline:
                root.update()
                time.sleep(0.01)
            assert not ui._busy

        ui._confirm = lambda request: False
        ui._edit_image_dialog()
        finish()
        assert not destination.exists()
        assert str(ui.preview_image_button.cget("state")) == "disabled"

        ui._confirm = lambda request: True
        ui._edit_image_dialog()
        finish()
        with Image.open(destination) as edited:
            assert edited.size == (24, 16)
            assert len(set(edited.convert("RGB").getpixel((0, 0)))) == 1
        assert source.read_bytes() == before
        assert destination.stat().st_mode & 0o777 == 0o600
        assert str(ui.preview_image_button.cget("state")) == "normal"
        assert ui._created_image_path == str(destination)

        monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "Meu projeto")
        monkeypatch.setattr(filedialog, "asksaveasfilename", lambda **kw: str(poster))
        ui._create_graphic_dialog()
        finish()
        with Image.open(poster) as graphic:
            assert graphic.size == (1200, 675)
        assert poster.stat().st_mode & 0o777 == 0o600
        assert source.read_bytes() == before
        ui._close()
        root.update()
    finally:
        confirmation.close()
        try:
            root.destroy()
        except tk.TclError:
            pass
