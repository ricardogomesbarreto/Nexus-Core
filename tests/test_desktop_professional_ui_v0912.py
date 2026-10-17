"""Presentation-only v0.9.12 desktop UX regression tests."""
import os
import time
from types import SimpleNamespace

import pytest

from nexus.desktop.presentation import (
    COLORS, FONT_MAX, FONT_MIN, activity_state, composer_count, message_size,
)


def test_brand_and_accessibility_limits_have_no_system_side_effects():
    assert COLORS.wine == "#722F37"
    assert COLORS.header == "#241c24"
    assert message_size(11, -100) == FONT_MIN
    assert message_size(11, +100) == FONT_MAX
    assert message_size(11, +1) == 12
    assert composer_count(4000) == ("4000 / 4000 caracteres", "Nexus.Counter.TLabel")
    assert composer_count(4001)[1] == "Nexus.CounterOver.TLabel"
    assert activity_state(busy=False, closing=False)[0] == "● PRONTO"
    assert activity_state(busy=True, closing=False)[0] == "● PROCESSANDO"
    assert activity_state(busy=True, closing=True)[0] == "● ENCERRANDO"


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Exige Tk/Xvfb")
def test_modern_tk_layout_works_in_small_window_with_safe_local_controls(monkeypatch):
    import tkinter as tk
    from tkinter import ttk

    from nexus.agent import AgentOutcome
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow

    class Agent:
        calls = 0
        def run(self, prompt, **kwargs):
            self.calls += 1
            return AgentOutcome(True, content="Resposta de teste")

    class App:
        agent = Agent()
        closed = False
        def status(self):
            return SimpleNamespace(database=True)
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
        assert ttk.Style(root).lookup("Nexus.Primary.TButton", "background") == "#722F37"
        assert ttk.Style(root).lookup("Nexus.Card.TFrame", "background") == "#ffffff"
        assert ui.transcript.winfo_height() >= 70
        assert ui.send_button.winfo_ismapped()
        assert ui.activity_badge.cget("text") == "● PRONTO"
        assert ui.quick_guide_button.winfo_ismapped()
        assert "CONVERSA LOCAL" in [
            widget.cget("text") for widget in ui.quick_guide_button.master.winfo_children()
            if isinstance(widget, ttk.Label)
        ]
        for widget in [ui.send_button, ui.composer_counter,
                       ui.activity_badge, ui.quick_guide_button]:
            assert widget.winfo_rootx() >= root.winfo_rootx()
            assert widget.winfo_rootx() + widget.winfo_width() <= root.winfo_rootx() + root.winfo_width() + 2
            assert widget.winfo_rooty() + widget.winfo_height() <= root.winfo_rooty() + root.winfo_height() + 2

        dialogs = []
        monkeypatch.setattr(ui.messagebox, "showinfo",
                            lambda *args, **kwargs: dialogs.append((args, kwargs)))
        ui._show_quick_guide()
        assert "Ctrl+L" in dialogs[0][0][1]
        assert app.agent.calls == 0

        ui._zoom_conversation(1)
        assert ui._conversation_font_size == 12
        ui._zoom_conversation(-100)
        assert ui._conversation_font_size == FONT_MIN
        ui._zoom_conversation(100)
        assert ui._conversation_font_size == FONT_MAX

        ui.input.insert("1.0", "Oi" * 2001)
        ui._refresh_composer_count()
        assert ui.composer_counter.cget("text") == "4002 / 4000 caracteres"
        assert ui.composer_counter.cget("style") == "Nexus.CounterOver.TLabel"
        ui.input.delete("1.0", "end")
        ui._refresh_composer_count()
        assert ui.composer_counter.cget("style") == "Nexus.Counter.TLabel"

        ui._busy = True
        ui._refresh_activity_badge()
        assert ui.activity_badge.cget("text") == "● PROCESSANDO"
        ui._busy = False
        ui._refresh_activity_badge()
        assert ui.activity_badge.cget("text") == "● PRONTO"
        assert app.agent.calls == 0

        ui._append("Você", "Minha mensagem local", "user")
        location = ui.transcript.search("Minha mensagem local", "1.0", "end")
        assert location
        assert "message-user" in ui.transcript.tag_names(location)
        assert ui._focus_composer() == "break"
        root.update()

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
